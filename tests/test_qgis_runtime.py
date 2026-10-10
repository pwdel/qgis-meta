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

    def configure_transform(self, target='EPSG:32615', save=True, fallback=False, broken=False):
        python, env = runtime_environment(PYTHON, APP)
        script = '''
import sys
from qgis.core import *
app=QgsApplication([],False);app.initQgis()
p=QgsProject();p.read(sys.argv[1]);src=QgsCoordinateReferenceSystem('EPSG:4326');dst=QgsCoordinateReferenceSystem(sys.argv[2]);p.setCrs(dst)
if sys.argv[3]=='True':
 op=QgsDatumTransform.operations(src,dst)[0].proj
 if sys.argv[5]=='True':op='+proj=pipeline +step +proj=hgridshift +grids=missing-test-grid.gsb'
 ctx=p.transformContext();ctx.addCoordinateOperation(src,dst,op,sys.argv[4]=='True');p.setTransformContext(ctx)
p.write();p.clear()
'''
        subprocess.run([python,'-c',script,str(self.root/'maps/map.qgs'),target,str(save),str(fallback),str(broken)],env=env,check=True,capture_output=True)
        self.record['project']['crs']=target

    def test_missing_canvas_transform_fails_even_when_preview_crs_matches_data(self):
        self.configure_transform(target='EPSG:26915',save=False)
        result=self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='fail' and 'coordinate operation' in c['message'] for c in result['checks']),result)

    def test_saved_available_operation_passes(self):
        self.configure_transform(target='EPSG:3857')
        result=self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='pass' for c in result['checks']),result)

    def test_transform_fallback_is_rejected(self):
        self.configure_transform(target='EPSG:3857',fallback=True)
        result=self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='fail' and 'fallback' in c['message'] for c in result['checks']),result)

    def test_unavailable_transform_is_rejected(self):
        self.configure_transform(broken=True)
        result=self.run_worker()
        self.assertTrue(any(c['id']=='load' and c['status']=='fail' and 'coordinate operation' in c['message'] for c in result['checks']),result)

    def edit_project(self, code):
        python, env = runtime_environment(PYTHON, APP)
        script = '''
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QFont,QFontDatabase
app=QgsApplication([],False);app.initQgis()
p=QgsProject();p.read(sys.argv[1]);l=next(iter(p.mapLayers().values()))
'''+code+'\np.write();p.clear()\n'
        subprocess.run([python,'-c',script,str(self.root/'maps/map.qgs')],env=env,check=True,capture_output=True)

    def label_project(self, missing_font=False, invalid_field=False):
        self.edit_project("""
s=QgsPalLayerSettings();s.fieldName=%r
fmt=QgsTextFormat();fmt.setFont(QFont(%r or QFontDatabase.families()[0]));fmt.setSize(10);s.setFormat(fmt)
l.setLabeling(QgsVectorLayerSimpleLabeling(s));l.setLabelsEnabled(True)
""" % ('absent' if invalid_field else 'name', 'MissingFont_qgis_meta_6789' if missing_font else ''))

    def test_native_labels_pass(self):
        self.label_project()
        data=self.run_worker()
        self.assertTrue(all(c['status']=='pass' for c in data['checks']),data)

    def test_missing_label_font_fails(self):
        self.label_project(missing_font=True)
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'font' in c['message'].lower() for c in data['checks']),data)

    def test_missing_label_field_fails(self):
        self.label_project(invalid_field=True)
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'label' in c['message'].lower() for c in data['checks']),data)

    def test_embedded_layout_passes_and_exports(self):
        self.label_project()
        self.layout_with_legend()
        data=self.run_worker()
        self.assertTrue(all(c['status']=='pass' for c in data['checks']),data)
        self.assertTrue((Path(self.temp.name)/'work/layout-0.pdf').is_file())

    def test_declared_missing_svg_fails(self):
        path=self.root/'data/missing.svg'
        self.record['assets'].append(dict(self.record['assets'][0],id='symbol',path='data/missing.svg'))
        self.edit_project("l.renderer().setSymbol(QgsMarkerSymbol([QgsSvgMarkerSymbolLayer(%r)]))" % str(path))
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'SVG' in c['message'] for c in data['checks']),data)

    def svg_project(self, content):
        path=self.root/'data/symbol.svg';path.write_text(content)
        self.record['assets'].append(dict(self.record['assets'][0],id='symbol',path='data/symbol.svg',sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        self.edit_project("l.renderer().setSymbol(QgsMarkerSymbol([QgsSvgMarkerSymbolLayer(%r)]))" % str(path))

    def test_valid_local_svg_passes(self):
        self.svg_project('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><circle cx="5" cy="5" r="4" fill="red"/></svg>')
        data=self.run_worker()
        self.assertTrue(all(c['status']=='pass' for c in data['checks']),data)

    def test_corrupt_local_svg_fails(self):
        self.svg_project('not an svg')
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'SVG' in c['message'] for c in data['checks']),data)

    def test_svg_external_image_is_blocked(self):
        self.svg_project('<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.invalid/a.png"/></svg>')
        data=self.run_worker()
        self.assertTrue(any(c['status']=='blocked' and 'SVG' in c['message'] for c in data['checks']),data)

    def test_missing_layout_font_fails(self):
        self.edit_project('''
layout=QgsPrintLayout(p);layout.initializeDefaults();layout.setName('Bad font')
label=QgsLayoutItemLabel(layout);label.setText('Hello');fmt=QgsTextFormat();fmt.setFont(QFont('MissingFont_qgis_meta_6789'));label.setTextFormat(fmt);layout.addLayoutItem(label);p.layoutManager().addLayout(layout)
''')
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'font' in c['message'].lower() for c in data['checks']),data)

    def test_label_callout_is_blocked(self):
        self.label_project()
        self.edit_project('''
s=l.labeling().settings();callout=QgsBalloonCallout();callout.setEnabled(True)
callout.setMarkerSymbol(QgsMarkerSymbol([QgsSvgMarkerSymbolLayer('/missing/callout.svg')]))
s.setCallout(callout);l.setLabeling(QgsVectorLayerSimpleLabeling(s))
''')
        data=self.run_worker()
        self.assertTrue(any(c['status']=='blocked' and 'callout' in c['message'] for c in data['checks']),data)

    def test_symbol_level_expression_is_blocked(self):
        self.edit_project("l.renderer().symbol().dataDefinedProperties().setProperty(QgsSymbol.Property.Opacity,QgsProperty.fromExpression('missing_field'))")
        data=self.run_worker()
        self.assertTrue(any(c['status']=='blocked' and 'data-defined symbol' in c['message'] for c in data['checks']),data)

    def test_scale_bar_expression_is_blocked(self):
        self.edit_project('''
layout=QgsPrintLayout(p);layout.initializeDefaults();layout.setName('Bad scale')
m=QgsLayoutItemMap(layout);layout.addLayoutItem(m);m.attemptResize(QgsLayoutSize(100,100));m.setLayers([l]);m.setKeepLayerSet(True);m.setCrs(p.crs());m.zoomToExtent(QgsRectangle(-1,-1,1,1))
scale=QgsLayoutItemScaleBar(layout);layout.addLayoutItem(scale);scale.setLinkedMap(m);scale.setStyle('Single Box');scale.setNumericFormat(QgsExpressionBasedNumericFormat());p.layoutManager().addLayout(layout)
''')
        data=self.run_worker()
        self.assertTrue(any(c['status']=='blocked' and 'numeric format' in c['message'] for c in data['checks']),data)

    def test_preview_honors_saved_custom_layer_order(self):
        self.edit_project('''
second=QgsVectorLayer(l.source(),'Second','ogr');second.setId('second_layer');p.addMapLayer(second)
p.layerTreeRoot().setHasCustomLayerOrder(True);p.layerTreeRoot().setCustomLayerOrder([l,second])
''')
        self.record['layers'].append(dict(self.record['layers'][0],id='second_layer'))
        data=self.run_worker()
        render=next(c for c in data['checks'] if c['id']=='render')
        self.assertEqual(render['evidence']['visible_layers'],[self.record['layers'][0]['id'],'second_layer'])

    def test_arbitrary_label_text_is_supported(self):
        path=self.root/'data/points.geojson'
        data=json.loads(path.read_text());data['features'][0]['properties']['name']='Trail alpha 42 — North';path.write_text(json.dumps(data))
        self.label_project()
        result=self.run_worker()
        self.assertTrue(all(c['status']=='pass' for c in result['checks']),result)

    def test_label_missing_glyph_fails(self):
        path=self.root/'data/points.geojson'
        data=json.loads(path.read_text());data['features'][0]['properties']['name']='Trail '+chr(0x10FFFF);path.write_text(json.dumps(data))
        self.label_project()
        result=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'glyph' in c['message'] for c in result['checks']),result)

    def test_expression_label_missing_glyph_fails(self):
        self.label_project()
        self.edit_project("s=l.labeling().settings();s.isExpression=True;s.fieldName=%r;l.setLabeling(QgsVectorLayerSimpleLabeling(s))" % ("'"+chr(0x10FFFF)+"'"))
        result=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'glyph' in c['message'] for c in result['checks']),result)

    def test_layout_label_missing_glyph_fails(self):
        self.edit_project('''
layout=QgsPrintLayout(p);layout.initializeDefaults();layout.setName('Glyph check')
label=QgsLayoutItemLabel(layout);label.setText(chr(0x10FFFF));fmt=QgsTextFormat();fmt.setFont(QFont(QFontDatabase.families()[0]));label.setTextFormat(fmt);layout.addLayoutItem(label);p.layoutManager().addLayout(layout)
''')
        result=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'glyph' in c['message'] for c in result['checks']),result)

    def layout_with_legend(self, include=True, omit_layer=False):
        self.edit_project('''
layout=QgsPrintLayout(p);layout.initializeDefaults();layout.setName('Legend coverage')
m=QgsLayoutItemMap(layout);layout.addLayoutItem(m);m.attemptResize(QgsLayoutSize(100,100));m.setLayers([l]);m.setKeepLayerSet(True);m.setCrs(p.crs());m.zoomToExtent(QgsRectangle(-1,-1,1,1))
'''+('''
legend=QgsLayoutItemLegend(layout);layout.addLayoutItem(legend);legend.setLinkedMap(m);legend.setTitle('Key');legend.setAutoUpdateModel(False);legend.attemptResize(QgsLayoutSize(80,40));legend.attemptMove(QgsLayoutPoint(110,10))
for component in (Qgis.LegendComponent.Title,Qgis.LegendComponent.Group,Qgis.LegendComponent.Subgroup,Qgis.LegendComponent.SymbolLabel):legend.setStyleFont(component,QFont(QFontDatabase.families()[0],10))
'''+('legend.model().rootGroup().removeAllChildren()\n' if omit_layer else '') if include else '')+'''p.layoutManager().addLayout(layout)
''')

    def test_native_legend_covers_map(self):
        self.layout_with_legend()
        data=self.run_worker()
        self.assertTrue(all(c['status']=='pass' for c in data['checks']),data)

    def test_map_without_legend_fails(self):
        self.layout_with_legend(include=False)
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'legend' in c['message'].lower() for c in data['checks']),data)

    def test_legend_missing_map_layer_fails(self):
        self.layout_with_legend(omit_layer=True)
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'legend' in c['message'].lower() for c in data['checks']),data)

    def test_transparent_legend_fails(self):
        self.layout_with_legend()
        self.edit_project("next(i for i in p.layoutManager().layouts()[0].items() if isinstance(i,QgsLayoutItemLegend)).setItemOpacity(0)")
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'legend' in c['message'].lower() for c in data['checks']),data)

    def test_legend_outside_page_fails(self):
        self.layout_with_legend()
        self.edit_project("next(i for i in p.layoutManager().layouts()[0].items() if isinstance(i,QgsLayoutItemLegend)).attemptMove(QgsLayoutPoint(500,50))")
        data=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'legend' in c['message'].lower() for c in data['checks']),data)

    def test_prohibited_style_policy(self):
        self.record['layers'][0]['style_role'] = 'prohibited'
        cases = [
            ({}, 'NO — Access prohibited', True),
            ({'outline_color': '#ffffff'}, 'NO — Access prohibited', False),
            ({'name': 'circle'}, 'NO — Access prohibited', False),
            ({'outline_width': '0.1'}, 'NO — Access prohibited', False),
            ({'angle': '45'}, 'NO — Access prohibited', False),
            ({'size': '2'}, 'NO — Access prohibited', False),
            ({'outline_style': 'no'}, 'NO — Access prohibited', False),
            ({}, 'Access prohibited', False),
        ]
        for changes, caption, valid in cases:
            with self.subTest(changes=changes, caption=caption):
                props = dict(name='cross2', color='#b3261e', outline_color='#b3261e',
                             outline_width='0.8', outline_width_unit='MM', size='4', size_unit='MM')
                props.update(changes)
                self.edit_project(f'l.setName({caption!r}); l.renderer().setSymbol(QgsMarkerSymbol.createSimple({props!r}))')
                result = self.run_worker()
                failures = [c for c in result['checks'] if c['id'] == 'load' and c['status'] == 'fail']
                self.assertEqual(bool(failures), not valid, result)


    def test_unrelated_white_x_has_no_prohibition_policy(self):
        self.edit_project("l.renderer().setSymbol(QgsMarkerSymbol.createSimple({'name':'cross2', 'outline_color':'white'}))")
        result = self.run_worker()
        self.assertFalse(any(c['id'] == 'load' and c['status'] == 'fail' for c in result['checks']), result)

    def test_prohibited_layer_transparency_fails(self):
        self.record['layers'][0]['style_role'] = 'prohibited'
        self.edit_project("l.setName('NO — Access prohibited'); l.setOpacity(0.2); l.renderer().setSymbol(QgsMarkerSymbol.createSimple({'name':'cross2', 'outline_color':'#b3261e', 'outline_width':'0.8', 'size':'4'}))")
        result = self.run_worker()
        self.assertTrue(any(c['id'] == 'load' and c['status'] == 'fail' and 'fully opaque' in c['message'] for c in result['checks']), result)


    def test_prohibited_render_overrides_fail(self):
        self.record['layers'][0]['style_role'] = 'prohibited'
        setup = "l.setName('NO — Access prohibited'); l.renderer().setSymbol(QgsMarkerSymbol.createSimple({'name':'cross2', 'outline_color':'#b3261e', 'outline_width':'0.8', 'size':'4'})); "
        for change in ["l.renderer().symbol().symbolLayer(0).setEnabled(False)",
                       "from qgis.PyQt.QtGui import QPainter; l.setBlendMode(QPainter.CompositionMode.CompositionMode_Difference)"]:
            with self.subTest(change=change):
                self.edit_project(setup + change)
                result = self.run_worker()
                self.assertTrue(any(c['id'] == 'load' and c['status'] == 'fail' for c in result['checks']), result)

    def test_layout_png_dependency(self):
        path=self.root/'data/badge.png'
        self.edit_project(f'''
from qgis.PyQt.QtGui import QImage, QColor
image=QImage(32,32,QImage.Format.Format_ARGB32);image.fill(QColor('blue'));assert image.save({str(path)!r})
layout=QgsPrintLayout(p);layout.initializeDefaults();layout.setName('Badge')
shape=QgsLayoutItemShape(layout);shape.setShapeType(QgsLayoutItemShape.Ellipse);layout.addLayoutItem(shape);shape.attemptResize(QgsLayoutSize(30,30))
picture=QgsLayoutItemPicture(layout);layout.addLayoutItem(picture);picture.attemptResize(QgsLayoutSize(20,20));picture.setPicturePath({str(path)!r});picture.setClippingItem(shape);picture.setClipToItem(True);p.layoutManager().addLayout(layout)
''')
        self.record['assets'].append(dict(self.record['assets'][0],id='badge',kind='image',path='data/badge.png'))
        result=self.run_worker()
        self.assertTrue(all(c['status']=='pass' for c in result['checks']),result)
        self.edit_project("picture=next(i for i in p.layoutManager().layouts()[0].items() if isinstance(i,QgsLayoutItemPicture));picture.setPicturePath(picture.picturePath(),Qgis.PictureFormat.SVG)")
        result=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'picture' in c['message'] for c in result['checks']),result)
        self.edit_project("picture=next(i for i in p.layoutManager().layouts()[0].items() if isinstance(i,QgsLayoutItemPicture));picture.setPicturePath(picture.picturePath(),Qgis.PictureFormat.Raster)")
        self.record['assets'].pop()
        result=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'picture' in c['message'] for c in result['checks']),result)
        self.record['assets'].append(dict(self.record['assets'][0],id='badge',kind='image',path='data/badge.png'))
        path.write_bytes(b'not a PNG')
        result=self.run_worker()
        self.assertTrue(any(c['status']=='fail' and 'picture' in c['message'] for c in result['checks']),result)
