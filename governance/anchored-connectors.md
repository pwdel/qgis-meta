# Anchored connectors

Displaced point markers must use a native geometry-generated connector on the same feature, never a separately editable line. The registered `anchor_source_asset` identifies a GeoJSON point asset keyed by unique `id`. In this supported WGS84 contract, `source_lon` and `source_lat` must match the source coordinates.

The only supported connector expression is `make_line(make_point("source_lon", "source_lat"), $geometry)` in map units with a line subsymbol. Other expressions remain blocked. A registered layer must contain exactly one enabled connector. Any generated connector without an anchor registration fails validation.

The validator evaluates every feature and simulates a point move: the source endpoint must stay fixed and the display endpoint must follow. Missing connectors, altered expressions and altered anchor fields fail. Source hashes remain covered by asset validation. Marker collision checks use marker footprints separately from the connector lines; they do not assert that connector lines never cross.

This anchors connectors to symbols, not separately positioned text labels. Text-only displacement should instead use QGIS label callouts with a separately validated contract.

`tests/test_anchored_connectors.py` runs native checks for movement and negative cases. Project builders must preserve saved manual display positions as overrides and retain original source coordinates. Do not rebuild over an active editing session.
