# Python and virtual environments

**Recommendation:** Python with a project-local `.venv`, created from a Python interpreter compatible with the project's QGIS build. Python's minor version, architecture, Qt bindings and QGIS native libraries must agree. Record exact runtime versions and resolved dependencies in the registry and a lock file.

Use two environments where useful:

- A lightweight governance environment for JSON Schema and documentation checks; QGIS is unnecessary here.
- A QGIS-aware integration environment for pytest, pytest-qgis and the selected plugins. QGIS/PyQGIS is provided by the QGIS installation or a pinned system/container distribution, not by an ordinary `pip install qgis`.

## Root project dependencies (recommended)

Use the root `pyproject.toml` and `uv.lock` for the installable CLI:

```sh
uv sync --locked
uv run --locked qgis-meta --help
uv sync --locked --extra test
uv run --locked --extra test python -m unittest discover -s tests -v
```

`jsonschema` is the direct runtime dependency; uv locks its transitive dependencies.
The `test` extra adds pytest and its dependencies. Setuptools is declared as the
isolated build backend in `pyproject.toml`; it is not a CLI runtime dependency and
its build environment is separate from the application's uv lock. Python standard
library modules and bundled `qgis_meta` helpers are not separate dependencies.

The lock covers supported Python resolution, not a certification on every OS or
Python version. It does not provision QGIS or desktop plugins. Keep the engine
venv separate from the QGIS-selected interpreter; native imports run in that
interpreter. For native acceptance, use the clean checkout pinned by the map registry.

To update Python dependencies deliberately, run `uv lock --upgrade`, inspect the
lock diff and rerun tests. Ordinary installation uses `--locked` to reject a stale
lock instead of silently resolving new versions. See [uv projects](https://docs.astral.sh/uv/guides/projects/).

## Earlier governance-only setup

The requirements files below preserve the earlier environment snapshot. New CLI
installations should use the root project files above; these older lock files are
not the source of truth for the current CLI dependency resolution.


Run from a checkout of qgis-meta:

```sh
python3 -m venv .venv-governance
.venv-governance/bin/python -m pip install -r packages/requirements-governance.lock.txt
.venv-governance/bin/python -m unittest discover -s tests -v
```

The committed [governance lock](../packages/requirements-governance.lock.txt) was resolved and its structural tests passed on Python 3.14.6, macOS arm64. It is not a QGIS runtime lock or a cross-platform certification. The [input constraints](../packages/requirements-governance.txt) are available for deliberate dependency updates. A schema-only check must never be labeled a project-opening test.

## QGIS integration setup

On a system where `/usr/bin/python3` already imports the installed PyQGIS bindings, for example a matching Linux distribution installation:

```sh
/usr/bin/python3 -c 'from qgis.core import Qgis; print(Qgis.QGIS_VERSION)'
/usr/bin/python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r /path/to/qgis-meta/packages/requirements-integration.txt
.venv/bin/python -c 'import sys; from qgis.core import Qgis; print(sys.version); print(Qgis.QGIS_VERSION)'
.venv/bin/python -m pip freeze > requirements-qgis.lock.txt
```

The `/path/to/qgis-meta` argument denotes the actual pinned checkout. Run project tests through `.venv/bin/python -m pytest`, with `QT_QPA_PLATFORM=offscreen` for supported headless workflows. GUI-only plugin tests may need a display and a real QGIS interface.

`--system-site-packages` deliberately exposes system-installed QGIS bindings; the virtual environment alone is therefore not a complete runtime lock. Record the QGIS distribution version/source or container digest and OS/architecture as well. Review `pip freeze` for local paths or credential-bearing URLs before committing. For stronger reproducibility, use a resolver-generated lock with hashes and lock the host QGIS distribution separately.

On macOS or Windows, first identify the QGIS distribution's supported Python launcher/environment. Do not assume Homebrew Python, system Python or a copied app-bundle wrapper can load it. Verify the import both before and after venv creation. If that distribution cannot support a working venv, use a pinned Linux QGIS environment for automated tests and test the intended desktop distribution separately; do not modify QGIS's installed Python to force compatibility.

Keep `.venv`, `.venv-governance`, QGIS temporary profiles, caches and credentials out of Git. Commit dependency inputs and the tested environment's lock file. Never carry a venv directory between machines.

## QGIS plugin packages

Resource Sharing, QuickMapServices, QuickOSM and Geopacker are QGIS plugins. They are not pip requirements. Acquire their exact versions from recorded plugin releases into a dedicated test profile, record archive SHA-256 or immutable source commit, and verify installed `metadata.txt` version and QGIS compatibility. Do not treat installing Python dependencies as installing these plugins.

The registry records acquisition and integration tests; it does not install or execute packages automatically. Never evaluate registry strings as shell commands. pytest-qgis is a Python/pytest plugin, and belongs in the virtual environment.

Sources: [Python venv](https://docs.python.org/3/library/venv.html), [pytest-qgis](https://github.com/GispoCoding/pytest-qgis), [QGIS standalone applications](https://docs.qgis.org/4.2/en/docs/pyqgis_developer_cookbook/intro.html#python-applications). Reviewed 2026-10-09; no runtime matrix was certified by writing this guide.
