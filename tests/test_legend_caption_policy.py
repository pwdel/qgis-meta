import os,subprocess,unittest
from pathlib import Path
from qgis_meta.runtime import runtime_environment

@unittest.skipUnless(os.environ.get('QGIS_META_QGIS_APP'),'explicit QGIS runtime required')
class LegendCaptionTests(unittest.TestCase):
 def test_caption_policy(self):
  py,env=runtime_environment(qgis_app=os.environ['QGIS_META_QGIS_APP'])
  script='''
from qgis.core import *
from qgis_meta.cartography import check_legend_label_repetition
app=QgsApplication([],False);app.initQgis()
p=QgsProject();l=QgsVectorLayer('Point?crs=EPSG:4326&field=name:string','Gate — may be locked','memory');p.addMapLayer(l)
f=QgsFeature(l.fields());f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(0,0)));f['name']='GATE: may be locked';l.dataProvider().addFeatures([f])
settings=QgsPalLayerSettings();settings.fieldName='name';l.setLabeling(QgsVectorLayerSimpleLabeling(settings));l.setLabelsEnabled(True)
layout=QgsPrintLayout(p);layout.initializeDefaults();m=QgsLayoutItemMap(layout);layout.addLayoutItem(m);m.setLayers([l]);legend=QgsLayoutItemLegend(layout);layout.addLayoutItem(legend);legend.setLinkedMap(m)
errors=[];check_legend_label_repetition(m,legend,errors);assert errors,'Repeated legend caption must fail'
settings.isExpression=True;settings.fieldName="'Osceola'";l.setLabeling(QgsVectorLayerSimpleLabeling(settings));errors=[];check_legend_label_repetition(m,legend,errors);assert not errors,errors
settings.fieldName="'7'";l.setLabeling(QgsVectorLayerSimpleLabeling(settings));errors=[];check_legend_label_repetition(m,legend,errors);assert not errors,errors
l.setCustomProperty('qgis_meta/label_role','legend-caption');settings.fieldName="'Potentially locked gate'";l.setLabeling(QgsVectorLayerSimpleLabeling(settings));errors=[];check_legend_label_repetition(m,legend,errors);assert errors,'Declared captions must not reappear even with different words'
settings.fieldName="''";l.setLabeling(QgsVectorLayerSimpleLabeling(settings));errors=[];check_legend_label_repetition(m,legend,errors);assert not errors,errors
l.setLabelsEnabled(False);errors=[];check_legend_label_repetition(m,legend,errors);assert not errors,errors
p.clear();app.exitQgis()
'''
  script='import sys;sys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[1]))+')\n'+script
  result=subprocess.run([py,'-c',script],env=env,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
