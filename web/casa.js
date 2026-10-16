// SPDX-License-Identifier: AGPL-3.0-or-later
// Llegeix casa.json (el genera casa.py) i pinta el temps a casa: el que mesura
// ara l'estació de casa i la previsió hora a hora, 24 hores com a mínim i
// fins a les 21 h de demà (ADR 0041).

// La pàgina pública («Temps a Montflorit», ADR 0024) és aquesta mateixa amb
// tres coses canviades a l'etiqueta <html>: el nom del lloc, com s'anomena
// l'estació pròpia i el fitxer de dades.
const LLOC = document.documentElement.dataset.lloc || 'casa';
const ESTACIO_PROPIA = document.documentElement.dataset.estacio || 'l\u2019estació de casa';
const FITXER_DADES = document.documentElement.dataset.dades || 'casa.json';

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

// Com canvia la pressió en tres hores, amb els llindars habituals: menys d'1
// hPa és estable; 3,6 hPa o més, un canvi ràpid.
function textPressio(casa) {
  const p = T`Pressió ${coma(casa.pressio, 0)} hPa`;
  const d = casa.pressio_3h;
  if (d == null) return p;
  if (Math.abs(d) < 1) return T`${p}, estable`;
  const sentit = d > 0 ? T('pujant') : T('baixant');
  const rapid = Math.abs(d) >= 3.6 ? T(' ràpid') : '';
  const signe = d > 0 ? '+' : '\u2212';
  return T`${p}, ${sentit}${rapid} (${signe}${coma(Math.abs(d))} en 3 h)`;
}

// La temperatura i la pressió, de l'estació de casa; la pluja i la humitat, de
// la xarxa del barri (casa.consens); el vent, de Meteocat.
// Cada dada, amb la seva icona, perquè es llegeixi d'una ullada.
function dada(id, text) {
  const li = element('li');
  li.append(icona(id), document.createTextNode(text));
  return li;
}

// Resum del que ve per trams del dia (matí 7–14, tarda 14–21, nit 21–7): el
// cel i les temperatures sempre; la pluja, només si alguna hora en té com a
// mínim de possible (Juanjo, 09-10-2026: «símbolo de lluvia solo si va a
// llover»); els fenòmens, només quan es donen, amb els llindars grocs del Pla
// Meteoalerta que ja usa config.RISC_LLINDARS, més neu i gel. Cada tram és un
// desplegable de la taula, amb aquest resum a la capçalera (Juanjo,
// 09-10-2026: «dividir la lista del tiempo en mañana, tarde, noche como
// desplegables»).
const TRAMS = [[7, 14, 'Matí'], [14, 21, 'Tarda'], [21, 7, 'Nit']];
const FENOMENS = { pluja_forta: INTENSITAT_PLUJA[1], pluja_torrencial: INTENSITAT_PLUJA[2], ratxa: 70, calor: 36, glaçada: 0 };
// Els noms, amb T() literal perquè les proves de traducció els trobin.
const NOM_TRAM = { Matí: () => T('Matí'), Tarda: () => T('Tarda'), Nit: () => T('Nit') };
const NOM_TRAM_DEMA = { Matí: () => T('Demà matí'), Tarda: () => T('Demà tarda'), Nit: () => T('Demà nit') };
const NOM_FENOMEN = {
  tempesta: () => T('tempesta'), pluja_forta: () => T('pluja forta'), pluja_torrencial: () => T('pluja torrencial'),
  neu: () => T('neu'), calor: () => T('calor'), glaçada: () => T('glaçada'),
  glaçadaRiera: () => T('glaçada vora la riera'),
};

function tramDe(f) {
  const d = new Date(f.hora);
  const h = d.getHours();
  const [ini, fi, nom] = TRAMS.find(([a, b]) => (a < b ? h >= a && h < b : h >= a || h < b));
  // La nit comença el dia anterior si som a la matinada.
  const dia = new Date(d);
  if (nom === 'Nit' && h < 7) dia.setDate(dia.getDate() - 1);
  return { clau: `${dia.toDateString()}|${nom}`, nom, ini, fi, dia };
}

// El cel del tram: boira si n'hi ha la major part de les hores; si no, la
// mitjana dels núvols. Només el cel: la pluja la diu el paraigua.
function celTram(files, nit) {
  if (files.filter(esBoira).length * 2 > files.length) return [T('Boira'), 'i-cloud-fog'];
  const n = files.filter((f) => f.nuvols != null).map(nuvolsHora);
  return n.length ? celNuvols(n.reduce((a, b) => a + b, 0) / n.length, nit) : null;
}

// Tots els trams que toca la previsió, sense les hores ja passades. Les hores
// diuen les que hi ha de veritat: el tram en curs, «fins a les…», i l'últim,
// sencer (casa.py arriba fins a les 21 h de demà i acaba amb un tram), o fins
// on arribin les dades si en falten.
// Quants graus més o menys que el dia abans (Juanjo, 10-10-2026; ADR 0061):
// el tram d'avui, amb les mateixes hores d'ahir, mesurades a l'estació; el de
// demà, amb avui (el mesurat fins ara i la previsió de la resta). La màxima de
// dia i la mínima de nit; la xifra, només des de COMPARA_MIN graus. Igual que
// bot.compara_temp, que les proves comparen.
const COMPARA_MIN = 2;

function diaAbans(clau) {
  // Sense el desfase de l'hora que es repeteix a l'octubre («T02:00+01:00»):
  // el dia abans, aquella hora només hi és una vegada.
  const [dia, resta] = clau.split('T');
  const hora = resta.slice(0, 5);
  const t = new Date(`${dia}T12:00`);
  t.setDate(t.getDate() - 1);
  const dos = (n) => String(n).padStart(2, '0');
  return `${t.getFullYear()}-${dos(t.getMonth() + 1)}-${dos(t.getDate())}T${hora}`;
}

function comparaTemp(files, nit, mesurada, totes) {
  if (!mesurada || !Object.keys(mesurada).length || !files.length) return null;
  const previstes = Object.fromEntries((totes || []).map((f) => [f.hora, f]));
  const abans = [];
  for (const f of files) {
    const a = mesurada[diaAbans(f.hora)];
    const b = mesurada[diaAbans(f.fins)];
    const p = previstes[diaAbans(f.hora)];
    const v = a != null && b != null ? (a + b) / 2 : (p ? p.temperatura : null);
    if (v == null || f.temperatura == null) return null;
    abans.push(v);
  }
  const ara = files.map((f) => f.temperatura);
  const d = nit ? Math.min(...ara) - Math.min(...abans) : Math.max(...ara) - Math.max(...abans);
  return Math.sign(d) * Math.floor(Math.abs(d) + 0.5);
}

function textComparacio(n, esDema) {
  if (n == null) return null;
  if (Math.abs(n) < COMPARA_MIN) return esDema ? T('semblant a avui') : T('semblant a ahir');
  if (esDema) return n > 0 ? T`${Math.abs(n)}° més que avui` : T`${Math.abs(n)}° menys que avui`;
  return n > 0 ? T`${Math.abs(n)}° més que ahir` : T`${Math.abs(n)}° menys que ahir`;
}

