"""Schema plus cross-reference/file validation. Never execute registry commands."""
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from .common import contained, digest, finding

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = Path(__file__).parent / 'contracts'


def contract(name):
    return json.loads((CONTRACTS / name).read_text())


def check_registry(root, record):
    schema = contract('qgis-registry-v2.schema.json')
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record),
                    key=lambda e: str(list(e.path)))
    if errors:
        return [finding('registry', 'fail', '; '.join(
            f'{"/".join(map(str, e.path))}: {e.message}' for e in errors))]
    issues = []
    for key in ('assets', 'layers', 'tests'):
        ids = [x['id'] for x in record[key]]
        if len(set(ids)) != len(ids):
            issues.append(f'Duplicate {key} IDs')
    assets = {x['id']: x for x in record['assets']}
    tests = {x['id']: x for x in record['tests']}
    for layer in record['layers']:
        if not set(layer['asset_ids']) <= assets.keys():
            issues.append(f'Unknown asset on layer {layer["id"]}')
        bounds = layer['feature_count']
        if bounds and bounds['min'] > bounds['max']:
            issues.append(f'Reversed feature-count bounds: {layer["id"]}')
    if not record['layers'] or not assets:
        issues.append('At least one expected layer and asset must be inventoried')
    ext = record['render']['extent']
    if ext[0] >= ext[2] or ext[1] >= ext[3]:
        issues.append('Render extent must have positive width and height')
    paths = [record['project']['file'], record['runtime']['lock_file']]
    for package in record['packages']:
        paths.extend(package['config_paths'])
        if package['status'] == 'used':
            if package['source_revision'] and not re.fullmatch(r'[a-fA-F0-9]{40}', package['source_revision']):
                issues.append(f'{package["id"]}: source_revision must be an immutable Git SHA')
            for tid in package['test_ids']:
                if tid not in tests or tests[tid]['package_id'] != package['id']:
                    issues.append(f'{package["id"]}: missing/mismatched test {tid}')
    for test in record['tests']:
        paths.append(test['nodeid'].split('::')[0])
        package = next((p for p in record['packages'] if p['id'] == test['package_id']), None)
        if not package or package['status'] != 'used' or test['id'] not in package['test_ids']:
            issues.append(f'Orphan or inactive package test: {test["id"]}')
    for asset in assets.values():
        if asset['acquisition_recipe']:
            paths.append(asset['acquisition_recipe'])
    for value in paths:
        try:
            p = contained(root, value)
            if not p.is_file():
                issues.append(f'Missing file: {value}')
        except ValueError as exc:
            issues.append(str(exc))
    status = 'fail' if issues else 'pass'
    return [finding('registry', status, '; '.join(issues) if issues else 'Schema, references and declared files checked')]


def check_assets(root, record):
    issues, hashes = [], {}
    for asset in record['assets']:
        if asset['kind'] == 'service':
            continue
        try:
            path = contained(root, asset['path'])
            if not path.is_file():
                issues.append(f'Missing asset: {asset["path"]}')
                continue
            with path.open('rb') as stream:
                if stream.read(128).startswith(b'version https://git-lfs.github.com/spec/v1'):
                    issues.append(f'Unhydrated LFS asset: {asset["path"]}')
            actual = digest(path)
            hashes[asset['id']] = actual
            if actual != asset['sha256']:
                issues.append(f'Checksum mismatch: {asset["path"]}')
        except (ValueError, OSError) as exc:
            issues.append(str(exc))
    return finding('assets', 'fail' if issues else 'pass',
                   '; '.join(issues) if issues else 'All local asset hashes match', hashes=hashes)
