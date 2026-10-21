// SPDX-License-Identifier: AGPL-3.0-or-later
// Visual home page for Las Palmas: forecast first, then radar, wind, calima and sea.
// Every value keeps its source; a missing source is shown as unavailable, never as zero.
const LH_TZ = 'Atlantic/Canary';
const LH_SVG = 'http://www.w3.org/2000/svg';
const lhFmt = (options) => new Intl.DateTimeFormat('es', {timeZone: LH_TZ, ...options});
const lhHour = lhFmt({hour: '2-digit', minute: '2-digit'});
const lhHourShort = lhFmt({hour: 'numeric'});
const lhDayKey = new Intl.DateTimeFormat('en-CA', {timeZone: LH_TZ, year: 'numeric', month: '2-digit', day: '2-digit'});
const lhWeekday = lhFmt({weekday: 'short', day: 'numeric'});
const lhWeekdayLong = lhFmt({weekday: 'long'});
const lhNumber = (value, digits = 0) => value == null || !Number.isFinite(value) ? '—'
  : new Intl.NumberFormat('es', {maximumFractionDigits: digits, minimumFractionDigits: 0}).format(value);
const lhEsc = (text) => String(text).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[c]);

function lh(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key === 'html') node.innerHTML = value;
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) if (child != null) node.append(child);
  return node;
}

function lhSvg(width, height, body, label) {
  const svg = document.createElementNS(LH_SVG, 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);
  if (label) {
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', label);
  } else svg.setAttribute('aria-hidden', 'true');
  svg.innerHTML = body;
  return svg;
}

function lhDayName(date, today) {
  const key = lhDayKey.format(date);
  const diff = Math.round((Date.parse(key) - Date.parse(today)) / 86400000);
  if (diff === 0) return 'Hoy';
  if (diff === 1) return 'Mañana';
  return lhWeekday.format(date);
}

// --- Weather icons: colour SVG built from constant shapes only ---
const LH_CLOUD = 'M19 50h28a11 11 0 0 0 1.5-21.9A15 15 0 0 0 19.6 25 12.5 12.5 0 0 0 19 50z';
const LH_ICON_PARTS = {
  sun: '<g class="lh-i-sun"><circle cx="32" cy="32" r="11"/><path d="M32 8v7M32 49v7M8 32h7M49 32h7M15 15l5 5M44 44l5 5M15 49l5-5M44 20l5-5"/></g>',
  moon: '<path class="lh-i-moon" d="M41 10a20 20 0 1 0 13 33A16 16 0 0 1 41 10z"/>',
  cloud: `<path class="lh-i-cloud" d="${LH_CLOUD}"/>`,
  darkCloud: `<path class="lh-i-cloud lh-i-dark" d="${LH_CLOUD}"/>`,
  rain: '<path class="lh-i-rain" d="M24 54l-3 7M34 54l-3 7M44 54l-3 7"/>',
  drizzle: '<path class="lh-i-rain" d="M25 55v3M35 55v3M45 55v3M30 60v2M40 60v2"/>',
  snow: '<g class="lh-i-snow"><circle cx="24" cy="57" r="2.4"/><circle cx="34" cy="60" r="2.4"/><circle cx="44" cy="57" r="2.4"/></g>',
  bolt: '<path class="lh-i-bolt" d="M35 44l-7 11h7l-4 9 11-14h-7l4-6z"/>',
  fog: '<path class="lh-i-fog" d="M12 30h40M8 39h48M14 48h36"/>',
};

function lhKind(code) {
  if (code == null) return 'cloud';
  if (code <= 1) return 'clear';
  if (code === 2) return 'partly';
  if (code === 3) return 'cloud';
  if (code === 45 || code === 48) return 'fog';
  if (code >= 51 && code <= 57) return 'drizzle';
  if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) return 'rain';
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'snow';
  if (code >= 95) return 'storm';
  return 'cloud';
}

const LH_CONDITIONS = {
  0: 'Despejado', 1: 'Casi despejado', 2: 'Intervalos nubosos', 3: 'Cubierto', 45: 'Niebla', 48: 'Niebla',
  51: 'Llovizna débil', 53: 'Llovizna', 55: 'Llovizna intensa', 56: 'Llovizna helada', 57: 'Llovizna helada',
  61: 'Lluvia débil', 63: 'Lluvia', 65: 'Lluvia fuerte', 66: 'Lluvia helada', 67: 'Lluvia helada',
  71: 'Nieve débil', 73: 'Nieve', 75: 'Nieve intensa', 77: 'Nieve', 80: 'Chubascos débiles', 81: 'Chubascos',
  82: 'Chubascos fuertes', 85: 'Chubascos de nieve', 86: 'Chubascos de nieve', 95: 'Tormenta',
  96: 'Tormenta con granizo', 99: 'Tormenta con granizo',
};

function lhIconMarkup(code, night) {
  const p = LH_ICON_PARTS;
  const kind = lhKind(code);
  const sky = night ? p.moon : p.sun;
  const small = (part) => `<g transform="translate(-6 -8) scale(.78)">${part}</g>`;
  return {
    clear: sky,
    partly: small(sky) + p.cloud,
    cloud: p.cloud,
    fog: p.fog,
    drizzle: small(sky) + p.cloud + p.drizzle,
    rain: p.darkCloud + p.rain,
    snow: p.cloud + p.snow,
    storm: p.darkCloud + p.bolt,
  }[kind];
}

function lhIcon(code, night, size = 40) {
  const svg = lhSvg(64, 64, lhIconMarkup(code, night));
  svg.setAttribute('width', size);
  svg.setAttribute('height', size);
  svg.classList.add('lh-icon');
  return svg;
}

