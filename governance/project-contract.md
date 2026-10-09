# Project registry contract — version 2

Authority: **local project policy**, adopted 2026-10-09. These requirements govern projects adopting qgis-meta; they are not requirements imposed by QGIS or plugin publishers.

Every individual map project MUST keep a `qgis-registry.json` at its project root, which contains its `.qgs`/`.qgz` and asset subdirectories, including when several map projects share a repository. Validate it against [schema version 2](../schemas/qgis-registry-v2.schema.json). A repository-wide registry cannot substitute for individual project records. Start from the [synthetic example](../templates/qgis-registry-v2.example.json), replacing the example values with measured facts.

This is our inventory and test contract. QGIS and the listed plugins do not natively consume it. Plugin compliance means that recorded inputs, outputs and settings pass our [integration requirements](integration-tests.md) using the actual selected plugin version. It does not mean upstream certification.

## Required records

- **Governance:** exact qgis-meta Git commit and schema version. The contract and package catalog at that commit control the adoption.
- **Project:** stable ID, relative project-file path, intended online/offline/print outputs and project CRS.
- **Runtime:** exact QGIS and Python versions, OS/architecture, recommended `.venv` location, and a project-local dependency lock file. Record the tested runtime, not a guessed compatible version.
- **Packages:** every ID in the pinned [package catalog](../packages/catalog.json) with `used`, `not-used` or `blocked` status and a reason. Used entries record exact versions, immutable source references or archive hashes, build/test/open purpose, config/asset paths and integration-test IDs. A required incompatible dependency is blocked; it cannot be relabeled not-used to pass.
- **Assets:** project-local paths and SHA-256 hashes for data, styles, SVGs, images, attachments and auxiliary databases; public provenance/source URL, license/terms references, attribution, acquisition date and download recipe where applicable. Include shapefile sidecars and dependencies referenced by styles/forms/layouts. Never store credentials in URLs.
- **Layers:** stable QGIS layer ID, asset IDs, provider, CRS, geometry, required fields, explicit feature-count bounds and filter expression. Raster layers may have null feature counts; document raster-specific assertions separately. Online layers still need an asset entry describing their service.
- **Tests and evidence:** test IDs and kinds, package mapping, repository-relative pytest node IDs, fresh pass/fail/blocked/not-run status and a report path when executed. Evidence includes tested repository commit plus working-tree diff hash when dirty, runtime/package versions, UTC time, command, exit code, collected/passed/failed/skipped counts, asset hashes and render outputs.

Paths resolve from the registry directory, use `/`, stay within the project directory after resolving symlinks, and cannot contain `..` components or absolute paths. QGIS datasource URIs must be parsed with the provider's URI facilities before comparing their file components. Service URLs belong in asset `source_url`, not a file-path field. Test node IDs resolve from the same directory. Every linked file and referenced ID must actually exist; JSON Schema alone cannot establish that.

## Lifecycle and acceptance

`draft` records work in progress. `blocked` records missing prerequisites. `compliant` requires all baseline gates and every used package's integration tests to pass on the recorded runtime, plus review of the report. JSON syntax, schema validation, a successful import, or a plugin's declared compatibility is insufficient.

Only `not-used` packages with a substantive reason are exempt from their package-specific tests. All projects still require baseline integration tests. Unavailable QGIS, incompatible plugins, unavailable required services, missing files, skipped or uncollected required tests, and stale evidence prevent compliant status. Optional online-service failures must be reported; they need not block a separately tested offline output that excludes that service.

Re-run affected tests after changes to project files, data, styles, plugin configuration, dependency versions, or governance revision. Re-run the complete acceptance suite before distribution. A previous report does not validate a new revision. Record any temporary exception with scope, owner, reason, review date and evidence in project documentation; exceptions keep the project draft or blocked, rather than silently weakening this contract.

Existing maps are **unassessed** until they have a populated registry and passing evidence. Introducing this policy does not retroactively certify or modify them.

## Download and storage policy

Acquisition is a separate, explicit preparation step; tests MUST NOT silently repair or download missing dependencies. Store its command/script, endpoint/query, expected destination, acquisition date, license decision and checksum. Test the preparation step in a disposable directory when it changes, including checksum mismatch and unavailable-source failures. Cache reuse must verify hashes.

Keep redistributable modest-size assets in Git. For larger assets choose Git LFS or documented external storage, recording how a fresh checkout is hydrated. An unhydrated LFS pointer is not valid layer data. Offline-required assets must be present before validation; hosted basemaps alone cannot satisfy offline requirements. Public service availability and upstream dataset revisions are separate from repeatable tests against pinned local data.

## Repository boundaries

qgis-meta holds generic policies, the package catalog, schemas and synthetic examples. Each consuming project holds its registry, dependency locks, plugin settings, data, private acquisition recipes, test implementations and reports. The [shared engine](validation-engine.md) lives in qgis-meta and is consumed at a pinned revision. It owns baseline gates; project `tests` records refer only to package-specific tests. The registry includes `render` expectations. See the engine guide for supported workflows and explicit v1 migration.

Private map paths, coordinates, inventories and reports remain in private repositories. Publication and land-access decisions continue to follow [governance](../GOVERNANCE.md) and the existing rulesets.
