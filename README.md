# qgis-meta

A public catalog of map-governance sources, resource pointers, rulesets, project acceptance contracts, and a reusable validation engine for different kinds of maps.

Start with a map type, find suitable resources, and follow the linked conditions for using them. The library covers basemaps, datasets, styles, symbols, palettes, accessibility, and publication requirements. It starts with existing resources; original artifacts can be cataloged alongside them later.

## Start with a map type

| Profile | Purpose |
| --- | --- |
| [Trail and hiking](map-types/trail-and-hiking.md) | Recreation and route-planning maps, including offline-use decisions |
| [Habitat scouting](map-types/habitat-scouting.md) | Habitat evidence and field observations, with access decisions kept separate |
| [General reference](map-types/general-reference.md) | Orientation, regional context, and location maps |

These are starter profiles with editorial recommendations, not external certifications or completed map approvals.

## Browse the library

- [Resource catalog](resources/README.md): existing libraries, services, datasets, and guidance.
- [Rulesets](rulesets/README.md): linked requirements and recommendations with explicit scope.
- [Governance](GOVERNANCE.md): what “allowed” means, review states, and source authority.
- [Artifact consistency checks](governance/artifact-checks.md): declarative local file/export checks through the same CLI.
- [Validation engine](governance/validation-engine.md): point one CLI/Python function at a map repository.
- [Project registry contract](governance/project-contract.md): mandatory per-map inventories and adoption rules.
- [Package catalog](packages/README.md): plugin declarations and required integration boundaries.
- [Integration tests](governance/integration-tests.md): load, render, relocate and package-specific acceptance requirements.
- [Python environments](governance/python-environments.md): QGIS-aware virtual environments and dependency locks.
- [Camping permissions](governance/camping-permissions.md): permit conditions, zone scope and sourced atlas rules.
- [Vehicle access and parking](governance/vehicle-access.md): distinguish admission, camping seasons, parking permissions and jurisdiction.
- [Layer Properties](governance/layer-properties.md): standard QGIS settings linked to evidence and tests.
- [Contributing](CONTRIBUTING.md): add sources, map types, or original artifacts using Markdown.

## How to use it

1. Choose a profile and state the map's audience, area, scale, and output: interactive, print, or offline.
2. Follow its resource and ruleset links. Check the exact item, version, endpoint, and use case.
3. Record your choices, attribution, source versions, review date, and unresolved questions in your map project's README.
4. Create a `qgis-registry.json` beside each project file using the [registry contract](governance/project-contract.md); pin this catalog revision and record test evidence before claiming compliance.
5. Recheck changing service terms and time-sensitive information before publication.

Catalog inclusion is discovery, not blanket permission. Resource licensing, service access, design suitability, and permission to enter land are separate decisions. A source-read date records an inspection, not a guarantee that terms remain unchanged.

The catalog includes ten resource entries, three profiles, five package declarations, and a versioned project-registry schema with a draft example. The shared engine implements structural, load/render, relocation and negative gates, with a runner for project-authored package integration tests. Unsupported workflows remain blocked. Each map adopts registry v2 and supplies its own data, expectations and test evidence.

## Reuse

External resources retain their own licenses and terms. A license for this repository's original prose has not yet been selected; public visibility does not grant an additional reuse license.

## Check the governance contract

Create the [governance virtual environment](governance/python-environments.md), then run:

```sh
.venv-governance/bin/python -m unittest discover -s tests -v
```

The suite covers registry contracts and the engine. Native QGIS tests run when an explicit runtime is configured; otherwise they are skipped. Follow the [engine guide](governance/validation-engine.md) for full runtime testing.
