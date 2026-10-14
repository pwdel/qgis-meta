import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qgis_meta'))
from qgis.core import *
from anchors import *
a=QgsApplication([],False);a.initQgis()
l=QgsVectorLayer('Point?crs=EPSG:4326&field=id:string&field=source_lon:double&field=source_lat:double','test','memory')
f=QgsFeature(l.fields());f.setAttributes(['a',-92.7,45.3]);f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-92.6,45.4)));l.dataProvider().addFeatures([f])
s=l.renderer().symbol();g=QgsGeometryGeneratorSymbolLayer.create({'geometryModifier':EXPRESSION,'SymbolType':'Line'});g.setUnits(Qgis.RenderUnit.MapUnits);s.insertSymbolLayer(0,g)
tmp=tempfile.TemporaryDirectory();p=Path(tmp.name)/'source.geojson';p.write_text(json.dumps({'features':[{'properties':{'id':'a'},'geometry':{'coordinates':[-92.7,45.3]}}]}))
e=[];check_anchors(l,p,e);assert not e,e
from qgis.PyQt.QtCore import QPointF
marker=s.symbolLayer(1)
marker.setOffset(QPointF(2,0));e=[];check_anchors(l,p,e);assert any('offset' in x for x in e),e
marker.setOffset(QPointF(0,0));marker.setHorizontalAnchorPoint(QgsMarkerSymbolLayer.HorizontalAnchorPoint.Left)
e=[];check_anchors(l,p,e);assert any('center' in x for x in e),e
marker.setHorizontalAnchorPoint(QgsMarkerSymbolLayer.HorizontalAnchorPoint.Center)
e=[];check_anchors(l,p,e);assert not e,e
fid=next(l.getFeatures()).id();l.dataProvider().changeGeometryValues({fid:QgsGeometry.fromPointXY(QgsPointXY(-92.5,45.2))});e=[];check_anchors(l,p,e);assert not e,e
l.dataProvider().changeAttributeValues({fid:{1:-92.8}});e=[];check_anchors(l,p,e);assert e
l.dataProvider().changeAttributeValues({fid:{1:-92.7}});g.setGeometryExpression('make_line($geometry, $geometry)');e=[];check_anchors(l,p,e);assert e
s.deleteSymbolLayer(0);e=[];check_anchors(l,p,e);assert e
print('PASS: dynamic movement, fixed anchor, anchor tamper, expression tamper, missing connector')
