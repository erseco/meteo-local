// SPDX-License-Identifier: AGPL-3.0-or-later
// La gràfica de la previsió (ADR 0096) i el que necessita per dibuixar-se: el
// cel, la pluja i el perill de cada hora. La fan servir la portada (casa.js:
// la gràfica, la vista en gran i les taules) i «Consultes» (consultes.js: la
// d'«Avui» i la de «Demà»), perquè el dibuix sigui un de sol (Juanjo,
// 17-10-2026). Es carrega després de comu.js i abans de la pàgina.

// Si l'hora és de pluja, segons la probabilitat i no segons els mil·límetres
// del model més plujós: «pluja» si és més probable que plogui que no (50 % o
// més) i «possible» des del 20 %, els mateixos llindars que config.py. Sense
// probabilitat, manen els mil·límetres.
const PROB_PLUJA = 0.5;
const PROB_POSSIBLE = 0.2;
// Només a la gràfica: de 10 al 20 % plou una de cada set hores, i per sota
// del 20 % queia una de cada cinc hores de pluja (arxiu 2024-2026; Juanjo,
// 16-10-2026). La taula no ho distingeix: al cel, «possible pluja» és des del 20 %.
const PROB_POCA = 0.1;
function plujaHora(f) {
  const p = f.probabilitat;
  if (f.plou_ara || (p == null ? f.pluja_mm >= 0.2 : p >= PROB_PLUJA)) return 'pluja';
  return p != null && p >= PROB_POSSIBLE ? 'possible' : null;
}
function plujaGrafica(f) {
  const p = f.probabilitat;
  return plujaHora(f) || (p != null && p >= PROB_POCA ? 'poca' : null);
}

// Descripció del cel i la icona que hi correspon. Els mil·límetres diuen com
// seria la pluja, no si n'hi haurà: sense prou probabilitat, només els
// núvols. De nit, la lluna en lloc del sol (a mitja hora del tram).
// Les paraules són les del manual d'estil de Meteocat (ADR 0043). Intensitat
// en una hora (el manual la dona per 30 minuts, aquí el doble): pluja
// moderada des de 6 mm, forta des de 40, torrencial des de 80; neu moderada
// des de 2 cm, forta des de 10. Tipus pels codis de temps d'Open-Meteo.
const INTENSITAT_PLUJA = [6, 40, 80];
const INTENSITAT_NEU = [2, 10];
const esNeu = (c) => (c >= 71 && c <= 77) || c === 85 || c === 86;
const esGelant = (c) => c === 56 || c === 57 || c === 66 || c === 67;
const esCalamarsa = (c) => c === 96 || c === 99;

function cel(f) {
  const nit = alturaSol(new Date(new Date(f.hora).getTime() + 18e5)) < 0;
  const pluja = plujaHora(f);
  const tempesta = f.codi >= 95;
  if (pluja === 'pluja') {
    if (tempesta) return esCalamarsa(f.codi) ? [T('Tempesta amb calamarsa'), 'i-cloud-hail'] : [T('Tempesta'), 'i-cloud-lightning'];
    if (esNeu(f.codi)) {
      const cm = f.neu || 0;
      return [cm >= INTENSITAT_NEU[1] ? T('Neu forta') : cm >= INTENSITAT_NEU[0] ? T('Neu moderada') : T('Neu feble'), 'i-cloud-snow'];
    }
    if (esGelant(f.codi)) return [T('Pluja gelant'), 'i-cloud-rain'];
    const mm = f.pluja_mm || 0;
    if (mm >= INTENSITAT_PLUJA[2]) return [T('Pluja torrencial'), 'i-cloud-rain-wind'];
    if (mm >= INTENSITAT_PLUJA[1]) return [T('Pluja forta'), 'i-cloud-rain-wind'];
    if (mm >= INTENSITAT_PLUJA[0]) return [T('Pluja moderada'), 'i-cloud-rain'];
    return [T('Pluja feble'), 'i-cloud-drizzle'];
  }
  if (pluja === 'possible') {
    if (esNeu(f.codi)) return [T('Possible neu'), 'i-cloud-snow'];
    return [tempesta ? T('Possible tempesta') : T('Possible pluja'), nit ? 'i-cloud-moon-rain' : 'i-cloud-sun-rain'];
  }
  if (esBoira(f)) return [T('Boira'), 'i-cloud-fog'];
  if (f.nuvols == null) return ['', null];
  // Si algun model hi posa pluja (0,2 mm o més, el que ja mulla), el cel no
  // pot sortir serè encara que la probabilitat sigui baixa: com a mínim, núvols.
  return celNuvols(nuvolsHora(f), nit);
}

const nuvolsHora = (f) => ((f.pluja_mm || 0) >= 0.2 ? Math.max(f.nuvols, 50) : f.nuvols);
const esBoira = (f) => f.codi === 45 || f.codi === 48;

// Per vuitens de cel tapat: serè 0, poc 1-2, mig 3-5, molt 6-7, cobert 8.
function celNuvols(nuvols, nit) {
  if (nuvols < 20) return [T('Serè'), nit ? 'i-moon-cel' : 'i-sun'];
  if (nuvols < 45) return [T('Poc ennuvolat'), nit ? 'i-cloud-moon' : 'i-cloud-sun'];
  if (nuvols < 70) return [T('Mig ennuvolat'), 'i-cloud'];
  if (nuvols < 85) return [T('Molt ennuvolat'), 'i-cloudy'];
  return [T('Cobert'), 'i-cloudy'];
}

// La part alta del barri, quan la diferència arriba a un grau (ADR 0087):
// «+2» al costat de la temperatura del tram i, a «Ara», una
// línia amb la mesurada ara.
// Arrodonit: 0,9 compta com un grau (Juanjo, 13-10-2026).
function arrodoneixAlta(n) {
  if (n == null) return 0;
  const r = Math.sign(n) * Math.round(Math.abs(n));
  return Math.abs(r) >= 1 ? r : 0;
}

