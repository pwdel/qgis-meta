"""Verify georeferencing in exported map pages with the native GDAL runtime."""
import math


def inspect_pdf(path, pages):
    try:
        from osgeo import gdal
    except ImportError:
        return [], ['Native GDAL (osgeo) is required to verify georeferenced PDF output']
    evidence, errors = [], []
    for page in sorted(set(pages)):
        try:
            dataset = gdal.OpenEx(f'PDF:{page + 1}:{path}', gdal.OF_RASTER,
                                  open_options=['DPI=72'])
            if dataset is None:
                raise ValueError('GDAL cannot open exported map page')
            transform = dataset.GetGeoTransform(can_return_null=True)
            projection = dataset.GetProjectionRef()
            gcps = dataset.GetGCPs()
            affine = (bool(projection) and transform is not None
                      and all(math.isfinite(n) for n in transform)
                      and abs(transform[1] * transform[5] - transform[2] * transform[4]) > 0)
            control_points = (bool(dataset.GetGCPProjection()) and len(gcps) >= 3
                              and all(math.isfinite(v) for p in gcps
                                      for v in (p.GCPX, p.GCPY, p.GCPPixel, p.GCPLine)))
            if not (affine or control_points):
                raise ValueError('exported map page lacks usable CRS/georeferencing')
            evidence.append({'page': page + 1, 'crs_wkt': projection or dataset.GetGCPProjection(),
                             'geotransform': transform, 'control_points': len(gcps)})
            dataset = None
        except (RuntimeError, ValueError) as exc:
            errors.append(f'page {page + 1}: georeferenced PDF verification failed: {exc}')
    return evidence, errors


def export_map_pages(layout, output, stem):
    """Export each map page independently; QGIS GeoPDF composition is single-page."""
    from qgis.core import QgsLayoutExporter, QgsLayoutItem, QgsLayoutItemMap, QgsLayoutItemPage
    pages = {item.page() for item in layout.items()
             if isinstance(item, QgsLayoutItemMap) and item.isVisible()
             and not item.excludeFromExports()
             and not layout.pageCollection().page(item.page()).excludeFromExports()}
    evidence, errors = [], []
    for page in sorted(pages):
        clone = layout.clone()
        if clone is None:
            errors.append(f'page {page + 1}: cannot create disposable export layout')
            continue
        kept = []
        for item in list(clone.items()):
            if not isinstance(item, QgsLayoutItem) or isinstance(item, QgsLayoutItemPage):
                continue
            if item.page() == page:
                kept.append((item, item.pagePositionWithUnits()))
            else:
                clone.removeLayoutItem(item)
        for index in reversed(range(clone.pageCollection().pageCount())):
            if index != page:
                clone.pageCollection().deletePage(index)
        for item, position in kept:
            item.attemptMove(position, page=0)
        maps = [item for item, _ in kept if isinstance(item, QgsLayoutItemMap)
                and item.isVisible() and not item.excludeFromExports()]
        clone.setReferenceMap(maps[0])
        cfg = QgsLayoutExporter.PdfExportSettings()
        cfg.dpi = 120
        cfg.rasterizeWholeImage = True
        cfg.appendGeoreference = True
        cfg.writeGeoPdf = True
        cfg.includeGeoPdfFeatures = False
        path = output / f'{stem}-page-{page + 1}.geopdf.pdf'
        exporter = QgsLayoutExporter(clone)
        if exporter.exportToPdf(str(path), cfg) != QgsLayoutExporter.Success:
            errors.append(f'page {page + 1}: GeoPDF export failed')
        else:
            checked, failures = inspect_pdf(path, {0})
            errors.extend(f'layout page {page + 1}: {error}' for error in failures)
            for item in checked:
                item.update(layout_page=page + 1, pdf=path.name)
            evidence.extend(checked)
        # The clone is never added to the project or saved over the source layout.
    return evidence, errors