// --- Wind helpers ---
const LH_POINTS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'];
const lhCardinal = (deg) => deg == null ? '' : LH_POINTS[Math.round(((deg % 360) + 360) % 360 / 22.5) % 16];
function lhWindWord(speed) {
  if (speed == null) return 'Sin datos';
  if (speed < 6) return 'Calma';
  if (speed < 20) return 'Flojo';
  if (speed < 39) return 'Moderado';
  if (speed < 50) return 'Fuerte';
  if (speed < 62) return 'Muy fuerte';
  return 'Temporal';
}
const lhWindLevel = (speed) => speed == null ? 0 : speed < 20 ? 1 : speed < 39 ? 2 : speed < 50 ? 3 : 4;
// The arrow points where the wind blows to; its label says where it comes from.
function lhArrow(deg, size = 18) {
  const svg = lhSvg(24, 24, `<g transform="rotate(${(Number(deg) + 180) % 360} 12 12)"><path d="M12 3l6 15-6-4-6 4z"/></g>`);
  svg.setAttribute('width', size);
  svg.setAttribute('height', size);
  svg.classList.add('lh-arrow');
  return svg;
}

// --- Calima and UV scales ---
const LH_DUST = {
  none: {label: 'Sin calima', color: '#16a34a'}, light: {label: 'Calima leve', color: '#ca8a04'},
  moderate: {label: 'Calima moderada', color: '#ea580c'}, intense: {label: 'Calima intensa', color: '#dc2626'},
  very_intense: {label: 'Calima muy intensa', color: '#7e22ce'},
};
const LH_DUST_STOPS = [[0, 'none'], [20, 'light'], [50, 'moderate'], [100, 'intense'], [200, 'very_intense']];
function lhUv(uv) {
  if (uv == null) return {label: 'Sin datos', color: '#94a3b8'};
  if (uv < 3) return {label: 'Bajo', color: '#16a34a'};
  if (uv < 6) return {label: 'Moderado', color: '#ca8a04'};
  if (uv < 8) return {label: 'Alto', color: '#ea580c'};
  if (uv < 11) return {label: 'Muy alto', color: '#dc2626'};
  return {label: 'Extremo', color: '#7e22ce'};
}
const LH_AIR = {
  bona: ['Buena', '#16a34a'], raonablement_bona: ['Razonablemente buena', '#65a30d'], regular: ['Regular', '#ca8a04'],
  desfavorable: ['Desfavorable', '#ea580c'], molt_desfavorable: ['Muy desfavorable', '#dc2626'],
  extremadament_desfavorable: ['Extremadamente desfavorable', '#7e22ce'],
};
const LH_ALERT_TYPES = {
  tempestes: 'tormentas', inundacions: 'inundaciones', pluja: 'lluvia', vent: 'viento', calor: 'calor',
  fred: 'frío', neu: 'nieve', boira: 'niebla', incendis: 'incendios', costaners: 'fenómenos costeros',
  allaus: 'aludes', pols: 'polvo en suspensión', altres: 'otros fenómenos',
};
const LH_ALERT_LEVELS = {groc: 'amarillo', taronja: 'naranja', vermell: 'rojo'};

function lhCard(id) {
  const box = document.getElementById(id);
  if (box) box.querySelectorAll(':scope > :not(h2):not(.lh-card-head)').forEach((node) => node.remove());
  return box;
}

function lhUnavailable(box, text) {
  box.append(lh('p', {class: 'lh-empty', text}));
}

// --- Alerts ---
function lhAlerts(data, stale) {
  const box = document.getElementById('lh-alerts');
  box.replaceChildren();
  if (stale) return;
  if (data.avisos === null) {
    box.append(lh('a', {class: 'lh-alert lh-alert-unknown', href: 'perill.html'},
      lh('strong', {text: 'Avisos no comprobados.'}), ' No se pudo consultar AEMET; no equivale a «sin avisos».'));
    return;
  }
  for (const alert of data.avisos || []) {
    const level = LH_ALERT_LEVELS[alert.nivel] || alert.nivel;
    const type = LH_ALERT_TYPES[alert.tipo] || alert.tipo;
    const end = new Date(alert.fin);
    box.append(lh('a', {class: `lh-alert lh-alert-${alert.nivel}`, href: 'perill.html'},
      lh('span', {class: 'lh-alert-dot', 'aria-hidden': 'true'}),
      lh('strong', {text: `Aviso ${level} por ${type}`}),
      ` · ${alert.zona} · hasta ${lhDayName(end, lhDayKey.format(new Date())).toLowerCase()} a las ${lhHour.format(end)}`));
  }
}

// --- Now ---
function lhReferenceStation(data) {
  const stations = data.lpa?.observations?.stations || [];
  for (const id of ['C659M', 'GRAFCAN-3705']) {
    const station = stations.find((s) => s.id === id);
    if (station?.temperature_c != null && typeof lpaStationStatus === 'function' && lpaStationStatus(station) === 'ok') return station;
  }
  return null;
}

