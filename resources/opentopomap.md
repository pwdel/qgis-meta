# OpenTopoMap

- Publisher: OpenTopoMap project.
- Category: topographic basemap; hosted raster tiles and rendering style.
- Official map: [opentopomap.org](https://opentopomap.org/).
- Documentation: [usage and FAQ](https://opentopomap.org/about#verwendung), [project repository](https://github.com/der-stefan/OpenTopoMap).
- Candidate endpoint: `https://a.tile.opentopomap.org/{z}/{x}/{y}.png` (the documented service also lists b/c hosts).
- Review state: **conditions summarized** for the published raster offering; endpoint migration and project-specific acquisition need review.
- Checked: 2026-10-11. Original about page and project README inspected; the wiki mirror was unavailable. No tile retrieval, QGIS rendering or offline acceptance test was performed.

## Fit and QGIS connection

OSM/SRTM-derived relief, contours and trail context suit hiking and orientation; habitat maps can use it as background, not ecological evidence.

Candidate QGIS setup: Browser → XYZ Tiles → New Connection, using the endpoint above. Confirm supported zooms and live availability before adoption. No plugin is needed for an XYZ connection. These are setup instructions, not runtime verification.

**Lifecycle:** the project README describes the old raster tiles as deprecated and a transition to vector tiles. The about page reports a smaller render server from January 2026 and replacement raster service planned alongside vector tiles. Retain this as a potential source, not a guaranteed long-term endpoint; recheck the migration before selecting it for a new deliverable.

## Use conditions

The online map/style uses [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Preserve visible credits to OpenStreetMap contributors, SRTM and OpenTopoMap, plus the license link. The FAQ permits commercial printed maps with attribution and share-alike conditions for the reproduced map.

Interactive embedding must avoid excessive server load; availability is not guaranteed. A reuse license is not unlimited download capacity. For offline or bulk acquisition, resolve the exact method and service load first; consider separately licensed downloads or self-rendering. The project's Garmin offering has different terms—do not transfer the online-map license to it. Do not apply OSM Foundation standard-tile policy as if it were this provider's policy.

For print, assess raster label readability at the intended scale and document attribution/share-alike treatment. Trail completeness, current closures and land access require separate evidence.

Related: [OSM data](osm-data.md), [resource-use rules](../rulesets/resource-use.md), [cartographic-resource packaging](../governance/cartographic-resources.md). Live tiles alone do not satisfy the repository's offline relocation requirements.
