# Shared map integrity rules

These rules apply across projects. The engine contains no required place names, activity rules or record totals. Project registries supply assets, filters, CRS, fields and expected layer bounds.

| Family | Enforced checks | Details |
| --- | --- | --- |
| Anchors (A) | Fixed source endpoint, following display geometry, unique source IDs, supported generator, centered markers with zero independent offset | [Anchored connectors](anchored-connectors.md) |
| Files (F) | Strict schemas, contained paths, asset hashes/LFS, registered QGS/QGZ, archive integrity/companion equality, universal `./sources/`, manifests, source/display ID coverage, pinned engine/runtime and post-run input preservation | [Artifact checks](artifact-checks.md) |
| Data (D) | Valid project/layers, declared providers/sources, CRS/transforms, project-specific layer IDs/fields/filters/visibility/count bounds, readable features; unsupported dependencies block | [Cartographic resources](cartographic-resources.md) |
| Labels (L) | Available fonts/glyphs, supported expressions and symbols, overlap prevention, obstacle priority, symbol-bound spacing; unsupported labeling/effects block | [Label collisions](label-collisions.md) |
| Marker spacing (C) | Conservative bounds closer than 0.2 mm at layout scale produce review warnings; unsupported bounds block | [Symbol spacing](symbol-spacing.md) |
| Layout/legend (P) | Native layouts, visible linked same-page legend, exact layer/symbol coverage and actual swatches, valid raster legends, no duplicate legend captions, supported pictures/text/scale bars; georeferenced PDFs verified with GDAL and rendered previews | [Legends and output](legends-and-notes.md) |
| Style roles (S) | Explicit `prohibited` role requires NO caption and opaque red X with declared minimum dimensions; no inference about domain permissions | [Style roles](legends-and-notes.md#declaring-a-shared-style-rule) |
| Portability (R) | Isolated relocated load/render, missing-file/hash-tamper negatives, declared plugin provenance and required integration tests | [Governance](../GOVERNANCE.md) |
| Optional integration suite (T) | Native project/layer validity, readable feature geometry, render smoke test, negative child-test propagation | [pytest-qgis](pytest-qgis-tests.md) |

Warnings remain visible in JSON/CLI output and do not prevent rendering or relocation. Failures still return exit 1; unsupported/incomplete gates return exit 2. Passing checks do not replace visual review or verify real-world source accuracy. The optional pytest-qgis suite is run separately; it is not silently claimed by CLI success.
