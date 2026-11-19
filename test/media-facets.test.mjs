// Galeria: a faceta SÉRIE (PH, BP, BT…). As facetas filtram em JS, direto dos
// records (facetRows em web/lib/media-query.js), e a consulta SPARQL
// equivalente é montada pelo buildQueryFromFacets — as duas têm que dizer a
// mesma coisa. Aqui: o que é puro (records, filtro em JS, o texto da consulta)
// sobre um catálogo mínimo. A paridade com o Comunica rodando a consulta de
// verdade é conferida no navegador.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// media-query.js e o N3 vendorado são scripts clássicos (UMD / IIFE no
// `window`): carregados aqui como no worker da galeria, num `self` de mentira.
const read = (rel) => readFileSync(new URL(rel, import.meta.url), 'utf8');
const n3mod = { exports: {} };
new Function('module', 'exports', read('../web/lib/n3.min.js'))(n3mod, n3mod.exports);
const N3 = n3mod.exports;
const scope = { N3 };
new Function('self', 'window', read('../web/lib/media-query.js'))(scope, undefined);
const MQ = scope.PhidroMediaQuery;

const TTL = `
@prefix ph: <https://id.pedalhidrografi.co/terms#> .
@prefix pas: <https://id.pedalhidrografi.co/passeio/> .
@prefix ser: <https://id.pedalhidrografi.co/serie/> .
@prefix med: <https://id.pedalhidrografi.co/midia/> .
@prefix schema: <https://schema.org/> .
@prefix dcterms: <http://purl.org/dc/terms/> .

ser:PH a schema:EventSeries ; dcterms:title "Pedais Hidrográficos Regulares" .
ser:BP a schema:EventSeries ; dcterms:title "Bicipassarinhadas" .
ser:S  a schema:EventSeries ; dcterms:title "Pedais Hidrográficos Suados" .
ser:BT a schema:EventSeries ; dcterms:title "Bicicletografia" .

# só PH
pas:aaaaaaaa a ph:Tour ; dcterms:title "Tietê" ; dcterms:date "2026-01-10T09:00:00-03:00"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
  ph:inSeriesEdition <https://id.pedalhidrografi.co/passeio/PH/1> .
<https://id.pedalhidrografi.co/passeio/PH/1> ph:inEventSeries ser:PH ; ph:sequenceInSeries 1 .
# PH e BP ao mesmo tempo
pas:bbbbbbbb a ph:Tour ; dcterms:title "Passarinhos do Pinheiros" ; dcterms:date "2026-02-10" ;
  ph:inSeriesEdition <https://id.pedalhidrografi.co/passeio/PH/2>, <https://id.pedalhidrografi.co/passeio/BP/1> .
<https://id.pedalhidrografi.co/passeio/PH/2> ph:inEventSeries ser:PH ; ph:sequenceInSeries 2 .
<https://id.pedalhidrografi.co/passeio/BP/1> ph:inEventSeries ser:BP ; ph:sequenceInSeries 1 .
# só S
pas:cccccccc a ph:Tour ; dcterms:title "Suado" ; dcterms:date "2026-03-10" ;
  ph:inSeriesEdition <https://id.pedalhidrografi.co/passeio/S/1> .
<https://id.pedalhidrografi.co/passeio/S/1> ph:inEventSeries ser:S ; ph:sequenceInSeries 1 .
# passeio sem série nenhuma
pas:dddddddd a ph:Tour ; dcterms:title "Avulso" ; dcterms:date "2026-04-10" .

med:0000000000000001 a ph:StillImage ; ph:capturedDuring pas:aaaaaaaa .
med:0000000000000002 a ph:StillImage ; ph:capturedDuring pas:bbbbbbbb .
med:0000000000000003 a ph:MotionImage ; ph:capturedDuring pas:bbbbbbbb .
med:0000000000000004 a ph:StillImage ; ph:capturedDuring pas:cccccccc .
med:0000000000000005 a ph:StillImage ; ph:capturedDuring pas:dddddddd .
med:0000000000000006 a ph:StillImage .
`;