// Avisos de Meteocat i de l'AEMET (el que Meteocat no cobreix, ADR 0093) en
// trams d'hores seguides del mateix tram del dia amb el mateix avís: per a cada hora, el tram que hi comença ({nivell, tipus, hores}),
// undefined si la cobreix un tram que ha començat abans, o null si no n'hi ha.
const ORDRE_NIVELL = ['groc', 'taronja', 'vermell'];

// El perill d'una hora: els avisos de l'AEMET i els que calcula aquesta web
// (riscos.py, ADR 0018) per a aquella hora, amb el nivell més alt (Juanjo,
// 12-10-2026: «la franja de peligro … tiene que estar destacada también …
// pluja forta en sí no indica ningún peligro especial»; ADR 0076).
// NOM_RISC, a comu.js: també el fa servir el bloc «Avisos actius» plegat (ADR 0094).

function riscosHora(f, riscos, ara = new Date()) {
  const ini = new Date(f.hora);
  const fi = new Date(f.fins);
  return (riscos || []).filter((r) => (r.origen === 'previsio'
    ? r.des_de && new Date(r.des_de) < fi && new Date(r.fins) > ini
    : ini <= ara && ara < fi));
}

// Es diu el nivell més alt i només el que el dona: amb un avís groc de
// l'AEMET per pluja i un de taronja de la web, «taronja: pluja molt forta».
// El fenomen de cada risc de la web, per no dir-lo dues vegades amb l'avís
// oficial del mateix fenomen («pluja intensa» de la web i «pluja» de l'AEMET).
const FENOMEN_RISC = { pluja_30min: 'pluja', pluja_3h: 'pluja', pluja_24h: 'pluja', ratxa: 'vent', neu_24h: 'neu' };

function elementsPerill(f) {
  return [...(f.avisos || []).flatMap((a) => a.tipus.map((t) => ({ nivell: a.nivell, nom: TD(t), font: a.font || 'aemet', fenomen: t }))),
    ...(f.riscos_hora || []).map((r) => ({ nivell: r.nivell, nom: NOM_RISC()[r.tipus] || r.tipus, font: 'web',
      fenomen: FENOMEN_RISC[r.tipus] || r.tipus }))];
}

function delNivellMesAlt(elements) {
  if (!elements.length) return null;
  const nivell = elements.map((a) => a.nivell).sort((a, b) => ORDRE_NIVELL.indexOf(b) - ORDRE_NIVELL.indexOf(a))[0];
  const daquest = elements.filter((a) => a.nivell === nivell);
  const noms = [...new Set(daquest.map((a) => a.nom))].sort();
  const fonts = ['meteocat', 'aemet', 'web'].filter((x) => daquest.some((a) => a.font === x)).join('');
  // Cada nivell i cada font amb els seus fenòmens, del nivell més alt al més
  // baix: el color és el del més alt, però el text els diu tots (Juanjo,
  // 17-10-2026: amb perill alt de Meteocat per pluja i avís groc de l'AEMET
  // per tempestes, «que la franja diga las dos cosas»). Cada fenomen, una
  // sola vegada, al seu nivell més alt: un groc de l'AEMET per pluja no es
  // diu sota un taronja de pluja intensa de la web.
  const nivells = ORDRE_NIVELL.filter((nv) => elements.some((a) => a.nivell === nv)).reverse();
  const dits = new Set();
  const perFont = nivells.flatMap((nv) => {
    const aquests = elements.filter((a) => a.nivell === nv && !dits.has(a.fenomen || a.nom));
    aquests.forEach((a) => dits.add(a.fenomen || a.nom));
    return ['meteocat', 'aemet', 'web'].map((x) => [x, [...new Set(aquests.filter((a) => a.font === x).map((a) => a.nom))].sort(), nv])
      .filter(([, n]) => n.length);
  });
  return { nivell, noms, fonts, perFont };
}

function avisHora(f) {
  const p = delNivellMesAlt(elementsPerill(f));
  return p && { ...p, clau: p.perFont.map(([font, noms, nv]) => `${nv}|${font}|${noms.join(',')}`).join(';') };
}

function tramsAvis(hores) {
  const res = [];
  let obert = null;
  for (const f of hores) {
    const a = avisHora(f);
    if (a && obert && obert.clau === a.clau) {
      obert.hores += 1;
      res.push(undefined);
    } else {
      obert = a && { ...a, hores: 1 };
      res.push(obert);
    }
  }
  return res;
}

// El perill dit com el diu cada font: Meteocat, en grau de perill (moderat,
// alt, molt alt); l'AEMET i aquesta web, en colors (ADR 0093). El complet, amb
// d'on surt cada cosa; el curt, per a la franja i l'etiqueta del tram.
const GRAU_METEOCAT = () => ({ groc: T('moderat'), taronja: T('alt'), vermell: T('molt alt') });

function perFonts(p) {
  return p.perFont || [[p.fonts, p.noms]];
}

function textPerill(p) {
  return perFonts(p).map(([font, noms, nv = p.nivell]) => {
    const que = noms.join(T(' i '));
    const nivell = TD(nv);
    if (font === 'meteocat') return T`Perill ${GRAU_METEOCAT()[nv]} de Meteocat per ${que}`;
    if (font === 'web') return T`Avís ${nivell} d\u2019aquesta web: ${que}`;
    return T`Avís ${nivell} de l\u2019AEMET per ${que}`;
  }).join('; ');
}

// «Perill alt: pluja», «Avís groc: tempestes»; si n'hi ha de les dues maneres
// o de diversos nivells, juntes, del nivell més alt al més baix. Amb ambFont,
// també d'on surt cada un, «Perill alt (Meteocat): pluja» (la franja de la
// gràfica; Juanjo, 17-10-2026: «añade el origen: meteocat, aemet, etc»).
const NOM_FONT = () => ({ meteocat: 'Meteocat', aemet: 'AEMET', web: T('aquesta web') });
function partsPerill(p, ambQue = true, ambFont = false) {
  const parts = new Map();
  for (const [font, noms, nv = p.nivell] of perFonts(p)) {
    const origen = ambFont && NOM_FONT()[font] ? ` (${NOM_FONT()[font]})` : '';
    const nom = (font === 'meteocat' ? T`Perill ${GRAU_METEOCAT()[nv]}` : T`Avís ${TD(nv)}`) + origen;
    const abans = parts.get(nom);
    parts.set(nom, { nivell: nv, que: [...new Set([...(abans ? abans.que : []), ...noms])] });
  }
  return [...parts].map(([nom, { nivell, que }]) => ({ nivell, text: ambQue ? `${nom}: ${que.join(', ')}` : nom }));
}

