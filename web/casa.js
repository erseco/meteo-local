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


// Barra vertical del color de l'avís al llarg de les hores que cobreix. El
// text, tan llarg com hi càpiga; el complet, per als lectors de pantalla.
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
  const graf = grafica(hores);
  const botons = element('div', 'cap-previsio-botons');
  // La gràfica en gran, amb les seves opcions, que valen per a tota la web
  // (Juanjo, 17-10-2026: «no me gusta esa doble flecha… o un botón de
  // configuración… decide tú»): «Opcions», amb la icona d'ajustos de Lucide.
  if (graf) {
    const amplia = element('button', 'boto-tot');
    amplia.type = 'button';
    amplia.title = T('Opcions de la gràfica');
    amplia.setAttribute('aria-label', T('Opcions de la gràfica'));
    // Al mòbil, només la icona: amb el text, els dos botons no caben al costat del títol.
    amplia.append(icona('i-sliders-horizontal'), element('span', 'text-amplia', T('Opcions')));
    amplia.addEventListener('click', vistaGrafica);
    botons.append(amplia);
  }
  botons.append(boto);
  cap.append(element('h2', 'perque', T('Previsió')), botons);
  sec.append(cap);
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
  GENERAT_GRAFICA = dades.generat;
  AVISOS_GRAFICA = dades;
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
    obreGraficaDeLEnllac();
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
