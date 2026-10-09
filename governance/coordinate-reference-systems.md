# Coordinate reference systems and reproducible transformations

A project must open without asking its recipient to choose a coordinate operation.
A successful headless render alone is not sufficient evidence: the render CRS can
match the source layers while the desktop canvas uses a different datum.

## Required project decisions

Record the source CRS, canvas CRS, each print/export CRS, coordinate units, area of
interest, purpose and precision limits in project documentation. Choose a suitable
regional projection for distance/scale displays. Keep the source datum when it
meets the use case; a datum change needs a stated reason. Never relabel coordinates
with another CRS to suppress a prompt: transform coordinates or change the canvas
CRS using QGIS's transformation machinery.

For every differing source/destination pair, save an explicit coordinate operation
in the **project transform context**, even when only one candidate exists. Do not
rely on a user's global “Make default” preference. Disable fallback transformations.
Select operations by area of use and source accuracy, not simply the smallest
accuracy number in the dialog. A state-specific grid is not automatically suitable
for a project spanning multiple states. Document the selected pipeline, authority
identifiers when available, nominal accuracy and any grid dependencies. Record
unknown accuracy as unknown; operation accuracy is not source-data accuracy.

Required grids must be installed reproducibly with provenance/license and a
verified checksum in the runtime dependency inventory, or packaged as licensed
project assets with an explicit PROJ search-path setup. Do not download them
implicitly during validation. A missing operation or grid is a failure.

## Automated acceptance

The native validator's `load` gate checks every layer against both the project CRS
and configured preview CRS. For differing pairs it requires a saved direct catalog
operation, fallback disabled, availability in the current QGIS/PROJ runtime, and a
finite transformed layer-center coordinate with no fallback. It records pipelines
and nominal accuracy in the report, and repeats these checks during relocation.
Custom pipelines and inverse-only saved operations currently fail this conservative
check; they require additional validation support, not a silent pass.

Regression cases cover the reported bug (a NAD83 canvas with a WGS 84 preview and
no saved operation), an available saved operation, enabled fallback, and a missing
grid. Same-CRS projects need no coordinate operation.

This is a minimum automated gate, not a positional-accuracy certification. Layer
center probes do not prove grid coverage across all features. For datum-shift or
high-accuracy work, add independent known-coordinate checks and boundary samples
covering the full area of use. Vertical/dynamic CRSs, epochs and specialized
pipelines require dedicated tests. Print templates need their own reopen/export
checks for their CRSs and styles; the base-project validator does not inspect QPTs.

## Desktop acceptance

Before release, open a disposable project copy in a fresh QGIS profile with
transformation prompts enabled. Record QGIS/PROJ versions and verify no missing
layer, coordinate-operation, grid, font or plugin dialogs occur. Inspect the canvas
and each print layout at the intended scale. This desktop check is separate from
headless integration testing and must not be represented as automated unless a GUI
test actually exercised it. Do not suppress global prompts to pass acceptance.

References: [QGIS transform context](https://api.qgis.org/api/classQgsCoordinateTransformContext.html),
[QGIS coordinate transform](https://www.qgis.org/pyqgis/master/core/QgsCoordinateTransform.html),
[QGIS operation catalog](https://www.qgis.org/pyqgis/master/core/QgsDatumTransform.html).
