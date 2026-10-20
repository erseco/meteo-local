// SPDX-License-Identifier: AGPL-3.0-or-later
// Compact, accessible seven-day overview; all values retain their provenance.
const lpaDayKey=time=>new LpaDate(time).toLocaleDateString('en-CA');
const lpaTime=time=>new LpaDate(time).toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'});
function lpaSky(code) {
  if(code==null)return ['Sin previsión','cloud'];
  if(code===0)return ['Despejado','sun'];
  if(code<=2)return [code===1?'Poco nuboso':'Intervalos nubosos','mixed'];
  if(code===3)return ['Nuboso','cloud'];
  if(code===45||code===48)return ['Niebla','cloud'];
  if(code>=95)return ['Tormenta','storm'];
  if([71,73,75,77,85,86].includes(code))return ['Nieve','rain'];
  return ['Lluvia','rain'];
}
function lpaSkyIcon(code,night=false) {
  const [name,sky]=lpaSky(code),kind=night&&sky==='sun'?'moon':night&&sky==='mixed'?'cloud':sky,ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');
  for(const [key,value] of Object.entries({viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','stroke-width':'1.7','stroke-linecap':'round','stroke-linejoin':'round',role:'img','aria-label':name+(night?' de noche':'')}))svg.setAttribute(key,value);
  const paths=kind==='moon'?['M20 15A8 8 0 0 1 9 4a8 8 0 1 0 11 11']:
    kind==='sun'?['M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4','M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0']:
    [...(kind==='mixed'?['M18 2v2m4 3h-2m-6-4 1 1m5 6a3 3 0 1 0-5-4']:[]),
     'M5 16a5 5 0 1 1 9-5 3.6 3.6 0 1 1 4 5',...(['cloud','mixed'].includes(kind)?[]:kind==='storm'?['m13 15-3 4h4l-3 4']:['M8 18v3m5-3v3m5-3v3'])];
  for(const d of paths){const p=document.createElementNS(ns,'path');p.setAttribute('d',d);svg.append(p);}return svg;
}
function lpaMetric(label,value,unit) {
  const box=lpaText('div','','lpa-metric');
  box.append(lpaText('span',label),lpaText('strong',lpaFormat(value)+(value==null?'':unit)));return box;
}
function lpaScrollable(node) {
  node.tabIndex=0;node.setAttribute('role','region');
  let drag=null,blockClick=false;
  node.addEventListener('pointerdown',e=>{
    if(e.pointerType!=='mouse'||e.button!==0)return;
    drag={x:e.clientX,left:node.scrollLeft,id:e.pointerId,moved:false};blockClick=false;
  });
  node.addEventListener('pointermove',e=>{
    if(!drag||!(e.buttons&1))return;
    const distance=e.clientX-drag.x;
    if(Math.abs(distance)>6){drag.moved=true;node.setPointerCapture(e.pointerId);node.classList.add('is-dragging');}
    if(drag.moved){node.scrollLeft=drag.left-distance;e.preventDefault();}
  });
  const stop=()=>{if(drag)blockClick=drag.moved;drag=null;node.classList.remove('is-dragging');};
  node.addEventListener('pointerup',stop);node.addEventListener('pointercancel',stop);
  node.addEventListener('lostpointercapture',stop);
  node.addEventListener('click',e=>{if(blockClick){e.preventDefault();e.stopPropagation();blockClick=false;}},true);
  node.addEventListener('keydown',e=>{
    if(e.target!==node)return;
    if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) {
      e.preventDefault();
      if(e.key==='Home'||e.key==='End')node.scrollLeft=e.key==='Home'?0:node.scrollWidth;
      else node.scrollLeft+=e.key==='ArrowLeft'?-180:180;
    }
  });
}
function lpaDashboard(data) {
  const target=document.getElementById('casa');target.replaceChildren();
  if(dadesVelles(data)||!data.hores?.length) {
    target.append(lpaText('p','Datos caducados. Consulte AEMET para conocer la situación actual.','avis'),
      lpaLink('Abrir AEMET','https://www.aemet.es/es/eltiempo/prediccion/municipios/palmas-de-gran-canaria-las-id35016'));
    return;
  }
  const updated=document.getElementById('lpa-updated');
  if(updated)updated.textContent=`Actualizado ${lpaTime(data.generat)} · hora canaria`;
  const notice=lpaText('div','','lpa-alert-summary');
  if(data.avisos===null)notice.append(lpaLink('Avisos sin comprobar · consultar AEMET','https://www.aemet.es/es/eltiempo/prediccion/avisos?l=659001'));
  else if(data.avisos.length) {
    notice.classList.add('avis');notice.append(lpaLink(`${data.avisos.length} aviso${data.avisos.length===1?'':'s'} de AEMET · Ver detalles`,'perill.html'));
  } else notice.append(lpaText('span','Sin avisos en la zona · AEMET','lpa-badge'));
  target.append(notice);
  const stations=data.lpa?.observations?.stations||[];
  const station=stations.find(s=>s.id==='C659M'&&lpaStationStatus(s)==='ok');
  const current=data.lpa?.current_model;
  const hero=lpaText('section','','lpa-hero');hero.setAttribute('aria-label','Tiempo actual');
  const headline=lpaText('div');
  headline.append(lpaText('h2','Ahora'),lpaText('p',station?'Plaza de la Feria':'Las Palmas', 'lpa-muted'));
  const temperature=station?.temperature_c??current?.temperature_2m;
  headline.append(lpaText('p',lpaFormat(temperature)+(temperature==null?'':'°'),'lpa-temperature'));
  const source=lpaLink(station?'Medido · AEMET':'Estimación · Open-Meteo',station?station.url:'https://open-meteo.com/');
  source.className='lpa-badge';headline.append(source);
  if(station)headline.append(lpaText('p',`${lpaTime(station.observed_at)} · hora canaria`,'lpa-muted'));
  const metrics=lpaText('div','','lpa-hero-metrics');
  metrics.append(lpaMetric('Viento',station?station.wind_kmh:current?.wind_speed_10m,' km/h'),
    lpaMetric('Humedad',station?station.relative_humidity_pct:current?.relative_humidity_2m,' %'));
  const next=data.hores[0];
  metrics.append(lpaMetric('Lluvia esta hora',next.probabilitat==null?null:next.probabilitat*100,' %'));
  metrics.append(lpaText('small','Lluvia: previsión de Open-Meteo.','lpa-muted'));
  hero.append(headline,metrics);target.append(hero);
  const days=(data.lpa?.daily_forecast||[]).slice(0,7);
  const week=lpaText('section','','targeta lpa-week');
  const heading=lpaText('div','','lpa-section-heading');
  heading.append(lpaText('h2',`Próximos ${days.length} días`),lpaText('span','Open-Meteo · previsión','lpa-badge'));week.append(heading);
  const strip=lpaText('div','','lpa-days');strip.setAttribute('aria-label','Elegir día de la previsión');lpaScrollable(strip);
  const hourly=lpaText('section','','targeta lpa-hourly');
  const hourHeading=lpaText('h2','Por horas');const controls=lpaText('div','','lpa-hour-controls');
  const previous=lpaText('button','←');previous.type='button';previous.setAttribute('aria-label','Horas anteriores');
  const forward=lpaText('button','→');forward.type='button';forward.setAttribute('aria-label','Horas siguientes');
  controls.append(previous,forward);
  const hourHeader=lpaText('div','','lpa-section-heading');hourHeader.append(hourHeading,controls);hourly.append(hourHeader);
  const hours=lpaText('div','','lpa-hours');hours.setAttribute('aria-label','Previsión por horas; desliza para ver más');lpaScrollable(hours);
  previous.addEventListener('click',()=>{hours.scrollLeft-=hours.clientWidth*.75;});
  forward.addEventListener('click',()=>{hours.scrollLeft+=hours.clientWidth*.75;});
  const hint=lpaText('p','','lpa-muted lpa-scroll-hint');hourly.append(hours,hint);
  function updateControls() {
    const overflow=hours.scrollWidth>hours.clientWidth+2;
    previous.disabled=!overflow||hours.scrollLeft<=1;
    forward.disabled=!overflow||hours.scrollLeft+hours.clientWidth>=hours.scrollWidth-2;
    hint.textContent=overflow?'Desliza para ver más horas · lluvia en probabilidad':'Selecciona otro día para ver más horas';
  }
  hours.addEventListener('scroll',updateControls);
  const nextDay=new LpaDate(data.generat);nextDay.setDate(nextDay.getDate()+1);
  const today=lpaDayKey(data.generat),tomorrow=lpaDayKey(nextDay);
  function choose(day,button) {
    for(const b of strip.children)b.setAttribute('aria-pressed',String(b===button));
    hours.replaceChildren();hours.scrollLeft=0;
    const rows=data.hores.filter(h=>lpaDayKey(h.hora)===day.date);
    hourHeading.textContent=day.date===today?'Hoy por horas':new LpaDate(day.date+'T12:00:00').toLocaleDateString('es',{weekday:'long',day:'numeric',month:'short'});
    for(const row of rows) {
      const card=lpaText('article','','lpa-hour');
      const sun=data.sol?.find(s=>s.dia===day.date),time=Date.parse(row.hora);
      const night=Boolean(sun)&&(time<Date.parse(sun.sortida)||time>=Date.parse(sun.posta));
      card.append(lpaText('h3',lpaTime(row.hora)),lpaSkyIcon(row.codi,night),
        lpaText('strong',lpaFormat(row.temperatura)+'°'),
        lpaText('span',(row.probabilitat==null?'—':lpaFormat(row.probabilitat*100)+' %')+' lluvia','lpa-hour-rain'),
        lpaText('span',lpaFormat(row.vent)+' km/h','lpa-muted'));
      hours.append(card);
    }
    if(!rows.length)hours.append(lpaText('p','No quedan horas previstas para este día. El resumen corresponde al día completo.'));
    requestAnimationFrame(updateControls);
  }
  for(const day of days) {
    const date=new LpaDate(day.date+'T12:00:00'),button=lpaText('button','','lpa-day');button.type='button';button.setAttribute('aria-pressed','false');
    const name=day.date===today?'Hoy':day.date===tomorrow?'Mañana':date.toLocaleDateString('es',{weekday:'short',day:'numeric'});
    button.append(lpaText('span',name),lpaSkyIcon(day.weather_code),
      lpaText('strong',lpaFormat(day.temperature_2m_max)+'°'),lpaText('span',lpaFormat(day.temperature_2m_min)+'° mín.','lpa-muted'),
      lpaText('span',lpaFormat(day.precipitation_probability_max)+' % lluvia','lpa-hour-rain'));
    button.addEventListener('click',()=>choose(day,button));strip.append(button);
  }
  week.append(strip,lpaText('p','A partir del cuarto día, mayor incertidumbre.','lpa-muted'));target.append(week,hourly);
  if(days.length)choose(days[0],strip.firstElementChild);
  const info=document.createElement('details');info.className='lpa-explanation';
  info.append(lpaText('summary','Cómo interpretar la previsión'),
    lpaText('p','Los resúmenes corresponden al día completo y las horas muestran lo que queda por venir. El porcentaje de cada día es el máximo de sus probabilidades horarias; no es la cantidad de agua. Las Palmas tiene distintos microclimas.'),
    lpaText('p',data.lpa?.temperature_adjustment?'La temperatura a 2–6 horas incorpora un ajuste local validado para la costa urbana.':'Previsión del modelo sin corrección local validada.'),
    lpaLink('Fuentes y método','fuentes.html'),document.createTextNode(' · '),lpaLink('Consultar o descargar los datos','datos.html'));
  target.append(info);
  if(typeof posaVersio==='function')posaVersio(data.versio);
}
async function lpaRefreshDashboard() {
  try {lpaDashboard(await llegeixDades('montflorit.json'));}
  catch {document.getElementById('casa').replaceChildren(lpaText('p','No se pudieron cargar los datos.','avis'),lpaLink('Consultar AEMET','https://www.aemet.es/'));}
}
lpaRefreshDashboard();
setInterval(()=>{if(document.visibilityState==='visible')lpaRefreshDashboard();},300000);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')lpaRefreshDashboard();});
