"""Real QGIS worker tests. Set QGIS_META_QGIS_APP or QGIS_META_QGIS_PYTHON."""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_engine import fixture
from qgis_meta.runtime import runtime_environment, run_worker

APP = os.environ.get('QGIS_META_QGIS_APP')
PYTHON = os.environ.get('QGIS_META_QGIS_PYTHON')


@unittest.skipUnless(APP or PYTHON, 'explicit QGIS runtime required')
class QgisRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'map'
        self.record = fixture(self.root)
        asset = self.root / 'data/points.geojson'
        asset.write_text(json.dumps({'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'name': 'synthetic'},
             'geometry': {'type': 'Point', 'coordinates': [0, 0]}}]}))
        self.record['assets'][0]['sha256'] = hashlib.sha256(asset.read_bytes()).hexdigest()
        python, env = runtime_environment(PYTHON, APP)
        script = '''
import sys
from qgis.core import QgsApplication,QgsProject,QgsVectorLayer,Qgis
app=QgsApplication([],False);app.initQgis()
p=QgsProject();l=QgsVectorLayer(sys.argv[1],"Example","ogr")
p.addMapLayer(l);p.setCrs(l.crs());p.setFileName(sys.argv[2]);p.write()
print(l.id())
'''
        out = subprocess.run([python, '-c', script, str(asset), str(self.root / 'maps/map.qgs')],
                             env=env, capture_output=True, text=True, check=True)
        self.record['layers'][0].update(id=out.stdout.strip(), fields=['name'], feature_count={'min':1,'max':1})

    def run_worker(self):
        return run_worker(self.root, self.record, Path(self.temp.name) / 'work', qgis_python=PYTHON, qgis_app=APP)

    def test_real_project_loads_and_renders(self):
        data = self.run_worker()
        checks = {c['id']: c for c in data['checks']}
        self.assertEqual(checks['load']['status'], 'pass', data)
        self.assertEqual(checks['render']['status'], 'pass', data)
        self.assertTrue((Path(self.temp.name) / 'work/preview.png').is_file())

    def test_wrong_filter_is_a_failure(self):
        self.record['layers'][0]['subset'] = '"name" = \'absent\''
        data = self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='fail' and 'filter' in c['message'] for c in data['checks']), data)

    def test_wrong_count_is_a_failure(self):
        self.record['layers'][0]['feature_count'] = {'min': 10, 'max': 10}
        data = self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='fail' for c in data['checks']), data)

    def test_missing_data_fails_qgis_loading(self):
        (self.root / 'data/points.geojson').unlink()
        data = self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='fail' for c in data['checks']), data)

    def test_blank_extent_does_not_pass_render(self):
        self.record['render']['extent'] = [10, 10, 11, 11]
        data = self.run_worker()
        self.assertTrue(any(c['id']=='render' and c['status']=='fail' for c in data['checks']), data)

    def test_virtual_datasource_is_blocked_before_loading(self):
        project = self.root / 'maps/map.qgs'
        import xml.etree.ElementTree as ET
        xml = ET.parse(project)
        xml.find('.//projectlayers/maplayer/datasource').text = '../data/indirect.vrt'
        xml.write(project)
        path = self.root / 'data/indirect.vrt'
        path.write_text('<OGRVRTDataSource/>')
        a = self.record['assets'][0]
        a.update(path='data/indirect.vrt', sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        result = self.run_worker()
        self.assertTrue(any(c['id']=='dependencies' and c['status']=='blocked' for c in result['checks']), result)
        self.assertFalse((Path(self.temp.name) / 'work/preview.png').exists())

    def test_online_provider_is_blocked_before_loading(self):
        import xml.etree.ElementTree as ET
        project = self.root / 'maps/map.qgs'
        xml = ET.parse(project)
        xml.find('.//projectlayers/maplayer/provider').text = 'wms'
        xml.find('.//projectlayers/maplayer/datasource').text = 'type=xyz&url=https://example.invalid/{z}/{x}/{y}.png'
        xml.write(project)
        result = self.run_worker()
        self.assertTrue(any(c['id']=='dependencies' and c['status']=='blocked' for c in result['checks']), result)
        self.assertFalse((Path(self.temp.name) / 'work/preview.png').exists())

    def test_relocation_confirms_source_and_network_are_inaccessible(self):
        import shutil
        copied = Path(self.temp.name) / 'copy'
        shutil.copytree(self.root, copied)
        result = run_worker(copied, self.record, Path(self.temp.name) / 'isolated',
                            qgis_python=PYTHON, qgis_app=APP, isolated_from=self.root)
        # An unavailable host sandbox must block; it cannot silently run without isolation.
        if any(c['status']=='blocked' and c['id']=='load' for c in result['checks']):
            self.assertFalse(any(c['status']=='pass' for c in result['checks']), result)
        else:
            self.assertTrue(any(c['id']=='isolation' and c['status']=='pass' for c in result['checks']), result)

    def test_data_defined_symbol_is_blocked(self):
        python, env = runtime_environment(PYTHON, APP)
        script = '''
import sys
from qgis.core import QgsApplication,QgsProject,QgsProperty,QgsSymbolLayer
app=QgsApplication([],False);app.initQgis()
p=QgsProject();p.read(sys.argv[1]);l=next(iter(p.mapLayers().values()))
sl=l.renderer().symbol().symbolLayer(0)
sl.setDataDefinedProperty(QgsSymbolLayer.Property.PropertySize,QgsProperty.fromExpression('3'))
p.write();p.clear()
'''
        subprocess.run([python,'-c',script,str(self.root/'maps/map.qgs')],env=env,check=True,capture_output=True)
        data=self.run_worker()
        self.assertTrue(any(c['id']=='dependencies' and c['status']=='blocked' for c in data['checks']), data)
