"""Shared report and path operations, independent of the QGIS runtime."""
import hashlib
import re
from pathlib import Path


def finding(check_id, status, message, **evidence):
    return {'id': check_id, 'status': status, 'message': message, 'evidence': evidence}


def contained(root, value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError(f'Invalid project-relative path: {value!r}')
    p = Path(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'Path escapes project root: {value}')
    resolved = (root / p).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f'Symlink escapes project root: {value}')
    return resolved


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def exit_code(checks):
    states = {c['status'] for c in checks}
    return 1 if 'fail' in states else 2 if 'blocked' in states or not states else 0
