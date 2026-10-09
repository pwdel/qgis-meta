# Package catalog

[Machine-readable catalog](catalog.json) and [integration acceptance criteria](../governance/integration-tests.md). These are dependency declarations and source pointers, not vendored plugin ZIPs or an installer. Third-party code and assets retain their upstream licenses.

Every project registry must account for every catalog ID at its pinned qgis-meta revision. Mark packages used, not-used with a reason, or blocked. Do not install the entire catalog simply to satisfy governance. Used packages require all listed integration-test IDs and exact tested versions plus immutable source/hash records. Listed candidate versions are discovery evidence, not project pins or local test results.

| Package | Candidate version checked 2026-10-09 | Declared QGIS range | Purpose |
| --- | --- | --- | --- |
| [QGIS Resource Sharing](https://plugins.qgis.org/plugins/qgis_resource_sharing/) | 1.2.0 | 3.34.6–3.99.0 | Install reusable collections of styles, symbols and scripts. QGIS 4 compatibility unresolved. |
| [QuickMapServices](https://plugins.qgis.org/plugins/quick_map_services/) | 1.5.2 | 3.32.0–4.99.0 | Discover and add online basemaps/services; not an offline-data entitlement. |
| [QuickOSM](https://plugins.qgis.org/plugins/QuickOSM/) | 2.5.4 | 3.40.0–4.99.0 | Query/download OSM data and persist selected results. |
| [Geopacker](https://plugins.qgis.org/plugins/geopacker/) | 1.6 | 3.0.0–4.99.0 | Package project dependencies and rewrite paths. Verify roundtrip on actual assets. |
| [pytest-qgis](https://github.com/GispoCoding/pytest-qgis) | Resolve an exact version during environment setup | Upstream documents QGIS >=3.34 | Initialize real QGIS for Python tests; GUI interface fixtures include stubs. |

Publisher-declared compatibility above was inspected in the linked listings. None of these rows asserts local runtime testing. Resource Sharing may be omitted with the reason that built-in Style Manager imports are used instead; that replacement still requires baseline asset and rendering tests.

Python dependency inputs: [governance](requirements-governance.txt), [integration](requirements-integration.txt). Follow [virtual-environment guidance](../governance/python-environments.md), then commit the resolved lock in the consuming project. Do not `pip install` QGIS desktop plugins.

The [governance lock](requirements-governance.lock.txt) records the dependency resolution used for structural contract tests on Python 3.14.6/macOS arm64. An integration lock must be generated and tested in each consuming project’s actual QGIS environment.

[Engine test lock](requirements-engine-test.lock.txt) records the Python 3.14.6/macOS arm64 environment used for engine tests. Install the local engine separately with `pip install -e .`; the lock contains only third-party packages and no machine-local editable path. Native QGIS runs in its own interpreter.
