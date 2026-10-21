# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seven-day availability, public contract, HTML escaping and metadata coherence."""
import json
from pathlib import Path
import tempfile
import unittest

from lpa import collect as C, public_data as D
from lpa.build import build
from lpa.tests.test_lpa import NOW, forecast, feed


class PublicData(unittest.TestCase):
    def data(self):
        def reader(url,params):
            if url==C.FORECAST:return json.dumps(forecast())
            if url==C.ALERTS:return feed()
            raise TimeoutError()
        return C.collect(NOW,reader,include_observations=False)

    def test_week_is_retained_and_probabilities_are_separate_from_mm(self):
        data=self.data()
        self.assertEqual(C.parameters()['forecast_days'],7)
        self.assertEqual(len(data['lpa']['daily_forecast']),7)
        self.assertGreater(len(data['hores']),144)
        public=D.normalize(data)
        self.assertEqual(public['forecast']['hourly'][0]['precipitation_probability_pct'],35)
        self.assertEqual(public['forecast']['hourly'][0]['precipitation_mm'],.4)
        self.assertTrue(public['expires_at'].startswith('2026-10-20T18:00'))

    def test_public_station_whitelist_missing_values_and_script_safety(self):
        data=self.data()
        data['lpa']['observations']={'stations':[{'id':'test','name':'</script><script>alert(1)</script>',
            'provider':'AEMET','status':'unavailable','temperature_c':None,'token':'private',
            'observed_at':'2026-10-20T12:00:00Z','max_age_minutes':30}], '_archive':['private']}
        public=D.normalize(data)
        self.assertNotIn('private',json.dumps(public))
        self.assertIsNone(public['observations'][0]['temperature_c'])
        html=D.snapshot(public)
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)

    def test_published_html_and_dataset_are_server_readable_and_consistent(self):
        with tempfile.TemporaryDirectory() as temp:
            build(temp);data=self.data();C.publish(Path(temp)/'montflorit.json',data)
            public=json.loads((Path(temp)/'weather.json').read_text())
            page=(Path(temp)/'datos.html').read_text()
            self.assertIn(public['generated_at'],page)
            self.assertIn('2026-10-26',page)
            self.assertIn('application/ld+json',page)
            schema=D.dataset(public)
            self.assertEqual(schema['dateModified'],public['generated_at'])
            self.assertEqual(schema['url'],D.SITE+'datos.html')
            self.assertEqual(public['links']['human'],D.SITE)
            self.assertEqual(public['links']['sources'],D.SITE+'fuentes.html')
            self.assertNotIn('lpa-public-snapshot',(Path(temp)/'es/datos.html').read_text())
            self.assertIn(public['forecast']['hourly'][-1]['end'],schema['temporalCoverage'])
            self.assertEqual(schema['distribution']['contentUrl'],D.SITE+'weather.json')
            index=(Path(temp)/'index.html').read_text()
            self.assertIn('index,follow',index)
            self.assertNotIn('noindex',index)
            self.assertIn('rel="canonical"',index)
            self.assertIn('weather.json',index)
            self.assertIn('id="lpa-home"',index)
            self.assertIn('src="lpa-home.js"',index)
            self.assertNotIn('src="casa.js"',index)
            self.assertTrue((Path(temp)/'sitemap.xml').exists())
            # Repeated publication replaces the snapshot rather than appending copies.
            C.publish(Path(temp)/'montflorit.json',data)
            self.assertEqual((Path(temp)/'datos.html').read_text().count('id="lpa-public-snapshot"'),1)


if __name__=='__main__':unittest.main()
