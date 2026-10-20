// SPDX-License-Identifier: AGPL-3.0-or-later
// Observed values remain tied to their station: no airport/school/city average.
function lpaText(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}
const lpaFormat = value => value == null ? '—' : new Intl.NumberFormat('es', {maximumFractionDigits: 1}).format(value);
function lpaStationStatus(station) {
  if (station.status === 'unavailable' || station.status === 'invalid') return station.status;
  const age = (Date.now() - new Date(station.observed_at).getTime()) / 60000;
  if (!Number.isFinite(age) || age < -5) return 'invalid';
  return age > station.max_age_minutes ? 'stale' : 'ok';
}
const LPA_STATES = {ok:'Lectura reciente', stale:'Lectura antigua', invalid:'Lectura descartada', unavailable:'Sin datos', not_configured:'Acceso pendiente'};
function lpaStationCard(station) {
  const status = lpaStationStatus(station);
  const card = lpaText('article', '', 'lpa-station');
  card.append(lpaText('h3', station.name), lpaText('p', `${station.region} · ${station.provider}`),
    lpaText('p', LPA_STATES[status], status === 'ok' ? 'lpa-fresh' : 'nota'));
  if (station.observed_at) {
    const time = new LpaDate(station.observed_at);
    card.append(lpaText('p', `${time.toLocaleString('es', {dateStyle:'short',timeStyle:'short'})} · hora canaria`));
  }
  if (status !== 'invalid' && status !== 'unavailable') {
    card.append(lpaText('p', `Temperatura: ${lpaFormat(station.temperature_c)} °C · Humedad: ${lpaFormat(station.relative_humidity_pct)} %`));
    card.append(lpaText('p', `Viento: ${lpaFormat(station.wind_kmh)} km/h · Racha: ${lpaFormat(station.gust_kmh)} km/h`));
    if (station.rain_mm != null) card.append(lpaText('p', `Lluvia acumulada en ${station.rain_period_minutes || '?'} min: ${lpaFormat(station.rain_mm)} mm`));
    if (station.rain_rate_mmh != null) card.append(lpaText('p', `Intensidad de lluvia: ${lpaFormat(station.rain_rate_mmh)} mm/h`));
    if (station.pressure_hpa != null) card.append(lpaText('p', `Presión: ${lpaFormat(station.pressure_hpa)} hPa (${station.pressure_kind === 'sea_level' ? 'reducida al nivel del mar' : station.pressure_kind === 'station' ? 'en la estación' : 'referencia no especificada'})`));
  }
  if (station.raw_report) {
    const report = document.createElement('details');
    report.append(lpaText('summary','Parte METAR original'), lpaText('p',station.raw_report));
    card.append(report);
  }
  if (station.detail) card.append(lpaText('p', station.detail, 'nota'));
  const link = lpaText('a', 'Consultar la fuente');
  // Only links from the trusted station registry are emitted by the collector.
  if (station.url?.startsWith('https://')) link.href = station.url;
  card.append(link);
  return card;
}
function lpaShowHistory(box, history) {
  box.append(lpaText('h2', 'Historial y comprobación de la previsión'));
  if (!history) {
    box.append(lpaText('p', 'El historial aún no está disponible.'));
    return;
  }
  box.append(lpaText('p', `${history.observations} observaciones archivadas · ${history.matched_samples} comparaciones válidas · ventana de ${history.retention_days} días.`));
  box.append(lpaText('p', history.method));
  for (const [id, model] of Object.entries(history.stations)) {
    const label = {C659M:'Plaza de la Feria',C658X:'Tafira',GCLP:'Aeropuerto'}[id] || id;
    const text = model.status === 'validated' ? 'Corrección validada en el periodo de prueba' : model.status === 'rejected' ? 'Corrección descartada: no mejora suficientemente' : 'Recogiendo datos: sin corrección validada';
    const item = lpaText('p', `${label}: ${text}. ${model.samples} comparaciones en ${model.days} días.`);
    if (model.mae_c != null) item.append(document.createTextNode(` Error absoluto medio del modelo: ${lpaFormat(model.mae_c)} °C.`));
    box.append(item);
  }
  box.append(lpaText('p', 'Se exigen al menos 14 días y una prueba temporal independiente. El aeropuerto y Tafira no corrigen automáticamente la costa urbana. No se calibra la lluvia con METAR.', 'nota'));
  if (history.forecast_error) box.append(lpaText('p', history.forecast_error, 'avis'));
}
function lpaShowEnvironment(box, environment) {
  if (!environment) return;
  box.append(lpaText('h2', 'Polen y esporas · Las Palmas'));
  const pollen = environment.pollen;
  if (pollen?.last_count) {
    const count = pollen.last_count;
    box.append(lpaText('p', `SEAIC · Fecha del último recuento: ${count.date}.`));
    if (pollen.status === 'stale') box.append(lpaText('p', 'Dato antiguo: no representa el polen actual.', 'avis'));
    box.append(lpaText('p', pollen.detail));
    const details = document.createElement('details');
    details.append(lpaText('summary', 'Ver los recuentos por especie'));
    const list = document.createElement('ul');
    for (const value of count.values) list.append(lpaText('li', `${value.taxon}: ${lpaFormat(value.value)} ${value.unit}`));
    details.append(list); box.append(details);
  } else box.append(lpaText('p', 'No se pudieron obtener recuentos de SEAIC. No equivale a un nivel cero.', 'nota'));
  const pollenLink = lpaText('a', 'Consultar Polenes.com');
  pollenLink.href = 'https://www.polenes.com/'; box.append(pollenLink);
  box.append(lpaText('h2', 'Actividad sísmica · IGN'));
  const seismic = environment.earthquakes;
  if (seismic?.status === 'ok') {
    box.append(lpaText('p', seismic.detail));
    if (!seismic.events.length) box.append(lpaText('p', 'No aparecen eventos de Canarias en el feed consultado. El feed no es un catálogo completo de la actividad sísmica.'));
    for (const event of seismic.events) {
      const p = lpaText('p', event.description + ' ');
      const link = lpaText('a', 'Detalle en IGN');
      if (event.url.startsWith('https://www.ign.es/')) link.href = event.url;
      p.append(link); box.append(p);
    }
  } else box.append(lpaText('p', 'No se pudo consultar el feed del IGN.', 'nota'));
}
llegeixDades('montflorit.json').then(data => {
  const box = document.getElementById('lpa-status');
  const current = data.lpa?.current_model;
  const observations = data.lpa?.observations;
  if (box && current && !dadesVelles(data)) {
    box.append(lpaText('p', `Estimación actual del modelo: ${lpaFormat(current.temperature_2m)} °C; humedad ${lpaFormat(current.relative_humidity_2m)} %; viento ${lpaFormat(current.wind_speed_10m)} km/h. No es una medición de una estación.`));
    const coast = observations?.stations.find(s => s.id === 'C659M');
    if (coast && lpaStationStatus(coast) === 'ok') box.append(lpaText('p', `Medido en Plaza de la Feria a las ${new LpaDate(coast.observed_at).toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'})}: ${lpaFormat(coast.temperature_c)} °C y ${lpaFormat(coast.relative_humidity_pct)} % de humedad. Referencia de costa urbana; no de todo el municipio.`));
    if (data.lpa.temperature_adjustment) box.append(lpaText('p', `La temperatura prevista de la costa urbana a 2–6 horas incorpora un ajuste validado de ${lpaFormat(data.lpa.temperature_adjustment.bias_c)} °C.`, 'nota'));
  }
  if (box && data.avisos === null) box.append(lpaText('p', 'No se pudieron comprobar los avisos oficiales. Consulte AEMET.', 'avis'));
  const target = document.getElementById('lpa-observations');
  if (!target) return;
  target.replaceChildren();
  if (dadesVelles(data)) target.append(lpaText('p', 'La publicación está caducada. Las lecturas siguientes son las últimas recibidas, no el tiempo actual.', 'avis'));
  target.append(lpaText('h2', 'Estaciones de referencia'));
  const grid = lpaText('div', '', 'lpa-station-grid');
  for (const station of observations?.stations || []) {
    if (['C659M','C658X','GCLP'].includes(station.id)) grid.append(lpaStationCard(station));
  }
  target.append(grid);
  target.append(lpaText('h2', 'Otras estaciones del municipio'));
  const urbanGrid = lpaText('div', '', 'lpa-station-grid');
  for (const station of observations?.stations || []) if (station.category === 'urban') urbanGrid.append(lpaStationCard(station));
  target.append(urbanGrid);
  const schools = document.createElement('details');
  schools.append(lpaText('summary', 'Red de estaciones de centros educativos'));
  const schoolGrid = lpaText('div', '', 'lpa-station-grid');
  for (const station of observations?.stations || []) if (station.category === 'school') schoolGrid.append(lpaStationCard(station));
  schools.append(lpaText('p', 'Contexto regional: no se mezclan las medidas de colegios de otros municipios con la temperatura de Las Palmas.'),schoolGrid);
  target.append(schools,lpaText('h2','Otras redes institucionales'));
  for (const provider of observations?.providers || []) {
    const p = lpaText('p', `${provider.name}: ${provider.detail} `);
    const link = lpaText('a','Fuente institucional');
    if (provider.url?.startsWith('https://')) link.href = provider.url;
    p.append(link); target.append(p);
  }
  lpaShowHistory(target, data.lpa?.history);
  lpaShowEnvironment(target, data.lpa?.environment);
}).catch(() => {
  const target = document.getElementById('lpa-observations');
  if (target) target.replaceChildren(lpaText('p','No se pudieron cargar las observaciones. Consulte las fuentes oficiales.','avis'));
});
