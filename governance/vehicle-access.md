# Vehicle access and parking evidence

Project research must distinguish camping authorization, campground operating season, vehicle admission fees, daytime parking and overnight parking. A camping permit, public-land polygon, year-round forest opening or absent fee sign does not establish permission for overnight parking.

For each researched location, retain a `vehicle_access` object in the canonical location record with `manager`, `admission_pass`, `day_parking`, `overnight_parking`, `hours`, `sources` and `checked`. Unknown permissions must remain `unverified` or `not-assessed`. Record campsite vehicle limits and designated parking restrictions where documented. Keep user observations separately with their source and observed date; an unknown date is null. Observations must not silently override official requirements.

Identify the actual jurisdiction and geographic scope of every rule. Adjacent properties can have different managers and permit systems. Distinguish agency-owned land, easements and administrative boundaries; none automatically authorizes camping or public access throughout a polygon. Preserve GIS provenance, source CRS, coordinate operation and original geometries.

Project integration tests must assert that supported admission requirements remain separate from parking permission, seasonal closure is preserved, and unknown overnight access cannot become allowed merely because camping or a nearby jurisdiction allows it. These are project-specific evidence tests; the generic rendering validator cannot determine legal permission from a map symbol.

## Shared access symbols

The bundled SVGs in `assets/symbols/access/` distinguish `parking-free-day`, `parking-free-overnight`, `parking-paid-overnight`, and `parking-unverified-day`. A sun denotes daytime use; a moon denotes overnight use; 0, $, and ? distinguish free, paid, and unverified fees. Legends must spell out these meanings. Use a free or overnight symbol only with evidence of that permission at that particular parking area. Absence of a visible fee sign is an observation, not a verified fee exemption.

Use `gate.svg` for an observed gate. Preserve original coordinates, coordinate source, observation date (null if unknown), potential lockability and verified current status separately. A potentially lockable gate does not mean the gate is currently closed. Displaced overview markers must retain their true coordinates and a connector. Local maps use the original point, and must pass the same label and symbol clearance tests as overview maps.

## Terrain and canopy

Register local raster extracts with source URL, download request, horizontal and vertical reference information where available, units, source pixel size, exported pixel size and checksum. Test for valid, non-NoData pixels in the study area; successfully opening an empty raster is insufficient. Disclose fallback generations and resolutions. A finer rendering grid does not increase source detail. Percentage tree canopy is not a map of individual trees. Keep layer-specific provenance and include every displayed terrain, canopy and access symbol in the native layout legend.
