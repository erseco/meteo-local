// SPDX-License-Identifier: AGPL-3.0-or-later
// Run against generated fixture data with a local HTTP server on port 8765.
const { chromium, firefox, webkit } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const axe = require('axe-core');
const root = process.env.LPA_TEST_URL || 'http://127.0.0.1:8765';
const screenshots = process.env.LPA_SCREENSHOTS || '/tmp/lpa-screenshots';
const selected = process.env.LPA_BROWSERS?.split(',') || ['chromium', 'firefox', 'webkit'];

(async () => {
  fs.mkdirSync(screenshots, {recursive: true});
  for (const [name, type] of Object.entries({chromium, firefox, webkit})) {
    if (!selected.includes(name)) continue;
    const browser = await type.launch({headless: true});
    try {
      for (const mobile of [false, true]) for (const dark of [false, true]) {
        const context = await browser.newContext({
          viewport: mobile ? {width: 390, height: 844} : {width: 1440, height: 1000},
          colorScheme: dark ? 'dark' : 'light', timezoneId: 'America/New_York',
        });
        const page = await context.newPage();
        let errors = [], external = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('request', request => {
          if (!request.url().startsWith(root + '/')) external.push(request.url());
        });
        for (const file of ['index.html', 'sortir.html', 'consultes.html', 'perill.html',
                            'riera.html', 'fonts.html', 'avisos.html', 'fuentes.html', 'observaciones.html', 'fiabilitat.html']) {
          errors = []; external = [];
          await page.goto(`${root}/es/${file}`);
          if (file === 'index.html') await page.locator('#casa .previsio').first().waitFor();
          if (file === 'sortir.html') await page.getByText('No hay datos de servicio de Guaguas Municipales ni Global.').waitFor();
          if (file === 'observaciones.html' || file === 'fiabilitat.html') await page.getByText('Plaza de la Feria: Recogiendo datos', {exact:false}).waitFor();
          if (file === 'perill.html') await page.getByText('No hay avisos de AEMET en el feed consultado', {exact: false}).waitFor();
          await page.addScriptTag({content: axe.source});
          const violations = await page.evaluate(async () => (await axe.run()).violations.map(v => ({id:v.id, nodes:v.nodes.length})));
          assert.deepEqual(violations, [], `${name}/${file}: accessibility violations`);
          assert.deepEqual(errors, [], `${name}/${file}: JavaScript errors`);
          assert.deepEqual(external, [], `${name}/${file}: external requests`);
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${name}/${file}: overflow`);
          await page.screenshot({path: path.join(screenshots, `${name}-${mobile?'mobile':'desktop'}-${dark?'dark':'light'}-${file}.png`), fullPage:true});
        }
        // Exercise air, unavailable providers, source failure and stale-data handling.
        await page.goto(`${root}/es/consultes.html`);
        await page.getByRole('radio', {name:'Aire',exact:true}).check();
        await page.locator('#consulta').getByText('Calidad del aire', {exact:false}).waitFor();
        await page.getByRole('radio', {name:'Polen',exact:true}).check();
        await page.getByText('Polen local no disponible', {exact:false}).waitFor();
        await page.route('**/montflorit.json?*', async route => {
          const response = await route.fetch();
          const data = await response.json();
          data.avisos = null;
          await route.fulfill({json:data});
        });
        await page.goto(`${root}/es/perill.html`);
        await page.getByText('Avisos no disponibles o datos caducados.', {exact:false}).waitFor();
        await page.unroute('**/montflorit.json?*');
        await page.route('**/montflorit.json?*', async route => {
          const response = await route.fetch();
          const data = await response.json();
          data.generat = '2000-01-01T00:00:00+00:00';
          await route.fulfill({json:data});
        });
        await page.goto(`${root}/es/index.html`);
        await page.getByText('Datos caducados.', {exact:false}).waitFor();
        assert.equal(await page.locator('#casa .previsio').count(),0);
        await context.close();
        console.log(`${name}: ${mobile?'mobile':'desktop'}, ${dark?'dark':'light'} passed`);
      }
    } finally { await browser.close(); }
  }
})().catch(error => {console.error(error);process.exitCode=1;});
