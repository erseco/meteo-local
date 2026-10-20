// SPDX-License-Identifier: AGPL-3.0-or-later
// Enhance the upstream graph without replacing its UI or native touch scrolling.
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

function lpaEnhanceForecast() {
  for (const node of document.querySelectorAll('.g-desplaca')) {
    if (node.dataset.lpaDrag) continue;
    node.dataset.lpaDrag = 'true';
    lpaScrollable(node);
    const source = document.createElement('p');
    source.className = 'lpa-forecast-source';
    source.append('Previsión · Open-Meteo · 7 días. Arrastra para ver más. ');
    const link = document.createElement('a');
    link.href = 'fuentes.html'; link.textContent = 'Fuentes'; source.append(link);
    node.closest('figure').after(source);
    const note = document.createElement('small');
    note.textContent = 'A partir del cuarto día aumenta la incertidumbre.';
    source.append(document.createElement('br'), note);
  }
}
new MutationObserver(lpaEnhanceForecast).observe(document.getElementById('casa'), {childList:true, subtree:true});
lpaEnhanceForecast();