function lhNow(data) {
  const box = document.getElementById('lh-now');
  const current = data.lpa?.current_model;
  const first = data.hores?.[0];
  const today = data.lpa?.daily_forecast?.[0];
  const code = current?.weather_code ?? first?.codi;
  const night = (current?.is_day ?? first?.es_dia) === 0;
  const kind = lhKind(code);
  box.className = `lh-hero lh-sky-${night ? 'night' : kind === 'clear' || kind === 'partly' ? 'day' : kind === 'rain' || kind === 'storm' || kind === 'drizzle' ? 'rain' : 'cloud'}`;
  const station = lhReferenceStation(data);
  const temp = station?.temperature_c ?? current?.temperature_2m ?? first?.temperatura;
  const origin = station ? `Medido en ${station.name} a las ${lhHour.format(new Date(station.observed_at))}`
    : current ? 'Estimación del modelo Open-Meteo' : 'Previsión de la hora en curso';
  const wind = current?.wind_speed_10m ?? first?.vent;
  const gust = current?.wind_gusts_10m ?? first?.ratxa;
  const dir = current?.wind_direction_10m ?? first?.direccio;
  const humidity = station?.relative_humidity_pct ?? current?.relative_humidity_2m ?? first?.humitat;
  const uv = first?.uv;
  const updated = new Date(data.generat);
  const left = lh('div', {class: 'lh-hero-main'},
    lh('p', {class: 'lh-hero-place'}, 'Las Palmas de Gran Canaria ',
      lh('span', {text: `· actualizado a las ${lhHour.format(updated)}`})),
    lh('div', {class: 'lh-hero-temp'}, lhIcon(code, night, 88),
      lh('p', {}, lh('span', {class: 'lh-big', text: `${lhNumber(temp)}°`}),
        lh('span', {class: 'lh-cond', text: LH_CONDITIONS[code] || 'Sin datos del cielo'}))),
    lh('p', {class: 'lh-hero-origin', text: origin}),
    lh('p', {class: 'lh-hero-range'},
      today ? `Máx. ${lhNumber(today.temperature_2m_max)}° · Mín. ${lhNumber(today.temperature_2m_min)}°` : '',
      current?.apparent_temperature != null ? ` · Sensación ${lhNumber(current.apparent_temperature)}°` : ''));
  const chip = (label, value, extra) => lh('li', {class: 'lh-chip'}, lh('span', {class: 'lh-chip-label', text: label}),
    lh('span', {class: 'lh-chip-value'}, extra || null, value));
  const rainToday = today ? `${lhNumber(today.precipitation_probability_max)} % · ${lhNumber(today.precipitation_sum, 1)} mm` : '—';
  const chips = lh('ul', {class: 'lh-chips', 'aria-label': 'Condiciones actuales'},
    chip('Viento', `${lhNumber(wind)} km/h ${lhCardinal(dir)}`, dir != null ? lhArrow(dir, 16) : null),
    chip('Rachas', `${lhNumber(gust)} km/h`),
    chip('Humedad', `${lhNumber(humidity)} %`),
    chip('Lluvia hoy', rainToday),
    chip('Índice UV', `${lhNumber(uv)} · ${lhUv(uv).label}`));
  box.replaceChildren(lh('h2', {class: 'lh-sr', text: 'El tiempo ahora'}), left, chips);
}