function textPerillCurt(p, ambQue = true, ambFont = false) {
  return partsPerill(p, ambQue, ambFont).map((x) => x.text).join(' · ');
}

// --- La gràfica de la previsió (Juanjo, 16-10-2026: «un resumen visual …
// muy visual y muy claro»). Un meteograma, de l'hora en curs fins al final de
// la taula: la franja de perill, el cel cada 3 h, la temperatura i la
// probabilitat de pluja, amb el mateix eix d'hores. Les dades, les de la
// taula; la gràfica no diu res que no sigui a sota, tret de la fitxa de
// cada hora, que hi afegeix la part alta i l'UV. ---
const SVG_NS = 'http://www.w3.org/2000/svg';
function svg(nom, atributs = {}, text = null) {
  const e = document.createElementNS(SVG_NS, nom);
  for (const [k, v] of Object.entries(atributs)) e.setAttribute(k, v);
  if (text != null) e.textContent = text;
  return e;
}

// L'alçada de la barra de pluja, en mil·límetres (Juanjo, 16-10-2026: «la
// lluvia sale pequeña… aquí hay mucha»): escala fixa, perquè un dia de
// plovisqueig no sembli un diluvi, i d'arrel quadrada, perquè 1 o 2 mm no
// desapareguin. Dalt de tot, 40 mm en una hora (el llindar taronja de la web).
const MM_DALT = 40;
const alcadaPluja = (mm) => Math.min(1, Math.sqrt(Math.max(0, mm) / MM_DALT));
// La pluja forta i la torrencial, amb color propi: les intensitats del manual
// d'estil de Meteocat, les mateixes paraules que la columna «Cel» de la taula
// (INTENSITAT_PLUJA; ADR 0043). L'avís, a la franja de dalt (Juanjo,
// 16-10-2026: «no hay unas etiquetas normalizadas?»).
function intensitatPluja(mm) {
  if (mm >= INTENSITAT_PLUJA[2]) return 'torrencial';
  if (mm >= INTENSITAT_PLUJA[1]) return 'forta';
  return null;
}

// El cel d'un bloc de 3 h: la pluja, si n'hi ha en alguna hora; si no, la del mig.
function celBloc(files) {
  const amb = files.map((f) => [f, cel(f)]).filter(([, c]) => c[1]);
  if (!amb.length) return null;
  const plujoses = amb.filter(([f]) => plujaHora(f));
  if (plujoses.length) return plujoses.sort(([a], [b]) => (b.probabilitat || 0) - (a.probabilitat || 0))[0][1];
  return amb[Math.floor(amb.length / 2)][1];
}

// La línia de temperatura, suau (Juanjo, 16-10-2026: «tiene picos… que
// parezca más profesional»): corba cúbica monòtona (Fritsch i Carlson, la
// «monotoneX» de d3), que passa per cada hora i no fa pujades ni baixades
// que no siguin a les dades.
function corbaSuau(p) {
  const n = p.length;
  const f = (v) => v.toFixed(1);
  if (n < 3) return 'M' + p.map(([a, b]) => `${f(a)},${f(b)}`).join(' L');
  const h = [], s = [];
  for (let i = 0; i < n - 1; i++) {
    h.push(p[i + 1][0] - p[i][0]);
    s.push((p[i + 1][1] - p[i][1]) / h[i]);
  }
  const m = new Array(n);
  for (let i = 1; i < n - 1; i++) {
    if (s[i - 1] * s[i] <= 0) { m[i] = 0; continue; }
    const q = (s[i - 1] * h[i] + s[i] * h[i - 1]) / (h[i - 1] + h[i]);
    m[i] = (Math.sign(s[i - 1]) + Math.sign(s[i])) * Math.min(Math.abs(s[i - 1]), Math.abs(s[i]), 0.5 * Math.abs(q));
  }
  m[0] = (3 * s[0] - m[1]) / 2;
  m[n - 1] = (3 * s[n - 2] - m[n - 2]) / 2;
  let d = `M${f(p[0][0])},${f(p[0][1])}`;
  for (let i = 0; i < n - 1; i++) {
    const t = h[i] / 3;
    d += ` C${f(p[i][0] + t)},${f(p[i][1] + m[i] * t)} ${f(p[i + 1][0] - t)},${f(p[i + 1][1] - m[i + 1] * t)} ${f(p[i + 1][0])},${f(p[i + 1][1])}`;
  }
  return d;
}

// Les hores de la gràfica, per a la vista gran (vistaGrafica).
let HORES_GRAFICA = null;

function grafica(hores) {
  const ara = new Date();
  const files = (hores || []).filter((f) => new Date(f.fins) > ara && f.temperatura != null);
  if (files.length < 6) return null;
  HORES_GRAFICA = hores;
  return figuraGrafica(files,
    T('Gràfica de la previsió: perill, cel, temperatura i probabilitat de pluja. Les mateixes dades són a les taules de sota.'));
}

function figuraGrafica(files, peu) {
  const fig = element('figure', 'grafica');
  fig.append(element('figcaption', 'visualment-amagat', peu));
  fig._files = files;
  return fig;
}

// Des d'aquesta hora, el resum del dia ja és el de demà (bot.HORA_DEMA).
const HORA_DEMA = 18;

