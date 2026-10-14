"""Reusable PyQGIS integration checks using real pytest-qgis fixtures.

These are smoke tests, not registry, layout-quality or policy acceptance.
Run explicitly with a QGIS-aware interpreter and --map-project.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from qgis.core import (Qgis, QgsCoordinateTransform, QgsMapRendererParallelJob,
                       QgsMapSettings, QgsRectangle, QgsVectorLayer)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor


def test_saved_project_has_valid_layers(loaded_map, record_property):
    record_property('qgis_version', Qgis.QGIS_VERSION)
    record_property('python_version', sys.version.split()[0])
    layers = list(loaded_map.mapLayers().values())
    assert layers, 'Saved project has no layers'
    assert loaded_map.crs().isValid(), 'Project CRS is invalid'
    for layer in layers:
        assert layer.isValid(), f'Invalid layer: {layer.id()}'
        assert layer.crs().isValid(), f'Invalid CRS: {layer.id()}'


def test_real_vector_features_are_readable(loaded_map, record_property):
    vectors = [x for x in loaded_map.mapLayers().values() if isinstance(x, QgsVectorLayer)]
    assert vectors, 'This suite requires at least one vector layer'
    readable = 0
    for layer in vectors:
        assert layer.isValid(), f'Invalid layer: {layer.id()}'
        count = layer.featureCount()
        assert count >= 0, f'Feature count unavailable: {layer.id()}'
        if count:
            feature = next(layer.getFeatures(), None)
            assert feature is not None and feature.isValid(), f'Cannot read feature: {layer.id()}'
            assert not feature.geometry().isNull(), f'First feature has null geometry: {layer.id()}'
            readable += 1
    assert readable, 'No nonempty vector layer was read'
    record_property('nonempty_vector_layers', readable)


def test_project_renders_nonblank_image(loaded_map, tmp_path, record_property):
    assert loaded_map.crs().isValid(), 'Cannot certify rendering with an invalid project CRS'
    layers = loaded_map.layerTreeRoot().checkedLayers()
    assert layers, 'No visible layers to render'
    extent = QgsRectangle()
    extent.setNull()
    for layer in layers:
        assert layer.isValid(), f'Invalid layer: {layer.id()}'
        bounds = QgsCoordinateTransform(layer.crs(), loaded_map.crs(), loaded_map).transformBoundingBox(layer.extent())
        if not bounds.isEmpty():
            extent.combineExtentWith(bounds)
    assert not extent.isEmpty(), 'No usable render extent'
    extent.scale(1.05)
    settings = QgsMapSettings()
    settings.setLayers(layers)
    settings.setDestinationCrs(loaded_map.crs())
    settings.setTransformContext(loaded_map.transformContext())
    settings.setExtent(extent)
    settings.setOutputSize(QSize(800, 600))
    settings.setBackgroundColor(QColor('white'))
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    assert not job.errors(), [e.message for e in job.errors()]
    image = job.renderedImage()
    assert not image.isNull(), 'Renderer returned no image'
    ink = sum(image.pixelColor(x, y) != QColor('white')
              for y in range(0, image.height(), 2) for x in range(0, image.width(), 2))
    assert ink > 100, f'Insufficient nonbackground sample pixels: {ink}'
    preview = tmp_path / 'render.png'
    assert image.save(str(preview)), 'Cannot save preview'
    record_property('preview', str(preview))
    record_property('nonbackground_samples', ink)


def test_missing_dependency_causes_child_pytest_failure(qgis_new_project, tmp_path):
    """A real broken saved project must fail an independent fixture-based run."""
    data = tmp_path / 'points.geojson'
    data.write_text(json.dumps({'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'id': 'sample'},
         'geometry': {'type': 'Point', 'coordinates': [1, 2]}}]}))
    layer = QgsVectorLayer(str(data), 'sample', 'ogr')
    assert layer.isValid()
    qgis_new_project.addMapLayer(layer)
    project = tmp_path / 'broken.qgs'
    assert qgis_new_project.write(str(project))
    qgis_new_project.clear()
    data.unlink()
    child = tmp_path / 'test_missing.py'
    child.write_text('''from pathlib import Path

def test_missing(qgis_new_project):
    assert qgis_new_project.read(str(Path(__file__).with_name("broken.qgs")))
    layers = list(qgis_new_project.mapLayers().values())
    assert layers
    assert all(layer.isValid() for layer in layers), "missing dependency detected"
''')
    junit = tmp_path / 'negative.xml'
    command = [sys.executable, '-m', 'pytest', '-p', 'pytest_qgis.pytest_qgis',
               str(child), '--rootdir', str(tmp_path), '-o', 'qgis_gui_enabled=false',
               '-p', 'no:cacheprovider', '--junitxml', str(junit), '-q']
    proc = subprocess.run(command, env={**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'},
                          capture_output=True, text=True, timeout=90, cwd=tmp_path)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    cases = ET.parse(junit).getroot().findall('.//testcase')
    assert len(cases) == 1 and cases[0].find('failure') is not None, proc.stdout
    assert 'missing dependency detected' in cases[0].find('failure').get('message', ''), proc.stdout
