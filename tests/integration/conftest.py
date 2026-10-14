"""Opt-in native tests; supply a project without embedding consumer data here."""
from pathlib import Path
import json
import pytest


def pytest_addoption(parser):
    parser.addoption('--map-project', help='Local QGS/QGZ to inspect read-only; default: generated synthetic project')


@pytest.fixture
def map_path(request, qgis_app, tmp_path):
    value = request.config.getoption('--map-project')
    if not value:
        from qgis.core import QgsProject, QgsVectorLayer
        from qgis.PyQt.QtGui import QColor
        data = tmp_path / 'sample.geojson'
        data.write_text(json.dumps({'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'id': 'sample'},
             'geometry': {'type': 'Point', 'coordinates': [1, 2]}},
            {'type': 'Feature', 'properties': {'id': 'other'},
             'geometry': {'type': 'Point', 'coordinates': [2, 3]}}]}))
        project = QgsProject()
        layer = QgsVectorLayer(str(data), 'sample', 'ogr')
        assert layer.isValid()
        layer.renderer().symbol().setSize(8)
        layer.renderer().symbol().setColor(QColor("black"))
        project.setCrs(layer.crs())
        project.addMapLayer(layer)
        path = tmp_path / 'sample.qgz'
        assert project.write(str(path))
        project.clear()
        return path
    path = Path(value).resolve()
    assert path.is_file() and path.suffix.lower() in {'.qgs', '.qgz'}, 'Expected a saved QGS/QGZ'
    return path


@pytest.fixture
def loaded_map(qgis_new_project, map_path):
    assert qgis_new_project.read(str(map_path)), 'Saved project cannot be read'
    yield qgis_new_project
    qgis_new_project.clear()
