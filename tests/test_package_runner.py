import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


class PackageRunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('qgis_meta.package_tests'), 'package test runner missing')
        from qgis_meta.package_tests import check_packages
        self.run = check_packages
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = {'packages': [{'id': 'example', 'status': 'used', 'test_ids': ['example-test']}],
                       'tests': [{'id':'example-test','package_id':'example', 'nodeid':'test_example.py::test_case'}]}

    def test_requires_opt_in_to_execute_project_code(self):
        (self.root / 'test_example.py').write_text('def test_case():\n    assert False\n')
        result = self.run(self.root,self.record,self.root/'results',enabled=False)
        self.assertEqual(result[0]['status'], 'blocked')

    def test_skipped_test_is_not_a_pass(self):
        (self.root / 'test_example.py').write_text('import pytest\n@pytest.mark.skip(reason="missing")\ndef test_case(): pass\n')
        result = self.run(self.root,self.record,self.root/'results',enabled=True,qgis_python=sys.executable)
        self.assertEqual(result[0]['status'], 'blocked', result)

    def test_failing_test_propagates(self):
        (self.root / 'test_example.py').write_text('def test_case():\n    assert False\n')
        result = self.run(self.root,self.record,self.root/'results',enabled=True,qgis_python=sys.executable)
        self.assertEqual(result[0]['status'], 'fail', result)

    def test_collected_pass_is_reported(self):
        (self.root / 'test_example.py').write_text('def test_case():\n    assert 2 + 2 == 4\n')
        result = self.run(self.root,self.record,self.root/'results',enabled=True,qgis_python=sys.executable)
        self.assertEqual(result[0]['status'], 'pass', result)

    def test_missing_node_is_not_a_pass(self):
        (self.root / 'test_example.py').write_text('def test_other(): pass\n')
        result = self.run(self.root,self.record,self.root/'results',enabled=True,qgis_python=sys.executable)
        self.assertNotEqual(result[0]['status'], 'pass', result)

    def test_missing_or_wrong_package_version_blocks_execution(self):
        (self.root / 'test_example.py').write_text('def test_case(): pass\n')
        self.record['packages'][0].update(id='pytest-qgis',version='0.0.0')
        self.record['tests'][0]['package_id']='pytest-qgis'
        result = self.run(self.root,self.record,self.root/'results',enabled=True,qgis_python=sys.executable)
        self.assertEqual(result[0]['status'], 'blocked', result)

    def test_same_version_without_source_identity_is_blocked(self):
        import os
        from unittest.mock import patch
        module=self.root/'QuickOSM'
        module.mkdir();(module/'__init__.py').write_text('')
        (module/'metadata.txt').write_text('[general]\nversion=1.2.3\n')
        (self.root/'test_example.py').write_text('def test_case(): pass\n')
        self.record['packages'][0].update(id='quickosm',version='1.2.3',source_revision=None,archive_sha256='0'*64)
        self.record['tests'][0]['package_id']='quickosm'
        with patch.dict(os.environ,{'PYTHONPATH':str(self.root)}):
            result=self.run(self.root,self.record,self.root/'results',enabled=True,qgis_python=sys.executable)
        self.assertTrue(any(c['id'].startswith('package-source:') and c['status']=='blocked' for c in result),result)
