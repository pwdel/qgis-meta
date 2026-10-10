# Map key and technical information

Every delivered map page must include a native linked QGIS legend (map key),
with the actual symbols, lines and fills used by that map. See
[legend coverage](legends-and-notes.md). Keep the key in the saved project layout,
so it is editable and exported with the map.

Provide a readable coordinate/style/source panel on each standalone map page.
Store fuller descriptions in native QGIS project and layer metadata. Record:

- Source CRS and datum, authority code, coordinate order and angular units.
  Distinguish file order (e.g. GeoJSON longitude, latitude) from a GPS interface
  that may display latitude first. Do not describe all of this simply as GPS encoding.
- Display CRS/projection, authority code, projected units, scale-bar units and
  selected coordinate operation. Record vertical datum, epoch and positional
  accuracy if known; otherwise state that they are unknown rather than infer them
  from the number of decimal places. See [CRS policy](coordinate-reference-systems.md).
- File format and character encoding, separately from geographic coordinates.
- Basemap dataset/provider, resolution or nominal source scale where known,
  snapshot/acquisition date, source URLs, attribution and license. Distinguish an
  offline vector basemap from live tile services. Source scale is not map zoom.
- Style identity and location: native project renderer, external style file or
  style library, plus a version where available. Describe meaningful visual
  conventions; retain machine-verifiable semantic roles in the project registry.
- Thematic-data provenance, relevant limitations, and references to fuller records.

Do not invent GPS survey accuracy, elevations, source versions or refreshed dates.
Changing cartography does not refresh the underlying source data. Avoid placing
private source details in public governance documentation.

The current shared validator checks declared CRSs/operations, resources, native
legend coverage, text rendering and semantic style roles. It does not yet certify
metadata completeness or compare prose against renderer settings. Project tests
may verify that their required information panels and native metadata survive a
save/reopen; source correctness and readability still require review.
