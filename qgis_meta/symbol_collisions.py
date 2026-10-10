"""Conservative point-marker bounds checks at each saved layout map scale."""
def marker_boxes(map_item, project, blocked):
    from qgis.core import QgsVectorLayer, Qgis, QgsRenderContext, QgsCoordinateTransform
    from qgis.PyQt.QtCore import QSizeF, QPointF, QRectF
    # Ten painter units per millimetre; native bounds include marker offsets/strokes.
    size=map_item.layout().renderContext().measurementConverter().convert(map_item.sizeWithUnits(),Qgis.LayoutUnit.Millimeters)
    settings=map_item.mapSettings(map_item.extent(),QSizeF(size.width()*10,size.height()*10),254,True)
    context=QgsRenderContext.fromMapSettings(settings)
    viewport=QRectF(0,0,settings.outputSize().width(),settings.outputSize().height())
    boxes=[]
    for layer in map_item.layers():
        if not isinstance(layer,QgsVectorLayer) or layer.geometryType()!=Qgis.GeometryType.Point:
            continue
        if not layer.isInScaleRange(map_item.scale()):
            continue
        renderer=layer.renderer()
        if renderer.type()!='singleSymbol':
            blocked.append(f'{layer.id()}: symbol collision bounds require a single-symbol renderer')
            continue
        from anchors import is_connector
        symbol=renderer.symbol().clone()
        for i in reversed(range(symbol.symbolLayerCount())):
            if is_connector(symbol.symbolLayer(i)):symbol.deleteSymbolLayer(i)
        transform=QgsCoordinateTransform(layer.crs(),map_item.crs(),project)
        symbol.startRender(context,layer.fields())
        try:
            for feature in layer.getFeatures():
                geometry=feature.geometry()
                if geometry.isNull() or geometry.isEmpty():continue
                if geometry.isMultipart():
                    blocked.append(f'{layer.id()}: multipart marker collision bounds need validation')
                    continue
                xy=transform.transform(geometry.asPoint())
                point=settings.mapToPixel().transform(xy)
                box=symbol.bounds(QPointF(point.x(),point.y()),context,feature)
                if not box.isValid():
                    blocked.append(f'{layer.id()}: unavailable symbol collision bounds')
                elif viewport.intersects(box):
                    boxes.append((f'{layer.id()}:{feature.id()}',box.intersected(viewport)))
        finally:
            symbol.stopRender(context)
    return boxes

def check_symbol_collisions(map_item, project, errors, blocked):
    boxes=marker_boxes(map_item,project,blocked)
    for index,(name,box) in enumerate(boxes):
        for other,other_box in boxes[:index]:
            # A 0.2 mm gap between conservative rectangular footprints.
            if box.adjusted(-1,-1,1,1).intersects(other_box.adjusted(-1,-1,1,1)):
                errors.append(f'page {map_item.page()+1}: symbol collision {other} / {name}')
