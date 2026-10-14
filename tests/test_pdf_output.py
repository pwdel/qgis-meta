import unittest
from pathlib import Path
from unittest.mock import patch
from qgis_meta.pdf_output import inspect_pdf

class PdfDependencyTests(unittest.TestCase):
    def test_missing_native_gdal_is_an_explicit_export_failure(self):
        with patch.dict('sys.modules', {'osgeo': None}):
            evidence, errors = inspect_pdf(Path('unused.pdf'), {0})
        self.assertFalse(evidence)
        self.assertIn('GDAL', errors[0])
