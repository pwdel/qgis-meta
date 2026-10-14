"""Bounded, declarative consistency checks for local artifact bundles."""
import csv
import hashlib
import io
import json
import lzma
import math
import re
import zipfile
import zlib
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from jsonschema import Draft202012Validator

from .common import contained, finding


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, f'Duplicate JSON key: {key}')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f'Non-finite JSON number: {value}')

    def finite(value):
        number = float(value)
        _require(math.isfinite(number), 'Non-finite JSON number')
        return number

    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite)


def _equal(left, right):
    # JSON booleans are distinct from numbers; object order is immaterial.
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


class _Inputs:
    def __init__(self, root):
        self.root = root
        self.hashes = {}

    def read(self, name):
        path = contained(self.root, name)
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        _require(name not in self.hashes or self.hashes[name] == sha, f'Input changed during validation: {name}')
        self.hashes[name] = sha
        return data

    def ref(self, ref):
        value = _json(self.read(ref['file']))
        pointer = ref.get('pointer', '')
        if pointer:
            _require(pointer.startswith('/') and not re.search(r'~(?![01])', pointer), 'Invalid JSON pointer')
            for part in pointer[1:].split('/'):
                part = part.replace('~1', '/').replace('~0', '~')
                if isinstance(value, list):
                    _require(re.fullmatch(r'0|[1-9][0-9]*', part), f'Invalid JSON array index: {part}')
                    value = value[int(part)]
                else:
                    _require(isinstance(value, dict), 'JSON pointer traverses a scalar')
                    value = value[part]
        return value


def _geometry(geometry, wgs84):
    if geometry is None:
        return
    _require(isinstance(geometry, dict), 'Geometry must be an object or null')
    kind = geometry.get('type')
    if kind == 'GeometryCollection':
        items = geometry.get('geometries')
        _require(isinstance(items, list), 'GeometryCollection requires geometries')
        for item in items:
            _require(item is not None, 'GeometryCollection contains null geometry')
            _geometry(item, wgs84)
        return
    coords = geometry.get('coordinates')

    def position(p):
        _require(isinstance(p, list) and len(p) >= 2, 'Position requires at least two ordinates')
        _require(all(type(n) in (float, int) and math.isfinite(n) for n in p), 'Coordinates must be finite numbers')
        if wgs84:
            _require(-180 <= p[0] <= 180 and -90 <= p[1] <= 90, 'Coordinates outside WGS84 bounds')

    def line(items, ring=False):
        _require(isinstance(items, list) and len(items) >= (4 if ring else 2), 'Invalid coordinate line or ring length')
        for item in items:
            position(item)
        if ring:
            _require(items[0] == items[-1], 'Polygon ring is not closed')

    def polygon(items):
        _require(isinstance(items, list) and items, 'Polygon requires rings')
        for item in items:
            line(item, ring=True)

    if kind == 'Point':
        position(coords)
    elif kind == 'LineString':
        line(coords)
    elif kind == 'Polygon':
        polygon(coords)
    elif kind in ('MultiPoint', 'MultiLineString', 'MultiPolygon'):
        _require(isinstance(coords, list) and coords, f'{kind} requires coordinates')
        validator = {'MultiPoint': position, 'MultiLineString': line, 'MultiPolygon': polygon}[kind]
        for item in coords:
            validator(item)
    else:
        raise ValueError(f'Unsupported geometry type: {kind}')


def _features(value, wgs84=False):
    _require(isinstance(value, dict) and value.get('type') == 'FeatureCollection', 'Expected GeoJSON FeatureCollection')
    features = value.get('features')
    _require(isinstance(features, list), 'FeatureCollection requires features array')
    for feature in features:
        _require(isinstance(feature, dict) and feature.get('type') == 'Feature', 'Invalid GeoJSON feature')
        _require('geometry' in feature and 'properties' in feature, 'Feature requires geometry and properties')
        _require(feature['properties'] is None or isinstance(feature['properties'], dict), 'Invalid feature properties')
        _geometry(feature['geometry'], wgs84)
    return features


