"""Tests of observable validator behavior against disposable project directories."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'maps').mkdir()
    (root / 'data').mkdir()
    (root / 'maps/map.qgs').write_text('<qgis/>')
    asset = root / 'data/points.geojson'
    asset.write_text(json.dumps({'type': 'FeatureCollection', 'features': []}))
    record = json.loads((ROOT / 'templates/qgis-registry.example.json').read_text())
    record.update(schema_version=2, governance_revision=subprocess.check_output(
        ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip())
    record['project'].update(file='maps/map.qgs', id='example-map')
    record['render'] = {'extent': [-1, -1, 1, 1], 'crs': 'EPSG:4326',
                        'width': 320, 'height': 240, 'minimum_nonbackground_pixels': 1}
    record['tests'] = []
    for package in record['packages']:
        package.update(status='not-used', reason='Not required for this synthetic fixture.',
                       test_ids=[], purposes=[])
    record['assets'] = [{'id': 'points', 'kind': 'data', 'path': 'data/points.geojson',
        'sha256': hashlib.sha256(asset.read_bytes()).hexdigest(),
        'source_url': 'https://example.org/data', 'license_url': 'https://example.org/license',
        'attribution': 'Synthetic fixture', 'acquired_on': None, 'offline_required': True,
        'acquisition_recipe': None}]
    record['layers'] = [{'id': 'points', 'asset_ids': ['points'], 'provider': 'ogr',
        'crs': 'EPSG:4326', 'geometry': 'Point', 'fields': [], 'feature_count': {'min': 0, 'max': 0},
        'subset': ''}]
    (root / 'requirements-qgis.lock.txt').write_text('# Native QGIS only; no pip dependencies\n')
    (root / 'qgis-registry.json').write_text(json.dumps(record))
    return record


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('qgis_meta'), 'shared validation engine is missing')
        from qgis_meta import validate
        self.validate = validate
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, record, root=None):
        ((root or self.root) / 'qgis-registry.json').write_text(json.dumps(record))

    def findings(self, report):
        return [c for p in report['projects'] for c in p['checks']] + report['checks']

    def test_empty_repository_is_blocked(self):
        report = self.validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 2)
        self.assertTrue(any('No registered' in c['message'] for c in report['checks']))

    def test_unregistered_project_fails(self):
        (self.root / 'orphan.qgs').write_text('<qgis/>')
        report = self.validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 1)

    def test_directory_and_registry_inputs_agree(self):
        fixture(self.root)
        a = self.validate(str(self.root), mode='static')
        b = self.validate(self.root / 'qgis-registry.json', mode='static')
        self.assertEqual(a['projects'][0]['project_id'], b['projects'][0]['project_id'])
        self.assertEqual(a['exit_code'], 2)  # static cannot certify runtime
        self.assertTrue(any(c['id'] == 'assets' and c['status'] == 'pass' for c in self.findings(a)))

    def test_missing_asset_fails_without_repair(self):
        fixture(self.root)
        (self.root / 'data/points.geojson').unlink()
        report = self.validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 1)
        self.assertFalse((self.root / 'data/points.geojson').exists())

    def test_wrong_hash_fails(self):
        r = fixture(self.root)
        r['assets'][0]['sha256'] = '0' * 64
        self.save(r)
        self.assertEqual(self.validate(self.root, mode='static')['exit_code'], 1)

    def test_duplicate_asset_ids_fail(self):
        r = fixture(self.root)
        r['assets'].append(copy.deepcopy(r['assets'][0]))
        self.save(r)
        self.assertEqual(self.validate(self.root, mode='static')['exit_code'], 1)

    def test_unknown_layer_asset_fails(self):
        r = fixture(self.root)
        r['layers'][0]['asset_ids'] = ['missing']
        self.save(r)
        self.assertEqual(self.validate(self.root, mode='static')['exit_code'], 1)

    def test_external_symlink_fails(self):
        r = fixture(self.root)
        (self.root / 'data/points.geojson').unlink()
        (self.root / 'data/points.geojson').symlink_to(ROOT / 'README.md')
        self.assertEqual(self.validate(self.root, mode='static')['exit_code'], 1)

    def test_reversed_feature_bounds_fail(self):
        r = fixture(self.root)
        r['layers'][0]['feature_count'] = {'min': 5, 'max': 1}
        self.save(r)
        self.assertEqual(self.validate(self.root, mode='static')['exit_code'], 1)

    def test_malformed_json_is_reported(self):
        (self.root / 'qgis-registry.json').write_text('{')
        self.assertEqual(self.validate(self.root, mode='static')['exit_code'], 1)

    def test_multiple_projects_aggregate(self):
        fixture(self.root / 'one')
        r = fixture(self.root / 'two')
        r['project']['id'] = 'second-map'
        self.save(r, self.root / 'two')
        (self.root / 'two/data/points.geojson').unlink()
        report = self.validate(self.root, mode='static')
        self.assertEqual(len(report['projects']), 2)
        self.assertEqual(report['exit_code'], 1)

    def test_missing_qgis_runtime_is_blocked(self):
        fixture(self.root)
        report = self.validate(self.root, qgis_python='/not/a/python')
        self.assertEqual(report['exit_code'], 2)
        self.assertTrue(any(c['status'] == 'blocked' and c['id'] == 'load' for c in self.findings(report)))

    def test_unknown_required_adapter_does_not_pass(self):
        r = fixture(self.root)
        p = r['packages'][0]
        p.update(status='blocked', reason='Required plugin unavailable.')
        self.save(r)
        self.assertTrue(any(c['status'] == 'blocked' and 'package' in c['id']
                            for c in self.findings(self.validate(self.root, mode='static'))))

    def test_missing_governance_pin_is_blocked(self):
        r = fixture(self.root)
        r['governance_revision'] = None
        self.save(r)
        report = self.validate(self.root, mode='static')
        self.assertTrue(any(c['id'] == 'governance' and c['status'] == 'blocked' for c in self.findings(report)))

    def test_cli_writes_json_and_returns_nonzero(self):
        fixture(self.root)
        output = self.root / 'reports/test'
        result = subprocess.run([sys.executable, '-m', 'qgis_meta', 'validate', str(self.root),
                                 '--mode', 'static', '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads((output / 'report.json').read_text())['exit_code'], 2)

    def test_validation_does_not_rewrite_registry(self):
        fixture(self.root)
        before = (self.root / 'qgis-registry.json').read_bytes()
        self.validate(self.root, mode='static')
        self.assertEqual(before, (self.root / 'qgis-registry.json').read_bytes())

    def test_report_fingerprints_project_and_lock(self):
        fixture(self.root)
        report = self.validate(self.root, mode='static')
        fingerprints = report['projects'][0]['input_hashes']
        self.assertIn('maps/map.qgs', fingerprints)
        self.assertIn('requirements-qgis.lock.txt', fingerprints)
        old = fingerprints['maps/map.qgs']
        (self.root / 'maps/map.qgs').write_text('<qgis projectname="changed"/>')
        new = self.validate(self.root, mode='static')['projects'][0]['input_hashes']['maps/map.qgs']
        self.assertNotEqual(old, new)

    def test_review_warning_does_not_skip_relocation_or_negative_checks(self):
        from unittest.mock import patch
        fixture(self.root)
        worker_result = {'checks': [
            {'id': 'load', 'status': 'pass', 'message': 'loaded', 'evidence': {}},
            {'id': 'render', 'status': 'pass', 'message': 'rendered', 'evidence': {}},
            {'id': 'marker-spacing', 'status': 'warning', 'message': 'review bounds', 'evidence': {}}],
            'runtime': {}}
        def run(root, record, work, **kwargs):
            work.mkdir(parents=True, exist_ok=True)
            return worker_result
        with patch('qgis_meta.engine.run_worker', side_effect=run) as worker:
            report = self.validate(self.root, mode='full')
        self.assertEqual(worker.call_count, 2)
        checks = {c['id']: c for c in self.findings(report)}
        self.assertEqual(checks['relocate']['status'], 'pass', report)
        self.assertEqual(checks['negative']['status'], 'pass', report)
        self.assertEqual(checks['marker-spacing']['status'], 'warning')
