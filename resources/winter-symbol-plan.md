# Winter map symbol shortlist

Status: candidate library, not installed or applied to map features.

Keep feature type separate from permission. A tent identifies a campsite; it does
not establish winter availability. Preserve the shared red X / NO prohibition
role and the existing documented, unverified and unassessed status distinctions.
Only show facility or route symbols where source data supports the assertion.

| Meaning | Candidate found in QGIS 4.2.3 bundled SVG collection | Qualification |
| --- | --- | --- |
| Campsite | accommodation/accommodation_camping.svg | Does not imply winter permission |
| Shelter | accommodation/accommodation_shelter.svg | Does not imply heated or open |
| Parking | transport/transport_parking.svg | Verify seasonal access |
| Toilets | amenity/amenity_toilets.svg | Verify seasonal availability |
| Information | amenity/amenity_information.svg | Identify the actual facility |
| Cross-country ski route | sport/sport_skiing_crosscountry.svg | Only documented designated routes |

Also consider distinct hiking, portage and verified winter-route line styles.
Do not infer a winter route or safe ice crossing from a summer path or waterbody.
Drinking water and fire facilities need explicit source evidence and suitable
symbols before adoption. Unused symbols belong in the library, not the map key.

## QGIS menus

- Settings → Style Manager manages reusable styles. Browse Online Styles opens
  the QGIS Style Hub; Import/Export imports downloaded QGIS style XML.
- Layer Properties → Symbology → select the marker symbol layer → SVG marker
  selects bundled or local SVGs. Some useful symbols are already installed.
- QGIS Resource Sharing is an optional plugin for installing resource collections.
  It is not required to use the bundled SVGs or a project-local SVG.

Sources:
- https://docs.qgis.org/4.2/en/docs/user_manual/style_library/style_manager.html
- https://docs.qgis.org/3.44/en/docs/user_manual/style_library/symbol_selector.html
- https://qgis-contribution.github.io/QGIS-ResourceSharing/usage/installing-collection.html

Before vendoring a symbol, inspect its license and attribution, preserve required
notices, and record source/version/hash. Put adopted assets inside each consuming
project and declare them in its registry. A symbol existing in one author's QGIS
installation is not sufficient evidence of portability. Run SVG, legend, export
and relocation validation after adoption.

## Brand badge and source notes

Use the user's supplied Rapid Water Labs logo, preserving its proportions, inside
a white circular badge. Keep the reusable master in qgis-meta and a declared local
copy in each consuming project. Keep branding separate from geographical legend
symbols. Confirm the final resource is supported by the layout validator before
using it; unsupported picture items must not be exempted silently.

Use the reference map as a layout reference, not as a source of factual claims.
A red footer may carry this project's own source/limitation language. Do not copy
claims about Forest Service review, annual revisions or navigation suitability
from the photographed example. Preserve actual attribution and snapshot dates.
