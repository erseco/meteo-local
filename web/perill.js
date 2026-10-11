// SPDX-License-Identifier: AGPL-3.0-or-later
// «Perill» (ADR 0071): les situacions de perill a Montflorit, ara i durant
// l'últim any, amb el mateix text dels avisos del mòbil i de Telegram. Cada
// situació, una fitxa amb el començament i, si ja ha acabat, el final
// (Juanjo, 11-10-2026). A dalt, les actives; després, les dels últims
// DIES_RECENTS dies; els mesos d'abans, plegats, un per mes.
// Les dades, l'historial que deixa avisos_bot.py a avisos.json.

const FITXER_AVISOS = 'avisos.json';
const DIES_RECENTS = 30;
const RELLEGEIX_MIN = 5;
// El color de la fitxa, el del cercle amb què comença l'avís; l'incendi, que
// no té nivell, porta 🔥 i la franja vermella (ADR 0071).
const CLASSE_CERCLE = { '🔴': 'vermell', '🟠': 'taronja', '🟡': 'groc', '🔥': 'vermell' };

const idiomaText = () => (IDIOMA.codi === 'es' ? 'es' : 'ca');
const locale = () => (IDIOMA.codi === 'es' ? 'es-ES' : 'ca-ES');

// Quan ha acabat: el missatge de final o, en els avisos de l'AEMET, que no en
// tenen, l'hora fins a la qual valien.
function finalDe(e, ara) {
  if (e.fi) return e.fi;
  if (e.fins && new Date(e.fins) <= ara) return e.fins;
  return null;
}

function dia(iso) {
  return new Date(iso).toLocaleDateString(locale(), { weekday: 'short', day: 'numeric', month: 'numeric' });
}

function moment(iso) {
  return `${dia(iso)}, ${horaCurta(iso)}`;
}

// «Des de dg. 11/10, 23:30»; «Dg. 11/10, de 23:30 a 23:55», o, si passa la
// mitjanit, «De dg. 11/10, 23:30 a dl. 12/10, 00:30».
function quan(e, fi) {
  if (!fi) return T`Des de ${moment(e.inici)}`;
  if (dia(e.inici) === dia(fi)) {
    const d = dia(e.inici);
    return T`${d.charAt(0).toUpperCase() + d.slice(1)}, de ${horaCurta(e.inici)} a ${horaCurta(fi)}`;
  }
  return T`De ${moment(e.inici)} a ${moment(fi)}`;
}

function nodesText(linies) {
  return linies.filter((l) => l.length).map((l) => {
    const p = element('p');
    p.append(...nodesLinia(l));
    return p;
  });
}

// Cada fitxa té la seva adreça (perill.html#…), per compartir-la (ADR 0072).
function idFitxa(e) {
  return 'a-' + `${e.clau}-${e.inici}`.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Za-z0-9-]+/g, '-').replace(/-+/g, '-').toLowerCase();
}

function botoCompartir(e, titol) {
  const b = element('button', 'compartir-avis');
  b.type = 'button';
  b.title = T('Comparteix aquest avís');
  b.setAttribute('aria-label', T('Comparteix aquest avís'));
  b.append(icona('i-share-2'));
  const url = new URL(location.href);
  url.hash = idFitxa(e);
  b.addEventListener('click', () => comparteix(url.href, titol));
  return b;
}

function fitxa(e, ara) {
  const text = e[idiomaText()] || e.ca;
  const [primera, ...resta] = trossos(text);
  const cercle = [...((primera[0] || {}).t || '')][0];
  const fi = finalDe(e, ara);
  const art = element('article', `avis-item episodi ${CLASSE_CERCLE[cercle] || 'compte'}`);
  art.id = idFitxa(e);
  const titol = element('p', 'episodi-titol');
  titol.append(...nodesLinia(primera));
  const cap = element('div', 'episodi-cap');
  cap.append(titol, botoCompartir(e, primera.map((t) => t.t).join('').trim()));
  const estat = element('p', 'episodi-quan');
  if (fi) estat.append(element('span', 'episodi-acabat', `🟢 ${T('Acabat')}`), ' · ');
  else estat.append(element('span', 'episodi-actiu', T('Actiu ara')), ' · ');
  estat.append(quan(e, fi));
  art.append(cap, estat);
  const cos = nodesText(resta);
  // Més informació, si el text no porta ja un enllaç (ADR 0071).
  const enllac = e.enllac && (e.enllac[idiomaText()] || e.enllac.ca);
  if (enllac && !/<a href=/.test(text)) {
    const p = element('p');
    const a = element('a', null, T('Més informació'));
    a.href = enllac;
    a.target = '_blank';
    a.rel = 'noopener';
    p.append(a);
    cos.push(p);
  }
  const textFi = fi && (e[`fi_${idiomaText()}`] || e.fi_ca);
  if (textFi) cos.push(...nodesText(trossos(textFi)));
  if (!fi) {
    art.append(...cos);
  } else if (cos.length) {
    // Les acabades, amb el detall plegat dins la fitxa.
    const plec = element('details', 'episodi-detall');
    plec.append(element('summary', null, T('Detalls')), ...cos);
    art.append(plec);
  }
  return art;
}

// El nom del mes, fet aquí: Firefox i Safari no diuen igual «agost de 2026».
const MESOS = {
  ca: ['Gener', 'Febrer', 'Març', 'Abril', 'Maig', 'Juny', 'Juliol', 'Agost', 'Setembre', 'Octubre', 'Novembre', 'Desembre'],
  es: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
};

