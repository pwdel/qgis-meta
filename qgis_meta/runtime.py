"""Run QGIS in its own interpreter with bounded time and explicit isolation."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from .common import finding


def runtime_environment(qgis_python=None, qgis_app=None):
    env = os.environ.copy()
    env.pop('PYQGIS_STARTUP', None)
    env['QT_QPA_PLATFORM'] = 'offscreen'
    if qgis_app:
        contents = Path(qgis_app).resolve() / 'Contents'
        resources = contents / 'Resources'
        versions = sorted(resources.glob('python3.*'))
        if len(versions) != 1:
            raise ValueError('QGIS app must contain exactly one bundled Python resource directory')
        lib = versions[0]
        python = str(contents / 'MacOS' / lib.name)
        env.update(PYTHONHOME=str(contents / 'Frameworks'),
                   PYTHONPATH=os.pathsep.join([str(lib / 'site-packages'), str(resources / 'qgis/python')]),
                   QGIS_PREFIX_PATH=str(resources / 'qgis'),
                   QT_PLUGIN_PATH=str(contents / 'PlugIns'),
                   PROJ_DATA=str(resources / 'qgis/proj'),
                   GDAL_DATA=str(resources / 'qgis/gdal'))
    else:
        python = str(qgis_python or sys.executable)
    return python, env


def isolated_command(command, original_root):
    """Deny source reads and networking at the OS boundary, or decline the gate."""
    root = str(original_root.resolve())
    if sys.platform == 'darwin' and shutil.which('sandbox-exec'):
        # JSON quoting produces a valid quoted Sandbox Profile Language string.
        profile = '(version 1)(allow default)(deny network*)(deny file-read* (subpath ' + json.dumps(root) + '))'
        return ['sandbox-exec', '-p', profile, *command]
    if sys.platform.startswith('linux') and shutil.which('bwrap'):
        return ['bwrap', '--die-with-parent', '--ro-bind', '/', '/', '--bind', tempfile.gettempdir(),
                tempfile.gettempdir(), '--tmpfs', root, '--unshare-net', '--', *command]
    raise ValueError('Relocation requires sandbox-exec on macOS or bubblewrap on Linux to deny original reads and network')


def run_worker(root, record, work, *, qgis_python=None, qgis_app=None, timeout=120, isolated_from=None):
    work.mkdir(parents=True, exist_ok=True)
    request = work / 'request.json'
    response = work / 'response.json'
    request.write_text(json.dumps({'root': str(root), 'registry': record, 'output': str(work),
        'isolation_source': str(isolated_from / record['project']['file']) if isolated_from else None,
        'isolation_source_existed': (isolated_from / record['project']['file']).is_file() if isolated_from else False,
        'isolation_method': 'bwrap' if sys.platform.startswith('linux') else 'sandbox-exec'}))
    try:
        python, env = runtime_environment(qgis_python, qgis_app)
        command = [python, str(Path(__file__).with_name('worker.py')), str(request), str(response)]
        if isolated_from:
            command = isolated_command(command, isolated_from)
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env,
                              cwd=work)
        if proc.returncode != 0 or not response.exists():
            return {'checks': [finding('load', 'blocked', 'QGIS worker could not complete',
                returncode=proc.returncode, diagnostic=(proc.stderr or proc.stdout)[-4000:])],
                'runtime': {}, 'process': {'returncode': proc.returncode}}
        data = json.loads(response.read_text())
        data['process'] = {'returncode': proc.returncode, 'diagnostic': proc.stderr[-4000:]}
        return data
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {'checks': [finding('load', 'blocked', f'QGIS runtime unavailable: {exc}')], 'runtime': {}}