def _indexed(rows, key):
    _require(isinstance(rows, list), 'Expected array of records')
    result = {}
    for row in rows:
        _require(isinstance(row, dict) and key in row, f'Missing record key: {key}')
        value = row[key]
        _require(type(value) in (str, int, float) and str(value) != '', 'Identifiers must be nonempty strings or numbers')
        if isinstance(value, float):
            _require(math.isfinite(value), 'Identifier must be finite')
        identifier = str(value)
        _require(identifier not in result, f'Duplicate identifier: {identifier}')
        result[identifier] = row
    return result


class _EmbeddedJSON(HTMLParser):
    def __init__(self, element_id):
        super().__init__(convert_charrefs=False)
        self.element_id = element_id
        self.matches = []
        self.active = False
        self.closed = False

    def handle_starttag(self, tag, attrs):
        if dict(attrs).get('id') == self.element_id:
            _require(tag == 'script', 'Embedded JSON must be in a script element')
            self.matches.append('')
            self.active = True
            self.closed = False

    def handle_data(self, data):
        if self.active:
            self.matches[-1] += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.active = False
            self.closed = True


def _check(inputs, check):
    op = check['op']
    if op == 'manifest':
        records = _json(inputs.read(check['manifest']))
        records = records if isinstance(records, list) else [records]
        _require(records, 'Manifest must contain records')
        base = contained(inputs.root, check['base'])
        seen = set()
        for record in records:
            _require(isinstance(record, dict) and set(record) == {'path', 'bytes', 'sha256'}, 'Manifest record requires only path, bytes and sha256')
            _require(type(record['bytes']) is int and record['bytes'] >= 0, 'Invalid manifest byte count')
            _require(isinstance(record['sha256'], str) and re.fullmatch('[a-fA-F0-9]{64}', record['sha256']), 'Invalid manifest SHA256')
            path = contained(base, record['path'])
            name = str(path.relative_to(inputs.root))
            _require(name not in seen, f'Duplicate manifest path: {name}')
            seen.add(name)
            data = inputs.read(name)
            _require(len(data) == record['bytes'], f'Manifest byte count mismatch: {name}')
            _require(hashlib.sha256(data).hexdigest() == record['sha256'].lower(), f'Manifest SHA256 mismatch: {name}')
    elif op == 'qgis_sources':
        data = inputs.read(check['file'])
        _require(b'<!ENTITY' not in data.replace(b'\x00', b'').upper(), 'XML entity declarations are unsupported')
        project = ElementTree.fromstring(data)
        layers = project.findall('.//maplayer')
        _require(layers, 'QGIS project contains no map layers')
        for layer in layers:
            provider = (layer.findtext('provider') or '').strip()
            _require(provider in ('ogr', 'gdal'), f'Unsupported QGIS provider: {provider}')
            name = (layer.findtext('datasource') or '').strip()
            _require(name.startswith(check['prefix']), f'Data source does not use required prefix: {name}')
            name = name.split('|', 1)[0]
            path = contained(inputs.root, str(Path(check['file']).parent / name))
            payload = inputs.read(str(path.relative_to(inputs.root)))
            if provider == 'gdal':
                _require(path.suffix.lower() in ('.tif', '.tiff'), 'GDAL source must be a TIFF file')
                _require(payload[:4] in (b'II*\x00', b'MM\x00*') or payload[:8] in (b'II+\x00\x08\x00\x00\x00', b'MM\x00+\x00\x08\x00\x00'), 'Invalid TIFF signature')
            else:
                _features(_json(payload))
    elif op == 'archive':
        with zipfile.ZipFile(io.BytesIO(inputs.read(check['file']))) as archive:
            _require(archive.testzip() is None, 'Archive member CRC mismatch')
            _require(archive.namelist().count(check['member']) == 1, 'Archive member missing or duplicated')
            _require(archive.read(check['member']) == inputs.read(check['equals']), 'Archive member content mismatch')
    elif op == 'json_equal':
        _require(_equal(inputs.ref(check['left']), inputs.ref(check['right'])), 'JSON values differ')
    elif op == 'json_value':
        _require(_equal(inputs.ref(check['source']), check['value']), 'JSON value does not match expected value')
    elif op == 'json_length':
        value = inputs.ref(check['source'])
        _require(isinstance(value, list), 'JSON length requires an array')
        _require(len(value) == check['length'], 'JSON length mismatch')
    elif op == 'html_json':
        parser = _EmbeddedJSON(check['element_id'])
        parser.feed(inputs.read(check['file']).decode('utf-8'))
        parser.close()
        _require(len(parser.matches) == 1 and parser.closed, 'Expected one complete embedded JSON element')
        _require(_equal(_json(parser.matches[0]), inputs.ref(check['source'])), 'Embedded JSON differs from source')
    elif op == 'geojson':
        _features(_json(inputs.read(check['file'])), check.get('wgs84', False))
    elif op in ('flattened_features', 'csv_ids'):
        features = _features(inputs.ref(check['source']))
        rows = [f['properties'] for f in features]
        expected = _indexed(rows, check['key'])
        if op == 'flattened_features':
            targets = _features(_json(inputs.read(check['target'])))
            actual = _indexed([f['properties'] for f in targets], check['key'])
            _require(expected.keys() == actual.keys(), 'Flattened feature identifiers differ')
            geometry = {str(f['properties'][check['key']]): f['geometry'] for f in targets}
            for feature in features:
                identifier = str(feature['properties'][check['key']])
                _require(_equal(feature['geometry'], geometry[identifier]), f'Flattened geometry differs: {identifier}')
                for name, value in feature['properties'].items():
                    _require(name in actual[identifier], f'Missing flattened property: {name}')
                    observed = actual[identifier][name]
                    if isinstance(value, (dict, list)) and isinstance(observed, str):
                        observed = _json(observed)
                    _require(_equal(value, observed), f'Flattened property differs: {identifier}/{name}')
        else:
            reader = csv.DictReader(io.StringIO(inputs.read(check['file']).decode('utf-8-sig'), newline=''))
            _require(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames) and check['column'] in reader.fieldnames, 'CSV identifier column missing or header duplicated')
            records = list(reader)
            _require(all(None not in row and all(v is not None for v in row.values()) for row in records), 'Malformed CSV row')
            actual = _indexed(records, check['column'])
            _require(actual.keys() == expected.keys(), 'CSV identifiers differ from source')
    else:
        raise ValueError(f'Unknown operation: {op}')