// D'on surt la tempesta d'un tram: d'un avís oficial o dels models.
function origenTempesta(files) {
  const avis = files.flatMap((f) => (f.avisos || []).filter((a) => (a.tipus || []).includes('tempestes')))[0];
  const font = avis && (avis.font === 'meteocat' ? 'Meteocat' : 'AEMET');
  const parts = [];
  if (font === 'AEMET') parts.push(T`Avís ${TD(avis.nivell)} de l\u2019AEMET per tempestes`);
  else if (font) parts.push(T`Perill ${GRAU_METEOCAT()[avis.nivell]} de Meteocat per tempestes`);
  if (files.some((f) => f.codi >= 95)) parts.push(T('Els models preveuen tempesta'));
  return parts.join('; ');
}

// El perill d'un tram: el nivell més alt de les seves hores i què és.
function perillTram(files) {
  return delNivellMesAlt(files.flatMap(elementsPerill));
}

function resumTrams(hores, ara, mesurada) {
  const grups = [];
  for (const f of hores || []) {
    if (new Date(f.fins) <= ara) continue;
    const t = tramDe(f);
    let g = grups.find((x) => x.clau === t.clau);
    if (!g) grups.push(g = { ...t, files: [] });
    g.files.push(f);
  }
  const dema = new Date(ara);
  dema.setDate(dema.getDate() + 1);
  return grups.map((g) => {
    const temps = g.files.map((f) => f.temperatura).filter((t) => t != null);
    // Les temperatures són de la riera; a la part alta, amb la diferència de
    // cada hora (part_alta.py, ADR 0087).
    const alta = g.files.filter((f) => f.temperatura != null).map((f) => f.temperatura + (f.dif_alta || 0));
    const fenomens = [];
    const tempesta = (f) => f.codi >= 95 || (f.avisos || []).some((a) => (a.tipus || []).includes('tempestes'));
    if (g.files.some(tempesta)) fenomens.push([NOM_FENOMEN.tempesta(), 'i-cloud-lightning', origenTempesta(g.files)]);
    if (g.files.some((f) => (f.pluja_mm || 0) >= FENOMENS.pluja_torrencial)) fenomens.push([NOM_FENOMEN.pluja_torrencial(), 'i-cloud-rain-wind']);
    else if (g.files.some((f) => (f.pluja_mm || 0) >= FENOMENS.pluja_forta)) fenomens.push([NOM_FENOMEN.pluja_forta(), 'i-cloud-rain-wind']);
    if (g.files.reduce((s, f) => s + (f.neu || 0), 0) >= 0.1) fenomens.push([NOM_FENOMEN.neu(), 'i-snowflake']);
    const ratxa = Math.max(...g.files.map((f) => f.ratxa || 0));
    if (ratxa >= FENOMENS.ratxa) fenomens.push([T`ratxes de ${Math.round(ratxa)}\u00a0km/h`, 'i-wind']);
    if (temps.length && Math.max(...temps) >= FENOMENS.calor) fenomens.push([NOM_FENOMEN.calor(), 'i-thermometer-sun']);
    if (temps.length && Math.min(...temps) <= FENOMENS.glaçada) {
      fenomens.push([Math.min(...alta) > FENOMENS.glaçada ? NOM_FENOMEN.glaçadaRiera() : NOM_FENOMEN.glaçada(),
        'i-thermometer-snowflake']);
    }
    const esDema = g.dia.toDateString() === dema.toDateString();
    const actual = new Date(g.files[0].hora) <= ara;
    const fi = new Date(g.files[g.files.length - 1].fins).getHours();
    return {
      clau: g.clau,
      nom: (esDema ? NOM_TRAM_DEMA : NOM_TRAM)[g.nom](),
      hores: actual ? T`fins a les ${fi} h` : `${g.ini}–${fi} h`,
      cel: celTram(g.files, g.nom === 'Nit'),
      plou: g.files.some((f) => plujaHora(f) !== null),
      prob: Math.max(...g.files.map((f) => f.probabilitat || 0)),
      mm: g.files.reduce((s, f) => s + (f.pluja_mm || 0), 0),
      tMin: temps.length ? Math.min(...temps) : null, tMax: temps.length ? Math.max(...temps) : null,
      // Quant més fa a la part alta: la màxima de dia i la mínima de nit.
      difAlta: temps.length ? (g.nom === 'Nit' ? Math.min(...alta) - Math.min(...temps)
        : Math.max(...alta) - Math.max(...temps)) : null,
      compara: textComparacio(comparaTemp(g.files, g.nom === 'Nit', mesurada, hores), esDema),
      fenomens,
      avis: g.files.some((f) => avisHora(f)),
      perill: perillTram(g.files),
      files: g.files,
    };
  });
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

function textAltaTram(n) {
  const r = arrodoneixAlta(n);
  // Als trams, només la xifra; el text, a «Ara» i al resum del dia (Juanjo,
  // 13-10-2026). Què vol dir, en prémer-la i a la llegenda.
  return r ? (r > 0 ? '+' : '−') + Math.abs(r) : '';
}

function textAltaAra(n) {
  const r = arrodoneixAlta(n);
  if (!r) return null;
  return r > 0 ? T`A la part alta, ${r} °C més` : T`A la part alta, ${-r} °C menys`;
}

// La capçalera del desplegable: el nom del tram, les hores i el resum.
function resumTram(t) {
  const sum = element('summary');
  sum.append(element('strong', null, t.nom), element('span', 'quan', ` (${t.hores})`));
  const peca = (id, text, classe = 'dada', titol = '') => {
    const s = element('span', classe);
    if (titol) s.title = titol;
    const contingut = element('span');
    contingut.append(...[].concat(text));
    s.append(icona(id), typeof text === 'string' ? text : contingut);
    sum.append(s);
  };
  if (t.cel) peca(t.cel[1], t.cel[0]);
  if (t.tMin != null) {
    // La mínima en blau i la màxima en vermell, com Meteocat (ADR 0063).
    const [min, max] = [Math.round(t.tMin), Math.round(t.tMax)];
    const xifres = min === max ? [`${min}`] : [element('span', 'temp-min', `${min}`), '–', element('span', 'temp-max', `${max}`)];
    // Cada tros sencer; si no hi cap, la part alta i la comparació passen a
    // la línia següent (Juanjo, 13-10-2026: «en movil … se desborda»).
    const nucli = element('span', 'tros');
    nucli.append(...xifres, ' °C');
    const trossos = [nucli];
    // La part alta i la comparació, diferenciades de la temperatura per
    // llegir-ho d'una ullada (Juanjo, 13-10-2026).
    const alta = textAltaTram(t.difAlta);
    if (alta) {
      const et = etiquetaAlta(alta, true);
      et.classList.add('tros');
      trossos.push(' ', et);
    }
    if (t.compara) trossos.push(' ', element('span', 'tros compara', `· ${t.compara}`));
    peca('i-thermometer', trossos, 'dada temp');
  }
  // El perill, primer i del color del nivell, com els avisos de dalt (ADR 0076).
  if (t.perill) {
    const xip = element('span', `perill-tram ${t.perill.nivell}`);
    xip.append(icona('i-triangle-alert'), textPerillCurt(t.perill));
    // D'on surt, en passar-hi el ratolí (Juanjo, 16-10-2026).
    xip.title = textPerill(t.perill);
    sum.append(xip);
  }
  if (t.plou) peca('i-umbrella', `${Math.round(t.prob * 100)} %` + (t.mm >= 1 ? T`, uns ${coma(t.mm, 0)} mm` : ''));
  for (const [text, id, origen] of t.fenomens) peca(id, text, 'dada fenomen', origen);
  return sum;
}

function blocAra(casa, radarDades, vent, veines, hores) {
  const sec = element('section', 'decisio targeta ara');
  sec.setAttribute('aria-label', T`El temps ara a ${LLOC}`);
  // Sense l'hora de la mesura: la línia «Actualitzat a les…» va al peu de la
  // targeta, i dues hores juntes semblaven un error (Juanjo, 16-10-2026; ADR 0094).
  sec.append(element('h2', 'data', T`Ara a ${LLOC}`));
  const temp = element('p', 'veredicte');
  const termometre = icona('i-thermometer');
  termometre.classList.add('vehicle');
  temp.append(termometre, `${coma(casa.temperatura)} °C`);
  sec.append(temp);
  // La part alta, en la seva etiqueta, si la diferència arriba a un grau; què
  // vol dir, en prémer-la (etiquetaAlta, a comu.js).
  const alta = textAltaAra(casa.dif_alta);
  if (alta) {
    const linia = element('p', 'ara-menys');
    linia.append(etiquetaAlta(alta));
    sec.append(linia);
  }
  // Plou si ha plogut en els últims 15 minuts a la xarxa del barri: l'estació
  // de casa o alguna de les veïnes que compten (ADR 0060), amb la intensitat
  // mediana de les que en marquen (casa.consens), sense dir de quina estació
  // surt (Juanjo, 13-10-2026). Les veïnes, per a les dades d'abans de la 3.76.0.
  const plou = !!casa.plou || (veines || []).some((v) => v.plou && v.compta);
  const intensitat = (casa.plou && casa.intensitat) || 0;
  const llista = element('ul', 'dades-ara');
  llista.append(!plou ? dada('i-umbrella-off', T('No plou'))
    : intensitat ? dada('i-umbrella', T`Plou: ${coma(intensitat)} mm/h`)
      : dada('i-umbrella', T('Plou')));
  llista.append(dada('i-cloud-rain', T`${coma(casa.pluja_avui || 0)} mm avui`));
  // El vent, de l'estació de Meteocat més propera, per mitges hores (ADR
  // 0037): l'estació i l'hora, a «D'on surt» (ADR 0074). Si ve de les veïnes
  // (ADR 0064), que «D'on surt» encara no diu, es diu aquí.
  if (vent && vent.mitja != null) {
    const ratxa = vent.ratxa != null ? T` (ratxes de ${coma(vent.ratxa, 0)})` : '';
    const veines = vent.font === 'veines' ? T(', estacions veïnes') : '';
    llista.append(dada('i-wind', T`Vent ${coma(vent.mitja, 0)} km/h${ratxa}` + veines));
  }
  sec.append(llista);
  // La humitat i la pressió, que es miren menys, juntes en una línia petita
  // (Juanjo, 12-10-2026; ADR 0074).
  const menys = [T`Humitat ${coma(casa.humitat, 0)} %`];
  if (casa.pressio != null) menys.push(textPressio(casa));
  sec.append(element('p', 'ara-menys', menys.join(' · ')));
  const radar = blocRadar(radarDades, plou, hores);
  if (radar) sec.append(radar);
  return sec;
}

// El resum del dia, el mateix de «Consultes › Avui», a sota d'«Ara»: el que es
// vol saber en obrir la pàgina, sense desplegar res (Juanjo, 12-10-2026; ADR
// 0074). Des de HORA_DEMA, també el de demà, com el bot. Sense la línia «Ara
// mateix», que ja és la targeta de sobre, ni la de la roba, que és cosa de
// «Si surts» (Juanjo, 12-10-2026: «lo de la ropa en pantalla principal, no es
// un poco frivolo?»), ni els avisos de l'AEMET, que ja surten a dalt, a
// «Avisos actius» (ADR 0076).
const HORA_DEMA = 18;   // la de bot.HORA_DEMA
// Les alertes tampoc: totes ja surten a «Avisos actius» (ADR 0093).
const LINIA_FORA = /^(⟦[a-z-]+⟧ ?)?(Ara mateix|Ahora mismo|Roba |Ropa )/;
const liniaFora = (l) => LINIA_FORA.test(l) || LINIA_PERILL.test(l);

function textosResum(dades) {
  const textos = (dades.consultes || {})[IDIOMA.codi === 'es' ? 'es' : 'ca'] || {};
  const claus = new Date(dades.generat).getHours() >= HORA_DEMA ? ['avui', 'dema'] : ['avui'];
  return claus.filter((c) => textos[c]).map((c) => textos[c].split('\n').filter((l) => !liniaFora(l)).join('\n'));
}

function blocsResum(dades) {
  const blocs = textosResum(dades).map((text) => {
    const sec = element('section', 'targeta resum-dia');
    sec.append(...ambDetalls(pintaResum(text)));
    return sec;
  });
  // Sense la invitació fixa a activar els avisos (Juanjo, 12-10-2026: «quita ese
  // texto fijo de activar avisos»; ADR 0080): ja hi ha la campana i, a qui té la
  // web instal·lada, la targeta d'oferta.
  return blocs;
}

// La pluja del radar portada endavant (ADR 0019): quan arribaria a casa i,
// si ja hi és, quan pararia, «en entrenament» mentre aprèn (ADR 0049): el
// tercer valor diu si cal la marca.
function textRadar(r, plou) {
  if (!r) return null;
  const aviat = (t) => new Date(t) <= new Date(Date.now() + 5 * 60e3);
  // El que es mesura mana: si ja plou, «Pluja a sobre», encara que el radar
  // només en vegi una part; si no en veu gens, sense hora (Juanjo, 08-10-2026).
  if ((plou && (r.arriba || r.possible)) || (r.arriba && aviat(r.arriba))) {
    const fi = r.fi ? T` · pararia cap a les\u00a0${horaCurta(r.fi)}`
      : r.sense_fi ? T(' · no s’acaba en 2 hores') : '';
    return ['arriba', T('Pluja a sobre') + fi, Boolean(fi)];
  }
  if (plou) return ['arriba', T('Pluja a sobre'), false];
  if (r.arriba) return ['arriba', T`Arribaria pluja cap a les\u00a0${horaCurta(r.arriba)}`];
  if (r.possible) {
    if (aviat(r.possible)) return ['possible', T('Pluja a prop: pot arribar')];
    return ['possible', T`Pot arribar pluja cap a les\u00a0${horaCurta(r.possible)}`];
  }
  return ['res', T('No s\u2019acosta pluja en 2 hores')];
}

// On veure el radar en directe, centrat a Montflorit quan es pot.
const RADAR_EN_DIRECTE = {
  rainviewer: 'https://www.rainviewer.com/map.html?loc=41.482,2.135,9&layer=radar',
  meteocat: 'https://www.meteo.cat/observacions/radar',
};

// Si la previsió dona pluja, com a mínim possible, en alguna de les dues
// hores que venen: llavors que el radar no en vegi és notícia.
function plujaPrevistaAviat(hores, ara = new Date()) {
  const fins = new Date(ara.getTime() + 2 * 3600e3);
  return (hores || []).some((f) => new Date(f.fins) > ara && new Date(f.hora) < fins && plujaHora(f));
}

// Franja pròpia dins «Ara a casa», amb el color del que diu: ambre si la
// pluja arriba, blau si és possible, neutre si no se n'acosta. Que no se
// n'acosti només surt si la previsió en dona aviat; si no, no diu res que no
// digui ja la previsió (Juanjo, 10-10-2026: «si no anuncia nada como ahora
// mejor que no salga»; ADR 0019).
function blocRadar(r, plou, hores) {
  const t = textRadar(r, plou);
  if (!t) return null;
  if (t[0] === 'res' && !plujaPrevistaAviat(hores)) return null;
  const [estat, text, proves] = t;
  const caixa = element('div', `radar-ara ${estat}`);
  caixa.append(icona('i-radar'));
  const cos = element('div');
  const p = element('p', 'radar-text', text);
  if (proves) {
    const marca = element('span', 'en-proves', T(' (en entrenament)'));
    marca.title = T('Hora estimada amb el radar. Encara s’està entrenant amb la pluja real: pot fallar.');
    p.append(marca);
  }
  cos.append(p);
  // La font i l'hora de la imatge, com demana Meteocat per reutilitzar-la,
  // amb l'enllaç al radar en directe (Juanjo, 08-10-2026).
  const font = r.imatge === 'rainviewer' ? 'RainViewer' : 'Meteocat';
  const mov = r.cap_a ? T` \u00b7 va cap ${TD(r.cap_a)} a ${r.velocitat_kmh}\u00a0km/h` : '';
  const detall = element('p', 'radar-detall');
  const [abans, despres] = T`Radar de ${font} de les ${horaCurta(r.hora)}${mov}`.split(font);
  const enllac = element('a', null, font);
  enllac.href = RADAR_EN_DIRECTE[r.imatge === 'rainviewer' ? 'rainviewer' : 'meteocat'];
  enllac.target = '_blank';
  enllac.rel = 'noopener';
  detall.append(abans, enllac, despres);
  cos.append(detall);
  caixa.append(cos);
  return caixa;
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
function elementsPerill(f) {
  return [...(f.avisos || []).flatMap((a) => a.tipus.map((t) => ({ nivell: a.nivell, nom: TD(t), font: a.font || 'aemet' }))),
    ...(f.riscos_hora || []).map((r) => ({ nivell: r.nivell, nom: NOM_RISC()[r.tipus] || r.tipus, font: 'web' }))];
}

function delNivellMesAlt(elements) {
  if (!elements.length) return null;
  const nivell = elements.map((a) => a.nivell).sort((a, b) => ORDRE_NIVELL.indexOf(b) - ORDRE_NIVELL.indexOf(a))[0];
  const daquest = elements.filter((a) => a.nivell === nivell);
  const noms = [...new Set(daquest.map((a) => a.nom))].sort();
  const fonts = ['meteocat', 'aemet', 'web'].filter((x) => daquest.some((a) => a.font === x)).join('');
  // Cada font amb els seus fenòmens, per al text complet.
  const perFont = ['meteocat', 'aemet', 'web'].map((x) => [x, [...new Set(daquest.filter((a) => a.font === x).map((a) => a.nom))].sort()])
    .filter(([, n]) => n.length);
  return { nivell, noms, fonts, perFont };
}

function avisHora(f) {
  const p = delNivellMesAlt(elementsPerill(f));
  return p && { ...p, clau: `${p.nivell}|${p.noms.join(',')}|${p.fonts}` };
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

// Barra vertical del color de l'avís al llarg de les hores que cobreix. El
// text, tan llarg com hi càpiga; el complet, per als lectors de pantalla.
// El perill dit com el diu cada font: Meteocat, en grau de perill (moderat,
// alt, molt alt); l'AEMET i aquesta web, en colors (ADR 0093). El complet, amb
// d'on surt cada cosa; el curt, per a la franja i l'etiqueta del tram.
const GRAU_METEOCAT = () => ({ groc: T('moderat'), taronja: T('alt'), vermell: T('molt alt') });

function perFonts(p) {
  return p.perFont || [[p.fonts, p.noms]];
}

function textPerill(p) {
  const nivell = TD(p.nivell);
  return perFonts(p).map(([font, noms]) => {
    const que = noms.join(T(' i '));
    if (font === 'meteocat') return T`Perill ${GRAU_METEOCAT()[p.nivell]} de Meteocat per ${que}`;
    if (font === 'web') return T`Avís ${nivell} d\u2019aquesta web: ${que}`;
    return T`Avís ${nivell} de l\u2019AEMET per ${que}`;
  }).join('; ');
}

// «Perill alt: pluja», «Avís groc: tempestes»; si n'hi ha de les dues maneres, juntes.
function textPerillCurt(p, ambQue = true) {
  const parts = [];
  const meteocat = perFonts(p).filter(([f]) => f === 'meteocat').flatMap(([, n]) => n);
  const altres = perFonts(p).filter(([f]) => f !== 'meteocat').flatMap(([, n]) => n);
  if (meteocat.length) parts.push([T`Perill ${GRAU_METEOCAT()[p.nivell]}`, meteocat]);
  if (altres.length) parts.push([T`Avís ${TD(p.nivell)}`, [...new Set(altres)]]);
  return parts.map(([nom, que]) => (ambQue ? `${nom}: ${que.join(', ')}` : nom)).join(' · ');
}

function franjaAvis(tram) {
  const td = element('td', `col-avis franja-avis ${tram.nivell}`);
  td.rowSpan = tram.hores;
  const complet = textPerill(tram);
  td.title = complet;
  const barra = element('span', 'barra-avis');
  barra.append(element('span', 'text-avis'));
  const curt = textPerillCurt(tram, false);
  barra.dataset.textos = JSON.stringify([textPerillCurt(tram).replace(/: /g, ' · '), curt,
    curt.startsWith(T('Perill')) ? T('Perill') : T('Avís'), '']);
  barra.setAttribute('aria-hidden', 'true');
  // D'on surt, també al mòbil, on no hi ha ratolí: en tocar-la, un missatge
  // breu a baix (Juanjo, 16-10-2026; ADR 0093).
  const boto = element('button', 'boto-franja');
  boto.type = 'button';
  boto.setAttribute('aria-label', complet);
  boto.addEventListener('click', () => avisBreu(`${complet}.`));
  boto.append(barra);
  td.append(boto);
  return td;
}

// El text més llarg que hi cap, mesurat ja a la pàgina (l'alçada de les
// files canvia amb la pantalla).
function ajustaFranges() {
  for (const barra of document.querySelectorAll('.barra-avis')) {
    const text = barra.querySelector('.text-avis');
    for (const t of JSON.parse(barra.dataset.textos)) {
      text.textContent = t;
      if (text.offsetHeight <= barra.clientHeight - 6) break;
    }
  }
}
addEventListener('resize', ajustaFranges);

// Quins trams surten oberts (Juanjo, 09-10-2026: «no debería ser
// persistente?»). Els trams canvien de nom al llarg del dia, així que no es
// recorda cadascun sinó com ho vol veure cadascú: amb «Desplega-ho tot», tots
// oberts, desat en aquest dispositiu; si no, els que tenen un avís o un
// fenomen, perquè el perill no quedi plegat. El primer ja no: el resum del dia
// ja diu el que ve, i els trams es veuen junts (Juanjo, 12-10-2026; ADR
// 0074). El que s'obre o es tanca a
// mà es manté mentre la pàgina és oberta, encara que es torni a pintar amb
// dades noves, però no es desa.
const CLAU_TOT_OBERT = 'meteo.previsio-tot-obert';
function totObert() {
  try { return localStorage.getItem(CLAU_TOT_OBERT) === '1'; } catch (_) { return false; }
}
const obertsAMa = new Map();
function obertDeSortida(t) {
  if (obertsAMa.has(t.clau)) return obertsAMa.get(t.clau);
  return totObert() || t.avis || t.fenomens.length > 0;
}

// Una taula per tram, amb les mateixes columnes.
// La sortida i la posta del sol, a la fila de l'hora en què passen, al costat
// del cel: discretes, en gris (Juanjo, 13-10-2026).
function solPerHora(sol) {
  const clau = (d) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}-${d.getHours()}`;
  const res = new Map();
  for (const dia of sol || []) {
    if (dia.sortida) res.set(clau(new Date(dia.sortida)), ['i-sunrise', T('Surt el sol a les'), dia.sortida]);
    if (dia.posta) res.set(clau(new Date(dia.posta)), ['i-sunset', T('Es pon el sol a les'), dia.posta]);
  }
  return (hora) => res.get(clau(new Date(hora)));
}

function marcaSol([id, text, quan]) {
  const m = element('span', 'sol-fila');
  // Sense el zero de davant (8:02), com les hores de la taula (8–9): al mòbil
  // ha de cabre al costat de la icona del cel.
  const hora = new Date(quan).toLocaleTimeString(IDIOMA.codi, { hour: 'numeric', minute: '2-digit' });
  m.append(icona(id), element('span', 'visualment-amagat', text + ' '), hora);
  return m;
}

function origenTram(t) {
  const parts = t.perill ? [textPerill(t.perill)] : [];
  const tempesta = (t.fenomens.find(([, id]) => id === 'i-cloud-lightning') || [])[2];
  if (tempesta && !parts.some((x) => x.includes(tempesta))) {
    parts.push(T`${NOM_FENOMEN.tempesta().replace(/^./, (c) => c.toUpperCase())}: ${tempesta.replace(/^./, (c) => c.toLowerCase())}`);
  }
  return parts.length ? `${parts.join('. ')}.` : '';
}

function taulaTram(t, obert, solHora) {
  const det = element('details', `tram-hores${t.perill ? ` amb-perill ${t.perill.nivell}` : ''}`);
  det.open = obert;
  det.dataset.clau = t.clau;
  det.append(resumTram(t));
  // D'on surten el perill i la tempesta del tram, a la vista en obrir-lo: al
  // mòbil no hi ha el text del ratolí (Juanjo, 16-10-2026; ADR 0093).
  const origen = origenTram(t);
  if (origen) {
    const p = element('p', 'origen-tram');
    p.append(icona('i-triangle-alert'), origen);
    det.append(p);
  }
  const contenidor = element('div', 'taula-contenidor');
  // Al mòbil la taula es desplaça de costat: s'hi ha de poder arribar amb el teclat (axe-core).
  contenidor.tabIndex = 0;
  contenidor.setAttribute('role', 'region');
  contenidor.setAttribute('aria-label', `${t.nom} (${t.hores})`);
  const taula = element('table', 'taula-hores');
  const cols = element('colgroup');
  for (const c of ['hora', 'col-avis', 'cel', 'temp', 'mm', 'prob', 'vent']) cols.append(element('col', `c-${c}`));
  taula.append(cols);
  const cap = element('thead');
  const fila = element('tr');
  // Les unitats van a la capçalera perquè la taula càpiga al mòbil.
  for (const [text, classe] of [[T('Hora'), ''], [T('Avisos'), 'col-avis'], [T('Cel'), ''], ['°C', 'num'],
    [T('Pluja (mm)'), 'num'], [T('Prob.'), 'num'], [T('Vent'), 'num']]) {
    const th = element('th', classe);
    // La columna dels avisos no porta títol a la vista: la barra ja ho diu.
    th.append(classe === 'col-avis' ? element('span', 'visualment-amagat', text) : text);
    th.scope = 'col';
    fila.append(th);
  }
  cap.append(fila);
  taula.append(cap);
  const cos = element('tbody');
  const avisos = tramsAvis(t.files);
  t.files.forEach((f, i) => {
    const tr = element('tr', { pluja: 'amb-pluja', possible: 'pluja-possible' }[plujaHora(f)] || '');
    const h0 = new Date(f.hora).getHours();
    const hora = element('th', 'hora', `${h0}–${(h0 + 1) % 24}`);
    hora.scope = 'row';
    tr.append(hora);
    const avis = avisos[i];
    if (avis === null) tr.append(element('td', 'col-avis'));
    else if (avis) tr.append(franjaAvis(avis));
    const [textCel, iconaCel] = f.plou_ara ? [T('Plou ara'), 'i-umbrella'] : cel(f);
    const celCel = element('td', 'cel');
    const sol = solHora && solHora(f.hora);
    const linia = element('span', sol ? 'cel-text amb-sol' : 'cel-text');
    if (iconaCel) linia.append(icona(iconaCel));
    linia.append(sol ? element('span', 'cel-nom', textCel) : textCel);
    if (sol) linia.append(marcaSol(sol));
    celCel.append(linia);
    tr.append(celCel);
    tr.append(element('td', 'num', f.temperatura == null ? '' : `${Math.round(f.temperatura)}`));
    tr.append(element('td', 'num', f.pluja_mm >= 0.1 ? coma(f.pluja_mm) : '\u2013'));
    const prob = element('td', 'num prob');
    if (f.probabilitat != null) {
      const pct = Math.round(f.probabilitat * 100);
      prob.textContent = `${pct} %${f.segons_estacio ? '*' : f.segons_radar ? '\u2020' : ''}`;
      prob.style.setProperty('--prob', `${pct}%`);
    }
    tr.append(prob);
    tr.append(element('td', 'num', f.vent == null ? ''
      : `${Math.round(f.vent)}${f.ratxa ? ` (${Math.round(f.ratxa)})` : ''}`));
    cos.append(tr);
  });
  taula.append(cos);
  contenidor.append(taula);
  det.append(contenidor);
  // Plegada, la barra de l'avís no té alçada: s'ajusta en obrir-la.
  det.addEventListener('toggle', () => {
    obertsAMa.set(t.clau, det.open);
    ajustaFranges();
    posaBotoTot();
  });
  return det;
}

function taula(hores, mesurada, riscos, sol) {
  const ara = new Date();
  for (const f of hores) f.riscos_hora = riscosHora(f, riscos, ara);
  const trams = resumTrams(hores, ara, mesurada);
  if (!trams.length) return null;
  const sec = element('section', 'previsio');
  const cap = element('div', 'cap-previsio');
  const boto = element('button', 'boto-tot');
  boto.type = 'button';
  boto.id = 'boto-tot';
  boto.addEventListener('click', () => {
    const obrir = boto.dataset.accio === 'obre';
    try { localStorage.setItem(CLAU_TOT_OBERT, obrir ? '1' : '0'); } catch (_) {}
    for (const d of document.querySelectorAll('.tram-hores')) {
      d.open = obrir;
      obertsAMa.set(d.dataset.clau, obrir);
    }
    posaBotoTot();
  });
  cap.append(element('h2', 'perque', T('Previsió')), boto);
  sec.append(cap);
  const graf = grafica(hores);
  if (graf) sec.append(graf);
  const solHora = solPerHora(sol);
  trams.forEach((t) => sec.append(taulaTram(t, obertDeSortida(t), solHora)));
  // Les notes, plegades: només les que diuen alguna cosa de les hores d'ara.
  const visibles = trams.flatMap((t) => t.files);
  const notes = element('details', 'com notes-taula');
  notes.append(element('summary', null, T('Com es llegeix la previsió')));
  // Només què vol dir cada cosa; com es calcula, a «D'on surt» (Juanjo,
  // 12-10-2026: «dice cosas poco útiles … solo lo que significa»; ADR 0077).
  // Cada terme en negreta i què vol dir al costat (Juanjo, 13-10-2026: «usa
  // negritas… esto es muy rancio»).
  const llista = element('dl', 'llegenda');
  const terme = (nom, text, classe = null) => {
    const dt = element('dt');
    dt.append(classe ? element('span', classe, nom) : nom);
    llista.append(dt, element('dd', null, text));
  };
  // Què fer amb la xifra, amb els mateixos llindars que el cel de la taula
  // (PROB_POSSIBLE i PROB_PLUJA; Juanjo, 13-10-2026: «alguna indicación útil»).
  // El cel, amb els llindars de celNuvols i de plujaHora (Juanjo, 13-10-2026:
  // «no hay nada sobre el cel»; ADR 0088).
  terme(T('Cel'), T('Quina part del cel tapen els núvols: serè, menys del 20\u00a0%; poc ennuvolat, fins al 45\u00a0%; mig ennuvolat, fins al 70\u00a0%; molt ennuvolat, fins al 85\u00a0%, i cobert, més. Si la probabilitat de pluja arriba al 20\u00a0%, hi surt «possible pluja», i del 50\u00a0% amunt, la pluja. A l’hora en curs, el cel és el que s’observa a l’aeroport de Sabadell, si hi veu núvols.'));
  // La sortida i la posta del sol, amb les icones tal com surten a la taula.
  if (visibles.some((f) => solHora(f.hora))) {
    const dt = element('dt', 'sol-fila');
    dt.append(icona('i-sunrise'), icona('i-sunset'));
    llista.append(dt, element('dd', null, T('L’hora en què surt i es pon el sol, a la fila de l’hora en què passa.')));
  }
  terme(T('Prob.'), T('La probabilitat que plogui en aquella hora. Per sota del 10\u00a0%, no s’espera pluja; del 10 al 20\u00a0%, és poc probable, però pot caure algun ruixat; del 20 al 50\u00a0%, pot ploure: si surts, porta paraigua; del 50\u00a0% amunt, el més probable és que plogui. Per exemple, un 40\u00a0% vol dir que, de cada 10 vegades que la previsió dona un 40\u00a0% per a una hora, en 4 acaba plovent.'));
  terme(T('Pluja'), T('Els mil·límetres que caurien si plou.'));
  if (visibles.some((f) => f.segons_estacio)) terme('*', T('Hi compta la pluja que cau ara al barri.'));
  if (visibles.some((f) => f.segons_radar)) terme('\u2020', T('Hi compta la pluja que el radar veu acostar-se.'));
  // La part alta, només si algun tram la diu, amb l'etiqueta tal com surt
  // (ADR 0087; Juanjo, 13-10-2026: «por qué ha desaparecido la explicación»).
  if (trams.some((t) => arrodoneixAlta(t.difAlta) || t.fenomens.some(([nom]) => nom === NOM_FENOMEN.glaçadaRiera()))) {
    terme('+1, +2…', T('Les temperatures són les de vora la riera, la zona més freda del barri. La xifra diu quants graus més sol fer a la part alta, que canvia segons l’hora del dia i l’època de l’any: surt del que han mesurat les estacions del barri a cada hora els últims 30 dies.'), 'alta');
  }
  if (visibles.some((f) => avisHora(f))) terme(T('Barra de color'), T('Hores amb avís, del color del nivell.'));
  terme(T('Vent'), T('La mitjana en km/h i, entre parèntesis, les ratxes.'));
  // Si la taula travessa un canvi d'hora, la franja de 2 a 3 surt dues
  // vegades (octubre) o no hi és (març): es diu per què (Juanjo, 13-10-2026).
  const desfasos = visibles.map((f) => new Date(f.hora).getTimezoneOffset());
  if (new Set(desfasos).size > 1) {
    terme(T('Canvi d’hora'), desfasos[desfasos.length - 1] > desfasos[0]
      ? T('Aquesta nit el rellotge es retarda una hora: a les 3 tornen a ser les 2, i la franja de 2 a 3 surt dues vegades.')
      : T('Aquesta nit el rellotge s’avança una hora: a les 2 passen a ser les 3, i la franja de 2 a 3 no hi és.'));
  }
  // La taula arriba fins a les 21 h de demà (ADR 0041): més enllà d'un dia, menys fina.
  if (visibles.length && new Date(visibles[visibles.length - 1].fins) - new Date() > 24 * 3600e3) {
    terme(T('Demà'), T('Més enllà de 24 hores, la previsió és menys segura.'));
  }
  notes.append(llista);
  sec.append(notes);
  return sec;
}

// --- La gràfica de la previsió (Juanjo, 16-10-2026: «un resumen visual …
// muy visual y muy claro»). Un meteograma, de l'hora en curs fins al final de
// la taula: la franja de perill, el cel cada 3 h, la temperatura i la
// probabilitat de pluja, amb el mateix eix d'hores. Les dades, les de la
// taula; la gràfica no diu res que no sigui a sota. ---
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

function grafica(hores) {
  const ara = new Date();
  const files = (hores || []).filter((f) => new Date(f.fins) > ara && f.temperatura != null);
  if (files.length < 6) return null;
  const fig = element('figure', 'grafica');
  fig.append(element('figcaption', 'visualment-amagat',
    T('Gràfica de la previsió: perill, cel, temperatura i probabilitat de pluja. Les mateixes dades són a les taules de sota.')));
  fig._files = files;
  return fig;
}

function dibuixaGrafica(fig) {
  const files = fig._files;
  const W = fig.clientWidth;
  if (!W) return;
  const n = files.length;
  const col = W / n;
  const x = (i) => i * col;
  const pas = col >= 28 ? 2 : 3;
  const hora = (f) => new Date(f.hora).getHours();
  const trams = tramsAvis(files);
  const ambAvis = trams.some(Boolean);
  // Les files de la gràfica, de dalt a baix.
  const yAvis = 0;
  const hAvis = ambAvis ? 22 : 0;
  const yDia = hAvis + (ambAvis ? 6 : 0);
  const yCel = yDia + 16;
  const hCel = 28;
  // La temperatura i la pluja comparteixen la zona: les barres darrere de la
  // línia, com als meteogrames habituals (Juanjo, 16-10-2026).
  // El cel queda a part, a dalt: les barres no hi arriben (Juanjo, 16-10-2026).
  // Sota cada icona, la temperatura d'aquella hora (Juanjo, 16-10-2026: «no
  // quedaría bien la temperatura bajo el cielo?»).
  const yXifra = yCel + hCel + 13;
  const yTemp = yXifra + 12;
  const hTemp = 100;
  const yPluja = yTemp;
  const hPluja = hTemp;
  const yEix = yPluja + hPluja + 16;
  const H = yEix + 4;
  const g = svg('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' });
  // A la pàgina des del principi: el text de la franja s'ha de poder mesurar.
  fig.querySelector('svg')?.remove();
  fig.prepend(g);

  // La nit, ombrejada, de la posta a la sortida (a mitja hora de cada tram),
  // en un sol rectangle per nit.
  const esNit = files.map((f) => alturaSol(new Date(new Date(f.hora).getTime() + 18e5)) < 0);
  for (let i = 0; i < n; i++) {
    if (!esNit[i] || (i && esNit[i - 1])) continue;
    let j = i;
    while (j < n && esNit[j]) j++;
    g.append(svg('rect', { class: 'g-nit', x: x(i), y: yCel - 2, width: x(j) - x(i), height: yPluja + hPluja - yCel + 2 }));
  }

  // Mitjanit: la ratlla que separa els dies, i el nom de cada dia.
  g.append(svg('text', { class: 'g-dia', x: 2, y: yDia + 11 }, T('Avui')));
  files.forEach((f, i) => {
    if (i && hora(f) === 0) {
      g.append(svg('line', { class: 'g-mitjanit', x1: x(i), x2: x(i), y1: yDia, y2: yPluja + hPluja }));
      g.append(svg('text', { class: 'g-dia', x: x(i) + 4, y: yDia + 11 }, T('Demà')));
    }
  });

  // La franja de perill, del color del nivell, amb el text que hi càpiga.
  trams.forEach((t, i) => {
    if (!t) return;
    const grup = svg('g', { class: `g-avis ${t.nivell}` });
    const amplada = t.hores * col;
    grup.append(svg('rect', { x: x(i) + 1, y: yAvis, width: amplada - 2, height: hAvis, rx: 4 }));
    const text = svg('text', { x: x(i) + 6, y: yAvis + 15 });
    grup.append(text);
    g.append(grup);
    let cap = false;
    for (const t2 of [textPerillCurt(t), textPerillCurt(t, false)]) {
      text.textContent = t2;
      if (text.getComputedTextLength() <= amplada - 12) { cap = true; break; }
    }
    // Si no hi cap (un avís de poques hores), el text va al costat de la
    // franja, a l'esquerra si hi ha lloc i si no, a la dreta.
    if (!cap) {
      text.classList.add('fora');
      for (const t2 of [textPerillCurt(t), textPerillCurt(t, false)]) {
        text.textContent = t2;
        const llarg = text.getComputedTextLength();
        if (llarg + 6 <= x(i)) { text.setAttribute('x', x(i) - 4); text.setAttribute('text-anchor', 'end'); break; }
        if (x(i) + amplada + 4 + llarg <= W) { text.setAttribute('x', x(i) + amplada + 4); break; }
        text.textContent = '';
      }
    }
    const complet = textPerill(t);
    grup.append(svg('title', {}, complet));
    grup.addEventListener('click', () => avisBreu(`${complet}.`));
  });

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
  const textAra = svg('text', { class: 'g-hora ara', x: 1, y: yEix }, T('Ara'));
  g.append(textAra);
  // Cap hora a sobre d'«Ara» («Ahora» és més llarg): mesurat a la pàgina.
  const finsAra = textAra.getComputedTextLength() + 14;
  // Una marca a cada hora: llarga i amb el número a les que toquen; curta i
  // sense número a la resta (Juanjo, 16-10-2026).
  files.forEach((f, i) => {
    if (!i) return;
    const gran = hora(f) % pas === 0;
    g.append(svg('line', { class: gran ? 'g-marca' : 'g-marca petita', x1: x(i), x2: x(i),
      y1: yPluja + hPluja, y2: yPluja + hPluja + (gran ? 4 : 2) }));
    if (!gran || x(i) < finsAra || x(i) > W - 8) return;
    g.append(svg('text', { class: 'g-hora', x: x(i), y: yEix, 'text-anchor': 'middle' }, String(hora(f))));
  });
  // Tocar una hora (o passar-hi el ratolí): la seva pluja en un rètol, perquè
  // els mil·límetres de cada barra no hi caben (Juanjo, 16-10-2026: «solo pone
  // la lluvia del mayor?»). Es treu tocant fora o la mateixa hora.
  const retol = svg('g', { class: 'g-retol' });
  let actiu = null;
  const amaga = () => {
    actiu = null;
    retol.replaceChildren();
  };
  const mostra = (i) => {
    const f = files[i];
    // Els mm com a la xifra de la barra: sense decimals a partir de 10.
    const v = f.pluja_mm || 0;
    const mm = v >= 10 ? String(Math.round(v)) : coma(Math.round(v * 10) / 10);
    const text = f.probabilitat == null
      ? T`${hora(f)}\u00a0h · ${mm}\u00a0mm`
      : T`${hora(f)}\u00a0h · ${mm}\u00a0mm · ${Math.round(f.probabilitat * 100)}\u00a0%`;
    actiu = i;
    retol.replaceChildren(svg('rect', { class: 'g-retol-columna', x: x(i), y: yCel - 2, width: col,
      height: yPluja + hPluja - yCel + 2 }));
    const t = svg('text', { class: 'g-retol-text', 'text-anchor': 'middle' }, text);
    const fons = svg('rect', { class: 'g-retol-fons', rx: 4 });
    retol.append(fons, t);
    const llarg = t.getComputedTextLength();
    const cx = Math.min(Math.max(x(i) + col / 2, llarg / 2 + 6), W - llarg / 2 - 6);
    const dalt_ = plujaGrafica(f) ? dalt(f) : base;
    const ty = Math.max(dalt_ - 10, yTemp + 10);
    t.setAttribute('x', cx);
    t.setAttribute('y', ty);
    Object.entries({ x: cx - llarg / 2 - 5, y: ty - 13, width: llarg + 10, height: 18 })
      .forEach(([k, v]) => fons.setAttribute(k, v));
  };
  files.forEach((f, i) => {
    const zona = svg('rect', { class: 'g-zona', x: x(i), y: yCel - 2, width: col, height: yPluja + hPluja - yCel + 2 });
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
  ll.append(clau('m-nit', T('Nit')));
  fig.append(ll);
}

function dibuixaGrafiques() {
  for (const fig of document.querySelectorAll('figure.grafica')) dibuixaGrafica(fig);
}
addEventListener('resize', dibuixaGrafiques);
// Tocar fora de la gràfica treu el rètol de l'hora.
addEventListener('click', () => {
  for (const fig of document.querySelectorAll('figure.grafica')) fig._amaga?.();
});

// El botó diu el que farà: desplegar-ho tot si en queda algun de plegat.
function posaBotoTot() {
  const boto = $('boto-tot');
  if (!boto) return;
  const obre = [...document.querySelectorAll('.tram-hores')].some((d) => !d.open);
  boto.dataset.accio = obre ? 'obre' : 'plega';
  boto.replaceChildren(icona(obre ? 'i-chevrons-up-down' : 'i-chevrons-down-up'), obre ? T('Desplega-ho tot') : T('Plega-ho tot'));
}

// En imprimir, tots els trams oberts; després, com estaven.
addEventListener('beforeprint', () => {
  for (const d of document.querySelectorAll('.previsio details:not([open])')) {
    d.dataset.plegat = '1';
    d.open = true;
  }
});
addEventListener('afterprint', () => {
  for (const d of document.querySelectorAll('.previsio details[data-plegat]')) {
    d.open = false;
    delete d.dataset.plegat;
  }
});

// Tots els avisos vigents en un sol bloc, a dalt; les notes, després. Es
// torna a pintar quan arriba l'historial de «Perill», per la riera (ADR 0076).
let DADES_AVISOS = null;
function pintaAvisos(dades) {
  const avisos = $('avisos');
  avisos.querySelector('.avisos-actius')?.remove();
  const actius = blocAvisos(dades);
  if (actius) avisos.prepend(actius);
}
function repintaAvisos() {
  if (DADES_AVISOS && !dadesVelles(DADES_AVISOS)) pintaAvisos(DADES_AVISOS);
}

// La línia «Actualitzat a les… · propera: …», al peu de la targeta «Ara» (ADR
// 0094): la pàgina en té una sola hora. El node és el de casa.html; com que
// #casa es buida a cada pintada, es torna a col·locar cada vegada.
let HORARI = null;

function pinta(dades) {
  const cont = $('casa');
  HORARI = HORARI || $('horari');
  cont.replaceChildren();
  // Dades de fa massa: només l'avís i on mirar (ADR 0031).
  if (dadesVelles(dades)) {
    $('avisos').replaceChildren();
    DADES_AVISOS = dades;
    cont.append(blocDadesVelles(dades), HORARI);
    pintaHorari(dades);
    posaVersio(dades.versio);
    return;
  }
  DADES_AVISOS = dades;
  $('avisos').replaceChildren();
  pintaAvisos(dades);
  const avisos = $('avisos');
  if (dades.previsio_de) avisos.append(element('p', 'avis', textPrevisioAnterior(dades)));
  if (dades.models && dades.models.no_encerten) {
    const m = dades.models;
    avisos.append(element('p', 'avis', T`Avui els models no veuen aquesta pluja: en les darreres ${m.hores} hores han caigut ${coma(m.mesurada_mm)}\u00a0mm a Montflorit i en preveien ${coma(m.prevista_mm)}. Les primeres hores de la taula parteixen del que mesura l\u2019estació; per a la resta, fes més cas dels avisos.`));
  }
  const ara = dades.ara_casa && blocAra(dades.ara_casa, dades.radar, dades.vent, dades.veines, dades.hores);
  if (ara) {
    ara.append(HORARI);
    cont.append(ara);
  } else {
    cont.append(HORARI);
  }
  if (OFERTA_AVISOS) cont.append(OFERTA_AVISOS);
  const resum = blocsResum(dades);
  cont.append(...resum);
  const previsio = dades.hores && taula(dades.hores, dades.temperatura_mesurada, dades.riscos, dades.sol);
  if (previsio) {
    cont.append(previsio);
    dibuixaGrafiques();
    ajustaFranges();
    posaBotoTot();
  }
  pintaHorari(dades);
  posaVersio(dades.versio);
}

// L'oferta d'avisos a qui té la web instal·lada (Juanjo, 12-10-2026; ADR 0080):
// el navegador no deixa enviar notificacions sense permís, i el permís només
// es pot demanar quan la persona toca un botó. Qui instal·la la web la vol a
// mà: en obrir-la instal·lada, i si encara no té els avisos, una targeta sota
// «Ara», sense finestra, amb un sol toc per rebre els de perill i la riera
// (AVISOS_PER_DEFECTE). «Ara no» la treu per sempre en aquest dispositiu.
const CLAU_OFERTA_AVISOS = 'meteo.oferta-avisos';
let OFERTA_AVISOS = null;

function webInstallada() {
  return matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
}

async function calOfertaAvisos() {
  if (!webInstallada() || !('serviceWorker' in navigator) || !('PushManager' in window)
      || !('Notification' in window) || Notification.permission === 'denied') return false;
  try { if (localStorage.getItem(CLAU_OFERTA_AVISOS) === 'no') return false; } catch (_) {}
  const registre = await navigator.serviceWorker.ready;
  return !(await registre.pushManager.getSubscription());
}

function targetaOfertaAvisos() {
  const sec = element('section', 'targeta oferta-avisos');
  sec.setAttribute('aria-label', T('Avisos de perill'));
  const estat = element('p', 'oferta-estat');
  estat.setAttribute('role', 'status');
  const si = element('button', 'boto', T('Activa-ho'));
  // Qui en vol uns altres, a «Avisos», on es trien (Juanjo, 12-10-2026: «que se
  // puede configurar en la sección avisos, con su botón»).
  const tria = element('a', 'boto secundari', T('Tria quins'));
  tria.href = 'avisos.html';
  const no = element('button', 'boto secundari', T('Ara no'));
  si.type = 'button';
  no.type = 'button';
  const botons = element('p', 'oferta-botons');
  botons.append(si, tria, no);
  sec.append(element('p', 'oferta-titol', T('Avisos de perill')),
    element('p', null, T('Riera, incendis, avisos oficials i temps extrem a Montflorit, al moment.')), botons, estat);
  no.addEventListener('click', () => {
    try { localStorage.setItem(CLAU_OFERTA_AVISOS, 'no'); } catch (_) {}
    sec.remove();
    OFERTA_AVISOS = null;
  });
  si.addEventListener('click', async () => {
    si.disabled = true;
    try {
      if ((await Notification.requestPermission()) !== 'granted') {
        estat.textContent = T('El navegador té bloquejades les notificacions d’aquesta web. Permet-les a la configuració del navegador (al cadenat, al costat de l’adreça) i torna-ho a provar.');
        return;
      }
      const subscripcio = await subscriuAvisos(await navigator.serviceWorker.ready);
      await cridaAvisos({ accio: 'desa', subscripcio: subscripcio.toJSON(), avisos: AVISOS_PER_DEFECTE, resum: '', nit: false,
        idioma: document.documentElement.lang === 'es' ? 'es' : 'ca' });
      botons.remove();
      estat.textContent = T('Fet: t’arribaran els avisos de perill i de la riera. Per triar-ne més, toca la campana.');
      OFERTA_AVISOS = null;
    } catch (_) {
      estat.textContent = T('No s’han pogut activar els avisos. Torna-ho a provar d’aquí a una estona.');
    } finally {
      si.disabled = false;
    }
  });
  return sec;
}

calOfertaAvisos().then((cal) => {
  if (!cal) return;
  OFERTA_AVISOS = targetaOfertaAvisos();
  const ara = document.querySelector('#casa .targeta.ara');
  if (ara) ara.after(OFERTA_AVISOS);
}).catch(() => {});

carrega(FITXER_DADES, pinta, () => {
  $('casa').replaceChildren(element('p', 'avis', T('No s’ha pogut carregar la previsió. Torna-ho a provar d’aquí a una estona.')));
});
