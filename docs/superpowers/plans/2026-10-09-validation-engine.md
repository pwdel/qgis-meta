# Shared validation engine implementation plan

User approved the package/CLI design and project-root convention on 2026-10-09.

**Goal:** Point qgis-meta at a repository, project directory or registry and obtain reproducible validation results without copying the engine into map repositories.

**Architecture:** Python package with CLI and `validate(target, mode="full")`; independent checks consume a project context and produce structured results. A separate QGIS-aware subprocess loads/renders projects. Engine reports remain with the consuming project. The registry directory is the project root and may contain sibling maps/data/styles folders.

**Constraints:** Never infer a pass from an unimplemented check, unavailable runtime, zero projects, skipped tests or previous registry status. No automatic downloads or source-project modifications. Respect existing local governance changes. No private fixtures/reports in qgis-meta.

- [x] Add failing tests for target discovery, missing registries, static validation, package coverage, evidence freshness and CLI exit codes.
- [x] Implement reusable discovery/context/report model, semantic checks, command entry point and package metadata.
- [x] Add QGIS worker tests using synthetic data and the installed runtime; implement real load/render checks and disposable relocation/negative checks. Unsupported dependency classes or unavailable isolation are blocked, not passed.
- [x] Add project-supplied package-test execution with explicit opt-in for trusted test code and actual pytest result collection; missing adapters/tests remain blocked.
- [x] Update governance/schema to support root-level registries, engine-owned baseline gates and render expectations; preserve the original schema as version 1 and document migration.
- [x] Add a private pilot project registry, execute the engine, inspect its preview and report actual failures/limitations.
- [x] Run regression/negative checks, review implementation, fix findings, and document install/run/API instructions and verification evidence.

## Outcome and limits

Implemented the shared engine, v2 contract, native worker, package-test runner and private pilot. Review fixes block compound/network providers before loading, active data-defined symbol dependencies and unverified package source identity. Linux masking distinguishes missing masked files from permission denial; macOS isolation is exercised natively. Engine code remains shared; the private pilot holds its registry and reports. Advanced QGIS features and archive-installed plugin source verification are explicitly blocked pending dedicated adapters.
