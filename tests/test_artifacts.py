"""Synthetic, domain-neutral artifact consistency fixtures."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('qgis_meta.artifacts'))
        from qgis_meta.artifacts import run_artifact_checks
        self.run_checks = run_artifact_checks
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fc = {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'id': 'a', 'value': 2},
             'geometry': {'type': 'Point', 'coordinates': [1, 2]}}]}
        self.write('points.json', self.fc)
        self.write('other.json', self.fc)
        self.write('flat.json', self.fc)
        (self.root / 'ids.csv').write_text('id\na\n')
        (self.root / 'page.html').write_text('<script id="data" type="application/json">'+json.dumps(self.fc)+'</script>')
        (self.root / 'map.qgs').write_text('<qgis><projectlayers><maplayer><provider>ogr</provider><datasource>./points.json</datasource></maplayer></projectlayers></qgis>')
        with zipfile.ZipFile(self.root / 'bundle.zip', 'w') as archive:
            archive.write(self.root / 'points.json', 'points.json')
        self.write('manifest.json', {'path': 'points.json', 'bytes': (self.root / 'points.json').stat().st_size,
                                   'sha256': hashlib.sha256((self.root / 'points.json').read_bytes()).hexdigest()})

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def run_one(self, op, **kwargs):
        self.write('qgis-checks.json', {'schema_version': 1, 'project_id': 'synthetic',
                                     'checks': [{'id': 'check', 'op': op, **kwargs}]})
        return self.run_checks(self.root / 'qgis-checks.json')

    def assert_status(self, report, status):
        self.assertEqual(report['scope'], 'artifacts')
        self.assertTrue(report['checks'])
        self.assertEqual(any(c['status'] == 'fail' for c in report['checks']), status == 'fail', report)

    def cases(self):
        ref = {'file': 'points.json'}
        return [
            ('manifest', {'manifest': 'manifest.json', 'base': '.'}),
            ('qgis_sources', {'file': 'map.qgs', 'prefix': './'}),
            ('archive', {'file': 'bundle.zip', 'member': 'points.json', 'equals': 'points.json'}),
            ('json_equal', {'left': ref, 'right': {'file': 'other.json'}}),
            ('json_value', {'source': {'file': 'points.json', 'pointer': '/features/0/properties/value'}, 'value': 2}),
            ('json_length', {'source': {'file': 'points.json', 'pointer': '/features'}, 'length': 1}),
            ('html_json', {'file': 'page.html', 'element_id': 'data', 'source': ref}),
            ('geojson', {'file': 'points.json', 'wgs84': True}),
            ('flattened_features', {'source': ref, 'target': 'flat.json', 'key': 'id'}),
            ('csv_ids', {'file': 'ids.csv', 'column': 'id', 'source': ref, 'key': 'id'})]

    def test_all_operations_pass_and_hash_consumed_files(self):
        for op, args in self.cases():
            with self.subTest(op=op):
                report = self.run_one(op, **args)
                self.assert_status(report, 'pass')
                self.assertIn('qgis-checks.json', report['input_hashes'])
                self.assertGreater(len(report['input_hashes']), 1)
                for name, digest in report['input_hashes'].items():
                    self.assertEqual(digest, hashlib.sha256((self.root / name).read_bytes()).hexdigest())

    def test_every_operation_rejects_corrupt_input(self):
        for op, args in self.cases():
            with self.subTest(op=op):
                path = self.root / 'points.json'
                original = path.read_bytes()
                path.write_text('{bad')
                self.assert_status(self.run_one(op, **args), 'fail')
                path.write_bytes(original)

    def test_schema_rejects_unknown_fields_operations_and_wrong_types(self):
        for op, args in [('unknown', {}), ('geojson', {'file': 'points.json', 'extra': 1}),
                         ('geojson', {'file': 12}), ('json_length', {'source': {'file': 'points.json'}, 'length': -1})]:
            self.assert_status(self.run_one(op, **args), 'fail')
        for checks in [[], [{'id': 'a', 'op': 'geojson', 'file': 'points.json'}] * 2]:
            self.write('qgis-checks.json', {'schema_version': 1, 'project_id': 'synthetic', 'checks': checks})
            self.assert_status(self.run_checks(self.root / 'qgis-checks.json'), 'fail')

    def test_escape_missing_file_and_symlink_are_rejected(self):
        (self.root / 'escape').symlink_to(self.root.parent)
        for name in ['../outside', '/etc/passwd', 'missing', 'escape/outside']:
            self.assert_status(self.run_one('geojson', file=name), 'fail')

    def test_geojson_rejects_bad_geometry_and_nonfinite_numbers(self):
        for geom in [{'type': 'Point', 'coordinates': [200, 2]}, {'type': 'LineString', 'coordinates': [[1, 2]]},
                     {'type': 'Point', 'coordinates': [float('nan'), 2]}, {'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1]]]},
                     {'type': 'Unknown', 'coordinates': []}, {'type': 'Point', 'coordinates': [True, 2]}]:
            self.fc['features'][0]['geometry'] = geom
            self.write('points.json', self.fc)
            self.assert_status(self.run_one('geojson', file='points.json', wgs84=True), 'fail')

    def test_duplicate_ids_and_missing_properties_fail(self):
        self.fc['features'] *= 2
        self.write('points.json', self.fc)
        for op, args in self.cases()[-2:]:
            self.assert_status(self.run_one(op, **args), 'fail')
        (self.root / 'ids.csv').write_text('id\na\na\n')
        self.fc['features'] = self.fc['features'][:1]
        self.write('points.json', self.fc)
        self.assert_status(self.run_one('csv_ids', file='ids.csv', column='id', source={'file': 'points.json'}, key='id'), 'fail')

    def test_html_duplicate_element_and_invalid_json_pointer_fail(self):
        (self.root / 'page.html').write_text('<script id="data">{}</script><script id="data">{}</script>')
        self.assert_status(self.run_one('html_json', file='page.html', element_id='data', source={'file': 'points.json'}), 'fail')
        for pointer in ['/missing', '/features/-1', '/features/01', 'features', '/bad~2']:
            self.assert_status(self.run_one('json_value', source={'file': 'points.json', 'pointer': pointer}, value=None), 'fail')

    def test_manifest_size_hash_and_archive_mismatch_fail(self):
        self.write('manifest.json', {'path': 'points.json', 'bytes': 0, 'sha256': '0' * 64})
        self.assert_status(self.run_one('manifest', manifest='manifest.json', base='.'), 'fail')
        self.write('other.json', {})
        self.assert_status(self.run_one('archive', file='bundle.zip', member='points.json', equals='other.json'), 'fail')

    def test_malformed_configuration_returns_failure(self):
        path = self.root / 'qgis-checks.json'
        path.write_text('{')
        self.assert_status(self.run_checks(path), 'fail')

    def test_flattened_geojson_decodes_nested_properties_and_allows_extra_attributes(self):
        self.fc['features'][0]['properties']['nested'] = {'items': [1, 2]}
        self.write('points.json', self.fc)
        self.fc['features'][0]['properties']['nested'] = '{"items":[1,2]}'
        self.fc['features'][0]['properties']['extra'] = 'generated'
        self.write('flat.json', self.fc)
        args = {'source': {'file': 'points.json'}, 'target': 'flat.json', 'key': 'id'}
        self.assert_status(self.run_one('flattened_features', **args), 'pass')
        self.fc['features'][0]['geometry']['coordinates'] = [3, 4]
        self.write('flat.json', self.fc)
        self.assert_status(self.run_one('flattened_features', **args), 'fail')

    def test_json_boolean_is_not_number(self):
        self.assert_status(self.run_one('json_value', source={'file': 'points.json', 'pointer': '/features/0/properties/value'}, value=True), 'fail')

    def test_archive_crc_is_checked_for_unselected_members(self):
        path = self.root / 'bundle.zip'
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as archive:
            archive.write(self.root / 'points.json', 'points.json')
            archive.writestr('other.txt', 'unique synthetic payload')
        data = path.read_bytes().replace(b'unique synthetic payload', b'broken synthetic payload')
        path.write_bytes(data)
        self.assert_status(self.run_one('archive', file='bundle.zip', member='points.json', equals='points.json'), 'fail')

    def test_qgis_tiff_and_prefix(self):
        (self.root / 'image.tif').write_bytes(b'II*\x00' + b'\x00' * 8)
        (self.root / 'map.qgs').write_text('<qgis><maplayer><provider>gdal</provider><datasource>./image.tif</datasource></maplayer></qgis>')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'pass')
        (self.root / 'image.tif').write_bytes(b'bad image')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'fail')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./data/'), 'fail')

    def test_qgis_provider_options_are_not_part_of_path(self):
        (self.root / 'map.qgs').write_text('<qgis><maplayer><provider>ogr</provider><datasource>./points.json|layername=points</datasource></maplayer></qgis>')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'pass')

    def test_json_overflow_is_rejected(self):
        (self.root / 'other.json').write_text('{"value": 1e400}')
        self.assert_status(self.run_one('json_length', source={'file': 'other.json'}, length=1), 'fail')

    def test_inputs_are_rechecked_after_last_operation(self):
        from unittest.mock import patch
        import qgis_meta.artifacts as artifacts
        original = artifacts._check

        def mutate_after_check(inputs, check):
            original(inputs, check)
            (self.root / 'points.json').write_text('{}')

        with patch.object(artifacts, '_check', side_effect=mutate_after_check):
            report = self.run_one('geojson', file='points.json')
        self.assert_status(report, 'fail')
        self.assertTrue(any('changed' in check['message'] for check in report['checks']))

    def test_standard_qgis_doctype_is_accepted_but_entities_are_rejected(self):
        path = self.root / 'map.qgs'
        path.write_text('<?xml version="1.0"?><!DOCTYPE qgis PUBLIC "http://mrcc.com/qgis.dtd" "SYSTEM"><qgis><maplayer><provider>ogr</provider><datasource>./points.json</datasource></maplayer></qgis>')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'pass')
        path.write_text('<!DOCTYPE qgis [<!ENTITY source "./points.json">]><qgis><maplayer><provider>ogr</provider><datasource>&source;</datasource></maplayer></qgis>')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'fail')

    def test_qgis_unsupported_or_mismatched_provider_fails(self):
        for provider in ['unsupported', 'gdal', '']:
            (self.root / 'map.qgs').write_text('<qgis><maplayer><provider>'+provider+'</provider><datasource>./points.json</datasource></maplayer></qgis>')
            self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'fail')

    def test_json_length_requires_array(self):
        for pointer, length in [('', 2), ('/type', 17)]:
            self.assert_status(self.run_one('json_length', source={'file': 'points.json', 'pointer': pointer}, length=length), 'fail')

    def test_corrupt_lzma_archive_returns_structured_failure(self):
        import struct
        path = self.root / 'bundle.zip'
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_LZMA) as archive:
            archive.write(self.root / 'points.json', 'points.json')
            info = archive.getinfo('points.json')
        data = bytearray(path.read_bytes())
        name_length, extra_length = struct.unpack_from('<HH', data, info.header_offset + 26)
        payload_offset = info.header_offset + 30 + name_length + extra_length
        data[payload_offset + 4] ^= 255
        path.write_bytes(data)
        self.assert_status(self.run_one('archive', file='bundle.zip', member='points.json', equals='points.json'), 'fail')

    def test_unknown_xml_encoding_is_structured_failure(self):
        (self.root / 'map.qgs').write_bytes(b'<?xml version="1.0" encoding="invalid-encoding"?><qgis/>')
        self.assert_status(self.run_one('qgis_sources', file='map.qgs', prefix='./'), 'fail')
