# Project governance implementation plan

**Goal:** Establish the shared governance contract in qgis-meta before adopting it in individual maps.

**Scope:** Documentation, dependency declarations, JSON Schema and a synthetic registry example. This change does not install QGIS plugins, change map data, or deliver an integration-test runner.

## Tasks

- [x] Define mandatory per-project registries, dependency pins, asset provenance, and adoption states.
- [x] Catalog Resource Sharing, QuickMapServices, QuickOSM, Geopacker and pytest-qgis, with distinct integration acceptance criteria for each.
- [x] Add a versioned JSON Schema and a synthetic example. Require an explicit use/not-used decision for every catalog package.
- [x] Recommend QGIS-aware Python virtual environments, separate governance checks from QGIS runtime checks, and document lock-file requirements.
- [x] Index standard QGIS Layer Properties and connect governance to existing catalog navigation.
- [x] Validate schema and example, exercise rejection cases, inspect local links and git diff. Report runtime integration tests as not implemented in this governance phase.

## Review criteria

No private map inventory enters this public repository. Plugin compatibility claims distinguish publisher declarations from execution evidence. Missing dependencies, skipped required tests, unresolved data and missing evidence cannot produce a compliant result. Documentation does not imply that plugins understand our custom registry. Existing projects are unassessed until adopted and tested.

## Verification

Nine structural contract tests pass, including negative cases for unsafe paths, missing catalog packages, incomplete used-package declarations, absent reports, absent baseline gates and online services mislabeled as offline data. The governance dependencies were installed into a local virtual environment and the resolved versions recorded. Runtime QGIS/plugin integration tests and project adoption remain outside this first governance change.
