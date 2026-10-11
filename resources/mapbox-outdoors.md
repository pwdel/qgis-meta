# Mapbox Outdoors

- Publisher: Mapbox.
- Category: hosted outdoor/terrain basemap style.
- Product: [Mapbox Outdoors](https://www.mapbox.com/maps/outdoors).
- Exact candidate: `mapbox://styles/mapbox/outdoors-v12`; [style reference](https://docs.mapbox.com/map-styles/reference/outdoors/).
- Review state: **conditions summarized** for documented access, billing and attribution; account-specific rights, export/offline use and endpoint viability remain project checks.
- Checked: 2026-10-11. Official style, WMTS, Static Tiles and attribution documentation inspected. No token used, account configured, billable request made or QGIS render tested.

## Fit and lifecycle

Terrain and recreation cartography can provide hiking or reference-map context. It does not verify habitat, route openings or access rights.

**The Outdoors reference now calls this a classic style that is no longer actively maintained**, retained for existing applications. Keep it as a legacy candidate requiring a live test before adoption. Mapbox recommends Standard for new projects, but the Static Tiles API documentation currently excludes Standard; substituting it requires a separate integration review.

## QGIS connection candidates

Mapbox's [Styles API WMTS documentation](https://docs.mapbox.com/api/maps/styles/#retrieve-a-maps-wmts-document) explicitly names QGIS support. In QGIS, create a WMS/WMTS connection with this capabilities URL:

```text
https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/wmts?access_token=YOUR_MAPBOX_ACCESS_TOKEN
```

For a raster XYZ alternative, the [Static Tiles API](https://docs.mapbox.com/api/maps/static-tiles/) defines:

```text
https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/tiles/256/{z}/{x}/{y}?access_token=YOUR_MAPBOX_ACCESS_TOKEN
```

The 256-pixel example simplifies conventional XYZ setup but can increase request costs; 512-pixel tiles require correctly configured tile size/zoom handling. Static Tiles supports zooms 0–22. It also documents a 410 error for unsupported classic styles: the published Outdoors URL is not proof this endpoint still renders it. Test the exact WMTS/XYZ combination before adoption.

A Mapbox account and valid access token are required. Review [pricing](https://www.mapbox.com/pricing) for the selected API; Static Tiles is billed by requests. URL-restricted tokens can cause desktop-client 403 responses. Keep credentials out of this public repository, logs and distributed project URLs; examples intentionally contain only placeholders. Configure locally and inspect exported QGIS connection/project files before sharing.

## Attribution, print and offline

Follow the [Mapbox attribution guidance](https://docs.mapbox.com/help/dive-deeper/attribution/) and [applicable terms](https://www.mapbox.com/legal/tos). Other clients may not supply the logo or credits automatically. Printed output needs nearby Mapbox/OpenStreetMap attribution and the required logo; check the exact output method. Mapbox separately directs Studio print-export users to contact it before printing. Attribution compliance alone does not establish all export rights.

Offline packaging, bulk tile acquisition, redistribution and publishing token-bearing projects are **not approved by this entry**. Resolve those uses against current account/product terms before acquisition. A live authenticated layer does not meet the catalog's local, network-denied relocation requirement; any permitted local derivative needs declared provenance, assets and tests.

Related: [resource-use rules](../rulesets/resource-use.md), [cartographic-resource packaging](../governance/cartographic-resources.md).