def run_artifact_checks(config: Path) -> dict:
    """Return scoped findings and SHA256 hashes; never execute project code."""
    config = Path(config).absolute()
    inputs = _Inputs(config.parent.resolve())
    report = {'registry': str(config), 'project_id': config.parent.name, 'scope': 'artifacts',
              'checks': [], 'input_hashes': inputs.hashes}
    try:
        record = _json(inputs.read(config.name))
        schema = _json((Path(__file__).parent / 'contracts/artifact-checks.schema.json').read_bytes())
        errors = list(Draft202012Validator(schema).iter_errors(record))
        _require(not errors, 'Invalid artifact checks configuration: ' + '; '.join(e.message for e in errors))
        ids = [check['id'] for check in record['checks']]
        _require(len(ids) == len(set(ids)), 'Duplicate check IDs')
        report['project_id'] = record['project_id']
    except (ValueError, OSError, TypeError, RecursionError) as exc:
        report['checks'].append(finding('artifact-config', 'fail', str(exc)))
    else:
        for check in record['checks']:
            try:
                _check(inputs, check)
            except (ValueError, OSError, TypeError, LookupError, OverflowError,
                    RecursionError, zipfile.BadZipFile, RuntimeError, NotImplementedError,
                    ElementTree.ParseError, csv.Error, zlib.error, lzma.LZMAError) as exc:
                report['checks'].append(finding(check['id'], 'fail', f'{check["op"]}: {exc}', op=check['op']))
            else:
                report['checks'].append(finding(check['id'], 'pass', f'{check["op"]}: artifact check passed', op=check['op']))
    for name, original in list(inputs.hashes.items()):
        try:
            actual = hashlib.sha256(contained(inputs.root, name).read_bytes()).hexdigest()
            _require(actual == original, f'Input changed during validation: {name}')
        except (ValueError, OSError) as exc:
            report['checks'].append(finding('artifact-inputs', 'fail', str(exc), file=name))
    return report
