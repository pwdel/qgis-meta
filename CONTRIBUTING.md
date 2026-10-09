# Contributing

Prefer a primary-source link and a short, scoped explanation over copying another library or inventing a replacement standard.

## Add a resource

Create a descriptively named Markdown file in `resources/`, following an existing entry. Include:

- Publisher, category, official URL, and exact version or endpoint when relevant.
- What the resource offers and which map types it might suit.
- License or terms URL, attribution, and separate interactive/print/offline conditions where known.
- Review state, inspection date, what was actually checked, and unresolved questions.

Add it to the resource index and link it from appropriate map profiles. A portal-wide description does not approve every item in that portal. Avoid copying full third-party standards or distributing files without checking their specific terms.

## Add a ruleset or map type

A ruleset links sources and distinguishes publisher requirements, external standards, guidance, and local editorial policy. A map profile describes purpose, resource choices, applicable rulesets, and remaining decisions. Keep references linked rather than duplicating the same licensing summary across profiles.

## Add an original artifact later

Use the same catalog entry pattern, label the creator and original provenance, and specify an explicit license. Add the artifact file only when there is an actual item to share and its rights are clear. No placeholder asset hierarchy is necessary.

## Review a change

Check relative links, source claims, date and scope, attribution, and the distinction between guidance and requirements. Use public sources and examples. Review status must describe what was inspected; unresolved conditions cannot become approvals just because a link works.

The repository's original prose has no selected reuse license yet. Do not assume the terms of any linked resource license this repository or other linked resources.

## Change technical governance

Keep the [package catalog](packages/catalog.json), [registry schema](schemas/qgis-registry-v2.schema.json), [draft example](templates/qgis-registry-v2.example.json) and [test requirements](governance/integration-tests.md) consistent. Adding a required package ID or changing required fields is a contract change: publish a new schema version and migration guidance rather than silently invalidating pinned consumers. Check official source/version claims, validate the schema and example, exercise malformed-record rejection, and check documentation links. Public examples must be synthetic. Report schema checks separately from actual QGIS/plugin integration results.

The packaged copies in `qgis_meta/contracts/` must match the canonical schema and catalog byte-for-byte. Regression tests check this. Run the engine tests with an explicit QGIS runtime before claiming native integration coverage. Commit changes before pinning the governance revision in a consuming project; dirty engine checkouts cannot certify compliance.