const SER = 'https://id.pedalhidrografi.co/serie/';
const quads = new N3.Parser().parse(TTL);
const model = MQ.buildMediaRecords(MQ.indexQuads(quads));
const ids = (rows) => rows.map((r) => r.m.value.slice(-1)).sort().join('');
const bySeries = (...codes) => MQ.facetRows(model, { series: codes.map((c) => SER + c) });

test('o model traz o catálogo de séries, com código e título', () => {
  assert.deepEqual(model.series[SER + 'PH'], { code: 'PH', title: 'Pedais Hidrográficos Regulares' });
  assert.deepEqual(model.series[SER + 'S'], { code: 'PH-S', title: 'Pedais Hidrográficos Suados' },
    'a série S usa o mesmo código do rótulo dos passeios');
  assert.ok(model.series[SER + 'BT'], 'série declarada e ainda sem passeio também entra');
});

test('cada mídia carrega as séries do passeio dela', () => {
  const rec = (n) => model.records.find((r) => r.iri.endsWith(String(n)));
  assert.deepEqual(rec(1).seriesIris, [SER + 'PH']);
  assert.deepEqual([...rec(2).seriesIris].sort(), [SER + 'BP', SER + 'PH']);
  assert.deepEqual(rec(5).seriesIris, [], 'passeio sem série');
  assert.deepEqual(rec(6).seriesIris, [], 'mídia sem passeio');
});

test('o índice leve e o N3.Store dão os mesmos records', () => {
  const fromStore = MQ.buildMediaRecords(MQ.makeStore(quads));
  const shape = (m) => m.records.map((r) => [r.iri, [...r.seriesIris].sort()]).sort();
  assert.deepEqual(shape(fromStore), shape(model));
  assert.deepEqual(fromStore.series, model.series);
});

test('sem a faceta, tudo passa; com ela, só mídia de passeio da série', () => {
  assert.equal(ids(MQ.facetRows(model, {})), '123456');
  assert.equal(ids(MQ.facetRows(model, { series: [] })), '123456', 'lista vazia = sem filtro');
  assert.equal(ids(bySeries('PH')), '123');
  assert.equal(ids(bySeries('BP')), '23');
  assert.equal(ids(bySeries('S')), '4');
  assert.equal(ids(bySeries('BT')), '', 'série sem mídia');
});

test('várias séries = qualquer uma delas, e cada mídia sai uma vez só', () => {
  const rows = bySeries('PH', 'BP');
  assert.equal(ids(rows), '123', 'as mídias do passeio que é PH e BP não se repetem');
  assert.equal(new Set(rows.map((r) => r.m.value)).size, rows.length);
  assert.equal(ids(bySeries('BP', 'S')), '234');
});

test('combina com as outras facetas por "e"', () => {
  const PAS = 'https://id.pedalhidrografi.co/passeio/';
  assert.equal(ids(MQ.facetRows(model, { series: [SER + 'PH'], tours: [PAS + 'bbbbbbbb'] })), '23');
  assert.equal(ids(MQ.facetRows(model, { series: [SER + 'S'], tours: [PAS + 'bbbbbbbb'] })), '');
  assert.equal(ids(MQ.facetRows(model, { series: [SER + 'PH'], dateFrom: '2026-02-01' })), '23');
});

test('a consulta SPARQL equivalente restringe pela série do passeio', () => {
  const q = MQ.buildQueryFromFacets({ series: [SER + 'PH', SER + 'BP'] });
  assert.match(q, /VALUES \?fseries \{ <[^>]+\/serie\/PH> <[^>]+\/serie\/BP> \}/);
  assert.match(q, /\?m ph:capturedDuring \?fst \. \?fst ph:inSeriesEdition \?fed \. \?fed ph:inEventSeries \?fseries \./);
  assert.match(q, /SELECT DISTINCT \?m \?group/, 'DISTINCT: passeio em duas séries não duplica a mídia');
  assert.doesNotMatch(MQ.buildQueryFromFacets({ series: [] }), /fseries/);
});