// El Pla Alfa de Cerdanyola des del nivell 3 i els tancaments de Collserola:
// només a «Ara», sense avís ni historial, perquè canvia cada dia (ADR 0071).
const PLA_ALFA = 'https://interior.gencat.cat/ca/arees_dactuacio/agents-rurals/pla-alfa/';

function fitxaAlfa(alfa) {
  if (!alfa) return null;
  const dies = [['avui', T('avui')], ['dema', T('demà')]].filter(([d]) => alfa[d] != null && alfa[d] >= ALFA_NIVELL_MOSTRAR);
  const tancats = alfa.tancaments || [];
  if (!dies.length && !tancats.length) return null;
  const maxim = Math.max(0, ...dies.map(([d]) => alfa[d]));
  const art = element('article', `avis-item episodi ${maxim >= 4 || !dies.length ? 'vermell' : 'taronja'}`);
  const titol = element('p', 'episodi-titol');
  const nivells = dies.map(([d, nom]) => T`nivell ${alfa[d]} ${nom}`).join(', ');
  titol.append(element('strong', null, `${maxim >= 4 || !dies.length ? '🔴' : '🟠'} `
    + (nivells ? T`Pla Alfa de Cerdanyola: ${nivells}` : T('Agents Rurals: espais naturals tancats'))));
  art.append(titol, element('p', 'episodi-quan', T('El fixen cada dia els Agents Rurals; no arriba com a avís.')));
  if (dies.length) art.append(element('p', null, T('Accés restringit als espais forestals.')));
  for (const t of tancats) art.append(element('p', null, T`Tancat: ${t.espai}.`));
  const p = element('p');
  const a = element('a', null, T('Més informació'));
  a.href = PLA_ALFA;
  a.target = '_blank';
  a.rel = 'noopener';
  p.append(a);
  art.append(p);
  return art;
}

function nomMes(iso) {
  const t = new Date(iso);
  return `${MESOS[idiomaText()][t.getMonth()]} de ${t.getFullYear()}`;
}

function pinta(dades, ara = new Date()) {
  const historial = [...(dades.historial || [])].sort((a, b) => new Date(b.inici) - new Date(a.inici));
  const actius = historial.filter((e) => !finalDe(e, ara));
  const limit = new Date(ara.getTime() - DIES_RECENTS * 86400000);
  const acabats = historial.filter((e) => finalDe(e, ara));
  const recents = acabats.filter((e) => new Date(e.inici) >= limit);
  const antics = acabats.filter((e) => new Date(e.inici) < limit);
  const peces = [element('h2', 'seccio', T('Ara'))];
  const alfa = fitxaAlfa(dades.pla_alfa);
  if (actius.length) peces.push(...actius.map((e) => fitxa(e, ara)));
  if (alfa) peces.push(alfa);
  if (!actius.length && !alfa) peces.push(element('p', 'nota', T('Ara no hi ha cap situació de perill.')));
  peces.push(element('h2', 'seccio', T`Últims ${DIES_RECENTS} dies`));
  if (recents.length) peces.push(...recents.map((e) => fitxa(e, ara)));
  else peces.push(element('p', 'nota', T`Cap situació de perill acabada en els últims ${DIES_RECENTS} dies.`));
  // Els mesos d'abans, plegats, del més recent al més antic.
  const mesos = new Map();
  for (const e of antics) {
    const clau = e.inici.slice(0, 7);
    if (!mesos.has(clau)) mesos.set(clau, []);
    mesos.get(clau).push(e);
  }
  if (mesos.size) {
    peces.push(element('h2', 'seccio', T('Abans')));
    for (const llista of mesos.values()) {
      const plec = element('details', 'mes-perill');
      const n = llista.length;
      plec.append(element('summary', null, `${nomMes(llista[0].inici)} · ${n === 1 ? T('1 situació') : T`${n} situacions`}`),
        ...llista.map((e) => fitxa(e, ara)));
      peces.push(plec);
    }
  }
  $('perill').replaceChildren(...peces);
  // Vist fins ara: la pestanya ja no ha de senyalar res d'abans (comu.js).
  try { localStorage.setItem(CLAU_PERILL_VIST, ara.toISOString()); } catch (_) {}
  $('avis-dades').hidden = true;
  if (dades.versio) posaVersio(dades.versio);
}

// Si s'ha obert l'enllaç d'un avís: s'hi va, es desplega (també el mes que el
// conté) i es destaca una estona. Només la primera vegada que es pinta.
let anatAlAvis = false;

function vesAlAvis() {
  if (anatAlAvis || !location.hash) return;
  const art = document.getElementById(location.hash.slice(1));
  anatAlAvis = true;
  if (!art) return;
  art.closest('details.mes-perill')?.setAttribute('open', '');
  art.querySelector('details')?.setAttribute('open', '');
  art.scrollIntoView({ block: 'center' });
  art.classList.add('assenyalat');
  setTimeout(() => art.classList.remove('assenyalat'), 4000);
}

function llegeix() {
  llegeixDades(FITXER_AVISOS).then((d) => { pinta(d); vesAlAvis(); }, () => {
    if ($('perill').querySelector('.carregant')) {
      $('perill').replaceChildren();
      $('avis-dades').textContent = T('No s’han pogut carregar els avisos. Torna-ho a provar d’aquí a una estona.');
      $('avis-dades').hidden = false;
    }
  });
}

llegeix();
setInterval(llegeix, RELLEGEIX_MIN * 60000);
