"""Fixed GPS anchors for point-attached connector symbols (WGS84 layers)."""
import json
EXPRESSION = 'make_line(make_point("source_lon", "source_lat"), $geometry)'

def is_connector(sl):
    from qgis.core import Qgis
    return (sl.layerType() == 'GeometryGenerator' and sl.geometryExpression() == EXPRESSION
            and sl.symbolType() == Qgis.SymbolType.Line and sl.units() == Qgis.RenderUnit.MapUnits
            and sl.enabled())

def check_anchors(layer, source, errors):
    from qgis.core import QgsVectorLayer, QgsExpression, QgsFeature, QgsGeometry, QgsPointXY
    def fail(message): errors.append(f'{layer.id()}: anchored connector: {message}')
    if not isinstance(layer, QgsVectorLayer) or layer.crs().authid() != 'EPSG:4326' or layer.renderer().type() != 'singleSymbol':
        fail('requires a WGS84 single-symbol point layer');return
    generated=[s for s in layer.renderer().symbol().symbolLayers() if s.layerType()=='GeometryGenerator']
    if len(generated)!=1 or not is_connector(generated[0]):
        fail('missing or modified point-attached GPS connector');return
    try:
        features=json.loads(source.read_text())['features']
        originals={f['properties']['id']:f['geometry']['coordinates'] for f in features}
        if len(originals)!=len(features):raise ValueError('duplicate source IDs')
        for f in layer.getFeatures():
            anchor=originals[f['id']]
            if abs(float(f['source_lon'])-anchor[0])>1e-9 or abs(float(f['source_lat'])-anchor[1])>1e-9:
                fail(f"{f['id']}: GPS anchor differs from registered source")
            ctx=layer.createExpressionContext();expr=QgsExpression(EXPRESSION)
            for dx in (0,0.001):
                moved=QgsFeature(f);xy=f.geometry().asPoint();target=QgsPointXY(xy.x()+dx,xy.y())
                moved.setGeometry(QgsGeometry.fromPointXY(target));ctx.setFeature(moved)
                line=expr.evaluate(ctx).asPolyline()
                if len(line)!=2 or line[0].distance(QgsPointXY(*anchor))>1e-9 or line[1].distance(target)>1e-9:
                    fail(f"{f['id']}: connector does not follow symbol with fixed GPS anchor")
    except (KeyError,ValueError,TypeError,AttributeError) as exc:
        fail(f'invalid anchor data: {exc}')
