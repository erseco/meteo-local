# SPDX-License-Identifier: AGPL-3.0-or-later
"""Radar provenance, projection, age and partial-outage regression checks."""
import base64
import datetime as dt
import io
import json
import unittest

from PIL import Image
from lpa import radar as R

NOW = dt.datetime(2026,10,20,20,tzinfo=dt.timezone.utc)
BOUNDS = [[-25,19],[-7,19],[-7,37],[-25,37]]


def scan(minutes=0):
    time = NOW-dt.timedelta(minutes=minutes)
    return {'Nombre radar':'LPA','Fecha':time.astimezone(dt.timezone(dt.timedelta(hours=1))).isoformat(),
            'Nombre fichero':time.strftime('LPA%y%m%d%H%M%S.PPI.Z_005_240.png')}


def png():
    image=Image.new('RGBA',(1000,1000),'#0000fc')
    image.paste('#00fcfc',(500,0,1000,1000))
    output=io.BytesIO();image.save(output,format='PNG');return output.getvalue()


class Radar(unittest.TestCase):
    def test_scan_identity_offset_order_age_and_deduplication(self):
        entries=[scan(n) for n in [20,0,10,50,40,30,60,140,-20]]
        entries += [entries[0],{**scan(),'Nombre radar':'GLD'},
                    {**scan(),'Nombre fichero':'../../secret.png'},
                    {**scan(),'Fecha':'2026-10-20T20:00:00+01:00'}]
        result=R.scans([{'Producto':'PPI.Z_005_240','Elementos':entries}],NOW)
        self.assertEqual(len(result),6)
        self.assertEqual(result[-1]['observed_at'],NOW.isoformat())
        self.assertEqual(result[0]['observed_at'],(NOW-dt.timedelta(minutes=50)).isoformat())
        self.assertEqual(R.scans([{'Producto':'TOP','Elementos':[scan()]}],NOW),[])

    def test_mercator_projection_and_colour_preservation(self):
        result=R.render(png(),BOUNDS)
        image=Image.open(io.BytesIO(base64.b64decode(result.split(',')[1])))
        self.assertEqual(image.size,R.SIZE)
        # Neither of these ocean pixels contains coastline, marker or a label.
        self.assertEqual(image.getpixel((10,550)),(0,0,252))
        self.assertEqual(image.getpixel((990,550)),(0,252,252))
        # The middle latitude is not the arithmetic mean in Web Mercator.
        self.assertNotAlmostEqual(R.mercator(28),(R.mercator(19)+R.mercator(37))/2,places=4)
        with self.assertRaises(ValueError):R.render(png(),[[0,0],[1,1]])
        with self.assertRaises(OSError):R.render(b'not an image',BOUNDS)

    def reader(self,minutes=0,fail_latest=False):
        def read(url):
            if 'timeline' in url:return json.dumps([{'Producto':'PPI.Z_005_240','Elementos':[scan(minutes),scan(minutes+10)]}]).encode()
            if 'leyenda' in url:return b'{"Producto":"PPI","Lista RGBA":[{"RGBA":[0,0,252,255],"Valores":[12,18]}]}'
            if 'bounds' in url:return json.dumps(BOUNDS).encode()
            if fail_latest and scan(minutes)['Nombre fichero'] in url:raise TimeoutError()
            return png()
        return read

    def test_partial_outage_preserves_only_verified_frames(self):
        result=R.collect(NOW,self.reader(fail_latest=True))
        self.assertEqual(result['status'],'ok')
        self.assertEqual(len(result['frames']),1)
        self.assertEqual(result['observed_at'],(NOW-dt.timedelta(minutes=10)).isoformat())
        self.assertEqual(result['legend'][0]['label'],'12–18 dBZ')

    def test_old_radar_is_not_live_and_failure_is_not_no_rain(self):
        self.assertEqual(R.collect(NOW,self.reader(minutes=60))['status'],'stale')
        def failed(url):raise TimeoutError('private error not for publication')
        result=R.collect(NOW,failed)
        self.assertEqual(result['status'],'unavailable')
        self.assertEqual(result['frames'],[])
        self.assertNotIn('private error',result['detail'])


if __name__=='__main__':unittest.main()
