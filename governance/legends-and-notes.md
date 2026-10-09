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
at intended scales and native legend together. For the winter-camping profile the
chosen stroke is #B3261E, 0.8 mm, on a 4 mm X; the project regression test preserves
that choice. This semantic rule does not mean every cross in every domain denotes
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
