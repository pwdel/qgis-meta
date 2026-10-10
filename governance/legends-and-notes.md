# Legends, permission symbols and map notes

## Legend coverage

Each map item in a delivered print layout must have a visible, exported native
QGIS legend on the same page, linked to that map. Include every mapped layer and
every meaningful symbol/category, including context lines and fills. The legend
must use the actual renderer swatches, not separately typed look-alike characters.
Use explicit, readable names: a color or shape alone does not explain meaning.

The current validator admits single-symbol renderers. It checks linked-map
identity, same-page placement, visible/exported legend presence, exact layer
coverage and renderer legend-node count. It checks fonts and rendered exports.
Filtered legends, custom node labels/symbols/order and style overrides currently
block acceptance; classified renderers remain blocked until category-level checks
are implemented. A static note saying “see legend” is not a legend.

Native legends store references to project layers. Their swatches follow layer
styles. A deliberately selected layer list must be updated when layers are added;
the coverage check catches omissions. Headless checks do not replace visual review
for size, contrast, overlap or clear terminology.

The ordinary QGIS editing canvas uses the Layers panel as its interactive key.
Page legends and sidebar notes are saved in print layouts inside the QGZ and are
opened through Project → Layouts. They are not floating canvas decorations.

## Permission and restriction semantics

For maps describing access/permission, prohibited means **NO**. Use a red X with
an explicit “NO — [activity] prohibited” label. Keep documented, unverified and
not-assessed states distinct; do not infer permission from a trail or basemap.
Use shape plus wording so the map does not depend on color alone.

Open markers such as crosses draw with their **stroke/outline**, not their fill.
Set that visible stroke to the intended color. Do not use a white-only prohibition
mark on light land or water. Check the renderer preview, Layers-panel swatch, map
at intended scales and native legend together. The shared `prohibited` style role requires an opaque #B3261E solid stroke,
at least 0.8 mm wide, on a native `cross2` X at least 4 mm across. The layer and
symbol must be fully opaque, with the marker rotated only in multiples of 90°.
The marker must be enabled and use normal layer/feature blending.
Its layer/legend caption must start with `NO` as a separate word. This semantic rule does not mean every cross in every domain denotes
prohibition, nor that every project must contain a prohibited category.

## Editable note hierarchy

Keep notes as native layout labels with meaningful item IDs so authors can find
and edit them in the layout Items panel:

1. **Primary: reading instructions.** Explain number/index references, status
   definitions and how the reader should use the map.
2. **Secondary: context and limitations.** Describe geographic coverage, source
   generalization, incomplete coverage, access uncertainty and map purpose.
3. **Tertiary: credits and provenance.** Give attribution, source/snapshot dates,
   licenses and references without obscuring operational information.

Use topic-specific notes only where needed; avoid duplicating a long warning on
every page. A standalone map page still needs its own key and essential limits.
The validator checks text/font/glyph availability for these labels. Hierarchy,
accuracy of prose and readable placement remain explicit visual/editorial review.

## Declaring a shared style rule

Every layer conveying prohibition must declare `"style_role": "prohibited"` in
its registry layer entry. This is a semantic declaration, independent of layer
IDs, feature numbers and activity names. The native validator reads the saved
QGIS renderer and rejects noncompliant shape, stroke color, transparency, size,
width, orientation or caption in the load gate. Existing dependency checks also
block data-defined styling; native legend checks prevent independent swatch
substitutions. These checks run on both the original and relocated project.

The implementation lives in `qgis_meta/cartography.py::check_style_role`, governed
by the project's pinned governance revision. Update that pin to adopt a new rule.
Projects without this declaration do not receive this semantic check: the engine
cannot infer meaning from arbitrary symbols. Reviewers must verify declarations
are complete. An unrelated X may omit the role. Currently only single-symbol
native point markers are supported for this role; classified renderers block
acceptance rather than silently skipping checks.

This is a saved-style contract, not a guarantee of perceptual contrast on every
background. Review exported maps for overlap, scale and legibility as well.

For coordinate encodings, basemap style and source provenance, follow
[map key and technical information](map-information.md).
