# Integration-test requirements

Authority: local project policy. These are mandatory acceptance criteria. The [shared engine](validation-engine.md) implements baseline gates and executes project-authored package tests; unsupported workflows remain blocked. Use Python, pytest and pytest-qgis as described in [Python environments](python-environments.md).

## Baseline gates for every project

| Gate ID | Required assertion |
| --- | --- |
| `registry` | Registry matches the pinned schema; catalog coverage, unique IDs, referenced IDs, file existence, path containment and dependency pins are checked. |
| `assets` | All offline dependencies exist, are hydrated, and match recorded hashes. Missing data fails without automatic repair. |
| `load` | Real `QgsProject.read()` succeeds with layer resolution enabled. Actual and expected layer-ID sets match, every required layer is valid, fields/CRS/provider/geometry/filter/count expectations hold. No `DontResolveLayers` shortcut. |
| `render` | QGIS renders the declared extent, scale, CRS and output size; inspect renderer errors and assert expected content, not merely that a PNG exists. Record image and settings for human design review. |
| `relocate` | Copy the project and declared dependencies to a new directory; open and render in a fresh QGIS process/profile with the original location inaccessible. Resolve all file dependencies inside the copy, including SVGs, layout images and auxiliary storage. Disable network for offline output. |
| `negative` | Deliberately remove a required asset and alter a checksum in a disposable copy. The acceptance suite must fail for each expected reason. |

For counts, include empty-layer expectations explicitly. A nonzero total layer count does not prove all intended categories exist. Rendering success alone does not prove readable labels or correct visual semantics; the approved preview and human review remain part of design acceptance.

## Package-specific requirements

The stable test IDs below appear in [the package catalog](../packages/catalog.json). Require every ID for a `used` package; `not-used` requires a reason. Use synthetic/public fixtures for shared tests. Real private-project checks execute in the private project environment.

| Package / test ID | Integration boundary and required evidence |
| --- | --- |
| QGIS Resource Sharing / `resource-sharing-install` | With the actual plugin in a disposable QGIS profile, install a pinned collection from the recorded source. Verify expected collection assets and hashes, and import/use the expected style items. |
| QGIS Resource Sharing / `resource-sharing-portable` | Materialize selected redistributable assets inside the project; render a layer using them in a clean profile where the Resource Sharing cache is absent. Detect missing external SVGs/fonts explicitly. |
| QuickMapServices / `qms-service` | Use the actual plugin to add the selected catalog service. Check resulting provider, normalized endpoint, CRS and attribution against the registry; request/render an actual response in a separately marked network test. A valid provider object alone is insufficient. |
| QuickMapServices / `qms-offline` | For an offline output, verify required context comes from a separately permitted local asset and render with networking disabled. For online-only projects, assert online-only classification and verify unavailable-service failure handling. |
| QuickOSM / `quickosm-acquire` | Execute the recorded query/extent through the actual plugin against its declared endpoint in a network test. Verify geometry, required fields and explicit count bounds. Save the output to the declared project path; record its acquisition hash. |
| QuickOSM / `quickosm-reopen` | Reopen the persisted output in a fresh QGIS process without network or temporary layers. Assert schema, CRS and expected data; pinned snapshot tests must not depend on the current live OSM count. |
| Geopacker / `geopacker-roundtrip` | Run the actual plugin on a disposable project, extract its output into a new directory and load/render it with original files inaccessible. Check all supported declared vectors, rasters, styles, layout images and auxiliary assets; unsupported required assets block acceptance. |
| Geopacker / `geopacker-missing` | Remove a required input in a disposable fixture. The workflow must report the missing dependency and must not certify the produced bundle as complete. A successful archive operation alone is insufficient. |
| pytest-qgis / `pytest-qgis-runtime` | Run a collected test using `qgis_app`/`qgis_new_project` with the real PyQGIS provider. Open a saved fixture and check a real feature. Record actual QGIS/Python/Qt and package versions. |
| pytest-qgis / `pytest-qgis-failure` | Invoke a child test run with a deliberately broken project dependency. Assert its failure exit code and expected diagnostic, proving failures propagate through the test harness. |

Mocks may supplement unit tests but cannot satisfy these plugin integration gates. pytest-qgis's stubbed `iface` is not evidence that a GUI-only plugin workflow works. Where a plugin lacks a suitable noninteractive API, use a real desktop integration harness and capture version, actions and results; leave the gate blocked until that evidence exists.

## Execution and reporting

In registry v2 the engine owns baseline tests. Project-specific package test implementations expose pytest node IDs recorded in `tests[].nodeid`. Use markers `qgis`, `integration`, `network` and `packaging` to select jobs. Register markers in pytest configuration and use strict markers. A fast offline job and a separately enabled live-service job make failures attributable; excluding the live job cannot certify a required online workflow.

Store reports under the consuming project's `reports/` directory or restricted CI artifacts. Record the fields specified in the [project contract](project-contract.md), and retain preview images with their input hashes. A required test that is skipped, xfailed, not collected or blocked is not a pass. Zero collected tests must fail acceptance. Gate success requires every mandatory test ID to map to executed passing evidence; a generic pytest exit code alone is not enough.

Choose a tested runtime matrix per project. An upstream `qgisMaximumVersion` only declares support; it does not prove a specific OS/runtime/plugin combination has passed. Test each supported distribution target before calling it supported.
