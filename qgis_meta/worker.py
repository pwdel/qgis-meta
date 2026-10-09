"""Standalone worker; only stdlib plus the native QGIS distribution are imported."""
import json
import platform
import sys
from pathlib import Path


def main(request_path, response_path):
    global app  # Keep QgsApplication alive until all local SIP wrappers are released.
    from qgis.core import (QgsApplication, QgsProject, QgsProviderRegistry, QgsVectorLayer,
        QgsRasterLayer, QgsWkbTypes, QgsMapSettings, QgsRectangle, QgsCoordinateReferenceSystem,
        QgsMapRendererParallelJob, Qgis)
    from qgis.PyQt.QtCore import QSize, QT_VERSION_STR
    from qgis.PyQt.QtGui import QColor
    request = json.loads(Path(request_path).read_text())
    root = Path(request['root']).resolve()
    output = Path(request['output'])
    record = request['registry']
    profile = output / 'profile'
    profile.mkdir(exist_ok=True)
    app = QgsApplication([], False, str(profile))
    app.initQgis()
    project = QgsProject()
    result = {'runtime': {'qgis_version': Qgis.QGIS_VERSION.split('-')[0],
              'python_version': platform.python_version(),
              'platform': platform.system() + '-' + platform.machine(), 'qt_version': QT_VERSION_STR},
              'checks': []}

    def add(cid, state, message, **evidence):
        result['checks'].append({'id': cid, 'status': state, 'message': message, 'evidence': evidence})

    try:
        issues, unsupported, inventory = [], [], []
        if request.get('isolation_source'):
            import errno
            import socket
            source_denied = False
            try:
                with open(request['isolation_source'], 'rb') as source:
                    source.read(1)
            except PermissionError:
                source_denied = True
            except FileNotFoundError:
                source_denied = (platform.system() == 'Linux' and request.get('isolation_method') == 'bwrap'
                                 and request.get('isolation_source_existed', False))
            network_denied = False
            try:
                with socket.socket() as connection:
                    connection.settimeout(0.25)
                    connection.connect(('1.1.1.1', 443))
            except OSError as exc:
                network_denied = exc.errno in {errno.EACCES, errno.EPERM, errno.ENETUNREACH, errno.ENETDOWN}
            isolated = source_denied and network_denied
            add('isolation', 'pass' if isolated else 'blocked',
                'Probed original-file and network denial', source_denied=source_denied, network_denied=network_denied)
            if not isolated:
                add('load', 'blocked', 'Isolation probes did not confirm the required restrictions')
                return
        from preflight import inspect_sources
        source_errors, source_blocks = inspect_sources(root / record['project']['file'], root, record, QgsProviderRegistry.instance())
        if source_errors or source_blocks:
            add('load', 'fail' if source_errors else 'blocked', '; '.join(source_errors) or 'Datasource validation prevents project loading')
            add('dependencies', 'blocked' if source_blocks else 'fail', '; '.join(source_blocks or source_errors))
            add('render', 'blocked', 'Project was not loaded')
            return
        if not project.read(str(root / record['project']['file'])):
            issues.append('QgsProject.read failed')
        if project.crs().authid() != record['project']['crs']:
            issues.append('Project CRS differs from registry')
        layers = project.mapLayers()
        expected = {l['id']: l for l in record['layers']}
        if set(layers) != set(expected):
            issues.append(f'Layer IDs differ: missing={sorted(set(expected)-set(layers))}, unexpected={sorted(set(layers)-set(expected))}')
        assets = {a['id']: a for a in record['assets']}
        declared = {(root / a['path']).resolve() for a in record['assets'] if a['path']}
        for lid, layer in layers.items():
            spec = expected.get(lid)
            if not spec:
                continue
            node = project.layerTreeRoot().findLayer(lid)
            if node is None or node.isVisible() != spec.get('visible', True):
                issues.append(f'{lid}: layer visibility differs from registry')
            if not layer.isValid():
                issues.append(f'{lid}: invalid layer')
                continue
            if layer.providerType() != spec['provider']:
                issues.append(f'{lid}: provider mismatch')
            if layer.crs().authid() != spec['crs']:
                issues.append(f'{lid}: CRS mismatch')
            if layer.providerType() not in {'ogr', 'gdal'}:
                unsupported.append(f'{lid}: provider {layer.providerType()} requires a dedicated validator')
                continue
            uri = QgsProviderRegistry.instance().decodeUri(layer.providerType(), layer.source())
            source = uri.get('path', '')
            actual_path = Path(source).resolve()
            required_paths = {(root / assets[x]['path']).resolve() for x in spec['asset_ids'] if assets[x]['path']}
            if not source or not actual_path.is_relative_to(root) or actual_path not in required_paths:
                issues.append(f'{lid}: datasource outside declared layer assets: {source}')
            item = {'id': lid, 'source': source, 'provider': layer.providerType()}
            if isinstance(layer, QgsVectorLayer):
                count = layer.featureCount()
                item.update(count=count, subset=layer.subsetString())
                if layer.subsetString() != spec['subset']:
                    issues.append(f'{lid}: filter mismatch: expected {spec["subset"]!r}, got {layer.subsetString()!r}')
                bounds = spec['feature_count']
                if not bounds or not bounds['min'] <= count <= bounds['max']:
                    issues.append(f'{lid}: feature count {count} outside {bounds}')
                missing = set(spec['fields']) - {f.name() for f in layer.fields()}
                if missing:
                    issues.append(f'{lid}: missing fields {sorted(missing)}')
                geometry = QgsWkbTypes.displayString(layer.wkbType())
                if geometry != spec['geometry']:
                    issues.append(f'{lid}: geometry {geometry} != {spec["geometry"]}')
                # Ensure providers can actually stream data, not just read cached counts.
                if count > 0 and next(layer.getFeatures(), None) is None:
                    issues.append(f'{lid}: provider cannot read a feature')
                if layer.vectorJoins() or layer.auxiliaryLayer() or layer.editFormConfig().uiForm():
                    unsupported.append(f'{lid}: joins, auxiliary layers or external forms need additional validation')
                renderer = layer.renderer()
                if not renderer:
                    issues.append(f'{lid}: no renderer')
                else:
                    if renderer.type() != 'singleSymbol':
                        unsupported.append(f'{lid}: renderer {renderer.type()} requires expression/dependency validation')
                    from qgis.core import QgsRenderContext
                    for symbol in renderer.symbols(QgsRenderContext()):
                        for sl in symbol.symbolLayers():
                            if sl.dataDefinedProperties().hasActiveProperties():
                                unsupported.append(f'{lid}: active data-defined symbol properties require dependency validation')
                            if sl.layerType() == 'SvgMarker':
                                p = Path(sl.path()).resolve()
                                if p.is_file():
                                    import re
                                    svg = p.read_text()
                                    if re.search(r'(?:href\s*=\s*[\"\'](?!#|data:)|url\(\s*(?!#))', svg):
                                        unsupported.append(f'{lid}: SVG external references need dependency validation')
                                if p not in declared or not p.is_relative_to(root):
                                    issues.append(f'{lid}: SVG is not a declared project asset: {p}')
                            elif sl.layerType() not in {'SimpleMarker', 'SimpleLine', 'SimpleFill'}:
                                unsupported.append(f'{lid}: symbol layer {sl.layerType()} requires dependency validation')
                if layer.labelsEnabled():
                    unsupported.append(f'{lid}: label expression/font/placement acceptance requires an additional validator')
            elif isinstance(layer, QgsRasterLayer):
                if spec['geometry'] != 'Raster' or layer.width() <= 0 or layer.height() <= 0:
                    issues.append(f'{lid}: invalid raster dimensions or expected type')
            inventory.append(item)
        # A preview in the source CRS must not hide an unresolved canvas transform.
        from qgis.core import QgsDatumTransform, QgsCoordinateTransform
        import math
        operations = []
        context = project.transformContext()
        for destination in {project.crs().authid(), record['render']['crs']}:
            target = QgsCoordinateReferenceSystem(destination)
            for layer in layers.values():
                source = layer.crs()
                if source == target:
                    continue
                pair = f'{source.authid()} -> {destination}'
                operation = context.calculateCoordinateOperation(source, target)
                if not operation:
                    issues.append(f'{layer.id()}: missing saved coordinate operation for {pair}')
                    continue
                if context.allowFallbackTransform(source, target):
                    issues.append(f'{layer.id()}: coordinate operation permits fallback for {pair}')
                    continue
                candidates = QgsDatumTransform.operations(source, target)
                selected = next((op for op in candidates if op.proj == operation), None)
                if selected is None or not selected.isAvailable:
                    issues.append(f'{layer.id()}: coordinate operation unavailable or not a supported direct catalog operation for {pair}')
                    continue
                transform = QgsCoordinateTransform(source, target, context)
                try:
                    point = transform.transform(layer.extent().center())
                    if not all(math.isfinite(v) for v in (point.x(), point.y())) or transform.fallbackOperationOccurred():
                        raise ValueError('Nonfinite coordinates or fallback occurred')
                except Exception as exc:
                    issues.append(f'{layer.id()}: coordinate operation failed for {pair}: {exc}')
                operations.append({'layer': layer.id(), 'source': source.authid(),
                                   'destination': destination, 'operation': operation,
                                   'accuracy_metres': selected.accuracy})
        if project.layoutManager().layouts():
            unsupported.append('Print layouts require separate layout export/dependency checks')
        if project.mapThemeCollection().mapThemes():
            unsupported.append('Map themes require theme-specific rendering checks')
        add('load', 'fail' if issues else 'pass', '; '.join(issues) if issues else
            'QGIS loaded all expected layers and verified their data', layers=inventory, coordinate_operations=operations)
        add('dependencies', 'blocked' if unsupported else 'pass', '; '.join(unsupported) if unsupported
            else 'Supported local datasource and symbol dependencies resolved')
        if issues or unsupported:
            add('render', 'blocked', 'Resolve layer failures or unsupported dependencies before rendering')
        else:
            cfg = record['render']
            settings = QgsMapSettings()
            visible = project.layerTreeRoot().checkedLayers()
            settings.setLayers(visible)
            settings.setDestinationCrs(QgsCoordinateReferenceSystem(cfg['crs']))
            settings.setTransformContext(project.transformContext())
            settings.setExtent(QgsRectangle(*cfg['extent']))
            settings.setOutputSize(QSize(cfg['width'], cfg['height']))
            settings.setBackgroundColor(QColor('white'))
            job = QgsMapRendererParallelJob(settings)
            job.start()
            job.waitForFinished()
            errors = [e.message for e in job.errors()]
            image = job.renderedImage()
            pixels = 0
            if not image.isNull():
                for y in range(image.height()):
                    for x in range(image.width()):
                        color = image.pixelColor(x, y)
                        if color.alpha() and (color.red(), color.green(), color.blue()) != (255, 255, 255):
                            pixels += 1
            if not image.save(str(output / 'preview.png')):
                errors.append('Could not write preview')
            if pixels < cfg['minimum_nonbackground_pixels']:
                errors.append(f'Insufficient rendered content: {pixels} nonbackground pixels')
            add('render', 'fail' if errors else 'pass', '; '.join(errors) if errors else
                'Rendered expected extent with nonbackground content', nonbackground_pixels=pixels,
                settings=cfg, visible_layers=[l.id() for l in visible])
    except Exception as exc:
        add('load', 'fail', f'{type(exc).__name__}: {exc}')
    finally:
        Path(response_path).write_text(json.dumps(result, indent=2))
        project.clear()
        # exitQgis runs after this function releases its local SIP wrappers.


if __name__ == '__main__':
    main(*sys.argv[1:])
    app.exitQgis()
