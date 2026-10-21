// SPDX-License-Identifier: AGPL-3.0-or-later
// Same-origin radar snapshots; official marine widgets load only on request.
const LPA_RADAR_URL = 'https://www.aemet.es/es/eltiempo/observacion/radar?w=1';
function lpaLink(text, href) {
  const link = lpaText('a', text); link.href = href; return link;
}
function lpaRadar(box, radar, expired) {
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
  box.append(lpaText('p','Gráficos oficiales de Puertos del Estado. Se consultan directamente al cargarlos; no dependen del despliegue de esta web.'));
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
    card.append(lpaText('h3',name),lpaText('p',detail),button,document.createTextNode(' '),lpaLink('Abrir en PORTUS',url));
    button.addEventListener('click',()=>{
      const frame=document.createElement('iframe');frame.title=name;frame.src=url;
      frame.className='lpa-portus-frame';frame.referrerPolicy='no-referrer';frame.loading='lazy';
      card.append(frame);button.remove();
      card.append(lpaText('p','Si el gráfico no carga o muestra datos antiguos, utilice «Abrir en PORTUS». Un gráfico vacío no significa mar en calma.','nota'));
    },{once:true});
    box.append(card);
  }
  box.append(lpaText('p','Las boyas de Las Palmas Este (1414) y Gran Canaria (2442) figuraban con «Sin trasmisión» y «En tierra» en la comprobación del 20/10/2026. Consulte PORTUS para su estado actual.','nota'));
  box.append(lpaText('p','Al cargar un gráfico se establece una conexión con Puertos del Estado, que aplica sus condiciones de uso y privacidad.'));
}
const lpaMarineBox=document.getElementById('lpa-marine');if(lpaMarineBox)lpaMarine(lpaMarineBox);
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
