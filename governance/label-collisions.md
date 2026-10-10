# Label collision policy

Map labels must not overlap other labels or obscure point symbols. When space is
insufficient, omit the lower-priority label rather than force it into the map.
Use camping/reference identifiers at higher priority than contextual town names.
Omission is not missing data: retain the complete attributes and location index.

For supported native simple labels the validator requires:

- PreventOverlap; no display-all override and no degraded placement. Project-wide
  UseAllLabels and DrawUnplacedLabels overrides also fail validation.
- Labeled point features act as high-priority obstacles (factor 10).
- Ordered placement around points, measured from symbol bounds, in millimetres;
  no OverPoint candidate centered on a marker.
- Label-to-symbol clearance at least the text buffer width plus 0.2 mm; buffer
  units must also be millimetres. Data-defined placement and label geometry
  generators remain blocked until their placement can be validated.

This is a placement-configuration gate, not a proof of every rendered pixel.
QGIS collision avoidance can still behave differently with scale, dense features,
complex symbols and layout overlays. Review each delivered map at its actual
scale. The current check covers labeled point layers, not unlabeled symbols,
road-line crossings or arbitrary layout text.
Do not describe those unchecked cases as certified collision-free. Add rendered
geometry tests before broadening that claim. Font/glyph and export/relocation
checks continue separately. Do not hard-code camping numbers or place names into
shared validation rules.

Point-marker-to-marker spacing at published layout scales is checked separately
under [symbol spacing](symbol-spacing.md).
