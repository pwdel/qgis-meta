import json
import tempfile
import unittest
from pathlib import Path
from qgis_meta.preflight import inspect_sources

class Providers:
    def decodeUri(self, provider, source):
        return {'path': source.split('|')[0]}

class SourcePathTests(unittest.TestCase):
    def test_every_native_project_requires_sources_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve(); (root/'sources').mkdir()
            for name in ('sources/points.geojson','points.geojson'):
                (root/name).write_text(json.dumps({'type':'FeatureCollection','features':[]}))
            record={'assets':[{'path':name} for name in ('sources/points.geojson','points.geojson')]}
            for source, passes in [('./sources/points.geojson',True),('./points.geojson',False),
                                    ('./sources/../points.geojson',False), (str(root/'sources/points.geojson'),False)]:
                project=root/'map.qgs'
                project.write_text('<qgis><projectlayers><maplayer><id>test</id><provider>ogr</provider><datasource>'+source+'</datasource></maplayer></projectlayers></qgis>')
                errors,blocked=inspect_sources(project,root,record,Providers())
                self.assertEqual(not errors and not blocked,passes,(source,errors,blocked))
