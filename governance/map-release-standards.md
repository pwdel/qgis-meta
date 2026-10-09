# Minimum map release standards

Each project records its map purpose, audience, geographic coverage, intended
scale/output size, data snapshot date and limitations. The project README links to
its registry, data provenance, coordinate-system decisions and test evidence.

- **Coordinates:** follow [CRS and transformation governance](coordinate-reference-systems.md).
- **Sources:** distinguish measured, generalized, inferred and reference-point
  geometry; record dates, attribution, licensing and unresolved accuracy.
- **Symbols:** use shapes as well as color for important distinctions; preserve
  unknown/unverified/prohibited as separate states. Record symbol and font sources.
- **Labels and legend:** identify important geography, explain every meaningful
  symbol, and check overlaps and omissions at the actual output scale.
- **Scale and orientation:** use a correctly configured scale bar and identify
  grid north versus true north when relevant. Do not imply navigational precision
  from generalized basemaps or approximate reference points.
- **Layout:** show title, geographic coverage, data/export dates, attribution,
  status definitions and purpose-specific limitations. Inspect every exported page.
- **Packaging:** include relative-path assets, styles, templates and reproduction
  instructions; validate a relocated copy without access to the original directory.
- **Acceptance:** keep machine validation, desktop opening, visual review and
  domain/source verification as separate evidence. Passing one does not imply the
  others passed. Changes to CRS, data or styles require rebuilding affected outputs.

Project-specific exceptions must describe their scope, reason and remaining risk.
These standards guide design review; the current validator does not automatically
certify cartographic quality, current legal access or every layout dependency.

Follow [legends, permission symbols and note hierarchy](legends-and-notes.md).
