# Declarative artifact checks implementation plan

Goal: extend the existing validator with reusable artifact consistency checks using only synthetic public fixtures. Consuming project data and expectations remain outside this repository.

Architecture: qgis-checks.json declares bounded operations implemented by qgis_meta.artifacts. The existing validate API discovers these alongside native registries and merges structured findings. Artifact success is explicitly scoped and never bypasses discovered native projects.

## Tasks
- [x] Implement run_artifact_checks(config: Path) -> dict with registry, project_id, scope='artifacts', checks, input_hashes; strict schema, contained inputs and hashes. Unit-test correct and corrupted synthetic artifacts before implementing handlers.
- [x] Integrate sidecar discovery into validate(), preserving native discovery and blocked semantics, and print scope in CLI. Test artifact-only, mixed and malformed targets and existing native regressions.
- [x] Configure private consumers outside this repository; compare each prior assertion with declarative checks and document parity privately. Replace old implementations with exit-code-preserving forwarding commands.
- [ ] Review boundary, run portable suite plus available native checks, commit and publish a reviewable branch. Do not merge existing unrelated engine commits automatically.

## Handler interface
Configuration: schema_version=1, project_id string, checks nonempty array. Each check has unique id and op. Operations: manifest (manifest path, base path); qgis_sources (file, prefix); archive (file, member, equals); json_equal (left/right {file,pointer}); json_value (source {file,pointer}, value); json_length (source, length); html_json (file, element_id, source); geojson (file, wgs84 boolean); flattened_features (source, target, key); csv_ids (file, column, source, key). JSON pointers default to root. Manifest supports one record or list with path, bytes, sha256. Public tests must not use real consuming project names or data.

Every failed, unknown, malformed or missing check returns fail. Unknown fields fail schema validation. All handlers read local contained paths only. No eval, shell, fetching or dynamically imported project code. Reports include hashes for all bytes consumed. Recheck hashes after execution. Archive checks never extract files. GeoJSON validates supported geometry coordinate structures and finite ordinates; WGS84 bounds apply only when declared. Feature comparisons reject duplicate keys; CSV identifiers reject duplicate IDs.

Verification: unittest suite under the existing governance venv; adversarial fixtures for invalid schema/path/symlink/manifest/ZIP/HTML/GeoJSON/CSV/JSON, integration smoke with output reports, private parity checks on untouched inputs, and staged-public-content inspection. Existing native gates and governance pin checks remain in place.
