"""Execute explicitly trusted project test nodes; require fresh passing evidence."""
import subprocess
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from .common import contained, finding
from .runtime import runtime_environment


def check_packages(root, record, work, *, enabled=False, qgis_python=None, qgis_app=None, timeout=120):
    results = []
    tests = {t['id']: t for t in record['tests']}
    for package in record['packages']:
        if package['status'] != 'used':
            continue
        if enabled and 'version' in package:
            try:
                python, env = runtime_environment(qgis_python, qgis_app)
                probe = subprocess.run([python, str(Path(__file__).with_name('package_probe.py')), package['id']],
                    cwd=root, env=env, timeout=timeout, capture_output=True, text=True)
                identity = json.loads(probe.stdout) if probe.stdout else {}
                matches = probe.returncode == 0 and identity.get('version') == package['version']
                results.append(finding('package-version:' + package['id'], 'pass' if matches else 'blocked',
                    'Installed package identity compared with registry', expected=package['version'], actual=identity))
                if not matches:
                    continue
                source_matches = bool(package.get('source_revision') and
                    identity.get('source_revision') == package['source_revision'] and identity.get('source_clean'))
                results.append(finding('package-source:' + package['id'], 'pass' if source_matches else 'blocked',
                    'Installed clean Git source matches registry' if source_matches else
                    'Installed source identity is not verified; archive-installed packages need an artifact verifier'))
            except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                results.append(finding('package-version:' + package['id'], 'blocked', str(exc)))
                continue
        for tid in package['test_ids']:
            if not enabled:
                results.append(finding('package:' + tid, 'blocked',
                    'Project integration test not executed; use --run-project-tests for trusted project code'))
                continue
            if tid not in tests:
                results.append(finding('package:' + tid, 'blocked', 'Required integration test is missing'))
                continue
            work.mkdir(parents=True, exist_ok=True)
            junit = work / (tid + '.xml')
            test = tests[tid]
            try:
                # Paths remain project-contained; subprocess receives an argument list, never a shell string.
                file, *selectors = test['nodeid'].split('::')
                contained(root, file)
                python, env = runtime_environment(qgis_python, qgis_app)
                command = [python, '-m', 'pytest', test['nodeid'], '--rootdir', str(root),
                           '--strict-markers', '-o', 'addopts=', '-o', 'xfail_strict=true', '-p', 'no:cacheprovider',
                           '--junitxml=' + str(junit), '-q']
                proc = subprocess.run(command, cwd=root, env=env, timeout=timeout, text=True, capture_output=True)
                cases = ET.parse(junit).getroot().findall('.//testcase') if junit.exists() else []
                skipped = sum(c.find('skipped') is not None for c in cases)
                failed = sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
                state = 'pass' if proc.returncode == 0 and cases and not skipped and not failed else (
                    'blocked' if skipped or not cases else 'fail')
                results.append(finding('package:' + tid, state, 'Project-supplied integration test result',
                    nodeid=test['nodeid'], collected=len(cases), skipped=skipped, failed=failed,
                    returncode=proc.returncode, command=command, diagnostic=(proc.stdout + proc.stderr)[-4000:]))
            except (OSError, ValueError, ET.ParseError, subprocess.TimeoutExpired) as exc:
                results.append(finding('package:' + tid, 'blocked', str(exc)))
    return results
