# Declarative artifact checks

Use the same `qgis-meta validate` command for portable file and export checks:

```sh
qgis-meta validate /path/to/project/qgis-checks.json
qgis-meta validate /path/to/repository --mode static
```

A `qgis-checks.json` file contains schema version 1, a `project_id`, and a nonempty
`checks` array. Each check has a unique `id`, an `op`, and its operation's arguments.
The [schema](../schemas/artifact-checks.schema.json) is the complete contract.

```json
{
  "schema_version": 1,
  "project_id": "sample-exports",
  "checks": [
    {
      "id": "display-coverage",
      "op": "feature_ids",
      "source": {"file": "sources/points.geojson"},
      "target": {"file": "sources/display-points.geojson"},
      "key": "id"
    }
  ]
}
```

Configuration, referenced files, expected values and reports belong to the
consuming project. The engine does not fetch data or infer semantic rules.
Public fixtures use synthetic data. Do not publish private configuration or
reports merely because the validator itself is public.

## Operations

| Operation | Purpose |
| --- | --- |
| `manifest` | Check file byte lengths and SHA-256 against a local single-record or list manifest. |
| `qgis_sources` | Require `./sources/` paths in every project, check existence, GeoJSON collections and TIFF headers. |
| `archive` | Check ZIP CRCs and compare an archive member to a companion file. |
| `json_equal` | Compare JSON documents or subtrees using JSON Pointers. |
| `json_value` | Compare a JSON subtree with a configured expected value. |
| `json_length` | Optional project-specific array length; no universal expected count. |
| `feature_ids` | Require equal sets of unique, nonempty identifiers in source/display GeoJSON collections; permits reordered records and displaced geometry. |
| `html_json` | Compare JSON in one named HTML script element with an external JSON source. |
| `geojson` | Check geometry coordinates, optionally against declared WGS84 bounds. |
| `flattened_features` | Compare GeoJSON features by identifier, preserving geometry and source attributes; decode JSON-encoded compound attributes. |
| `csv_ids` | Compare CSV identifiers with GeoJSON feature identifiers and reject duplicates. |

JSON source references use `file` and optional `pointer` (empty means the whole
JSON document). Paths resolve relative to the configuration, with manifest item
paths relative to its declared `base`. Path traversal and escaping symlinks fail.
Archive members are read without extracting files. Unknown operations, malformed
configuration, missing inputs and failed comparisons fail; no configured check
silently skips. There is no configuration-supplied Python, shell or expression execution.

## Scope and exit status

A file target runs that configuration only. A repository/directory target finds
both native registries and artifact configurations, excluding caches and reports.
Artifact-only success means these declared artifact checks passed. It makes no
claim about native QGIS rendering, visual quality, project completeness, licensing
or real-world policy. Target a repository to also discover unregistered QGIS files.

Existing native gates are unchanged: native static runs remain blocked (exit 2)
until the required runtime checks run. Unregistered QGS/QGZ files still fail.
Artifact-only runs can pass (exit 0) without QGIS. Any failure returns 1. Empty
repositories remain blocked. Reports explicitly record scope and consumed-input
hashes, including the check configuration. Native governance pins continue to
apply to native registries. Artifact-only reports record engine identity but do
not enforce a governance revision; pin your validator installation for repeatable runs.

These operations supplement native label, font, legend, spacing, layout and
rendering checks. They do not route through the opt-in plugin test runner.

The `./sources/` rule is universal in native preflight and artifact source checks. It is relative to each QGS/QGZ, rejects absolute paths, parent traversal and escaping symlinks. The optional legacy `prefix` argument must equal `./sources/`; it cannot weaken the rule. Existing projects using other directories must migrate deliberately. Validation never moves files.

`feature_ids` compares membership rather than a fixed number or full geometry. It catches missing/extra/duplicate IDs while allowing datasets to grow. It does not replace asset hashes, coordinate validation or registered private layer expectations.
