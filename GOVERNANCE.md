# Governance

This catalog records evidence for map-making decisions. It does not issue permissions on behalf of resource publishers or land managers.

## Separate the decisions

| Dimension | Question |
| --- | --- |
| License | May this exact data or artifact be used, modified, and redistributed? |
| Service terms | May this endpoint be used for interactive display, export, caching, or offline downloads? |
| Design suitability | Does the resource fit this map's scale, purpose, audience, and output? |
| External standard | Which published standard applies, and why? |
| Local policy | What has this project chosen to require beyond external obligations? |
| Land/activity access | What authority governs the particular place, activity, and date? |

Record these separately. An open data license does not establish hosted-service rights. A map feature does not establish land access.

## Resource review states

- **Pointer checked:** the linked source was inspected; item-level terms or suitability remain unresolved.
- **Conditions summarized:** relevant conditions were read and summarized for the stated scope. The source controls.
- **Needs review:** evidence is missing, inaccessible, changed, or insufficient for the proposed use.
- **Retired:** retained for history; do not select for a new map without renewed review.

No state is a universal approval. Keep the inspected date and unresolved questions on each entry. Mark an entry needs review when its source changes or its proposed use exceeds the checked scope. Git history records revisions; consumers should record the catalog commit they used.

## Ruleset authority

Every rule identifies its origin as publisher terms, external standard, published guidance, or local editorial policy. A local recommendation is never presented as an external obligation. A standard applies only within its actual scope; citing one criterion does not establish full conformance.

When sources disagree, retain both links and explain the unresolved scope. Do not silently pick whichever is more permissive. Reviewers must resolve the particular use case before recording it as permitted.

## Project decisions

A map project's README should identify its profile, exact resources and versions, output modes, source and terms URLs, required credits, checked date, reviewer, and any unresolved uses. Describe decisions as permitted with conditions, not permitted for this use, or unresolved, and include the supporting source. These are plain-language notes, not a new data format.

Changes to the catalog are reviewed through ordinary GitHub diffs. Additions to a profile are editorial selections. Any stricter local policy must be labeled and justified. Unknown terms remain unresolved.
