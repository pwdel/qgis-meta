import json
from pathlib import Path
import pytest
from qgis_meta.cli import main
from qgis_meta.location_qr import location_payload


def test_geo_payload():
    assert location_payload(12.5, -45.25, 'geo') == 'geo:12.5,-45.25'
    assert location_payload(-0.0, 180, 'geo') == 'geo:0,180'
    assert location_payload(12.5, -45.25, 'maps') == 'https://www.google.com/maps/search/?api=1&query=12.5%2C-45.25'


@pytest.mark.parametrize('lat,lon', [(91,0),(-91,0),(0,181),(0,-181),(float('nan'),0),(0,float('inf'))])
def test_invalid_coordinate(lat,lon):
    with pytest.raises(ValueError): location_payload(lat,lon,'geo')


@pytest.mark.parametrize('extension', ['png','svg'])
def test_cli_output_and_overwrite(tmp_path,extension):
    path=tmp_path/f'point.{extension}'
    args=['qr-location','--latitude','12.5','--longitude','-45.25','--output',str(path)]
    assert main(args)==0
    metadata=json.loads(path.with_suffix(path.suffix+'.json').read_text())
    assert metadata['payload']=='geo:12.5,-45.25'
    assert metadata['quiet_zone_modules']==4
    assert path.stat().st_size>100
    if extension=='png': assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    else: assert '<svg' in path.read_text()
    before=path.read_bytes()
    with pytest.raises(SystemExit):main(args)
    assert path.read_bytes()==before
    assert main(args+['--force'])==0


def test_bad_cli_does_not_write(tmp_path):
    path=tmp_path/'bad.png'
    with pytest.raises(SystemExit):main(['qr-location','--latitude','nan','--longitude','1','--output',str(path)])
    assert not path.exists()
