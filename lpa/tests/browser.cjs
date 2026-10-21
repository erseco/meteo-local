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
                            'riera.html', 'fonts.html', 'avisos.html', 'fuentes.html', 'observaciones.html', 'fiabilitat.html', 'radar.html', 'datos.html']) {
          errors = []; external = [];
          await page.goto(`${root}/${file}`);
          if (file === 'index.html') {
            const graph=page.locator('#casa .g-desplaca').first();
            await graph.waitFor();
            await page.getByText('Previsión · Open-Meteo · 7 días.',{exact:false}).waitFor();
            assert.ok(await page.locator('.g-dia').count()>=6,'graph must cover the forecast week');
            const labels=await page.locator('.g-dia').allTextContents();
            const lastDate=await page.evaluate(async()=>{
              const data=await (await fetch('./montflorit.json')).json();
              return new Intl.DateTimeFormat('es',{timeZone:'Atlantic/Canary',weekday:'long',day:'numeric',month:'short'}).format(new Date(data.hores.at(-1).hora));
            });
            assert.ok(labels.includes(lastDate),'last forecast date must be visible');
            await graph.focus();await page.keyboard.press('End');
            assert.ok(await graph.evaluate(el=>el.scrollLeft)>100,'keyboard must scroll the forecast');
            await page.keyboard.press('Home');
            if(!mobile) {
              const rect=await graph.boundingBox();
              const before=await graph.evaluate(el=>el.scrollLeft);
              await page.mouse.move(rect.x+rect.width*.7,rect.y+60);
              await page.mouse.down();await page.mouse.move(rect.x+rect.width*.2,rect.y+60,{steps:12});await page.mouse.up();
              assert.ok(await graph.evaluate(el=>el.scrollLeft)>before+40,'forecast must support mouse dragging');
            }
          }
          if (file === 'sortir.html') await page.getByText('No hay datos de servicio de Guaguas Municipales ni Global.').waitFor();
          if (file === 'observaciones.html' || file === 'fiabilitat.html') await page.getByRole('heading',{name:'Plaza de la Feria',exact:true}).waitFor();
          if (file === 'observaciones.html') {
            await page.getByRole('heading', {name:'La Isleta · Geonica 3705',exact:true}).waitFor();
            await page.getByText('Dato antiguo: no representa el polen actual.',{exact:true}).waitFor();
            await page.getByText('No aparecen eventos de Canarias en el feed consultado.',{exact:false}).waitFor();
            await page.getByText('Red de estaciones de centros educativos',{exact:true}).click();
            await page.getByRole('heading',{name:'IES Santiago Santana',exact:true}).waitFor();
          }
          if (file === 'perill.html') await page.getByText('No hay avisos de AEMET en el feed consultado', {exact: false}).waitFor();
          if (file === 'radar.html') {
            await page.locator('.lpa-radar-image').waitFor();
            const slider=page.getByLabel('Imagen de la secuencia',{exact:true});
            await slider.fill('0');
            await page.getByText('imagen 1 de 2',{exact:false}).waitFor();
            assert.equal(await page.locator('iframe').count(),0,'PORTUS must not load before a click');
          }
          if (file === 'sortir.html') {
            await page.getByRole('link',{name:'Consultar Próxima Guagua',exact:true}).waitFor();
          }
          if(file==='datos.html') {
            await page.getByRole('heading',{name:'Observaciones por estación',exact:true}).waitFor();
            const metadata=JSON.parse(await page.locator('#lpa-dataset').textContent());
            assert.equal(metadata['@type'],'Dataset');
          }
          await page.addScriptTag({content: axe.source});
          const violations = await page.evaluate(async () => (await axe.run()).violations.map(v => ({id:v.id, nodes:v.nodes.map(n=>({target:n.target,reason:n.failureSummary}))})));
          assert.deepEqual(violations, [], `${name}/${file}: accessibility violations`);
          assert.deepEqual(errors, [], `${name}/${file}: JavaScript errors`);
          assert.deepEqual(external, [], `${name}/${file}: external requests`);
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${name}/${file}: overflow`);
          await page.screenshot({path: path.join(screenshots, `${name}-${mobile?'mobile':'desktop'}-${dark?'dark':'light'}-${file}.png`), fullPage:true});
        }
        // Old bookmarks preserve the project prefix, query and fragment.
        await page.goto(`${root}/es/observaciones.html?legacy=1#lpa-observations`);
        await page.waitForURL(`${root}/observaciones.html?legacy=1#lpa-observations`);
        await page.getByRole('heading',{name:'Plaza de la Feria',exact:true}).waitFor();
        await page.goto(`${root}/es/?legacy=1#casa`);
        await page.waitForURL(`${root}/?legacy=1#casa`);
        assert.equal(await page.locator('html').getAttribute('lang'),'es');
        assert.equal(await page.locator('html').getAttribute('data-arrel'),'./');
        // Official embeds are opt-in and use the reviewed station URL, without a proxy.
        await page.goto(`${root}/radar.html`);
        await page.route('https://portus.puertos.es/**',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>PORTUS fixture</title><p>Official graph fixture</p>'}));
        await page.getByRole('button',{name:'Cargar gráfico de PORTUS',exact:true}).first().click();
        assert.equal(await page.locator('iframe').count(),1);
        assert.equal(await page.locator('iframe').getAttribute('src'),'https://portus.puertos.es/PortusData/rtChart?station=3450&params=SeaLevel&locale=es');
        await page.unroute('https://portus.puertos.es/**');
        // Exercise air, unavailable providers, source failure and stale-data handling.
        await page.goto(`${root}/consultes.html`);
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
        await page.goto(`${root}/perill.html`);
        await page.getByText('Avisos no disponibles o datos caducados.', {exact:false}).waitFor();
        await page.unroute('**/montflorit.json?*');
        await page.route('**/montflorit.json?*', async route => {
          const response = await route.fetch();
          const data = await response.json();
          data.generat = '2000-01-01T00:00:00+00:00';
          await route.fulfill({json:data});
        });
        await page.goto(`${root}/index.html`);
        await page.getByText('Datos caducados.', {exact:false}).waitFor();
        await page.getByText('Radar antiguo:',{exact:false}).waitFor();
        assert.equal(await page.locator('#casa .previsio').count(),0);
        await context.close();
        console.log(`${name}: ${mobile?'mobile':'desktop'}, ${dark?'dark':'light'} passed`);
      }
    } finally { await browser.close(); }
  }
})().catch(error => {console.error(error);process.exitCode=1;});
