"""Structural contract tests; these do not execute QGIS or certify any map."""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/qgis-registry.schema.json').read_text())
EXAMPLE = json.loads((ROOT / 'templates/qgis-registry.example.json').read_text())
CATALOG = json.loads((ROOT / 'packages/catalog.json').read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


class RegistryContractTests(unittest.TestCase):
    def test_schema_and_draft_example(self):
        Draft202012Validator.check_schema(SCHEMA)
        VALIDATOR.validate(EXAMPLE)

    def test_catalog_and_schema_agree(self):
        expected = {p['id'] for p in CATALOG['packages']}
        self.assertEqual(expected, set(SCHEMA['$defs']['package']['properties']['id']['enum']))
        self.assertEqual(expected, {p['id'] for p in EXAMPLE['packages']})

    def test_missing_or_duplicate_catalog_package_rejected(self):
        for mode in ('missing', 'duplicate'):
            with self.subTest(mode=mode):
                record = copy.deepcopy(EXAMPLE)
                if mode == 'missing':
                    record['packages'].pop()
                else:
                    record['packages'][-1] = copy.deepcopy(record['packages'][0])
                self.assertFalse(VALIDATOR.is_valid(record))

    def test_unsafe_paths_rejected(self):
        for path in ('/tmp/map.qgz', '../map.qgz', 'data/../../map.qgz',
                     'C:/maps/map.qgz', 'data\\map.qgz'):
            with self.subTest(path=path):
                record = copy.deepcopy(EXAMPLE)
                record['project']['file'] = path
                self.assertFalse(VALIDATOR.is_valid(record))

    def test_used_package_requires_pin_and_all_test_ids(self):
        for catalog_package in CATALOG['packages']:
            with self.subTest(package=catalog_package['id']):
                record = copy.deepcopy(EXAMPLE)
                package = next(p for p in record['packages'] if p['id'] == catalog_package['id'])
                package.update(status='used', version='1.2.3', purposes=['test'],
                               archive_sha256='a' * 64,
                               test_ids=catalog_package['required_test_ids'].copy())
                VALIDATOR.validate(record)
                package['test_ids'].pop()
                self.assertFalse(VALIDATOR.is_valid(record))
                package['test_ids'] = catalog_package['required_test_ids'].copy()
                package['archive_sha256'] = None
                self.assertFalse(VALIDATOR.is_valid(record))

    def test_incomplete_draft_cannot_be_marked_compliant(self):
        record = copy.deepcopy(EXAMPLE)
        record['status'] = 'compliant'
        self.assertFalse(VALIDATOR.is_valid(record))

    def test_pass_requires_report(self):
        record = copy.deepcopy(EXAMPLE)
        record['tests'][0]['status'] = 'pass'
        self.assertFalse(VALIDATOR.is_valid(record))

    def test_every_baseline_gate_is_required(self):
        for index in range(6):
            with self.subTest(gate=EXAMPLE['tests'][index]['id']):
                record = copy.deepcopy(EXAMPLE)
                record['tests'].pop(index)
                self.assertFalse(VALIDATOR.is_valid(record))

    def test_service_cannot_count_as_offline_asset(self):
        record = copy.deepcopy(EXAMPLE)
        record['assets'] = [{'id': 'example-service', 'kind': 'service',
                             'path': None, 'sha256': None,
                             'source_url': 'https://example.org/service',
                             'license_url': 'https://example.org/terms',
                             'attribution': 'Synthetic example', 'acquired_on': None,
                             'offline_required': False, 'acquisition_recipe': None}]
        VALIDATOR.validate(record)
        record['assets'][0]['offline_required'] = True
        self.assertFalse(VALIDATOR.is_valid(record))


if __name__ == '__main__':
    unittest.main()
