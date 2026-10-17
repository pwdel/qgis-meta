"""Offline location QR images; no QGIS runtime or site-specific policy."""
import io
import json
import math
from pathlib import Path
from urllib.parse import quote


def location_payload(latitude, longitude, format='geo'):
    latitude, longitude = float(latitude), float(longitude)
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError('latitude must be finite and between -90 and 90')
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError('longitude must be finite and between -180 and 180')
    def number(value):
        text = f'{value:.10f}'.rstrip('0').rstrip('.')
        return '0' if text == '-0' else text
    coordinates = f'{number(latitude)},{number(longitude)}'
    if format == 'geo':
        return f'geo:{coordinates}'
    if format == 'maps':
        return 'https://www.google.com/maps/search/?api=1&query=' + quote(coordinates, safe='')
    raise ValueError('format must be geo or maps')


def generate_location_qr(latitude, longitude, output, format='geo', force=False):
    import segno
    payload = location_payload(latitude, longitude, format)
    output = Path(output)
    kind = output.suffix.lower().lstrip('.')
    if kind not in {'png', 'svg'}:
        raise ValueError('output must end in .png or .svg')
    sidecar = output.with_suffix(output.suffix + '.json')
    for path in (output, sidecar):
        if path.exists() and not force:
            raise FileExistsError(f'{path} exists; use --force to replace it')
    # Standard QR avoids Micro QR reader incompatibility. Preserve the quiet zone.
    qr = segno.make(payload, error='m', micro=False, boost_error=False)
    image = io.BytesIO()
    qr.save(image, kind=kind, scale=10, border=4, dark='#000000', light='#ffffff')
    metadata = dict(payload=payload, latitude=float(latitude), longitude=float(longitude),
                    crs='EPSG:4326', format=format, image_format=kind,
                    error_correction='M', quiet_zone_modules=4,
                    coordinate_decimal_places_max=10,
                    note='Location only; does not establish access or parking permission. Test with the intended phone.')
    content = [(output, image.getvalue()),
               (sidecar, (json.dumps(metadata, indent=2) + '\n').encode())]
    created = []
    try:
        for path, data in content:
            with path.open('wb' if force else 'xb') as handle:
                if not force:
                    created.append(path)
                handle.write(data)
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return metadata
