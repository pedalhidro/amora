/*
 * Worker da galeria (imagens.html): baixa o catálogo, parseia o Turtle e monta
 * os records FORA da thread da página. Com o catálogo de 11/2026 (5,5 MB de
 * Turtle, 126 mil quads) isso travava a galeria — e o app inteiro, quando ela
 * abre embutida no modal: iframe da mesma origem divide a thread com o mapa —
 * por ~2 s num desktop e ~7 s num celular, a cada abertura e a cada recarga
 * depois de uma edição.
 *
 * Protocolo: página → {id, base}; worker → {id, model} | {id, error}.
 * `model` = {records, tours, people, lists} (só dados; ver loadMediaModel em
 * media-query.js). Qualquer falha — aqui ou ao carregar este arquivo — faz a
 * página rodar o mesmo caminho nela mesma (loadModel em imagens.html).
 */
'use strict';
// Mesmo ?api= do <script> da galeria: o worker tem que rodar a MESMA
// media-query.js que a página.
importScripts('./n3.min.js', './media-query.js?api=2');

self.onmessage = function (e) {
  var id = e.data && e.data.id;
  self.PhidroMediaQuery.loadMediaModel(e.data.base).then(
    function (model) { self.postMessage({ id: id, model: model }); },
    function (err) { self.postMessage({ id: id, error: String((err && err.message) || err) }); }
  );
};
