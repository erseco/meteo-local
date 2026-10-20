// SPDX-License-Identifier: AGPL-3.0-or-later
// AEMET only: no transplanted Catalan risks, plans or synthetic thresholds.
llegeixDades('montflorit.json').then(data => {
  const box = document.getElementById('perill');
  box.replaceChildren();
  if (dadesVelles(data) || data.avisos === null) {
    box.append(element('p', 'avis', 'Avisos no disponibles o datos caducados. Consulte AEMET.'));
  } else if (!data.avisos.length) {
    box.append(element('p', null, 'No hay avisos de AEMET en el feed consultado para Norte de Gran Canaria. Las alertas de Protección Civil no están integradas.'));
  } else for (const a of data.avisos) {
    const article = element('article', 'targeta');
    article.append(element('h2', null, `AEMET · ${TD(a.nivel)} · ${TD(a.tipo)}`),
      element('p', null, a.descripcio),
      element('p', null, `Desde ${new LpaDate(a.inicio).toLocaleString('es')} hasta ${new LpaDate(a.fin).toLocaleString('es')} (hora canaria).`));
    const link = element('a', null, 'Consultar el aviso oficial');
    link.href = a.url;
    article.append(link);
    box.append(article);
  }
  posaVersio(data.versio);
}).catch(() => {
  document.getElementById('perill').replaceChildren(element('p', 'avis', 'No se pudieron cargar los avisos. Consulte AEMET.'));
});
