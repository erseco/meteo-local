// SPDX-License-Identifier: AGPL-3.0-or-later
// Extra source status outside upstream rendering: missing is never 'all clear'.
llegeixDades('montflorit.json').then(data => {
  const box = document.getElementById('lpa-status');
  const current = data.lpa?.current_model;
  if (current && !dadesVelles(data)) {
    const p = document.createElement('p');
    const fmt = value => value == null ? 'no disponible' : new Intl.NumberFormat('es', {maximumFractionDigits: 1}).format(value);
    p.textContent = `Estimación actual del modelo: ${fmt(current.temperature_2m)} °C; humedad ${fmt(current.relative_humidity_2m)} %; viento ${fmt(current.wind_speed_10m)} km/h. No es una medición de una estación local.`;
    box.append(p);
  }
  if (data.avisos === null) {
    const p = document.createElement('p');
    p.className = 'avis';
    p.textContent = 'No se pudieron comprobar los avisos oficiales. Consulte AEMET.';
    box.append(p);
  }
}).catch(() => {});
