# Optional pytest-qgis integration tests

The root `integration` extra installs pytest and pytest-qgis. Both, including
transitive dependencies, are resolved in `uv.lock`:

```sh
uv sync --locked --extra integration
```

This does **not** install PyQGIS. `qgis.core` and `qgis.PyQt` come from a compatible
QGIS distribution. The test process must use that distribution's Python and
libraries, not an unrelated Python just because it has pytest installed.

The existing CLI/native suite uses PyQGIS directly. The additional tests in
`tests/integration/` use pytest-qgis's real `qgis_app` and `qgis_new_project`
fixtures. Their `iface` helper is a stub; these tests do not certify desktop-plugin
GUI workflows. They are smoke tests, not a replacement for registry, relocation,
layout-quality, licensing or domain-policy acceptance.

## Tests

- Read a saved project and require valid project/layer CRS and valid layers.
- Read actual features from nonempty vector layers.
- Render visible layers to a nonblank image, requiring a valid project CRS first.
- Save a synthetic project, remove its input data, and assert an independent child
  pytest run fails with the expected missing-dependency assertion and JUnit failure.

Without `--map-project`, the suite creates a temporary synthetic project. With it,
the specified file is read without saving changes. Use a disposable copy of a
trusted project. Reports and previews may contain private paths/data and belong in
private storage. A render smoke pass does not establish cartographic correctness.

## Configured QGIS Python environment

After installing the locked integration dependencies in a dedicated QGIS-aware
environment, run with that environment's interpreter:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest \
  -p pytest_qgis.pytest_qgis tests/integration \
  --map-project /absolute/path/to/map.qgz \
  -o qgis_gui_enabled=false -o junit_family=legacy -p no:cacheprovider \
  --junitxml /private/report-directory/junit.xml
```

Omit `--map-project` to run the synthetic baseline. Explicit plugin loading keeps
unrelated installed pytest plugins out of this process.

## macOS QGIS app: isolated dependencies

Tested with QGIS 4.2.3 / its Python 3.12.11 and pytest-qgis 4.1.1. This records a
tested combination, not universal compatibility. It does not alter the app bundle.

From this repository root, export the lock and install into a separate target
matching the app's Python minor version (3.12 for this example):

```sh
uv export --locked --extra integration --no-emit-project --quiet \
  --format requirements-txt --output-file /tmp/qgis-integration-requirements.txt
uv pip install --python-version 3.12 --target /tmp/qgis-integration-deps \
  --requirements /tmp/qgis-integration-requirements.txt
```

Then launch through the same native environment setup used by the public engine.
Set `MAP_PROJECT` to a local QGS/QGZ if desired; omit it for synthetic fixtures.
Choose an unused report directory because pytest clears its `--basetemp` on reruns.

```sh
uv run --locked python - <<'PY'
import os
import subprocess
from pathlib import Path
from qgis_meta.runtime import runtime_environment

root = Path.cwd()
output = root / 'reports/pytest-qgis'
output.mkdir(parents=True, exist_ok=True)
python, env = runtime_environment(qgis_app='/Applications/QGIS-final-4_2_3.app')
env['PYTHONPATH'] = '/tmp/qgis-integration-deps' + os.pathsep + env['PYTHONPATH']
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
command = [python, '-m', 'pytest', '-p', 'pytest_qgis.pytest_qgis',
           str(root / 'tests/integration'), '-o', 'qgis_gui_enabled=false',
           '-o', 'junit_family=legacy', '-p', 'no:cacheprovider',
           '--basetemp', str(output / 'temporary'),
           '--junitxml', str(output / 'junit.xml'), '-v']
if os.environ.get('MAP_PROJECT'):
    command += ['--map-project', os.environ['MAP_PROJECT']]
raise SystemExit(subprocess.run(command, env=env).returncode)
PY
```

On this macOS host, the shell sandbox aborted pytest-qgis's Qt fixture startup
before collection; execution outside that sandbox succeeded. This is distinct
from test assertion failures. Inspect the exit code and JUnit output; a crash or
uncollected test is not a pass.

The lightweight unittest suite remains runnable without QGIS. Installing the
integration extra alone cannot make native imports available in a generic uv venv.
