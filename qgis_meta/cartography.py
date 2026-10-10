"""Conservative native-QGIS checks for saved cartographic dependencies."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def check_symbol(symbol, root, declared, errors, blocked, name):
    from qgis.PyQt.QtSvg import QSvgRenderer
    if not symbol:
        errors.append(f'{name}: missing symbol')
        return
    if symbol.dataDefinedProperties().hasActiveProperties():
        blocked.append(f'{name}: data-defined symbol properties require validation')
    for sl in symbol.symbolLayers():
        if sl.paintEffect() and sl.paintEffect().enabled():
            blocked.append(f'{name}: symbol paint effects need validation')
        if sl.dataDefinedProperties().hasActiveProperties():
            blocked.append(f'{name}: data-defined symbol properties require validation')
        kind = sl.layerType()
        if kind == 'SvgMarker':
            path = Path(sl.path()).resolve()
            if not path.is_file() or path not in declared or not path.is_relative_to(root):
                errors.append(f'{name}: SVG missing or outside declared project assets: {path}')
                continue
            raw = path.read_text()
            try:
                tree = ET.fromstring(raw)
            except ET.ParseError:
                errors.append(f'{name}: invalid SVG XML: {path}')
                continue
            # Only standalone vector SVGs. CSS, fonts, images and includes require more checks.
            unsafe = bool(re.search(r'<!DOCTYPE|<!ENTITY|url\s*\(|@import', raw, re.I))
            unsafe |= any(e.tag.split('}')[-1] in {'image', 'text', 'style', 'script', 'foreignObject'}
                          or any(k.split('}')[-1] == 'href' and not v.startswith('#') for k,v in e.attrib.items())
                          for e in tree.iter())
            if unsafe:
                blocked.append(f'{name}: SVG external/rich content requires validation: {path}')
            elif not QSvgRenderer(str(path)).isValid():
                errors.append(f'{name}: SVG cannot be rendered: {path}')
        elif kind not in {'SimpleMarker', 'SimpleLine', 'SimpleFill'}:
            blocked.append(f'{name}: symbol layer {kind} requires dependency validation')
        if not sl.color().isValid():
            errors.append(f'{name}: invalid symbol color')


def check_text(fmt, errors, blocked, name, evidence):
    from qgis.PyQt.QtGui import QFontDatabase, QFontInfo
    family = fmt.font().family()
    resolved = QFontInfo(fmt.font()).family()
    evidence.append({'item': name, 'requested_font': family, 'resolved_font': resolved})
    if not fmt.fontFound() or family.casefold() not in {s.casefold() for s in QFontDatabase.families()} or family.casefold() != resolved.casefold():
        errors.append(f'{name}: missing or substituted font {family!r} -> {resolved!r}')
    if fmt.dataDefinedProperties().hasActiveProperties() or fmt.allowHtmlFormatting() or fmt.background().enabled() or fmt.shadow().enabled() or fmt.mask().enabled() or (fmt.buffer().paintEffect() and fmt.buffer().paintEffect().enabled()):
        blocked.append(f'{name}: rich/data-defined text needs additional validation')
    if not fmt.color().isValid() or not fmt.buffer().color().isValid():
        errors.append(f'{name}: invalid text color')


def check_glyphs(text, font, errors, name):
    """Shape actual text with Qt, including installed fallback fonts; reject tofu."""
    from qgis.PyQt.QtGui import QTextLayout
    from qgis.core import QgsVariantUtils
    if QgsVariantUtils.isNull(text):
        return
    # Shape complete lines so ligatures, combining marks and fallback runs are retained.
    for line in str(text).splitlines():
        if not line.strip():
            continue
        layout = QTextLayout(line, font)
        layout.beginLayout()
        text_line = layout.createLine()
        if text_line.isValid():
            text_line.setLineWidth(1e9)
        layout.endLayout()
        runs = layout.glyphRuns()
        if not runs or any(not run.rawFont().isValid() or 0 in run.glyphIndexes()
                           or 'lastresort' in run.rawFont().familyName().replace(' ', '').casefold()
                           for run in runs):
            errors.append(f'{name}: missing glyph in label text; install a font covering its characters')
            return


def check_labels(layer, errors, blocked, evidence):
    from qgis.core import QgsExpression, QgsVectorLayerSimpleLabeling, Qgis, QgsPalLayerSettings
    labeling = layer.labeling()
    name = layer.id() + ': labels'
    if not isinstance(labeling, QgsVectorLayerSimpleLabeling):
        blocked.append(f'{name}: only simple native labeling supported')
        return
    settings = labeling.settings()
    placement = settings.placementSettings()
    if settings.displayAll or placement.overlapHandling() != Qgis.LabelOverlapHandling.PreventOverlap or placement.allowDegradedPlacement():
        errors.append(f'{name}: label overlap is forbidden; prevent overlap and disable forced/degraded placement')
    if layer.geometryType() == Qgis.GeometryType.Point:
        obstacle = settings.obstacleSettings()
        if not obstacle.isObstacle() or obstacle.factor() < 10:
            errors.append(f'{name}: point symbols must be high-priority label obstacles (factor 10)')
        fmt = settings.format()  # Keep the C++ owner alive for its buffer reference.
        buffer = fmt.buffer()
        clearance = buffer.size() if buffer.enabled() else 0
        if (settings.placement != QgsPalLayerSettings.OrderedPositionsAroundPoint or
            settings.offsetType != QgsPalLayerSettings.FromSymbolBounds or
            Qgis.LabelPredefinedPointPosition.OverPoint in settings.pointSettings().predefinedPositionOrder() or
            settings.distUnits != Qgis.RenderUnit.Millimeters or settings.dist < clearance + 0.2 or
            (buffer.enabled() and buffer.sizeUnit() != Qgis.RenderUnit.Millimeters)):
            errors.append(f'{name}: labels must sit outside point symbol bounds with buffer plus 0.2 mm clearance')
    if (settings.callout() and settings.callout().enabled()) or settings.useSubstitutions:
        blocked.append(f'{name}: callouts or text substitutions need validation')
    if settings.geometryGeneratorEnabled:
        blocked.append(f'{name}: label geometry generators need placement validation')
    if settings.dataDefinedProperties().hasActiveProperties():
        blocked.append(f'{name}: data-defined label settings need validation')
    check_text(settings.format(), errors, blocked, name, evidence)
    if settings.isExpression:
        expr = QgsExpression(settings.fieldName)
        if expr.hasParserError():
            errors.append(f'{name}: invalid label expression')
            return
        # Field/literal/CASE expressions suffice for this release; no functions or variables.
        if expr.referencedFunctions() or expr.referencedVariables():
            blocked.append(f'{name}: label functions/variables require validation')
            return
        missing = expr.referencedColumns() - {f.name() for f in layer.fields()}
        if missing:
            errors.append(f'{name}: missing label fields {sorted(missing)}')
            return
        ctx = layer.createExpressionContext()
        if not expr.prepare(ctx):
            errors.append(f'{name}: label expression cannot prepare')
            return
        for feature in layer.getFeatures():
            ctx.setFeature(feature)
            value = expr.evaluate(ctx)
            if expr.hasEvalError():
                errors.append(f'{name}: label expression failed: {expr.evalErrorString()}')
                break
            check_glyphs(value, settings.format().font(), errors, name)
    elif settings.fieldName not in {f.name() for f in layer.fields()}:
        errors.append(f'{name}: missing label field {settings.fieldName!r}')
    else:
        for feature in layer.getFeatures():
            check_glyphs(feature[settings.fieldName], settings.format().font(), errors, name)


def inspect_layouts(project, root, declared, errors, blocked, fonts):
    from qgis.core import (QgsPrintLayout, QgsLayoutItem, QgsLayoutItemMap,
        QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutItemLabel, QgsLayoutItemScaleBar, QgsLayoutItemPage, QgsBasicNumericFormat, QgsLayoutItemLegend,
        Qgis)
    targets = set()
    for layout in project.layoutManager().layouts():
        if not isinstance(layout, QgsPrintLayout):
            blocked.append('Only native print layouts are supported')
            continue
        if layout.atlas().enabled():
            blocked.append(f'{layout.name()}: feature-driven atlas needs validation')
        if layout.pageCollection().pageCount() == 0:
            errors.append(f'{layout.name()}: no layout pages')
        legends = [i for i in layout.items() if isinstance(i, QgsLayoutItemLegend)]
        def legend_visible(legend, map_item):
            page = layout.pageCollection().page(map_item.page())
            return (legend.linkedMap() == map_item and legend.page() == map_item.page()
                    and legend.isVisible() and legend.effectiveOpacity() > 0
                    and not legend.excludeFromExports() and page is not None
                    and page.sceneBoundingRect().adjusted(-0.5,-0.5,0.5,0.5).contains(legend.sceneBoundingRect()))

        for item in layout.items():
            if not isinstance(item, QgsLayoutItem):
                continue
            name = layout.name() + ':' + type(item).__name__
            if item.dataDefinedProperties().hasActiveProperties():
                blocked.append(f'{name}: data-defined layout item needs validation')
            if isinstance(item, QgsLayoutItemMap):
                targets.add(item.crs().authid())
                if not any(legend_visible(l, item) for l in legends):
                    errors.append(f'{name}: missing visible linked legend on the map page')
                if item.layerStyleOverrides() or item.followVisibilityPreset() or item.atlasDriven() or item.grids().asList() or item.overviews().asList():
                    blocked.append(f'{name}: map overrides/themes/atlas/grids/overviews need validation')
                if not item.keepLayerSet() or not item.layers() or any(l.id() not in project.mapLayers() for l in item.layers()):
                    errors.append(f'{name}: map must reference explicit project layers')
            elif isinstance(item, QgsLayoutItemPicture):
                from qgis.PyQt.QtGui import QImageReader
                path = Path(item.picturePath()).resolve()
                if item.isMissingImage():
                    errors.append(f'{name}: picture cannot render with saved settings')
                if item.clipToItem() and (not isinstance(item.clippingItem(), QgsLayoutItemShape) or item.clippingItem() not in layout.items()):
                    blocked.append(f'{name}: picture clipping requires a native shape in the same layout')
                if not path.is_file() or path not in declared or not path.is_relative_to(root):
                    errors.append(f'{name}: picture missing or outside declared assets')
                elif path.suffix.lower() != '.png':
                    blocked.append(f'{name}: only local PNG layout pictures are supported')
                else:
                    reader = QImageReader(str(path))
                    if bytes(reader.format()).lower() != b'png' or reader.read().isNull():
                        errors.append(f'{name}: picture PNG cannot be decoded')
            elif isinstance(item, QgsLayoutItemShape):
                check_symbol(item.symbol(), root, declared, errors, blocked, name)
            elif isinstance(item, QgsLayoutItemLegend):
                linked = item.linkedMap()
                if not linked or linked not in layout.items() or linked.page() != item.page():
                    errors.append(f'{name}: legend must link to a map on the same page')
                    continue
                if item.legendFilterByMapEnabled() or item.legendFilterOutAtlas() or item.model().layerStyleOverrides():
                    blocked.append(f'{name}: filtered or overridden legends need validation')
                nodes = item.model().rootGroup().findLayers()
                actual = [node.layerId() for node in nodes]
                expected = {layer.id() for layer in linked.layers()}
                if set(actual) != expected or len(actual) != len(expected):
                    errors.append(f'{name}: legend layer coverage differs from linked map')
                components = (Qgis.LegendComponent.Title, Qgis.LegendComponent.Group,
                              Qgis.LegendComponent.Subgroup, Qgis.LegendComponent.SymbolLabel)
                for component in components:
                    style = item.style(component)  # Keep the C++ owner alive for its textFormat reference.
                    check_text(style.textFormat(), errors, blocked, name, fonts)
                check_glyphs(item.title(), item.style(Qgis.LegendComponent.Title).font(), errors, name)
                for node in nodes:
                    layer = node.layer()
                    if not layer or not layer.name().strip():
                        errors.append(f'{name}: legend layer missing or unnamed')
                        continue
                    if any(str(k).startswith('legend/') for k in node.customProperties()):
                        blocked.append(f'{name}: custom legend text/symbol/order needs validation')
                    renderer = getattr(layer, 'renderer', lambda: None)()
                    if not renderer or not hasattr(renderer, 'legendSymbolItems'):
                        blocked.append(f'{name}: legend renderer needs validation')
                        continue
                    entries = item.model().layerLegendNodes(node)
                    if len(entries) != len(renderer.legendSymbolItems()) or not entries:
                        errors.append(f'{name}: legend symbol coverage differs from renderer')
                    check_glyphs(layer.name(), item.style(Qgis.LegendComponent.SymbolLabel).font(), errors, name)
            elif isinstance(item, QgsLayoutItemLabel):
                if item.mode() != QgsLayoutItemLabel.ModeFont or '[%' in item.text():
                    blocked.append(f'{name}: HTML or expression text needs validation')
                check_text(item.textFormat(), errors, blocked, name, fonts)
                if item.mode() == QgsLayoutItemLabel.ModeFont and '[%' not in item.text():
                    check_glyphs(item.text(), item.textFormat().font(), errors, name)
            elif isinstance(item, QgsLayoutItemScaleBar):
                check_text(item.textFormat(), errors, blocked, name, fonts)
                if type(item.numericFormat()) is not QgsBasicNumericFormat:
                    blocked.append(f'{name}: custom numeric format needs validation')
                if not item.linkedMap() or item.style() != 'Single Box':
                    blocked.append(f'{name}: only linked Single Box scale bars supported')
                for method in ('fillSymbol', 'alternateFillSymbol', 'lineSymbol'):
                    check_symbol(getattr(item,method)(),root,declared,errors,blocked,name)
            elif isinstance(item, QgsLayoutItemPage):
                check_symbol(item.pageStyleSymbol(),root,declared,errors,blocked,name)
            else:
                blocked.append(f'{name}: layout item requires dependency validation')
    return targets


def export_layouts(project, output):
    from qgis.core import QgsLayoutExporter, QgsLayoutItemMap
    results, errors = [], []
    for index, layout in enumerate(project.layoutManager().layouts()):
        exporter = QgsLayoutExporter(layout)
        cfg = QgsLayoutExporter.PdfExportSettings(); cfg.dpi = 120
        cfg.rasterizeWholeImage = True
        path = output / f'layout-{index}.pdf'
        if exporter.exportToPdf(str(path),cfg) != QgsLayoutExporter.Success:
            errors.append(f'{layout.name()}: PDF export failed')
        for page in range(layout.pageCollection().pageCount()):
            image = exporter.renderPageToImage(page, dpi=72)
            if image.isNull() or not image.save(str(output/f'layout-{index}-page-{page+1}.png')):
                errors.append(f'{layout.name()}: page {page+1} render failed')
        for item in layout.items():
            if isinstance(item, QgsLayoutItemMap):
                errors.extend(f'{layout.name()}: {error.message}' for error in item.renderingErrors())
        results.append({'name':layout.name(),'pages':layout.pageCollection().pageCount(),'pdf':path.name})
    return results, errors


def check_style_role(layer, role, errors):
    """Enforce declared meaning without guessing from IDs, names or shape."""
    if role is None:
        return
    from qgis.core import QgsVectorLayer, Qgis
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtGui import QPainter
    name = layer.id()
    def fail(detail):
        errors.append(f'{name}: style role {role}: {detail}')
    if role != 'prohibited':
        fail('unknown semantic role')
        return
    if not re.match(r'^NO\b', layer.name()):
        fail('legend caption must begin with NO')
    if not isinstance(layer, QgsVectorLayer) or not layer.renderer() or layer.renderer().type() != 'singleSymbol':
        fail('requires a single-symbol point renderer')
        return
    symbol = layer.renderer().symbol()
    if not symbol or symbol.symbolLayerCount() != 1:
        fail('requires exactly one native X marker')
        return
    sl = symbol.symbolLayer(0)
    if sl.layerType() != 'SimpleMarker' or sl.properties().get('name') != 'cross2':
        fail('requires native cross2 (X) marker')
        return
    if sl.strokeColor().name().lower() != '#b3261e' or sl.strokeColor().alpha() != 255:
        fail('visible X stroke must be opaque #B3261E red')
    if sl.strokeWidthUnit() != Qgis.RenderUnit.Millimeters or sl.strokeWidth() < 0.8:
        fail('X stroke must be at least 0.8 mm')
    if sl.sizeUnit() != Qgis.RenderUnit.Millimeters or sl.size() < 4:
        fail('X size must be at least 4 mm')
    if sl.strokeStyle() != Qt.PenStyle.SolidLine or sl.angle() % 90 != 0:
        fail('X must have a solid stroke and retain X orientation')
    if symbol.opacity() != 1 or layer.opacity() != 1:
        fail('prohibition layer and symbol must be fully opaque')
    if not sl.enabled():
        fail('X marker must be enabled')
    normal = QPainter.CompositionMode.CompositionMode_SourceOver
    if layer.blendMode() != normal or layer.featureBlendMode() != normal:
        fail('prohibition styles require normal blending to preserve red')
