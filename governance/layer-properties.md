# QGIS Layer Properties reference

This index connects QGIS's standard Layer Properties interface to local governance decisions. It is not a replacement for the [QGIS vector-layer documentation](https://docs.qgis.org/4.2/en/docs/user_manual/working_with_vector/vector_properties.html). Available tabs depend on layer type, provider and QGIS version. Checked 2026-10-09.

| Properties | Record or review | Test when used |
| --- | --- | --- |
| Information, Source | Provider, CRS, geometry, datasource, query/filter, extent | Load real data; match layer IDs, fields, CRS, filters and count bounds. |
| Symbology | Chosen style, symbol collection/item, SVG dependencies, palette, scale | Load saved style; resolve symbols; render representative categories at target scales. |
| Labels, Masks | Label fields/expressions, fonts, scale range, buffer/masking | Evaluate expressions and render; human review for collisions/legibility. |
| 3D View, Elevation | DEM/height sources, units, vertical reference, exaggeration | Load elevation sources and verify units; include a 3D-specific test for 3D outputs. |
| Diagrams | Attribute fields, classification and placement | Verify fields and render known fixture values. |
| Fields, Attributes Form | Field types, aliases, constraints, widgets and external UI files | Inspect schema and exercise required form behavior using actual QGIS. |
| Joins | Join sources, key fields and expected cardinality | Resolve both sides; assert unmatched/duplicate-key behavior. |
| Auxiliary Storage | Project auxiliary database and required fields | Verify packaged database survives relocation and retains values. |
| Actions | Action purpose and explicit invocation conditions | Test only intended actions in a disposable environment; no auto-execution during inventory. |
| Display | Display expression and map tips | Evaluate representative records and inspect output. |
| Rendering | Scale visibility, opacity, blend modes and draw order | Render at declared output scales and verify intended layer visibility. |
| Temporal | Time fields, timezone and range semantics | Check known instants and boundaries with the temporal controller configured. |
| Variables | Project/layer variables used by styles and expressions | Check presence and types; detect unresolved expressions. |
| Metadata | Title, abstract, provenance, license, credits and source dates | Check required metadata against registry evidence. |
| Dependencies | Dependent layers and refresh relationships | Resolve dependencies; detect missing/circular relationships where relevant. |
| Legend | Category names, order, symbols and explanatory text | Compare intended category coverage with renderer/legend and rendered layout. |
| QGIS Server | Published fields, service settings and metadata | Require service integration checks only for a server publication target. |
| Digitizing | Snapping, defaults, constraints and topology behavior | Exercise intended editing workflow on disposable fixture data. |

All projects record Source, Symbology, Metadata and applicable rendering choices. Document other categories as used or not applicable in project design notes; not every tab needs a custom registry field. Refer to external style/config files through package `config_paths` and asset records.

For design discovery use [Style Hub](../resources/qgis-style-hub.md), [Style Manager](../resources/qgis-style-library.md), [NPS symbols](../resources/nps-symbols.md), [ColorBrewer](../resources/colorbrewer.md) and [Resource Sharing](../packages/README.md). Record the exact selected item, license, tested QGIS version, target scale, and a preview. These recommendations guide selection; successful tests do not establish aesthetic quality or permission to enter land.
