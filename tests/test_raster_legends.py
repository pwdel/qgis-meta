"""Exercise native raster legend support, including invalid color ranges."""
import os, subprocess, unittest
from pathlib import Path
from qgis_meta.runtime import runtime_environment

@unittest.skipUnless(os.environ.get('QGIS_META_QGIS_APP'), 'explicit QGIS runtime required')
class RasterLegendTests(unittest.TestCase):
 def test_native_raster_legend_ranges(self):
  py,env=runtime_environment(qgis_app=os.environ['QGIS_META_QGIS_APP'])
  script='''
from qgis.core import *
from qgis.PyQt.QtGui import QColor
from qgis_meta.cartography import check_raster_legend
from osgeo import gdal
import tempfile
from pathlib import Path
app=QgsApplication([],False);app.initQgis()
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'data.tif';d=gdal.GetDriverByName('GTiff').Create(str(f),2,2,1,gdal.GDT_Byte);d.GetRasterBand(1).Fill(50);d=None
 l=QgsRasterLayer(str(f),'Raster');p=QgsProject();p.addMapLayer(l)
 layout=QgsPrintLayout(p);layout.initializeDefaults();legend=QgsLayoutItemLegend(layout);layout.addLayoutItem(legend);legend.setAutoUpdateModel(False);legend.model().rootGroup().removeAllChildren();node=legend.model().rootGroup().addLayer(l)
 errors=[];blocked=[];check_raster_legend(l,legend.model().layerLegendNodes(node),errors,blocked,'gray');assert not errors and not blocked,(errors,blocked)
 shader=QgsRasterShader(0,100);ramp=QgsColorRampShader(0,100);ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(0,QColor('white'),'0%'),QgsColorRampShader.ColorRampItem(100,QColor('green'),'100%')]);shader.setRasterShaderFunction(ramp);r=QgsSingleBandPseudoColorRenderer(l.dataProvider(),1,shader);l.setRenderer(r)
 errors=[];blocked=[];check_raster_legend(l,[object()],errors,blocked,'invalid');assert errors,'NaN classification endpoints must fail'
 r.setClassificationMin(0);r.setClassificationMax(100);errors=[];check_raster_legend(l,[object()],errors,blocked,'valid');assert not errors and not blocked,(errors,blocked)
 errors=[];check_raster_legend(l,[],errors,blocked,'empty');assert errors,'Empty legend must fail'
 p.clear()
app.exitQgis()
'''
  script='import sys;sys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[1]))+')\n'+script
  result=subprocess.run([py,'-c',script],env=env,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
