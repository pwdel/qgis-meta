import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]


class ContractV2Tests(unittest.TestCase):
    def test_packaged_contracts_match_canonical_sources(self):
        for canonical,bundled in [('schemas/qgis-registry-v2.schema.json','qgis-registry-v2.schema.json'),
                                  ('packages/catalog.json','catalog.json')]:
            self.assertEqual((ROOT/canonical).read_bytes(),(ROOT/'qgis_meta/contracts'/bundled).read_bytes())

    def test_v2_template_is_a_valid_draft(self):
        schema=json.loads((ROOT/'schemas/qgis-registry-v2.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        example=json.loads((ROOT/'templates/qgis-registry-v2.example.json').read_text())
        Draft202012Validator(schema,format_checker=FormatChecker()).validate(example)
        self.assertEqual(example['status'],'draft')
