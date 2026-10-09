"""Inspect project sources before providers can open network/compound datasets."""
import json
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def inspect_sources(project_file, root, record, providers):
    if project_file.suffix == '.qgz':
        with zipfile.ZipFile(project_file) as archive:
            names = [n for n in archive.namelist() if n.endswith('.qgs')]
            if len(names) != 1:
                raise ValueError('QGZ must contain exactly one QGS')
            xml = ET.fromstring(archive.read(names[0]))
    else:
        xml = ET.parse(project_file).getroot()
    blocked, failed = [], []
    declared = {(root / a['path']).resolve() for a in record['assets'] if a['path']}
    for layer in xml.findall('projectlayers/maplayer'):
        provider = layer.findtext('provider', '')
        lid = layer.findtext('id', 'unknown')
        if provider not in {'ogr', 'gdal'}:
            blocked.append(f'{lid}: {provider} provider requires a dedicated validator; not loaded')
            continue
        source = providers.decodeUri(provider, layer.findtext('datasource', '')).get('path', '')
        path = Path(source)
        path = (project_file.parent / path).resolve() if not path.is_absolute() else path.resolve()
        if not source or not path.is_relative_to(root) or path not in declared:
            failed.append(f'{lid}: source is not a declared project-contained asset')
            continue
        if not path.is_file():
            failed.append(f'{lid}: missing datasource')
            continue
        with path.open('rb') as stream:
            header = stream.read(100)
        suffix = path.suffix.lower()
        supported = False
        if provider == 'ogr' and suffix in {'.geojson', '.json'}:
            try:
                supported = json.loads(path.read_text()).get('type') == 'FeatureCollection'
            except (ValueError, UnicodeError, AttributeError):
                pass
        elif provider == 'ogr' and suffix == '.gpkg' and header.startswith(b'SQLite format 3\x00'):
            # Virtual tables may depend on other files. Decline until closure is supported.
            with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
                virtual = db.execute("SELECT name FROM sqlite_master WHERE upper(sql) LIKE '%CREATE VIRTUAL TABLE%' AND name NOT LIKE 'rtree_%'").fetchall()
                supported = not virtual
        elif provider == 'gdal' and suffix in {'.tif', '.tiff'}:
            supported = header[:4] in {b'II*\x00', b'MM\x00*', b'II+\x00', b'MM\x00+'}
        if not supported:
            blocked.append(f'{lid}: compound or unsupported datasource format {suffix}; not loaded')
        for sidecar in (Path(str(path)+'.aux.xml'), Path(str(path)+'.ovr')):
            if sidecar.exists():
                blocked.append(f'{lid}: external raster sidecars require separate dependency validation')
    return failed, blocked
