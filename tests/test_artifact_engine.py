"""Artifact integration must not bypass native project acceptance."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from qgis_meta import validate


class ArtifactEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sample.json').write_text('{"items": [1, 2]}')
        self.config = self.root / 'qgis-checks.json'
        self.config.write_text(json.dumps({'schema_version': 1, 'project_id': 'sample',
            'checks': [{'id': 'count', 'op': 'json_length',
                        'source': {'file': 'sample.json', 'pointer': '/items'}, 'length': 2}]}))

    def test_artifact_file_and_directory_pass_with_explicit_scope(self):
        for target in [self.config, self.root]:
            report = validate(target, mode='static')
            self.assertEqual(report['exit_code'], 0, report)
            self.assertEqual(report['projects'][0]['scope'], 'artifacts')
            self.assertEqual(report['projects'][0]['input_hashes']['sample.json'],
                hashlib.sha256((self.root / 'sample.json').read_bytes()).hexdigest())

    def test_artifacts_do_not_hide_unregistered_native_project(self):
        (self.root / 'map.qgs').write_text('<qgis/>')
        report = validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 1)
        self.assertTrue(any('Unregistered' in c['message'] for c in report['checks']))

    def test_invalid_artifact_config_fails_without_traceback(self):
        self.config.write_text('{oops')
        report = validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 1)

    def test_report_is_written_for_artifact_failure(self):
        (self.root / 'sample.json').write_text('{"items": []}')
        report = validate(self.config, output=self.root / 'reports' / 'run')
        self.assertEqual(report['exit_code'], 1)
        self.assertEqual(json.loads((self.root / 'reports/run/report.json').read_text())['exit_code'], 1)

    def test_cached_artifact_config_is_not_discovered(self):
        hidden = self.root / 'reports'; hidden.mkdir()
        (hidden / 'qgis-checks.json').write_text('{oops')
        self.assertEqual(validate(self.root, mode='static')['exit_code'], 0)

    def test_symlink_artifact_config_is_rejected(self):
        self.config.rename(self.root / 'config.json')
        self.config.symlink_to(self.root / 'config.json')
        self.assertEqual(validate(self.root, mode='static')['exit_code'], 1)

    def test_mixed_native_and_artifact_checks_stay_blocked_in_static_mode(self):
        from test_engine import fixture
        fixture(self.root / 'native')
        report = validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 2, report)
        self.assertEqual(report['scope'], 'native-and-artifacts')
        self.assertEqual(len(report['projects']), 2)

    def test_explicit_file_has_narrow_scope_but_directory_reports_native_files(self):
        (self.root / 'map.qgz').write_bytes(b'not a zip')
        self.assertEqual(validate(self.config)['exit_code'], 0)
        report = validate(self.root, mode='static')
        self.assertEqual(report['exit_code'], 1)
        self.assertEqual(report['scope'], 'native-and-artifacts')