// --- Hourly chart ---
function lhHours(data) {
  const box = lhCard('lh-hours');
  const rows = (data.hores || []).slice(0, 48);
  if (!rows.length) return lhUnavailable(box, 'Previsión horaria no disponible.');
  const col = 60, top = 64, height = 296;
  const width = rows.length * col;
  const temps = rows.map((r) => r.temperatura).filter((v) => v != null);
  const tMin = Math.min(...temps), tMax = Math.max(...temps);
  const span = Math.max(tMax - tMin, 3);
  const ty = (t) => top + 26 + (1 - (t - tMin) / span) * 50;
  const rainMax = Math.max(2, ...rows.map((r) => r.pluja_mm || 0));
  const x = (i) => i * col + col / 2;
  let body = '';
  const today = lhDayKey.format(new Date());
  rows.forEach((r, i) => {
    const date = new Date(r.hora);
    const hour = Number(lhHourShort.format(date));
    if (hour === 0 || i === 0) {
      body += `<line class="lh-c-day" x1="${i * col}" x2="${i * col}" y1="0" y2="${height}"/>`;
      body += `<text class="lh-c-dayname" x="${i * col + 6}" y="13">${lhEsc(lhDayName(date, today))}</text>`;
    }
    if (r.es_dia === 0) body += `<rect class="lh-c-night" x="${i * col}" y="18" width="${col}" height="${height - 18}"/>`;
    body += `<text class="lh-c-hour" x="${x(i)}" y="34">${hour} h</text>`;
    body += `<g transform="translate(${x(i) - 17} 38) scale(.53)">${lhIconMarkup(r.codi, r.es_dia === 0)}</g>`;
  });
  // Temperature curve with a soft area below.
  const points = rows.map((r, i) => r.temperatura == null ? null : [x(i), ty(r.temperatura)]).filter(Boolean);
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join('');
  body += `<path class="lh-c-area" d="${line}L${points.at(-1)[0]} ${top + 84}L${points[0][0]} ${top + 84}Z"/>`;
  body += `<path class="lh-c-temp" d="${line}"/>`;
  rows.forEach((r, i) => {
    if (r.temperatura == null) return;
    body += `<circle class="lh-c-dot" cx="${x(i)}" cy="${ty(r.temperatura)}" r="3"/>`;
    body += `<text class="lh-c-tval" x="${x(i)}" y="${ty(r.temperatura) - 9}">${lhNumber(r.temperatura)}°</text>`;
  });
  // Rain: bar height is the accumulated amount; the label is the probability.
  const rainBase = top + 148;
  rows.forEach((r, i) => {
    const mm = r.pluja_mm || 0;
    const probability = r.probabilitat == null ? null : Math.round(r.probabilitat * 100);
    const h = mm > 0 ? Math.max(3, (mm / rainMax) * 40) : 0;
    if (h) body += `<rect class="lh-c-rain" x="${x(i) - 13}" y="${rainBase - h}" width="26" height="${h}" rx="3" opacity="${0.35 + 0.65 * (r.probabilitat ?? 1)}"/>`;
    if (mm >= 0.1) body += `<text class="lh-c-mm" x="${x(i)}" y="${rainBase - h - 4}">${lhNumber(mm, 1)}</text>`;
    body += `<text class="lh-c-prob${probability >= 40 ? ' is-high' : ''}" x="${x(i)}" y="${rainBase + 14}">${probability == null ? '—' : probability + ' %'}</text>`;
  });
  body += `<line class="lh-c-base" x1="0" x2="${width}" y1="${rainBase}" y2="${rainBase}"/>`;
  // Wind: arrow towards where it blows, speed and gust.
  rows.forEach((r, i) => {
    const level = lhWindLevel(r.vent);
    if (r.direccio != null) body += `<g class="lh-c-wind lh-w${level}" transform="translate(${x(i)} ${rainBase + 34}) rotate(${(r.direccio + 180) % 360})"><path d="M0 -9l6 14-6-4-6 4z"/></g>`;
    body += `<text class="lh-c-wval lh-w${level}" x="${x(i)}" y="${rainBase + 60}">${lhNumber(r.vent)}</text>`;
    body += `<text class="lh-c-gust" x="${x(i)}" y="${rainBase + 73}">${lhNumber(r.ratxa)}</text>`;
  });
  const svg = lhSvg(width, height + 6, body,
    `Próximas ${rows.length} horas: temperatura entre ${lhNumber(tMin)} y ${lhNumber(tMax)} grados, ` +
    `lluvia máxima ${lhNumber(Math.max(...rows.map((r) => r.pluja_mm || 0)), 1)} mm en una hora, ` +
    `racha máxima ${lhNumber(Math.max(...rows.map((r) => r.ratxa || 0)))} km/h. La tabla siguiente tiene los datos.`);
  svg.classList.add('lh-chart');
  const scroller = lh('div', {class: 'lh-scroll', tabindex: '0', role: 'region', 'aria-label': 'Previsión por horas, desplazable'});
  scroller.append(svg);
  lhDraggable(scroller);
  const legend = lh('ul', {class: 'lh-legend', 'aria-hidden': 'true'},
    lh('li', {}, lh('span', {class: 'lh-key lh-key-temp'}), 'Temperatura'),
    lh('li', {}, lh('span', {class: 'lh-key lh-key-rain'}), 'Lluvia (mm) y probabilidad'),
    lh('li', {}, lh('span', {class: 'lh-key lh-key-wind'}), 'Viento y racha (km/h)'));
  const table = lh('table', {class: 'lh-table'},
    lh('thead', {}, lh('tr', {}, ['Hora', 'Cielo', 'Temp.', 'Lluvia', 'Prob.', 'Viento', 'Racha'].map((t) => lh('th', {scope: 'col', text: t})))),
    lh('tbody', {}, rows.map((r) => lh('tr', {},
      lh('th', {scope: 'row', text: `${lhDayName(new Date(r.hora), today)} ${lhHour.format(new Date(r.hora))}`}),
      lh('td', {text: LH_CONDITIONS[r.codi] || '—'}), lh('td', {text: `${lhNumber(r.temperatura, 1)} °C`}),
      lh('td', {text: `${lhNumber(r.pluja_mm, 1)} mm`}),
      lh('td', {text: r.probabilitat == null ? '—' : `${Math.round(r.probabilitat * 100)} %`}),
      lh('td', {text: `${lhNumber(r.vent)} km/h ${lhCardinal(r.direccio)}`}), lh('td', {text: `${lhNumber(r.ratxa)} km/h`})))));
  box.append(scroller, legend, lh('details', {class: 'lh-more'}, lh('summary', {text: 'Ver como tabla'}), lh('div', {class: 'lh-table-wrap'}, table)));
}

function lhDraggable(node) {
  let drag = null;
  let moved = false;
  node.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'mouse' || e.button !== 0) return;
    drag = {x: e.clientX, left: node.scrollLeft};
    moved = false;
  });
  node.addEventListener('pointermove', (e) => {
    if (!drag || !(e.buttons & 1)) return;
    const distance = e.clientX - drag.x;
    if (Math.abs(distance) > 5) {
      moved = true;
      node.setPointerCapture(e.pointerId);
      node.classList.add('is-dragging');
    }
    if (moved) node.scrollLeft = drag.left - distance;
  });
  const stop = () => { drag = null; node.classList.remove('is-dragging'); };
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) node.addEventListener(type, stop);
  node.addEventListener('keydown', (e) => {
    if (e.key === 'Home' || e.key === 'End') {
      e.preventDefault();
      node.scrollLeft = e.key === 'Home' ? 0 : node.scrollWidth;
    }
  });
}

