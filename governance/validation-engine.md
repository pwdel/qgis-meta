# Shared validation engine

`qgis-meta` accepts a repository directory, an individual project directory, or a `qgis-registry.json` file. All inputs use the same Python API and command-line entry point. It validates registered projects and flags unregistered `.qgs`/`.qgz` files. A byte-identical `.qgs` companion to a registered `.qgz` is accepted; a divergent companion fails discovery.

## Install in a virtual environment

From a pinned qgis-meta checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/qgis-meta validate /path/to/map-repository --mode static
```

Static mode validates registries, references, paths and asset hashes. Its success at those stages still returns exit code **2**, because QGIS integration has not run. Empty repositories are blocked; an unregistered QGIS file is a failure. The target is never downloaded or repaired automatically.

Full validation needs a QGIS-aware runtime. The engine venv and the QGIS interpreter may use different Python versions; they communicate through JSON files in a temporary directory.

```sh
# macOS: explicit application bundle; no changes to the app installation
.venv/bin/qgis-meta validate /path/to/map-repository \
  --qgis-app /Applications/QGIS-final-4_2_3.app

# Linux/other configured QGIS Python environments
.venv/bin/qgis-meta validate /path/to/map-repository \
  --qgis-python /path/to/qgis-aware/python
```

For the macOS bundle, the launcher locates its bundled Python libraries, QGIS providers, Qt plugins and PROJ/GDAL data. Other distributions use their configured interpreter environment. QGIS/Qt/Python/platform versions are measured; missing or mismatched registry runtime pins block acceptance.

Editable installation is recommended: registry `governance_revision` must match the clean engine checkout. For a wheel/non-editable install, supply `--governance-root /path/to/pinned/qgis-meta`. Installed engine/contract hashes must match that checkout. An absent checkout, modified governance or mismatched revision blocks acceptance. The engine does not fetch arbitrary historical revisions on your behalf.

## Project layout and registry v2

```text
map-repository/
  projects/
    example/
      qgis-registry.json
      maps/example.qgz
      data/locations.geojson
      styles/
      symbols/
      requirements-qgis.lock.txt
      tests/
```

The registry directory is the project root. All registry paths resolve from it, while QGIS's internal relative datasources resolve from the QGIS project file. The engine checks both. Assets may be in sibling directories underneath this root, but may not escape it through `..`, absolute paths or symlinks.

Use [schema v2](../schemas/qgis-registry-v2.schema.json) and the [v2 draft template](../templates/qgis-registry-v2.example.json). V2 moves baseline gates into the shared engine: `tests` lists project-specific package tests only, and may be empty when all catalog packages are not-used. Each used package still needs every required catalog test ID. New `render` expectations specify extent, CRS, width, height and minimum nonbackground pixel count. Layer `visible` is optional and defaults to true when omitted.

The original [v1 schema](../schemas/qgis-registry.schema.json) is retained. Migration is explicit: set `schema_version` to 2, retain layer/asset/runtime/package records, remove baseline entries from `tests`, add `render`, and update the governance commit pin. Do not copy a historical `compliant` label or test results as proof of a fresh run. The engine never rewrites registry status.

## Checks and current support

- **Registry:** schema, catalog coverage, duplicate IDs, references, required files, path containment, count bounds and immutable package source references.
- **Assets:** SHA-256 and presence, including detection of unhydrated Git LFS pointers.
- **Load:** real `QgsProject.read`, exact layer-ID set, project/layer CRS, provider, geometry, required fields, filter, count bounds, visibility and ability to read a feature.
- **Render:** actual map rendering at declared extent/output size; error collection and minimum nonbackground content. This is a rendering smoke test, not visual-design approval or proof that every symbol is readable.
- **Relocate:** copy only the project and declared assets to a new directory, then load/render in a fresh process and profile with original project reads and networking denied by the OS. `sandbox-exec` on macOS or `bwrap` on Linux is required; unavailable isolation blocks the gate. Windows needs an isolation adapter before this gate can pass. Never silently substitute a normal file copy for this test.
- **Negative:** remove an asset and falsify a hash in disposable copies; verify the same asset validator rejects each mutation. Native regression tests separately verify QGIS rejects missing data.
- **Packages:** verify installed package version and clean Git source identity, then execute the registered pytest nodes when explicitly enabled. Required skipped, xfailed, absent, failing or uncollected tests cannot pass. Unavailable plugins/interpreters remain blocked.

This first engine supports local OGR GeoJSON/GeoPackage and GDAL GeoTIFF sources, single-symbol renderers with simple marker/line/fill symbols, and self-contained SVG markers without active data-defined properties. Compound formats such as VRT and unsupported providers are blocked **before** project loading. Online providers need dedicated validation support and are currently blocked. Joins, auxiliary layers, external forms, labels, map themes, print layouts and more complex symbol types need dedicated checks and currently block full acceptance. Native regression coverage currently concentrates on GeoJSON and simple markers; other admitted formats require project-specific acceptance evidence before declaring a supported distribution matrix.

Project supplied plugin tests provide the assertions for their actual workflows (collection installation, service requests, acquisition and packaging). The engine supplies execution and fresh result collection, not prewritten upstream-plugin integration adapters. Those tests must meet [the package-specific requirements](integration-tests.md); merely importing a plugin is insufficient.

## Trusted project test execution

Ordinary validation does not execute Python from the map repository. To run its authored integration tests:

```sh
.venv/bin/qgis-meta validate /path/to/trusted-project \
  --qgis-python /path/to/qgis-test-venv/bin/python \
  --run-project-tests
