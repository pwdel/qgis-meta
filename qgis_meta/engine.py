"""Shared orchestration. Validation never changes the supplied project or registry."""
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from .common import contained, digest, exit_code, finding
from .discovery import discover, discover_artifacts, is_xml_companion
from .static import ROOT, check_registry, check_assets
from .runtime import run_worker


def git_evidence(root):
    def git(*args):
        p = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
        return p.stdout if p.returncode == 0 else b''
    return {'commit': git('rev-parse', 'HEAD').decode().strip() or None,
            'root': git('rev-parse', '--show-toplevel').decode().strip() or None,
            'dirty': bool(git('status', '--porcelain', '--untracked-files=all')),
            'tracked_diff_sha256': hashlib.sha256(git('diff', 'HEAD', '--binary')).hexdigest()}


def validate(target, mode='full', *, output=None, qgis_python=None, qgis_app=None,
             timeout=120, run_project_tests=False, governance_root=None):
    """Accept a repository, project directory, or qgis-registry.json (str/Path).

    Returns a JSON-serializable report. Exit 0 = complete pass, 1 = failure,
    2 = blocked/incomplete. Static mode deliberately never certifies runtime.
    """
    if mode not in {'static', 'full'}:
        raise ValueError('mode must be static or full')
    target = Path(target).absolute()
    output = Path(output).absolute() if output else None
    if output:
        output.mkdir(parents=True, exist_ok=True)
    artifact_configs = discover_artifacts(target)
    if target.name == 'qgis-checks.json' and (target.is_file() or target.is_symlink()):
        registries, project_files, checks = [], [], []
    else:
        registries, project_files, checks = discover(target)
    if not registries and not artifact_configs:
        checks.append(finding('discovery', 'blocked', 'No registered projects found'))
    meta = Path(governance_root).resolve() if governance_root else ROOT
    valid_checkout = (meta / 'pyproject.toml').is_file() and (meta / 'qgis_meta/engine.py').is_file()
    engine_evidence = git_evidence(meta) if valid_checkout else {'commit': None}
    engine_evidence['files'] = {str(p.relative_to(Path(__file__).parent)): digest(p)
                                for p in [*Path(__file__).parent.glob('*.py'), *Path(__file__).parent.glob('contracts/*.json')]}
    engine_evidence['checkout_matches'] = valid_checkout and engine_evidence.get('root') == str(meta) and all(
        (meta / 'qgis_meta' / name).is_file() and sha == digest(meta / 'qgis_meta' / name)
        for name, sha in engine_evidence['files'].items())
    engine_evidence['contracts_match'] = valid_checkout and all(
        (meta / canonical).is_file() and digest(meta / canonical) == digest(Path(__file__).parent / 'contracts' / bundled)
        for canonical, bundled in [('schemas/qgis-registry-v2.schema.json', 'qgis-registry-v2.schema.json'), ('packages/catalog.json', 'catalog.json')])
    report = {'report_version': 1, 'started_at': datetime.now(timezone.utc).isoformat(),
              'target': str(target), 'mode': mode, 'engine': engine_evidence,
              'projects': [], 'checks': checks}
    if artifact_configs:
        from .artifacts import run_artifact_checks
        for config in artifact_configs:
            if config.is_symlink():
                checks.append(finding('discovery', 'fail', f'Symlink artifact configuration rejected: {config}'))
                continue
            artifact = run_artifact_checks(config)
            artifact['source'] = git_evidence(config.parent)
            report['projects'].append(artifact)
    report['scope'] = 'native-and-artifacts' if (registries or project_files) and artifact_configs else (
        'artifacts' if artifact_configs and not project_files else 'native')
    declared, ids = set(), set()
    with tempfile.TemporaryDirectory(prefix='qgis-meta-') as temp:
        for index, registry in enumerate(registries):
            root = registry.parent.resolve()
            result = {'registry': str(registry), 'project_id': None, 'checks': [],
                      'source': git_evidence(root), 'runtime': {}}
            report['projects'].append(result)
            try:
                record = json.loads(registry.read_text())
                result['registry_sha256'] = digest(registry)
                result['checks'].extend(check_registry(root, record))
                if result['checks'][0]['status'] == 'fail':
                    continue
                input_names = {record['project']['file'], record['runtime']['lock_file']}
                input_names.update(t['nodeid'].split('::')[0] for t in record['tests'])
                input_names.update(name for p in record['packages'] for name in p['config_paths'])
                input_names.update(a['acquisition_recipe'] for a in record['assets'] if a['acquisition_recipe'])
                result['input_hashes'] = {name: digest(contained(root, name)) for name in sorted(input_names)}
                pid = record['project']['id']
                result['project_id'] = pid
                if pid in ids:
                    result['checks'].append(finding('registry', 'fail', f'Duplicate project ID: {pid}'))
                ids.add(pid)
                declared.add(contained(root, record['project']['file']))
                pin = record['governance_revision']
                result['checks'].append(finding('governance', 'pass' if pin and pin == report['engine']['commit'] and engine_evidence['checkout_matches'] and engine_evidence['contracts_match'] and not engine_evidence.get('dirty', True) else 'blocked',
                    'Governance revision matches engine checkout' if pin and pin == report['engine']['commit'] and engine_evidence['checkout_matches'] and engine_evidence['contracts_match'] and not engine_evidence.get('dirty', True)
                    else 'Use the clean qgis-meta checkout pinned by this registry (missing/mismatched revision, modified engine or contracts)'))
                result['checks'].append(check_assets(root, record))
                for package in record['packages']:
                    if package['status'] == 'blocked':
                        result['checks'].append(finding('package:' + package['id'], 'blocked', package['reason']))
                if mode == 'static':
                    result['checks'].append(finding('runtime', 'blocked', 'Static mode omits required QGIS integration gates'))
                    continue
                if any(c['status'] == 'fail' for c in result['checks']):
                    result['checks'].append(finding('load', 'blocked', 'Fix registry/asset failures before QGIS loading'))
                    continue
                work = Path(temp) / str(index)
                runtime = run_worker(root, record, work / 'original', qgis_python=qgis_python,
                                     qgis_app=qgis_app, timeout=timeout)
                result['checks'].extend(runtime['checks'])
                result['runtime'] = runtime.get('runtime', {})
                result['worker'] = runtime.get('process', {})
                expected = record['runtime']
                if not expected['distribution_source']:
                    result['checks'].append(finding('runtime:distribution_source', 'blocked', 'Record the QGIS distribution source'))
                for key in ('qgis_version', 'python_version', 'platform'):
                    if not expected[key] or expected[key] != result['runtime'].get(key):
                        result['checks'].append(finding('runtime:' + key, 'blocked',
                            f'Registered {key} must match measured runtime', expected=expected[key],
                            actual=result['runtime'].get(key)))
                if bool(runtime['checks']) and all(c['status'] in {'pass', 'warning'} for c in runtime['checks']):
                    copied = work / 'relocated'
                    copied.mkdir()
                    # Materialize declared dependencies only. No plugin caches or neighboring files.
                    names = {record['project']['file']}
                    names.update(a['path'] for a in record['assets'] if a['path'])
                    for name in names:
                        dest = contained(copied, name)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(contained(root, name), dest)
                    moved = run_worker(copied, record, work / 'relocation-run', qgis_python=qgis_python,
                        qgis_app=qgis_app, timeout=timeout, isolated_from=root)
                    state = 'pass' if bool(moved['checks']) and all(c['status'] in {'pass', 'warning'} for c in moved['checks']) else (
                        'fail' if any(c['status'] == 'fail' for c in moved['checks']) else 'blocked')
                    result['checks'].append(finding('relocate', state,
                        'Isolated copy load/render with original source and networking denied', checks=moved['checks']))
                    asset = next((a for a in record['assets'] if a['path']), None)
                    if asset:
                        path = contained(copied, asset['path'])
                        path.unlink()
                        missing = check_assets(copied, record)['status'] == 'fail'
                        shutil.copy2(contained(root, asset['path']), path)
                        bad = copy.deepcopy(record)
                        bad['assets'][record['assets'].index(asset)]['sha256'] = '0' * 64
                        wrong = check_assets(copied, bad)['status'] == 'fail'
                        result['checks'].append(finding('negative', 'pass' if missing and wrong else 'fail',
                            'Missing-file and checksum-tamper checks reject disposable copies'))
                    else:
                        result['checks'].append(finding('negative', 'blocked', 'No local asset for negative checks'))
                else:
                    result['checks'].append(finding('relocate', 'blocked', 'Load/render must pass before relocation'))
                    result['checks'].append(finding('negative', 'blocked', 'Load/render must pass before negative checks'))
                from .package_tests import check_packages
                result['checks'].extend(check_packages(root, record, work / 'package-tests',
                    enabled=run_project_tests, qgis_python=qgis_python, qgis_app=qgis_app, timeout=timeout))
                after_hashes = {name: digest(contained(root, name)) for name in result['input_hashes']}
                if after_hashes != result['input_hashes'] or digest(registry) != result['registry_sha256'] or check_assets(root, record)['status'] != 'pass':
                    result['checks'].append(finding('inputs', 'fail', 'Inputs changed during validation'))
                if output:
                    dest = output / f'{index:03d}-{pid}'
                    dest.mkdir(exist_ok=True)
                    for artifact in work.rglob('layout-*'):
                        if artifact.is_file() and artifact.suffix in {'.pdf', '.png'}:
                            shutil.copy2(artifact, dest / (artifact.parent.name + '-' + artifact.name))
                    for preview in work.rglob('preview.png'):
                        shutil.copy2(preview, dest / (preview.parent.name + '-preview.png'))
                    for junit in work.rglob('*.xml'):
                        shutil.copy2(junit, dest / junit.name)
                    result['artifacts'] = str(dest)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                result['checks'].append(finding('registry', 'fail', f'Cannot validate registry: {exc}'))
    for file in project_files:
        if file.resolve() not in declared and not is_xml_companion(file, declared):
            checks.append(finding('discovery', 'fail', f'Unregistered QGIS project: {file}'))
    all_checks = checks + [c for p in report['projects'] for c in p['checks']]
    report['exit_code'] = exit_code(all_checks)
    report['status'] = {0: 'pass', 1: 'fail', 2: 'blocked'}[report['exit_code']]
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    if output:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
