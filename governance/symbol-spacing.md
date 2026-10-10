# Point-symbol spacing on published maps

Every supported layout map must keep separate point-marker footprints at least
0.2 mm apart at its saved print scale. The shared engine uses QGIS native marker
bounds with the layout CRS, extent, rotation and output resolution, including
marker size, stroke and fixed offsets. It checks point features across layers,
including amenity icons adjacent to a park marker. It never tests specific park
names, numeric labels or cabin categories.

Bounds are conservative rectangles, not a pixel-level silhouette comparison.
A multi-part composed symbol is one marker; roof/body strokes may intentionally
touch inside that marker. Unsupported renderers, multipart points and unavailable
bounds are blocked. Other dependency checks still block unvalidated effects and
data-defined symbol properties. Lines and polygon fills are not point markers:
roads may intersect, and connector lines may terminate at a marker.

This gate concerns saved layout scales, not arbitrary desktop zoom levels.
Displace crowded display markers with connector lines or use a separately
validated cluster design. Preserve original coordinates, document displacement,
and do not represent shifted cartographic coordinates as survey observations.
Amenity availability must remain separate from access permission and season.

Review exported pages for labels, map-key placement and other layout overlays;
this point-marker test does not certify those different collision classes.
