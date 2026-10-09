# Registry templates

Use [the v2 example](qgis-registry-v2.example.json) with the [shared engine](../governance/validation-engine.md). The registry directory is the project root; the QGIS file and assets may occupy sibling subdirectories. Baseline tests belong to the engine; only package-specific tests appear in v2 `tests`. Render settings are required.

## Historical v1 example


Copy [qgis-registry.example.json](qgis-registry.example.json) to `qgis-registry.json` beside each map's primary project file. The example is synthetic and deliberately `draft`: no actual project, dependencies, test functions, layers or runtime evidence are supplied. Its null runtime/revision fields and empty inventory must be completed from the real project. Do not turn example test names into claims that those tests exist.

The example demonstrates the required record shape and accounts for all five catalog packages. It is schema-valid, not project-compliant. Draft/blocked records may carry unknown runtime/revision values; a compliant record may not.

Populate layer and asset records using [the schema](../schemas/qgis-registry.schema.json), and follow [the project contract](../governance/project-contract.md). Every `used` package requires an exact version, immutable source commit or archive hash, and all of its catalog test IDs. Package test IDs must correspond to records in `tests` and executable test implementations in the consuming project.

JSON Schema checks structure. An adoption validator must additionally check catalog revision agreement, cross-references, unique asset/layer/test IDs, file/hash/path validity, min/max count consistency, exact package-test coverage, test collection and authentic current evidence. The shared engine implements these checks for v2; migrate v1 records explicitly using the engine guide. Neither template is a complete runnable map.
