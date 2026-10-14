# Generic map integrity implementation plan

Approved design: retain the existing integrity, cartography, legend and style checks; make source packaging universal, avoid domain-specific record counts, validate marker alignment with connectors, use collision bounds as review warnings, and require georeferenced PDFs for map layouts without feature attributes. Map edits are outside this implementation.

Architecture: extend the existing portable artifact operations and native preflight/anchor/layout checks. Use native GDAL to inspect PDF georeferencing; no new Python dependency. Keep project data and declared expectations in private configuration.

- [x] Add failing synthetic tests for universal `./sources/` containment and unique source/display IDs (including reordered/growing datasets and missing/duplicate records).
- [x] Enforce source paths in both artifact and native preflight; add `feature_ids` with strict schema. Retain `json_length` as an optional declared expectation, never a universal count.
- [x] Add native regression tests for offset/noncenter marker anchors; reject detached marker styles without rewriting map geometry.
- [x] Make marker collision findings warnings; ensure warnings do not skip relocation/negative/render tests. Retain unsupported bounds as blockers.
- [x] Require a geospatial PDF per exported map page with attribute export disabled, retaining the complete printable atlas and using disposable page-layout clones; inspect emitted PDFs with GDAL; fail on missing/unreadable georeferencing.
- [x] Update generic governance docs and private comparison decisions/configuration. Preserve saved maps and historical results.
- [x] Run portable/native tests, compare current private artifact results, inspect public diff for private material, and record evidence.

Validation: `.venv-governance/bin/python -m unittest discover -s tests -q`; repeat with `QGIS_META_QGIS_APP=/Applications/QGIS-final-4_2_3.app` for native cases. Run updated private artifact config separately; existing companion mismatch remains a real finding.

## Verification results

- Portable unittest suite: 131 collected, 77 passed, 54 native tests skipped as expected without a QGIS runtime.
- Full QGIS 4.2.3 unittest suite: 130 tests passed. The subsequently added missing-GDAL failure test also passed in the portable suite.
- Separate pytest-qgis synthetic integration suite: 4 passed. macOS Qt startup required execution outside the shell sandbox.
- Native regression coverage includes independent marker offsets, noncenter anchors, collision warnings continuing export, actual PDF georeferencing, ordinary/corrupt PDF rejection, multiple map pages, and excluded cover pages.
- Review: fixed excluded-page numbering and single-page GeoPDF composition via disposable per-page layout clones. Follow-up review found no remaining important issues.
- Generic source-path and ID-set tests cover weakening/traversal attempts, dataset growth/reordering/displacement, and missing/extra/duplicate IDs.
- Public diff inspected for newly introduced private project material; none found. Detailed consuming-project evidence remains private.
