# Location QR verification — 2026-10-17

- New tests first failed because the requested module did not yet exist.
- `python -m pytest tests/test_location_qr.py -q`: 10 passed.
- `python -m pytest tests --ignore=tests/integration -q`: 87 passed, 54 skipped, 38 subtests passed. Native QGIS integration tests require their separate runtime and were excluded from this pure-Python run.
- Independent decode with zxing-cpp + Pillow recovered exactly `geo:12.5,-45.25` from the generated PNG.
- Both PNG and SVG generation, range/nonfinite rejection, metadata and overwrite protection tested.
- No physical-phone scan test performed. App handling of geo URIs varies; HTTPS maps payload available.

Reproduce the independent decode after generating `/tmp/qgis-meta-qr-check.png`:

```sh
uv run qgis-meta qr-location --latitude 12.5 --longitude -45.25 --output /tmp/qgis-meta-qr-check.png --force
uv run --with zxing-cpp --with pillow python -c "from PIL import Image; import zxingcpp; r=zxingcpp.read_barcode(Image.open('/tmp/qgis-meta-qr-check.png')); assert r and r.text == 'geo:12.5,-45.25'; print(r.text)"
```