// La gràfica del dia de què parla el resum, a «Consultes» i a la imatge que
// l'acompanya a Telegram i als avisos (grafica_imatge.py; Juanjo,
// 17-10-2026): la d'«Avui», d'ara a mitjanit; la de «Demà», com el text del
// bot (bot.resum), de la nit d'avui (des de HORA_DEMA) al final de demà.
// Amb menys de 3 hores, cap.
function graficaDia(hores, riscos, dia, ara = new Date()) {
  const dies = (n, h = 0) => new Date(ara.getFullYear(), ara.getMonth(), ara.getDate() + n, h);
  const [des, fins] = dia === 'dema' ? [dies(0, HORA_DEMA), dies(2)] : [ara, dies(1)];
  const files = (hores || []).filter((f) => new Date(f.fins) > ara && new Date(f.fins) > des
    && new Date(f.hora) < fins && f.temperatura != null);
  if (files.length < 3) return null;
  for (const f of files) f.riscos_hora = riscosHora(f, riscos, ara);
  return figuraGrafica(files, T('Gràfica de la previsió hora a hora: perill, cel, temperatura i probabilitat de pluja.'));
}

function dibuixaGrafica(fig) {
  const files = fig._files;
  // A la vista gran: més alçada i, si es tria, el vent (vistaGrafica).
  const opcions = fig._opcions || {};
  const W = fig.clientWidth;
  if (!W || !files.length) return;
  const n = files.length;
  const col = W / n;
  const x = (i) => i * col;
  // El cel, la temperatura i les hores de l'eix, cada hora si hi ha lloc
  // (Juanjo, 17-10-2026: «la gráfica está bastante vacía, mejor que salga
  // cada hora»); si no, cada 2 o cada 3.
  const pas = col >= 30 ? 1 : col >= 18 ? 2 : 3;
  const hora = (f) => new Date(f.hora).getHours();
  const trams = tramsAvis(files);
  const ambAvis = trams.some(Boolean);
  // A la pàgina des del principi: el text de la franja s'ha de poder mesurar.
  const g = svg('svg', { width: W, 'aria-hidden': 'true' });
  fig.querySelector('svg')?.remove();
  fig.prepend(g);
  const mesura = (text) => {
    const prova = svg('g', { class: 'g-avis' });
    const t = svg('text', {}, text);
    prova.append(t);
    g.append(prova);
    const llarg = t.getComputedTextLength();
    prova.remove();
    return llarg;
  };
  // El text de cada avís, sencer (el nivell i el què), dins de la franja si
  // hi cap. Si no (un avís de poques hores), al costat, a la dreta o a
  // l'esquerra, només si allà no hi ha cap franja ni cap altre text (Juanjo,
  // 17-10-2026: el text a sota «no lo entiendo»). Si tampoc, en una fila a
  // sota, amb un quadret del seu color, on comença l'avís i sense trepitjar
  // l'anterior: si no hi cap, en una fila més (fins a tres), i només si
  // tampoc, el nivell sol. Abans anava al costat sense mirar-ho i podia caure
  // damunt del text d'una altra (Juanjo, 17-10-2026: «sin que se pierda
  // información vital. si es necesario usa dos filas»). Sencer, sempre en
  // tocar la franja.
  const MARCA = 14;
  const dins = trams.map((t) => t && mesura(textPerillCurt(t, true, true)) <= t.hores * col - 12);
  // La fila de les franges: el que ja hi ha (les franges i els textos del costat).
  const ocupada = trams.flatMap((t, i) => (t ? [[x(i), x(i) + t.hores * col]] : []));
  const lliure = (a, b) => a >= 0 && b <= W && ocupada.every(([c, d]) => b + 4 <= c || a >= d + 4);
  const costat = trams.map((t, i) => {
    if (!t || dins[i]) return null;
    const llarg = mesura(textPerillCurt(t, true, true));
    const fi = x(i) + t.hores * col;
    for (const [a, ancora] of [[fi + 4, 'start'], [x(i) - 4 - llarg, 'end']]) {
      if (!lliure(a, a + llarg)) continue;
      ocupada.push([a, a + llarg]);
      return { x: ancora === 'start' ? a : a + llarg, ancora };
    }
    return null;
  });
  // A sota, cada avís de la franja per separat, amb el quadret del seu nivell
  // («■ Perill alt (Meteocat): pluja», «■ Avís groc (AEMET): tempestes»): junts
  // no hi cabrien al mòbil.
  // Si no hi cap a cap fila, en fa una de nova: cap avís no es perd (amb
  // quatre avisos seguits al mòbil, el vermell es quedava sense lloc).
  const fila2 = [];
  const ocupat = [];
  trams.forEach((t, i) => {
    if (!t || dins[i] || costat[i]) return;
    const curts = partsPerill(t, false, true);
    partsPerill(t, true, true).forEach((part, k) => {
      // El text sencer; només si és més ample que la gràfica, el nivell sol.
      const p = MARCA + mesura(part.text) <= W ? part : curts[k];
      const llarg = MARCA + mesura(p.text);
      let fila = ocupat.findIndex((o) => Math.min(Math.max(x(i), o + 10), W - llarg) >= o + 10 - 0.5);
      if (fila < 0) fila = ocupat.push(-Infinity) - 1;
      const lx = Math.max(0, Math.min(Math.max(x(i), ocupat[fila] + 10), W - llarg));
      fila2.push({ t, nivell: p.nivell, text: p.text, x: lx, fila });
      ocupat[fila] = lx + llarg;
    });
  });
  // Les files de la gràfica, de dalt a baix.
  const yAvis = 0;
  const hAvis = ambAvis ? 22 : 0;
  const yFila2 = hAvis + 4;
  const hFila2 = fila2.length ? 16 * (1 + Math.max(...fila2.map((e) => e.fila))) : 0;
  const yDia = hAvis + hFila2 + (ambAvis ? 6 : 0);
  const yCel = yDia + 16;
  const hCel = 28;
  // La temperatura i la pluja comparteixen la zona: les barres darrere de la
  // línia, com als meteogrames habituals (Juanjo, 16-10-2026).
  // El cel queda a part, a dalt: les barres no hi arriben (Juanjo, 16-10-2026).
  // Sota cada icona, la temperatura d'aquella hora (Juanjo, 16-10-2026: «no
  // quedaría bien la temperatura bajo el cielo?»).
  const yXifra = yCel + hCel + 13;
  const yTemp = yXifra + 12;
  const hTemp = opcions.gran ? Math.round(Math.min(260, Math.max(110, innerHeight * 0.32))) : 100;
  const yPluja = yTemp;
  const hPluja = hTemp;
  // El vent, a sota de la pluja, amb el mateix eix d'hores.
  const hVent = opcions.vent ? (opcions.gran ? 70 : 50) : 0;
  const yVent = yPluja + hPluja + (hVent ? 12 : 0);
  const baix = hVent ? yVent + hVent : yPluja + hPluja;
  const yEix = baix + 16;
  const H = yEix + 4;
  g.setAttribute('height', H);
  g.setAttribute('viewBox', `0 0 ${W} ${H}`);

  // La nit, ombrejada, de la posta a la sortida (a mitja hora de cada tram),
  // en un sol rectangle per nit.
  const esNit = files.map((f) => alturaSol(new Date(new Date(f.hora).getTime() + 18e5)) < 0);
  for (let i = 0; i < n; i++) {
    if (!esNit[i] || (i && esNit[i - 1])) continue;
    let j = i;
    while (j < n && esNit[j]) j++;
    g.append(svg('rect', { class: 'g-nit', x: x(i), y: yCel - 2, width: x(j) - x(i), height: baix - yCel + 2 }));
  }

  // Mitjanit: la ratlla que separa els dies, i el nom de cada dia.
  // Cada dia pel seu nom, segons la data: de nit, la taula arriba fins a
  // demà passat (Juanjo, 17-10-2026: «el 2º demà debería haber sido demà
  // passat»). El primer nom, només si hi cap abans de mitjanit: si no, ja
  // s'entén («si avui no cabe no se escriba nada»).
  const nomDia = (f) => {
    const d = new Date(f.hora);
    const avui = new Date();
    const dies = Math.round((new Date(d.getFullYear(), d.getMonth(), d.getDate())
      - new Date(avui.getFullYear(), avui.getMonth(), avui.getDate())) / 864e5);
    return dies <= 0 ? T('Avui') : dies === 1 ? T('Demà') : T('Demà passat');
  };
  const mitjanits = files.map((f, i) => (i && hora(f) === 0 ? i : null)).filter((i) => i != null);
  const primer = svg('text', { class: 'g-dia', x: 2, y: yDia + 11 }, nomDia(files[0]));
  g.append(primer);
  if (mitjanits.length && 2 + primer.getComputedTextLength() + 8 > x(mitjanits[0])) primer.remove();
  for (const i of mitjanits) {
    g.append(svg('line', { class: 'g-mitjanit', x1: x(i), x2: x(i), y1: yDia, y2: baix }));
    g.append(svg('text', { class: 'g-dia', x: x(i) + 4, y: yDia + 11 }, nomDia(files[i])));
  }

  // La franja de perill, del color del nivell, amb el text si hi cap.
  const avisSencer = (grup, t) => {
    const complet = textPerill(t);
    grup.append(svg('title', {}, complet));
    grup.addEventListener('click', () => avisBreu(`${complet}.`));
  };
  trams.forEach((t, i) => {
    if (!t) return;
    const grup = svg('g', { class: `g-avis ${t.nivell}` });
    const amplada = t.hores * col;
    grup.append(svg('rect', { x: x(i) + 1, y: yAvis, width: amplada - 2, height: hAvis, rx: 4 }));
    if (dins[i]) grup.append(svg('text', { x: x(i) + 6, y: yAvis + 15 }, textPerillCurt(t, true, true)));
    else if (costat[i]) {
      grup.append(svg('text', { class: 'fora', x: costat[i].x, y: yAvis + 15, 'text-anchor': costat[i].ancora }, textPerillCurt(t, true, true)));
    }
    avisSencer(grup, t);
    g.append(grup);
  });
  for (const e of fila2) {
    const grup = svg('g', { class: `g-avis ${e.nivell}` });
    const y = yFila2 + 16 * e.fila;
    grup.append(svg('rect', { class: 'g-avis-marca', x: e.x, y: y + 2, width: 10, height: 10, rx: 2 }),
      svg('text', { class: 'fora', x: e.x + MARCA, y: y + 11 }, e.text));
    avisSencer(grup, e.t);
    g.append(grup);
  }

  // El cel, un per bloc de 3 h (o de 2, si hi ha lloc), al centre del bloc.
  for (let i = 0; i < n;) {
    let j = i + 1;
    while (j < n && hora(files[j]) % pas !== 0) j++;
    const c = celBloc(files.slice(i, j));
    const amplada = (j - i) * col;
    if (c && amplada >= 20) {
      const mida = Math.min(24, amplada - 6);
      const cx = x(i) + amplada / 2;
      const ic = svg('use', { href: '#' + c[1], x: cx - mida / 2, y: yCel + (hCel - mida) / 2, width: mida, height: mida, class: 'g-cel' });
      g.append(ic);
      const mig = files[Math.floor((i + j - 1) / 2)];
      g.append(svg('text', { class: 'g-xifra', x: cx, y: yXifra, 'text-anchor': 'middle' }, `${Math.round(mig.temperatura)}°`));
    }
    i = j;
  }

  // La temperatura, primer el farciment (darrere de les barres) i després la
  // línia (davant), sense xifres: són sota el cel.
  const temps = files.map((f) => f.temperatura);
  const tMin = Math.floor(Math.min(...temps)) - 1;
  const tMax = Math.ceil(Math.max(...temps)) + 1;
  const yT = (t) => yTemp + hTemp - ((t - tMin) / (tMax - tMin)) * hTemp;
  const punts = files.map((f, i) => [x(i) + col / 2, yT(f.temperatura)]);
  const corba = corbaSuau(punts);
  const base = yPluja + hPluja;
  const idGrad = 'g-temp-grad';
  const defs = svg('defs');
  const grad = svg('linearGradient', { id: idGrad, x1: 0, y1: 0, x2: 0, y2: 1 });
  grad.append(svg('stop', { offset: 0, class: 'g-grad-dalt' }), svg('stop', { offset: 1, class: 'g-grad-baix' }));
  defs.append(grad);
  g.append(defs);
  g.append(svg('path', { class: 'g-temp-area', fill: `url(#${idGrad})`,
    d: `${corba} L${punts[n - 1][0].toFixed(1)},${base} L${punts[0][0].toFixed(1)},${base} Z` }));

  // La pluja: una barra per hora, tan alta com els mil·límetres; plena si és
  // probable (del 50 % amunt) i clara si només és possible (del 20 %), els
  // mateixos llindars que el cel de la taula. Per sota, cap barra.
  g.append(svg('line', { class: 'g-base', x1: 0, x2: W, y1: base, y2: base }));
  // Dalt de tot queda lloc per a la xifra dels mm.
  const dalt = (f) => yPluja + hPluja - Math.max(3, alcadaPluja(f.pluja_mm || 0) * (hPluja - 14));
  files.forEach((f, i) => {
    const pluja = plujaGrafica(f);
    if (!pluja) return;
    const y = dalt(f);
    const intensa = intensitatPluja(f.pluja_mm || 0);
    g.append(svg('rect', { class: `g-pluja ${pluja === 'pluja' ? 'segura' : pluja}${intensa ? ' ' + intensa : ''}`,
      x: x(i) + col * 0.15, y, width: col * 0.7, height: base - y }));
  });
  // Una vora del color del fons, perquè la línia es vegi damunt de les barres.
  g.append(svg('path', { class: 'g-temp-vora', d: corba }));
  g.append(svg('path', { class: 'g-temp', d: corba }));

  // El vent i les ratxes, en km/h: una ratlla a dalt amb la xifra de l'escala,
  // de 10 en 10 (20 com a mínim, perquè un dia calmat no sembli de vent).
  if (hVent) {
    const vents = files.flatMap((f) => [f.vent, f.ratxa]).filter((v) => v != null);
    const vDalt = Math.max(20, Math.ceil(Math.max(0, ...vents) / 10) * 10);
    const yV = (v) => yVent + hVent - (Math.max(0, v) / vDalt) * hVent;
    g.append(svg('line', { class: 'g-vent-escala', x1: 0, x2: W, y1: yVent, y2: yVent }));
    g.append(svg('line', { class: 'g-base', x1: 0, x2: W, y1: baix, y2: baix }));
    g.append(svg('text', { class: 'g-vent-xifra', x: 2, y: yVent - 3 }, `${vDalt}\u00a0km/h`));
    const linia = (camp, classe) => {
      const p = files.map((f, i) => [x(i) + col / 2, f[camp]]).filter(([, v]) => v != null).map(([a, v]) => [a, yV(v)]);
      if (p.length > 1) g.append(svg('path', { class: classe, d: corbaSuau(p) }));
    };
    linia('ratxa', 'g-ratxa');
    linia('vent', 'g-vent');
  }

  // Els mil·límetres, només on la pluja és més forta de cada episodi, a sobre
  // de la barra; si hi ha una xifra de temperatura, a dins de la barra o al
  // costat, on no se superposi.
  const xifres = [...g.querySelectorAll('.g-xifra')].map((t) => t.getBBox());
  const xoca = (b) => xifres.some((c) => b.x < c.x + c.width && c.x < b.x + b.width && b.y < c.y + c.height && c.y < b.y + b.height);
  files.forEach((f, i) => {
    const mm = f.pluja_mm || 0;
    if (mm < 0.5 || !plujaHora(f)) return;
    const veins = files.slice(Math.max(0, i - 2), i + 3).map((v) => v.pluja_mm || 0);
    if (mm < Math.max(...veins) || files.slice(Math.max(0, i - 2), i).some((v) => (v.pluja_mm || 0) === mm)) return;
    const t = svg('text', { class: 'g-mm', 'text-anchor': 'middle' },
      `${mm >= 10 ? Math.round(mm) : coma(Math.round(mm * 10) / 10)}\u00a0mm`);
    g.append(t);
    const cx = x(i) + col / 2;
    const llarg = t.getComputedTextLength();
    const llocs = [[cx, dalt(f) - 4], [cx, dalt(f) + 14], [cx - llarg / 2 - col, dalt(f) + 4], [cx + llarg / 2 + col, dalt(f) + 4]];
    for (const [lx, ly] of llocs) {
      t.setAttribute('x', Math.min(Math.max(lx, llarg / 2 + 1), W - llarg / 2 - 1));
      t.setAttribute('y', ly);
      if (!xoca(t.getBBox())) break;
    }
  });

  // L'eix: «Ara» a l'esquerra i les hores en punt, cada 3 h (o 2).
  // Si la gràfica no comença ara (la vista de demà), la primera hora.
  const ambAra = new Date(files[0].hora) <= new Date();
  const textAra = svg('text', { class: ambAra ? 'g-hora ara' : 'g-hora', x: 1, y: yEix }, ambAra ? T('Ara') : String(hora(files[0])));
  g.append(textAra);
  // Cap hora a sobre d'«Ara» («Ahora» és més llarg): mesurat a la pàgina.
  const finsAra = textAra.getComputedTextLength() + 14;
  // Una marca a cada hora: llarga i amb el número a les que toquen; curta i
  // sense número a la resta (Juanjo, 16-10-2026).
  files.forEach((f, i) => {
    if (!i) return;
    const gran = hora(f) % pas === 0;
    g.append(svg('line', { class: gran ? 'g-marca' : 'g-marca petita', x1: x(i), x2: x(i),
      y1: baix, y2: baix + (gran ? 4 : 2) }));
    if (!gran || x(i) < finsAra || x(i) > W - 8) return;
    g.append(svg('text', { class: 'g-hora', x: x(i), y: yEix, 'text-anchor': 'middle' }, String(hora(f))));
  });
  // Tocar una hora (o passar-hi el ratolí): una fitxa amb tota la previsió
  // d'aquella hora, perquè a la gràfica no hi cap (Juanjo, 16-10-2026: «solo
  // pone la lluvia del mayor?»; 17-10-2026: «no se podrían añadir el resto de
  // datos?»). La part alta, la neu i l'UV, només quan diuen alguna cosa. Es
  // treu tocant fora o la mateixa hora.
  const retol = svg('g', { class: 'g-retol' });
  let actiu = null;
  const amaga = () => {
    actiu = null;
    retol.replaceChildren();
  };
  const liniesFitxa = (f, i) => {
    const [textCel] = f.plou_ara ? [T('Plou ara')] : cel(f);
    const linies = [textCel ? T`${hora(f)}\u00a0h · ${textCel}` : T`${hora(f)}\u00a0h`];
    const t = Math.round(f.temperatura);
    const alta = arrodoneixAlta(f.dif_alta);
    linies.push(T`Temperatura: ${t}\u00a0°C` + (alta ? T` (part alta: ${t + alta}\u00a0°C)` : ''));
    // Els mm com a la xifra de la barra: sense decimals a partir de 10.
    const v = f.pluja_mm || 0;
    const mm = v >= 10 ? String(Math.round(v)) : v < 0.05 ? '0' : coma(Math.round(v * 10) / 10);
    linies.push(f.probabilitat == null ? T`Pluja: ${mm}\u00a0mm`
      : T`Pluja: ${mm}\u00a0mm · ${Math.round(f.probabilitat * 100)}\u00a0%`);
    if ((f.neu || 0) >= 0.1) linies.push(T`Neu: ${coma(f.neu)}\u00a0cm`);
    if (f.vent != null) {
      linies.push(T`Vent: ${Math.round(f.vent)}\u00a0km/h` + (f.ratxa ? T`, ratxes de ${Math.round(f.ratxa)}\u00a0km/h` : ''));
    }
    // L'UV, de dia i des de 3, quan l'OMS ja recomana protegir-se.
    if (!esNit[i] && f.uv != null && Math.round(f.uv) >= 3) linies.push(T`Índex UV: ${Math.round(f.uv)}`);
    return linies;
  };
  const mostra = (i) => {
    actiu = i;
    retol.replaceChildren(svg('rect', { class: 'g-retol-columna', x: x(i), y: yCel - 2, width: col,
      height: baix - yCel + 2 }));
    const fons = svg('rect', { class: 'g-retol-fons', rx: 6 });
    retol.append(fons);
    const interlinia = 16;
    const textos = liniesFitxa(files[i], i).map((l, k) => {
      const t = svg('text', { class: k ? 'g-retol-text' : 'g-retol-text titol' }, l);
      retol.append(t);
      return t;
    });
    const ample = Math.max(...textos.map((t) => t.getComputedTextLength())) + 16;
    const alt = textos.length * interlinia + 8;
    // Al costat de la columna, on hi hagi lloc, perquè no tapi l'hora triada.
    // Si no hi cap per cap costat (al mòbil, les hores del mig), sota l'eix,
    // damunt de la llegenda.
    let fx = x(i) + col + 6;
    let fy = yCel;
    if (fx + ample > W) fx = x(i) - 6 - ample;
    if (fx < 0) {
      fx = Math.min(Math.max(x(i) + col / 2 - ample / 2, 0), W - ample);
      fy = yEix + 8;
    }
    Object.entries({ x: fx, y: fy, width: ample, height: alt }).forEach(([k, v_]) => fons.setAttribute(k, v_));
    textos.forEach((t, k) => {
      t.setAttribute('x', fx + 8);
      t.setAttribute('y', fy + 4 + interlinia * (k + 1) - 4);
    });
  };
  files.forEach((f, i) => {
    const zona = svg('rect', { class: 'g-zona', x: x(i), y: yCel - 2, width: col, height: baix - yCel + 2 });
    zona.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') mostra(i); });
    zona.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') amaga(); });
    zona.addEventListener('click', (e) => {
      e.stopPropagation();
      if (actiu === i && e.pointerType !== 'mouse') amaga();
      else mostra(i);
    });
    g.append(zona);
  });
  g.append(retol);
  fig._amaga = amaga;

  fig.querySelector('.g-llegenda')?.remove();
  const ll = element('p', 'g-llegenda');
  const clau = (classe, text) => {
    const c = element('span', 'g-clau');
    c.append(element('span', classe), text);
    return c;
  };
  // Una clau per cosa, sense explicacions entre parèntesis (Juanjo, 16-10-2026:
  // «es un galimatías»); què vol dir l'alçada ja ho diuen els mm de la barra.
  // Cada clau de pluja, només si n'hi ha (Juanjo, 16-10-2026).
  ll.append(clau('m-temp', T('Temperatura')));
  const plujes = files.map((f) => plujaGrafica(f));
  // La probabilitat en xifres: «probable» i «possible» no es distingeixen
  // (Juanjo, 16-10-2026: «entre lluvia probable y puede llover no hay
  // diferencia para un usuario normal»).
  const pct = (p) => Math.round(p * 100);
  if (plujes.includes('pluja')) ll.append(clau('m-pluja', T`Pluja, ${pct(PROB_PLUJA)}\u00a0% o més`));
  if (plujes.includes('possible')) {
    ll.append(clau('m-pluja possible', T`Pluja, del ${pct(PROB_POSSIBLE)} al ${pct(PROB_PLUJA)}\u00a0%`));
  }
  if (plujes.includes('poca')) {
    ll.append(clau('m-pluja poca', T`Pluja, del ${pct(PROB_POCA)} al ${pct(PROB_POSSIBLE)}\u00a0%`));
  }
  const intenses = files.filter((f) => plujaGrafica(f)).map((f) => intensitatPluja(f.pluja_mm || 0));
  if (intenses.includes('forta')) ll.append(clau('m-pluja forta', T('Pluja forta')));
  if (intenses.includes('torrencial')) ll.append(clau('m-pluja torrencial', T('Pluja torrencial')));
  if (hVent) ll.append(clau('m-vent', T('Vent')), clau('m-ratxa', T('Ratxes')));
  ll.append(clau('m-nit', T('Nit')));
  fig.append(ll);
}

