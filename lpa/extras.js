// SPDX-License-Identifier: AGPL-3.0-or-later
// Same-origin radar snapshots; official marine widgets load only on request.
const LPA_RADAR_URL = 'https://www.aemet.es/es/eltiempo/observacion/radar?w=1';
function lpaLink(text, href) {
  const link = lpaText('a', text); link.href = href; return link;
}
function lpaRadar(box, radar, expired) {
  if(box.dataset.compact==='true') {
    box.replaceChildren(lpaText('h2','Radar de Canarias'));
    const frame=radar?.frames?.at(-1);
    if(frame&&/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(frame.image)&&radar.status!=='unavailable') {
      const fresh=!expired&&lpaStationStatus(radar)==='ok';
      box.append(lpaText('p',`${fresh?'Última imagen':'Imagen antigua'} · ${new LpaDate(frame.observed_at).toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'})} · AEMET`,fresh?'lpa-muted':'avis'));
      const link=lpaLink('','radar.html'),image=document.createElement('img');image.className='lpa-radar-image';image.src=frame.image;image.width=1000;image.height=580;image.alt='Abrir el radar de Canarias con su fecha y escala';link.append(image);box.append(link);
      box.append(lpaText('p','Ecos en altura · no confirma lluvia en el suelo','lpa-muted'));
    } else box.append(lpaText('p','Radar no disponible.','nota'));
    box.append(lpaLink('Ver secuencia, escala y mar →','radar.html'));return;
  }
  box.replaceChildren(lpaText('h2','Radar de Canarias · AEMET'));
  box.append(lpaText('p','Reflectividad en dBZ: ecos detectados en altura, no lluvia medida en una estación. No se calcula una hora de llegada.'));
  const frames = radar?.frames || [];
  const valid = frames.filter(f => /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(f.image));
  if (!valid.length || radar.status === 'unavailable') {
    box.append(lpaText('p','No se pudo obtener una imagen válida del radar. No equivale a ausencia de lluvia.','avis'));
  } else {
    const fresh = !expired && lpaStationStatus(radar) === 'ok';
    if (!fresh) box.append(lpaText('p','Radar antiguo: estas imágenes no representan la situación actual.','avis'));
    const stamp = lpaText('p',''); stamp.setAttribute('aria-live','polite');
    const image = document.createElement('img');
    image.className = 'lpa-radar-image'; image.width=1000; image.height=580;
    function show(index) {
      const frame = valid[index];
      const date = new LpaDate(frame.observed_at).toLocaleString('es',{dateStyle:'short',timeStyle:'short'});
      stamp.textContent = `${date} · hora canaria · imagen ${Number(index)+1} de ${valid.length}`;
      image.alt = `Radar AEMET de Canarias del ${date}, con Las Palmas señalada. Consulte la escala de reflectividad.`;
      image.src = frame.image;
    }
    box.append(stamp,image);
    if (valid.length>1) {
      const label = lpaText('label','Imagen de la secuencia'); label.htmlFor='lpa-radar-frame';
      const range = document.createElement('input'); range.type='range';range.id='lpa-radar-frame';
      range.min=0;range.max=valid.length-1;range.value=valid.length-1;range.step=1;
      range.addEventListener('input',()=>show(Number(range.value)));
      box.append(label,range);
    }
    show(valid.length-1);
    const legend = lpaText('ul','','lpa-radar-legend'); legend.setAttribute('aria-label','Escala de reflectividad');
    for (const entry of radar.legend || []) {
      const item = lpaText('li',entry.label);
      if (/^#[0-9a-f]{6}$/i.test(entry.color)) {
        const swatch = lpaText('span','','lpa-swatch');swatch.style.backgroundColor=entry.color;swatch.setAttribute('aria-hidden','true');item.prepend(swatch);
      }
      legend.append(item);
    }
    box.append(legend,lpaText('p',radar.detail,'nota'));
  }
  box.append(lpaLink('Abrir el radar oficial de AEMET',LPA_RADAR_URL),lpaText('p','Imágenes y cartografía: AEMET. El marcador identifica la ciudad, no un pluviómetro.','nota'));
}
function lpaMarine(box) {
  box.replaceChildren(lpaText('h2','Mar y puerto · PORTUS'));
  box.append(lpaText('p','Datos y previsiones de Puertos del Estado.','lpa-muted'));
  const items = [
    ['Nivel del mar · mareógrafo de Las Palmas 2','https://portus.puertos.es/PortusData/rtChart?station=3450&params=SeaLevel&locale=es',
     'Medición en el puerto. Su referencia vertical es la del gráfico; no se interpreta como altura de las olas ni como predicción de pleamar.'],
    ['Viento · mareógrafo de Las Palmas 2','https://portus.puertos.es/PortusData/rtChart?station=3450&params=WindSpeed,WindSpeedMax&dirParams=WindDir&locale=es',
     'Viento medido en el puerto; no representa todos los barrios. Compruebe las unidades y la hora en PORTUS.'],
    ['Presión · mareógrafo de Las Palmas 2','https://portus.puertos.es/PortusData/rtChart?station=3450&params=AirPressure&locale=es',
     'Presión medida en el puerto. No se mezcla con presiones de otras referencias.'],
    ['Oleaje previsto · entorno de Gran Canaria','https://portus.puertos.es/#/predictionWidget?resourceId=oleaje-atl&var=WAVE&zoom=8&lat=28.1&lon=-15.4&vec=true&locale=es',
     'Predicción de un modelo, no observación de una boya ni indicación del estado de baño de Las Canteras.'],
  ];
  for (const [name,url,detail] of items) {
    const card=lpaText('article','','lpa-station');
    const button=lpaText('button','Cargar gráfico de PORTUS');button.type='button';
    const info=document.createElement('details');info.append(lpaText('summary','Qué muestra'),lpaText('p',detail));
    card.append(lpaText('h3',name),button,document.createTextNode(' '),lpaLink('Abrir en PORTUS',url),info);
    button.addEventListener('click',()=>{
      const frame=document.createElement('iframe');frame.title=name;frame.src=url;
      frame.className='lpa-portus-frame';frame.referrerPolicy='no-referrer';frame.loading='lazy';
      card.append(frame);button.remove();
      card.append(lpaText('p','Si el gráfico no carga o muestra datos antiguos, utilice «Abrir en PORTUS». Un gráfico vacío no significa mar en calma.','nota'));
    },{once:true});
    box.append(card);
  }
  const more=document.createElement('details');more.append(lpaText('summary','Boyas y privacidad'),
    lpaText('p','Las boyas de Las Palmas Este (1414) y Gran Canaria (2442) figuraban con «Sin trasmisión» y «En tierra» el 20/10/2026. Consulte PORTUS para su estado actual.'),
    lpaText('p','Al cargar un gráfico se conecta con Puertos del Estado, que aplica sus condiciones de uso y privacidad.'));box.append(more);
}
function lpaMobility(box) {
  box.replaceChildren(lpaText('h2','Guaguas Municipales'));
  box.append(lpaText('p','Las llegadas en tiempo real dentro de esta web están pendientes: el acceso automático no ha proporcionado datos verificables. Consulte el servicio oficial para saber cuánto falta.','nota'));
  box.append(lpaLink('Consultar Próxima Guagua','https://www.guaguas.com/lineas/proxima-guagua'),document.createTextNode(' · '),
    lpaLink('Incidencias del servicio','https://www.guaguas.com/lineas/estado-del-servicio'),document.createTextNode(' · '),
    lpaLink('Planear una ruta','https://www.guaguas.com/lineas/planea-tu-ruta'));
  const details=document.createElement('details');details.append(lpaText('summary','Códigos de algunas paradas de referencia'));
  const list=document.createElement('ul');
  for(const [code,name,line] of [['8','León y Castillo (pl. de La Feria)','1'],['3','Rafael Cabrera (San Telmo)','1'],['944','Manuel Becerra (Puerto)','21'],['423','Auditorio','32']]) {
    const item=lpaText('li',`${name} · parada ${code} · `);
    item.append(lpaLink(`Ver línea ${line}`,`https://www.guaguas.com/lineas/${line}`));list.append(item);
  }
  details.append(list,lpaText('p','Introduzca el código en Próxima Guagua. Un mismo intercambiador tiene varias paradas y sentidos; compruebe el poste y su línea.','nota'));box.append(details);
}
const lpaMarineBox=document.getElementById('lpa-marine');if(lpaMarineBox)lpaMarine(lpaMarineBox);
const lpaMobilityBox=document.getElementById('lpa-mobility');if(lpaMobilityBox)lpaMobility(lpaMobilityBox);
const lpaRadarBox=document.getElementById('lpa-radar');
if(lpaRadarBox) {
  let loading=false;
  const refresh=async()=>{
    if(loading)return; loading=true;
    try {
      const data=await llegeixDades('montflorit.json');
      lpaRadar(lpaRadarBox,data.lpa?.radar,dadesVelles(data));
    } catch {lpaRadar(lpaRadarBox,null,true);}
    finally {loading=false;}
  };
  refresh();
  setInterval(()=>{if(document.visibilityState==='visible')refresh();},300000);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refresh();});
}