// --- Seven days ---
function lhDays(data) {
  const box = lhCard('lh-days');
  const days = (data.lpa?.daily_forecast || []).filter((d) => d.temperature_2m_max != null);
  if (!days.length) return lhUnavailable(box, 'Previsión diaria no disponible.');
  const low = Math.min(...days.map((d) => d.temperature_2m_min));
  const high = Math.max(...days.map((d) => d.temperature_2m_max));
  const range = Math.max(high - low, 1);
  const today = lhDayKey.format(new Date());
  const list = lh('ol', {class: 'lh-days'});
  days.forEach((d, i) => {
    const date = new Date(`${d.date}T12:00:00Z`);
    const name = lhDayName(date, today);
    const probability = d.precipitation_probability_max;
    const bar = lh('span', {class: 'lh-range', 'aria-hidden': 'true'}, lh('span', {
      class: 'lh-range-fill',
      style: `left:${((d.temperature_2m_min - low) / range) * 100}%;right:${((high - d.temperature_2m_max) / range) * 100}%`,
    }));
    const row = lh('li', {class: `lh-day${i >= 3 ? ' is-uncertain' : ''}`},
      lh('span', {class: 'lh-day-name', title: lhWeekdayLong.format(date), text: name}),
      lhIcon(d.weather_code, false, 38),
      lh('span', {class: `lh-day-rain${probability >= 40 ? ' is-high' : ''}`},
        lh('span', {class: 'lh-sr', text: 'Probabilidad de lluvia '}), probability == null ? '—' : `${probability} %`,
        d.precipitation_sum >= 0.1 ? lh('small', {text: ` ${lhNumber(d.precipitation_sum, 1)} mm`}) : null),
      lh('span', {class: 'lh-day-min'}, lh('span', {class: 'lh-sr', text: 'mínima '}), `${lhNumber(d.temperature_2m_min)}°`),
      bar,
      lh('span', {class: 'lh-day-max'}, lh('span', {class: 'lh-sr', text: 'máxima '}), `${lhNumber(d.temperature_2m_max)}°`),
      lh('span', {class: `lh-day-wind lh-w${lhWindLevel(d.wind_gusts_10m_max ?? d.wind_speed_10m_max)}`},
        d.wind_direction_10m_dominant != null ? lhArrow(d.wind_direction_10m_dominant, 15) : null,
        lh('span', {class: 'lh-sr', text: 'viento máximo '}),
        `${lhNumber(d.wind_speed_10m_max)}`, d.wind_gusts_10m_max != null ? lh('small', {text: `/${lhNumber(d.wind_gusts_10m_max)}`}) : null,
        lh('small', {text: ' km/h'})));
    list.append(row);
  });
  box.append(list, lh('p', {class: 'lh-note', text: 'Viento medio/racha máxima. Desde el cuarto día la previsión es menos fiable.'}));
}