// --- La gràfica en gran (Juanjo, 17-10-2026: «verlo en su propia ventana …
// con posibilidad de alguna configuració»): a sobre de la pàgina, amb marge,
// i amb la seva adreça (#grafica) per compartir-la. Es tria quines hores (avui,
// demà o totes) i si s'hi veu el vent; es recorda en aquest dispositiu. ---
const CLAU_GRAFICA = 'meteo.grafica';

function horesVista(tram) {
  const ara = new Date();
  const totes = (HORES_GRAFICA || []).filter((f) => new Date(f.fins) > ara && f.temperatura != null);
  const dia = (f) => new Date(f.hora).toDateString();
  const dema = new Date(ara.getFullYear(), ara.getMonth(), ara.getDate() + 1).toDateString();
  if (tram === 'avui') return totes.filter((f) => dia(f) === ara.toDateString());
  if (tram === 'dema') return totes.filter((f) => dia(f) === dema);
  return totes;
}

function llegeixOpcionsGrafica() {
  try { return JSON.parse(localStorage.getItem(CLAU_GRAFICA)) || {}; } catch (_) { return {}; }
}

function vistaGrafica() {
  if (!HORES_GRAFICA || document.querySelector('dialog.vista-grafica')) return;
  const opcions = { tram: 'tot', vent: false, ...llegeixOpcionsGrafica() };
  const dlg = element('dialog', 'vista-grafica');
  dlg.setAttribute('aria-labelledby', 'vg-titol');
  const cap = element('div', 'vg-cap');
  const titol = element('h2', null, T('Previsió'));
  titol.id = 'vg-titol';
  const comparteixBoto = element('button', 'boto-icona');
  comparteixBoto.type = 'button';
  comparteixBoto.title = T('Comparteix la gràfica');
  comparteixBoto.setAttribute('aria-label', T('Comparteix la gràfica'));
  comparteixBoto.append(icona('i-share-2'));
  comparteixBoto.addEventListener('click', () => comparteix());
  // Tancar: la X de sempre, a dalt a la dreta (icona «x» de Lucide).
  const tanca = element('button', 'boto-icona');
  tanca.type = 'button';
  tanca.title = T('Tanca');
  tanca.setAttribute('aria-label', T('Tanca'));
  tanca.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>';
  tanca.addEventListener('click', () => dlg.close());
  const accions = element('div', 'vg-accions');
  accions.append(comparteixBoto, tanca);
  cap.append(titol, accions);

  // Les opcions: quines hores (només les que tenen prou hores) i el vent.
  const tramsBotons = element('div', 'vg-trams');
  tramsBotons.setAttribute('role', 'group');
  tramsBotons.setAttribute('aria-label', T('Quines hores'));
  const trams = [['avui', T('Avui')], ['dema', T('Demà')], ['tot', T('Tot')]]
    .filter(([clau]) => clau === 'tot' || horesVista(clau).length >= 3);
  if (!trams.some(([clau]) => clau === opcions.tram)) opcions.tram = 'tot';
  const vent = element('button', 'vg-opcio');
  vent.type = 'button';
  vent.append(icona('i-wind'), T('Vent'));
  const ambVent = HORES_GRAFICA.some((f) => f.vent != null);
  const fig = figuraGrafica([], T('Gràfica de la previsió hora a hora: perill, cel, temperatura i probabilitat de pluja.'));
  fig.classList.add('gran');
  const desa = () => {
    try { localStorage.setItem(CLAU_GRAFICA, JSON.stringify(opcions)); } catch (_) {}
  };
  const dibuixa = () => {
    for (const b of tramsBotons.children) b.setAttribute('aria-pressed', String(b.dataset.tram === opcions.tram));
    vent.setAttribute('aria-pressed', String(opcions.vent));
    fig._files = horesVista(opcions.tram);
    fig._opcions = { gran: true, vent: ambVent && opcions.vent };
    fig._amaga?.();
    dibuixaGrafica(fig);
  };
  for (const [clau, text] of trams) {
    const b = element('button', 'vg-opcio', text);
    b.type = 'button';
    b.dataset.tram = clau;
    b.addEventListener('click', () => { opcions.tram = clau; desa(); dibuixa(); });
    tramsBotons.append(b);
  }
  vent.addEventListener('click', () => { opcions.vent = !opcions.vent; desa(); dibuixa(); });
  const barra = element('div', 'vg-opcions');
  barra.append(tramsBotons);
  if (ambVent) barra.append(vent);

  dlg.append(cap, barra, fig);
  // Un toc fora de la finestra la tanca, com Esc.
  dlg.addEventListener('click', (e) => {
    if (e.target !== dlg) return;
    const r = dlg.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dlg.close();
  });
  dlg.addEventListener('close', () => {
    dlg.remove();
    if (location.hash === '#grafica') history.replaceState(null, '', location.pathname + location.search);
  });
  document.body.append(dlg);
  dlg.showModal();
  if (location.hash !== '#grafica') history.replaceState(null, '', '#grafica');
  dibuixa();
  tanca.focus();
}

// Si s'ha obert l'enllaç de la gràfica (#grafica), en gran, la primera vegada.
let obertaGrafica = false;
function obreGraficaDeLEnllac() {
  if (obertaGrafica || location.hash !== '#grafica') return;
  obertaGrafica = true;
  vistaGrafica();
}
addEventListener('hashchange', () => { if (location.hash === '#grafica') vistaGrafica(); });

function dibuixaGrafiques() {
  for (const fig of document.querySelectorAll('figure.grafica')) dibuixaGrafica(fig);
}
addEventListener('resize', dibuixaGrafiques);
// Tocar fora de la gràfica treu el rètol de l'hora.
addEventListener('click', () => {
  for (const fig of document.querySelectorAll('figure.grafica')) fig._amaga?.();
});

