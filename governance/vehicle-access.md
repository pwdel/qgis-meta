# Vehicle access and parking evidence

Project research must distinguish camping authorization, campground operating season, vehicle admission fees, daytime parking and overnight parking. A camping permit, public-land polygon, year-round forest opening or absent fee sign does not establish permission for overnight parking.

For each researched location, retain a `vehicle_access` object in the canonical location record with `manager`, `admission_pass`, `day_parking`, `overnight_parking`, `hours`, `sources` and `checked`. Unknown permissions must remain `unverified` or `not-assessed`. Record campsite vehicle limits and designated parking restrictions where documented. Keep user observations separately with their source and observed date; an unknown date is null. Observations must not silently override official requirements.

Identify the actual jurisdiction and geographic scope of every rule. Adjacent properties can have different managers and permit systems. Distinguish agency-owned land, easements and administrative boundaries; none automatically authorizes camping or public access throughout a polygon. Preserve GIS provenance, source CRS, coordinate operation and original geometries.

Project integration tests must assert that supported admission requirements remain separate from parking permission, seasonal closure is preserved, and unknown overnight access cannot become allowed merely because camping or a nearby jurisdiction allows it. These are project-specific evidence tests; the generic rendering validator cannot determine legal permission from a map symbol.