// --- Radar ---
function lhRadar(data, stale) {
  const box = lhCard('lh-radar');
  const radar = data?.lpa?.radar;
  const frames = (radar?.frames || []).filter((f) => /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(f.image));
  if (!frames.length || radar.status === 'unavailable') {
    lhUnavailable(box, 'Radar no disponible. No equivale a ausencia de lluvia.');
    box.append(lh('a', {class: 'lh-link', href: 'https://www.aemet.es/es/eltiempo/observacion/radar?w=1', text: 'Radar oficial de AEMET'}));
    return;
  }
  const fresh = !stale && typeof lpaStationStatus === 'function' && lpaStationStatus(radar) === 'ok';
  if (!fresh) box.append(lh('p', {class: 'lh-warn', text: 'Radar antiguo: estas imágenes no representan la situación actual.'}));
  const image = lh('img', {class: 'lh-radar-img', width: 1000, height: 580, alt: ''});
  const stamp = lh('span', {class: 'lh-radar-time', 'aria-live': 'polite'});
  const range = lh('input', {type: 'range', min: 0, max: frames.length - 1, step: 1, value: frames.length - 1,
    id: 'lh-radar-frame', 'aria-label': 'Imagen de la secuencia del radar'});
  const play = lh('button', {type: 'button', class: 'lh-play', 'aria-pressed': 'false'});
  const show = (index) => {
    const frame = frames[index];
    const date = new Date(frame.observed_at);
    const minutes = Math.round((Date.now() - date) / 60000);
    stamp.textContent = `${lhHour.format(date)} · hace ${minutes < 60 ? minutes + ' min' : Math.round(minutes / 60) + ' h'} · ${Number(index) + 1}/${frames.length}`;
    image.alt = `Radar de AEMET de Canarias a las ${lhHour.format(date)}, con Las Palmas señalada.`;
    image.src = frame.image;
    range.value = index;
  };
  let timer = null;
  const setPlaying = (on) => {
    clearInterval(timer);
    timer = null;
    play.setAttribute('aria-pressed', String(on));
    play.textContent = on ? 'Pausa' : 'Animar';
    play.setAttribute('aria-label', on ? 'Pausar la animación del radar' : 'Animar el radar');
    if (on) timer = setInterval(() => show((Number(range.value) + 1) % frames.length), 700);
  };
  play.addEventListener('click', () => setPlaying(!timer));
  range.addEventListener('input', () => { setPlaying(false); show(Number(range.value)); });
  setPlaying(false);
  show(frames.length - 1);
  const legend = (radar.legend || []).slice().reverse().filter((e) => /^#[0-9a-f]{6}$/i.test(e.color));
  const scale = lh('div', {class: 'lh-radar-scale', 'aria-hidden': 'true',
    style: `background:linear-gradient(90deg,${legend.map((e) => e.color).join(',')})`});
  box.append(lh('div', {class: 'lh-radar-frame'}, image, lh('span', {class: `lh-badge ${fresh ? 'is-ok' : 'is-old'}`, text: fresh ? 'En directo' : 'Antiguo'})),
    lh('div', {class: 'lh-radar-controls'}, play, range, stamp),
    lh('div', {class: 'lh-radar-legend'}, lh('span', {text: 'Débil'}), scale, lh('span', {text: 'Intensa'})),
    lh('p', {class: 'lh-note'}, 'Reflectividad de AEMET (dBZ): ecos en altura, no lluvia medida en el suelo. ',
      lh('a', {href: 'radar.html', text: 'Radar ampliado y mar'})));
}

// --- Wind ---
function lhWind(data) {
  const box = lhCard('lh-wind');
  const current = data.lpa?.current_model;
  const rows = (data.hores || []).slice(0, 24);
  const speed = current?.wind_speed_10m ?? rows[0]?.vent;
  const gust = current?.wind_gusts_10m ?? rows[0]?.ratxa;
  const dir = current?.wind_direction_10m ?? rows[0]?.direccio;
  if (speed == null) return lhUnavailable(box, 'Viento no disponible.');
  let dial = '<circle class="lh-d-ring" cx="70" cy="70" r="60"/>';
  for (let a = 0; a < 360; a += 30) {
    const r1 = a % 90 ? 54 : 50;
    const rad = (a * Math.PI) / 180;
    dial += `<line class="lh-d-tick" x1="${70 + Math.sin(rad) * r1}" y1="${70 - Math.cos(rad) * r1}" x2="${70 + Math.sin(rad) * 60}" y2="${70 - Math.cos(rad) * 60}"/>`;
  }
  dial += '<text class="lh-d-card" x="70" y="24">N</text><text class="lh-d-card" x="118" y="74">E</text><text class="lh-d-card" x="70" y="124">S</text><text class="lh-d-card" x="22" y="74">O</text>';
  if (dir != null) dial += `<g class="lh-d-arrow lh-w${lhWindLevel(speed)}" transform="rotate(${(dir + 180) % 360} 70 70)"><path d="M70 30l11 32h-7v28h-8V62h-7z"/></g>`;
  const compass = lhSvg(140, 140, dial, dir == null ? null : `Viento del ${lhCardinal(dir)}`);
  compass.classList.add('lh-compass');
  const trade = dir != null && dir >= 0 && dir <= 80 && speed >= 12;
  const stats = lh('div', {class: 'lh-wind-stats'},
    lh('p', {class: 'lh-metric'}, lh('span', {class: 'lh-metric-value', text: lhNumber(speed)}), lh('span', {class: 'lh-metric-unit', text: ' km/h'})),
    lh('p', {class: 'lh-metric-sub', text: `${lhWindWord(speed)}${dir != null ? ' del ' + lhCardinal(dir) : ''}`}),
    lh('p', {class: 'lh-metric-sub'}, 'Rachas ', lh('strong', {text: `${lhNumber(gust)} km/h`})),
    trade ? lh('span', {class: 'lh-tag', text: 'Alisio'}) : null);
  box.append(lh('div', {class: 'lh-wind-now'}, compass, stats));
  if (rows.length) {
    const col = 14, h = 70;
    const max = Math.max(40, ...rows.map((r) => r.ratxa || 0));
    let body = '';
    rows.forEach((r, i) => {
      const bh = ((r.vent || 0) / max) * h;
      body += `<rect class="lh-w${lhWindLevel(r.vent)} lh-c-wbar" x="${i * col + 2}" y="${h - bh + 4}" width="${col - 4}" height="${bh}" rx="2"/>`;
    });
    const gustLine = rows.map((r, i) => `${i ? 'L' : 'M'}${i * col + col / 2} ${h - ((r.ratxa || 0) / max) * h + 4}`).join('');
    body += `<path class="lh-c-gustline" d="${gustLine}"/>`;
    const peak = rows.reduce((a, b) => ((b.ratxa || 0) > (a.ratxa || 0) ? b : a));
    const chart = lhSvg(rows.length * col, h + 8, body,
      `Viento en las próximas 24 horas; racha máxima ${lhNumber(peak.ratxa)} km/h a las ${lhHour.format(new Date(peak.hora))}`);
    chart.classList.add('lh-mini');
    box.append(chart, lh('p', {class: 'lh-note'}, 'Próximas 24 h: barras = viento medio, línea = rachas. Máxima ',
      lh('strong', {text: `${lhNumber(peak.ratxa)} km/h`}), ` a las ${lhHour.format(new Date(peak.hora))}.`));
  }
}

// --- Calima ---
function lhGauge(value) {
  // Non-linear scale so that the usual 0–100 µg/m³ range fills most of the dial.
  const max = 300;
  const pos = (v) => Math.sqrt(Math.min(Math.max(v, 0), max) / max);
  const point = (f, r) => [80 - Math.cos(Math.PI * f) * r, 80 - Math.sin(Math.PI * f) * r];
  let body = '';
  const stops = [...LH_DUST_STOPS.map(([v]) => v), max];
  LH_DUST_STOPS.forEach(([from, level], i) => {
    const [x1, y1] = point(pos(from), 64);
    const [x2, y2] = point(pos(stops[i + 1]), 64);
    body += `<path d="M${x1} ${y1}A64 64 0 0 1 ${x2} ${y2}" stroke="${LH_DUST[level].color}" class="lh-g-seg"/>`;
  });
  if (value != null) {
    const [x, y] = point(pos(value), 50);
    body += `<line class="lh-g-needle" x1="80" y1="80" x2="${x}" y2="${y}"/><circle class="lh-g-hub" cx="80" cy="80" r="6"/>`;
  }
  return lhSvg(160, 90, body);
}

function lhCalima(data) {
  const box = lhCard('lh-calima');
  const calima = data.lpa?.calima;
  if (!calima?.now) return lhUnavailable(box, 'Previsión de calima no disponible. No equivale a aire limpio.');
  const now = calima.now;
  const level = LH_DUST[now.nivel] || {label: 'Sin datos', color: '#94a3b8'};
  const gauge = lhGauge(now.dust);
  gauge.classList.add('lh-gauge');
  box.append(lh('div', {class: 'lh-calima-now'}, gauge,
    lh('div', {},
      lh('p', {class: 'lh-level', style: `--lh-level:${level.color}`, text: level.label}),
      lh('p', {class: 'lh-metric-sub'}, 'Polvo ', lh('strong', {text: `${lhNumber(now.dust)} µg/m³`}),
        ' · PM10 ', lh('strong', {text: `${lhNumber(now.pm10)} µg/m³`})),
      lh('p', {class: 'lh-metric-sub'}, 'Turbidez (AOD) ', lh('strong', {text: lhNumber(now.aerosol_optical_depth, 2)}),
        now.aerosol_optical_depth >= 0.5 ? ' · cielo velado' : ''))));
  const rows = calima.hours.filter((r) => r.dust != null);
  const col = 5, h = 60;
  const max = Math.max(60, ...rows.map((r) => r.dust));
  let body = '';
  const today = lhDayKey.format(new Date());
  rows.forEach((r, i) => {
    const bh = Math.max(1, (r.dust / max) * h);
    body += `<rect x="${i * col}" y="${h - bh + 14}" width="${col - 1}" height="${bh}" fill="${(LH_DUST[r.nivel] || level).color}"/>`;
    const date = new Date(r.hora);
    if (lhHourShort.format(date) === '0') body += `<line class="lh-c-day" x1="${i * col}" x2="${i * col}" y1="0" y2="${h + 14}"/><text class="lh-c-dayname" x="${i * col + 3}" y="10">${lhEsc(lhDayName(date, today))}</text>`;
  });
  const peak = calima.peak;
  const peakDate = new Date(peak.hora);
  const chart = lhSvg(rows.length * col, h + 16, body,
    `Polvo previsto en ${Math.round(rows.length / 24)} días; máximo ${lhNumber(peak.dust)} µg/m³ ${lhDayName(peakDate, today).toLowerCase()} a las ${lhHour.format(peakDate)}`);
  chart.classList.add('lh-mini');
  box.append(chart, lh('p', {class: 'lh-note'}, 'Máximo previsto: ', lh('strong', {text: `${lhNumber(peak.dust)} µg/m³`}),
    ` (${(LH_DUST[peak.nivel] || level).label.toLowerCase()}) ${lhDayName(peakDate, today).toLowerCase()} a las ${lhHour.format(peakDate)}. `,
    'Modelo CAMS; niveles orientativos.'));
}

// --- Sea ---
function lhSea(data) {
  const box = lhCard('lh-sea');
  const marine = data.lpa?.marine;
  if (!marine?.now) return lhUnavailable(box, 'Previsión del mar no disponible.');
  const now = marine.now;
  box.append(lh('div', {class: 'lh-sea-now'},
    lh('div', {class: 'lh-stat'}, lh('span', {class: 'lh-stat-label', text: 'Olas'}),
      lh('span', {class: 'lh-stat-value'}, now.wave_direction != null ? lhArrow(now.wave_direction, 18) : null, `${lhNumber(now.wave_height, 1)} m`),
      lh('span', {class: 'lh-stat-sub', text: `del ${lhCardinal(now.wave_direction)}`})),
    lh('div', {class: 'lh-stat'}, lh('span', {class: 'lh-stat-label', text: 'Periodo'}),
      lh('span', {class: 'lh-stat-value', text: `${lhNumber(now.wave_period)} s`})),
    lh('div', {class: 'lh-stat'}, lh('span', {class: 'lh-stat-label', text: 'Agua'}),
      lh('span', {class: 'lh-stat-value', text: `${lhNumber(now.sea_surface_temperature, 1)}°`}))));
  const rows = marine.hours.slice(0, 48).filter((r) => r.wave_height != null);
  if (rows.length > 1) {
    const col = 6, h = 56;
    const max = Math.max(2, ...rows.map((r) => r.wave_height));
    const pts = rows.map((r, i) => [i * col, h - (r.wave_height / max) * (h - 6) + 4]);
    const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]} ${p[1].toFixed(1)}`).join('');
    const chart = lhSvg((rows.length - 1) * col, h + 4,
      `<path class="lh-c-sea-area" d="${line}L${pts.at(-1)[0]} ${h + 4}L0 ${h + 4}Z"/><path class="lh-c-sea" d="${line}"/>`,
      `Altura de las olas en las próximas 48 horas, entre ${lhNumber(Math.min(...rows.map((r) => r.wave_height)), 1)} y ${lhNumber(Math.max(...rows.map((r) => r.wave_height)), 1)} metros`);
    chart.classList.add('lh-mini');
    box.append(chart);
  }
  box.append(lh('p', {class: 'lh-note'}, 'Modelo para mar abierto frente a la ciudad; no describe el estado de cada playa. ',
    lh('a', {href: 'radar.html', text: 'Puerto y mareógrafo'})));
}

// --- Sun and UV ---
function lhSun(data) {
  const box = lhCard('lh-sun');
  const sun = data.sol?.[0];
  if (!sun) return lhUnavailable(box, 'Datos del sol no disponibles.');
  const rise = new Date(sun.sortida), set = new Date(sun.posta);
  const now = Date.now();
  const f = Math.min(Math.max((now - rise) / (set - rise), 0), 1);
  const angle = Math.PI * (1 - f);
  const sx = 80 + Math.cos(angle) * 64, sy = 76 - Math.sin(angle) * 60;
  const up = now > rise && now < set;
  const arc = lhSvg(160, 86, `<path class="lh-sun-path" d="M16 76A64 60 0 0 1 144 76"/>` +
    `<line class="lh-c-base" x1="6" x2="154" y1="76" y2="76"/>` +
    (up ? `<circle class="lh-sun-dot" cx="${sx.toFixed(1)}" cy="${sy.toFixed(1)}" r="8"/>` : ''));
  arc.classList.add('lh-sun-arc');
  const minutes = Math.round((set - rise) / 60000);
  const uv = lhUv(sun.uv_max);
  box.append(arc, lh('div', {class: 'lh-sun-times'},
    lh('span', {}, lh('small', {text: 'Sale '}), lh('strong', {text: lhHour.format(rise)})),
    lh('span', {}, lh('small', {text: 'Luz '}), lh('strong', {text: `${Math.floor(minutes / 60)} h ${minutes % 60} min`})),
    lh('span', {}, lh('small', {text: 'Se pone '}), lh('strong', {text: lhHour.format(set)}))),
  lh('div', {class: 'lh-uv'}, lh('span', {text: 'UV máximo hoy'}),
    lh('span', {class: 'lh-uv-bar', 'aria-hidden': 'true'}, lh('span', {class: 'lh-uv-mark', style: `left:${Math.min((sun.uv_max || 0) / 12, 1) * 100}%`})),
    lh('strong', {class: 'lh-level', style: `--lh-level:${uv.color}`, text: `${lhNumber(sun.uv_max, 1)} · ${uv.label}`})));
}

// --- Measured and air ---
function lhStations(data) {
  const box = lhCard('lh-stations');
  const wanted = ['C659M', 'GRAFCAN-3705', 'GCLP', 'C658X'];
  const stations = wanted.map((id) => data.lpa?.observations?.stations?.find((s) => s.id === id)).filter(Boolean);
  if (!stations.length) return lhUnavailable(box, 'Observaciones no disponibles.');
  const list = lh('ul', {class: 'lh-stations'});
  for (const station of stations) {
    const status = typeof lpaStationStatus === 'function' ? lpaStationStatus(station) : 'unavailable';
    const ok = status === 'ok';
    const name = station.name.split(' · ')[0].replace('Aeropuerto de Gran Canaria', 'Aeropuerto');
    list.append(lh('li', {class: ok ? 'is-ok' : 'is-old'},
      lh('span', {class: 'lh-st-dot', 'aria-hidden': 'true'}),
      lh('span', {class: 'lh-st-name'}, name, lh('small', {text: ok ? ` ${lhHour.format(new Date(station.observed_at))}` : ' sin lectura reciente'})),
      lh('strong', {class: 'lh-st-temp', text: ok ? `${lhNumber(station.temperature_c, 1)}°` : '—'}),
      lh('span', {class: 'lh-st-wind', text: ok && station.wind_kmh != null ? `${lhNumber(station.wind_kmh)} km/h` : ''})));
  }
  box.append(list, lh('p', {class: 'lh-note'}, lh('a', {href: 'observaciones.html', text: 'Todas las estaciones e historial'})));
}

function lhAir(data) {
  const box = lhCard('lh-air');
  const air = data.aire;
  if (!air) return lhUnavailable(box, 'Calidad del aire no disponible.');
  const [label, color] = LH_AIR[air.categoria] || ['Sin datos', '#94a3b8'];
  const pollen = data.lpa?.environment?.pollen;
  box.append(lh('p', {class: 'lh-level lh-level-big', style: `--lh-level:${color}`, text: label}),
    lh('p', {class: 'lh-metric-sub'}, 'Índice europeo ', lh('strong', {text: lhNumber(air.index)}),
      air.pitjor ? ` · peor hoy ${lhNumber(air.pitjor.index)} a las ${lhHour.format(new Date(air.pitjor.hora))}` : ''),
    lh('p', {class: 'lh-note'}, 'Modelo CAMS global, sin corrección local.',
      pollen?.last_count ? ` Polen: último recuento SEAIC del ${pollen.last_count.date}.` : ''));
}

function lhStale(data) {
  const box = document.getElementById('lh-now');
  box.className = 'lh-hero lh-sky-cloud';
  const link = lh('a', {href: 'https://www.aemet.es/es/eltiempo/prediccion/municipios/palmas-de-gran-canaria-las-id35016', text: 'Previsión de AEMET'});
  box.replaceChildren(lh('h2', {class: 'lh-sr', text: 'El tiempo ahora'}),
    lh('div', {class: 'lh-hero-main'}, lh('p', {class: 'lh-big-text', text: 'Datos caducados.'}),
      lh('p', {}, `La última publicación es de las ${data?.generat ? lhHour.format(new Date(data.generat)) : '—'}. Consulte la `, link, '.')));
  for (const id of ['lh-hours', 'lh-days', 'lh-wind', 'lh-calima', 'lh-sea', 'lh-sun', 'lh-stations', 'lh-air']) {
    const card = lhCard(id);
    if (card) lhUnavailable(card, 'Sin datos actuales.');
  }
}

function lhRender(data) {
  const stale = typeof dadesVelles === 'function' && dadesVelles(data);
  lhAlerts(data, stale);
  lhRadar(data, stale);
  if (stale) return lhStale(data);
  const sections = [lhNow, lhHours, lhDays, lhWind, lhCalima, lhSea, lhSun, lhStations, lhAir];
  for (const section of sections) {
    try {
      section(data);
    } catch (error) {
      console.warn(error);
    }
  }
}

if (document.getElementById('lpa-home')) {
  let loading = false;
  const refresh = async () => {
    if (loading) return;
    loading = true;
    try {
      lhRender(await llegeixDades('montflorit.json'));
    } catch {
      lhStale(null);
      lhRadar(null, true);
    } finally {
      loading = false;
    }
  };
  refresh();
  setInterval(() => { if (document.visibilityState === 'visible') refresh(); }, 300000);
}
