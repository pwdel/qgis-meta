# Location QR command

User-authorized generic CLI addition, without project-specific camping or parking rules.

Implement `qgis-meta qr-location --latitude LAT --longitude LON --output PATH.png|.svg`, with `--format geo|maps` (geo default), optional `--force`, and a JSON sidecar recording coordinates, payload, format, error correction and quiet zone. Use standard QR (not Micro QR), black on white, four-module quiet zone, error correction M. Validate finite coordinate ranges; refuse overwrites unless explicit. Default geo URI is RFC 5870; optional maps format is an HTTPS Google Maps search URL. No network or native QGIS dependency. A code identifies a point, not access/parking permission. Phone app handling varies.

Use Segno as a declared Python dependency, update uv.lock, add CLI/help documentation. Write and run failing tests first: payload normalization and invalid coordinates; CLI generation, non-overwrite, SVG and PNG; existing CLI behavior remains intact. Independently decode a generated PNG with a separate decoder. Run full pure-Python suite. Keep private map coordinates out of public examples/tests.
