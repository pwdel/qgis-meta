"""Deterministic discovery; ignore caches, never traverse directory symlinks."""
import os
import zipfile
from pathlib import Path
from .common import finding

EXCLUDED = {'.git', '.venv', '.venv-governance', '.pytest_cache', '__pycache__',
            'node_modules', 'reports', '.qgis-settings'}


def discover(target):
    target = Path(target).absolute()
    if target.is_file():
        if target.name != 'qgis-registry.json':
            return [], [], [finding('discovery', 'fail', 'File target must be qgis-registry.json')]
        return [target], [], []
    if not target.is_dir():
        return [], [], [finding('discovery', 'fail', f'Target does not exist: {target}')]
    registries, projects = [], []
    for folder, dirs, files in os.walk(target, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith('.venv')
                         and not (Path(folder) / d).is_symlink())
        for name in sorted(files):
            p = Path(folder) / name
            if name == 'qgis-registry.json':
                registries.append(p)
            elif p.suffix.lower() in {'.qgs', '.qgz'}:
                projects.append(p)
    return registries, projects, []


def is_xml_companion(path, declared):
    """Allow only byte-identical QGS companions to a registered QGZ."""
    if path.suffix != '.qgs':
        return False
    archive = path.with_suffix('.qgz')
    if archive.resolve() not in declared or not archive.is_file():
        return False
    try:
        with zipfile.ZipFile(archive) as z:
            names = [n for n in z.namelist() if n.endswith('.qgs')]
            return len(names) == 1 and z.read(names[0]) == path.read_bytes()
    except (OSError, zipfile.BadZipFile):
        return False


def discover_artifacts(target):
    """Find declarative checks without traversing cache or symlink directories."""
    target = Path(target).absolute()
    if target.is_file() or target.is_symlink():
        return [target] if target.name == 'qgis-checks.json' else []
    found = []
    if not target.is_dir():
        return found
    for folder, dirs, files in os.walk(target, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith('.venv')
                         and not (Path(folder) / d).is_symlink())
        if 'qgis-checks.json' in files:
            found.append(Path(folder) / 'qgis-checks.json')
    return found
