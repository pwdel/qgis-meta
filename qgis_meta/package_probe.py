"""Print installed package identity using the selected QGIS Python interpreter."""
import configparser
import hashlib
import importlib.metadata
import importlib.util
import json
import sys
import subprocess
from pathlib import Path

MODULES = {'qgis-resource-sharing': 'qgis_resource_sharing',
           'quickmapservices': 'quick_map_services', 'quickosm': 'QuickOSM', 'geopacker': 'geopacker'}


def probe(package_id):
    if package_id == 'pytest-qgis':
        return {'version': importlib.metadata.version('pytest-qgis')}
    module = MODULES[package_id]
    spec = importlib.util.find_spec(module)
    if spec is None or not spec.origin:
        raise ValueError(f'{module} is not available in the configured QGIS test environment')
    root = Path(spec.origin).parent
    config = configparser.ConfigParser()
    config.read(root / 'metadata.txt')
    files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.py', '.ui', '.json', '.qml', '.svg'}
             and '__pycache__' not in p.parts}
    git = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    status = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=all'], capture_output=True, text=True)
    return {'version': config['general']['version'], 'module': module, 'files': files,
            'source_revision': git.stdout.strip() if git.returncode == 0 else None,
            'source_clean': status.returncode == 0 and not status.stdout.strip()}


if __name__ == '__main__':
    try:
        print(json.dumps(probe(sys.argv[1])))
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        raise SystemExit(2)