```

The selected interpreter must have pytest, PyQGIS and the declared plugins available. Archive/wheel-installed packages currently remain blocked at the source-identity gate even if their authored tests pass; a verifier matching installed content to the pinned archive is not implemented. Clean Git-installed desktop plugins can satisfy this gate. Desktop plugins need to be importable from the configured dedicated test profile/Python path; the engine does not install them. Use a QGIS-aware virtual environment as described in [Python environments](python-environments.md). Any needed live-service access occurs only in the authored, explicitly enabled test workflow. Treat such a project like any repository whose Python tests you run.

## Reports and automation

Default CLI reports go in the supplied directory's `reports/<UTC-run-id>/` (or the registry's parent for a file target). Override with `--output /path/to/private/report-directory`. Existing named outputs are reused only when explicitly supplied; prefer a fresh output directory for each run. Previews and `report.json` remain with the consuming project. The engine API writes only when `output` is supplied.

Reports include project/registry/test/config/lockfile hashes, asset hashes, engine source/contract hashes, Git commit/diff metadata, timestamps, runtime, check statuses and plugin test counts/exit codes. Inputs are checked again after full execution to detect mutations. Results apply to these exact inputs; a working-tree change invalidates prior evidence. Reports may contain private paths and map data: keep them in the map repository or private CI artifacts.

| Exit | Meaning |
| --- | --- |
| 0 | All implemented required acceptance gates passed on this run. |
| 1 | At least one validation failure. |
| 2 | No failures, but required work is blocked/incomplete (including static-only runs). |

A plugin's registry status or an old report cannot override fresh results. A technical pass does not establish licensing, land access or cartographic quality.

```python
from qgis_meta import validate

report = validate(
    '/path/to/map-repository',
    qgis_app='/Applications/QGIS-final-4_2_3.app',
    output='/path/to/private/reports/current',
)
raise SystemExit(report['exit_code'])
```

The CLI is suitable for an organization repository's shell script without another wrapper framework:

```sh
/path/to/qgis-meta/.venv/bin/qgis-meta validate "$PROJECT_REPO" \
  --qgis-python /path/to/qgis-aware/python
```

## Engine regression tests

```sh
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m unittest discover -s tests -v
QGIS_META_QGIS_APP=/Applications/QGIS-final-4_2_3.app \
  .venv/bin/python -m unittest discover -s tests -v
```

The first command runs portable tests and explicitly skips native QGIS tests if no runtime is selected. For Linux set `QGIS_META_QGIS_PYTHON` instead. Native tests use synthetic data, assert real failures for wrong filters/counts/missing data/blank renders, and test relocation isolation when the host supports it. The v1 schema regression suite remains intact. No private project fixtures are included in qgis-meta.
