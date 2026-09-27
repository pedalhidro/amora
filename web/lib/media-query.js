/*
 * PhidroMediaQuery — infraestrutura de consulta compartilhada entre o mapa
 * (app.js) e a galeria (imagens.html).
 *
 * Substrato: os dados (tours.ttl + uploads.ttl) já são parseados com N3.js;
 * aqui eles viram um N3.Store em memória. A galeria filtra as facetas em JS,
 * direto dos records (facetRows) — o Comunica (@comunica/query-sparql-rdfjs,
 * SPARQL 1.1 completo, ~1,6 MB do jsdelivr) só é baixado, sob demanda, pra
 * consulta SPARQL escrita à mão (Avançado da galeria, filtro SPARQL do mapa).
 *
 * Carregado como <script> clássico (NÃO módulo) por app.js e imagens.html;
 * publica window.PhidroMediaQuery. Requer window.N3 já carregado.
 */
(function (global) {
  'use strict';

  var NS = {
    ph:      'https://id.pedalhidrografi.co/terms#',
    phd:     'https://pedalhidrografi.co/data/',
    med:     'https://id.pedalhidrografi.co/midia/',
    pas:     'https://id.pedalhidrografi.co/passeio/',
    ser:     'https://id.pedalhidrografi.co/serie/',
    lst:     'https://id.pedalhidrografi.co/listas/',
    schema:  'https://schema.org/',
    dcterms: 'http://purl.org/dc/terms/',
    prov:    'http://www.w3.org/ns/prov#',
    pav:     'http://purl.org/pav/',
    exif:    'http://www.w3.org/2003/12/exif/ns#',
    rdf:     'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    xsd:     'http://www.w3.org/2001/XMLSchema#',
  };
  var PADRAO_IRI = NS.lst + 'padrao';

  // Bundle browser single-file (global `Comunica`), pinado por commit SHA no
  // repo rdfjs/comunica-browser (o arquivo pronto-pra-<script> não existe no
  // npm, só nesse repo gh). v5 = SPARQL 1.1 completo.
  var COMUNICA_URL =
    'https://cdn.jsdelivr.net/gh/rdfjs/comunica-browser@d695d15e4da0b095315b327c9f6ecd6ab444be6e' +
    '/versions/v5/engines/query-sparql-rdfjs/comunica-browser.js';

  // ── util ────────────────────────────────────────────────────────────────
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { resolve(); };
      // Tira a tag que falhou: uma nova tentativa (ensureEngine) cria outra.
      s.onerror = function () { s.remove(); reject(new Error('falha ao carregar ' + src)); };
      document.head.appendChild(s);
    });
  }
  function short(iri) { return String(iri).split(/[/#]/).pop(); }
  function numOr(v, dflt) {
    if (v == null) return dflt === undefined ? null : dflt;
    var n = parseFloat(v);
    return isFinite(n) ? n : (dflt === undefined ? null : dflt);
  }
  function origExt(mime) {
    if (!mime) return 'jpg';
    mime = String(mime).toLowerCase();
    if (mime.indexOf('png') >= 0) return 'png';
    if (mime.indexOf('heic') >= 0) return 'heic';
    if (mime.indexOf('heif') >= 0) return 'heif';
    return 'jpg';
  }
  function parseDuration(iso) {
    // "PT15.1S" → 15.1 (segundos). Suporta minutos/horas simples.
    if (!iso) return null;
    var m = /P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?/.exec(iso);
    if (!m) return null;
    return (+(m[1] || 0)) * 86400 + (+(m[2] || 0)) * 3600 +
           (+(m[3] || 0)) * 60 + (+(m[4] || 0));
  }
  // Dia da semana (0=domingo) da DATA-calendário escrita, independente do TZ
  // do navegador: usa só a parte YYYY-MM-DD como um instante UTC.
  function weekdayOf(datetime) {
    if (!datetime) return null;
    var d = new Date(String(datetime).slice(0, 10) + 'T00:00:00Z');
    return isNaN(d.getTime()) ? null : d.getUTCDay();
  }

  // ── engine (lazy) ─────────────────────────────────────────────────────────
  var _engine = null, _enginePromise = null;
  function ensureEngine() {
    if (_engine) return Promise.resolve(_engine);
    if (!_enginePromise) {
      _enginePromise = (async function () {
        if (!global.Comunica) await loadScript(COMUNICA_URL);
        _engine = new global.Comunica.QueryEngine();
        return _engine;
      })();
      // Falhou (rede ruim, offline, CDN fora): não memoiza a rejeição — a
      // próxima consulta tenta de novo em vez de falhar pra sempre.
      _enginePromise.catch(function () { _enginePromise = null; });
    }
    return _enginePromise;
  }

  function makeStore(quads) {
    var store = new global.N3.Store();
    if (quads && quads.length) store.addQuads(quads);
    return store;
  }

  // Roda um SELECT e devolve as linhas como objetos {var: {value, termType}}.
  async function runQuery(store, sparql) {
    var engine = await ensureEngine();
    var stream = await engine.queryBindings(sparql, { sources: [store] });
    return await new Promise(function (resolve, reject) {
      var rows = [];
      stream.on('data', function (b) {
        var row = {};
        for (var pair of b) {
          // pair = [Variable, Term]
          row[pair[0].value] = { value: pair[1].value, termType: pair[1].termType };
        }
        rows.push(row);
      });
      stream.on('end', function () { resolve(rows); });
      stream.on('error', reject);
    });
  }

  // Conveniência pro filtro do mapa: roda o SPARQL e devolve um Set das IRIs
  // de mídia ligadas à variável `?m` (ou à primeira projetada).
  async function queryMediaIris(store, sparql) {
    var rows = await runQuery(store, sparql);
    var set = new Set();
    for (var r of rows) {
      var v = r.m || r[Object.keys(r)[0]];
      if (v && v.value) set.add(v.value);
    }
    return set;
  }

  // ── records (dados dos tiles + catálogos de facetas) ──────────────────────
  function buildMediaRecords(store) {
    var DF = global.N3.DataFactory;
    var nn = function (iri) { return DF.namedNode(iri); };
    var RDFT = nn(NS.rdf + 'type');
    function objs(s, p) {
      return store.getObjects(nn(s), nn(p), null).map(function (t) { return t.value; });
    }
    function obj1(s, p) { var a = objs(s, p); return a.length ? a[0] : null; }

    // Passeios: rótulo (série + título) + energia (kJ) pra faceta quilojaules.
    var tours = {};
    store.getQuads(null, RDFT, nn(NS.ph + 'Tour'), null).forEach(function (q) {
      var t = q.subject.value;
      tours[t] = {
        title: obj1(t, NS.dcterms + 'title') || short(t),
        date: (obj1(t, NS.dcterms + 'date') || '').slice(0, 10),
        energyKj: numOr(obj1(t, NS.ph + 'energyEstimate')),
        code: null,
      };
    });
    var seriesLabel = function (iri) { var s = short(iri); return s === 'S' ? 'PH-S' : s; };
    Object.keys(tours).forEach(function (t) {
      var parts = [];
      objs(t, NS.ph + 'inSeriesEdition').forEach(function (assoc) {
        var sIri = obj1(assoc, NS.ph + 'inEventSeries');
        var seq = obj1(assoc, NS.ph + 'sequenceInSeries');
        if (sIri && seq != null) parts.push(seriesLabel(sIri) + ' ' + seq);
      });
      parts.sort();
      if (parts.length) tours[t].code = parts.join(' & ');
    });
    var tourLabel = function (t) {
      var o = tours[t]; if (!o) return short(t);
      return o.code ? (o.code + ' — ' + o.title) : o.title;
    };

    // Pessoas e listas (catálogos p/ opções de faceta).
    var people = {};
    store.getQuads(null, RDFT, nn(NS.schema + 'Person'), null).forEach(function (q) {
      var p = q.subject.value;
      people[p] = obj1(p, NS.schema + 'name') || obj1(p, NS.schema + 'alternateName') || short(p);
    });
    var lists = {};
    store.getQuads(null, RDFT, nn(NS.schema + 'Collection'), null).forEach(function (q) {
      var l = q.subject.value;
      lists[l] = obj1(l, NS.schema + 'name') || short(l);
    });

    var records = [];
    [['StillImage', 'image'], ['MotionImage', 'video']].forEach(function (pair) {
      var cls = pair[0], kind = pair[1];
      store.getQuads(null, RDFT, nn(NS.ph + cls), null).forEach(function (q) {
        var iri = q.subject.value;
        var tourIri = obj1(iri, NS.ph + 'capturedDuring');
        var rec = {
          iri: iri, kind: kind,
          datetime: obj1(iri, NS.dcterms + 'date'),
          tourIri: tourIri,
          tourLabel: tourIri ? tourLabel(tourIri) : null,
          energyKj: (tourIri && tours[tourIri]) ? tours[tourIri].energyKj : null,
          authorIris: objs(iri, NS.prov + 'wasAttributedTo'),
          uploaderIris: objs(iri, NS.pav + 'providedBy'),
          authors: objs(iri, NS.prov + 'wasAttributedTo').map(function (p) { return people[p] || short(p); }),
          uploaders: objs(iri, NS.pav + 'providedBy').map(function (p) { return people[p] || short(p); }),
          lists: objs(iri, NS.schema + 'isPartOf'),
          weekday: weekdayOf(obj1(iri, NS.dcterms + 'date')),
          // Tem coordenada → tem marcador no mapa (só mídia georreferenciada
          // vira marcador; a galeria usa isto pra só oferecer "Ver no mapa"
          // quando faz sentido).
          geo: !!obj1(iri, NS.schema + 'locationCreated'),
        };
        if (kind === 'image') {
          var phash = iri.slice(NS.med.length);
          rec.phash = phash;
          rec.thumbUrl = './photos/' + phash + '/thumb.jpg';
          rec.largeUrl = './photos/' + phash + '/large.jpg';
          rec.fullUrl = './photos/' + phash + '/original.' + origExt(obj1(iri, NS.schema + 'encodingFormat'));
        } else {
          var vhash = iri.slice(NS.med.length);
          rec.vhash = vhash;
          var thumb = obj1(iri, NS.schema + 'thumbnail');
          var v = obj1(iri, NS.ph + 'video360p') || obj1(iri, NS.ph + 'video720p');
          var audio = obj1(iri, NS.ph + 'audio');
          rec.thumbUrl = thumb ? ('./clips/' + thumb) : null;
          rec.clipUrl = v ? ('./clips/' + v) : null;
          rec.audioUrl = audio ? ('./clips/' + audio) : null;
          rec.duration = parseDuration(obj1(iri, NS.schema + 'duration'));
          rec.largeUrl = rec.thumbUrl;
          rec.fullUrl = rec.clipUrl;
        }
        records.push(rec);
      });
    });
    return { records: records, tours: tours, people: people, lists: lists, tourLabel: tourLabel };
  }

  // ── facetas → SPARQL (visível/editável) ───────────────────────────────────
  function sparqlStr(s) {
    return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
  }
  function valuesBlock(varName, iris) {
    return 'VALUES ?' + varName + ' { ' + iris.map(function (i) { return '<' + i + '>'; }).join(' ') + ' }';
  }

  // facets = {group:'tour'|'day'|'month'|'year'|'none', lists:[], authors:[],
  //   uploaders:[], tours:[], dateFrom, dateTo, kjMin, kjMax, weekdays:[]}
  // Nota: dia-da-semana NÃO tem função SPARQL nativa → é aplicado no cliente
  // (comentado na query pra ficar visível); todo o resto é SPARQL puro.
  function buildQueryFromFacets(facets) {
    facets = facets || {};
    var P = [
      'PREFIX ph: <' + NS.ph + '>',
      'PREFIX phd: <' + NS.phd + '>',
      'PREFIX schema: <' + NS.schema + '>',
      'PREFIX dcterms: <' + NS.dcterms + '>',
      'PREFIX prov: <' + NS.prov + '>',
      'PREFIX pav: <' + NS.pav + '>',
      'PREFIX xsd: <' + NS.xsd + '>',
    ];
    var W = [];
    W.push('{ ?m a ph:StillImage } UNION { ?m a ph:MotionImage }');
    // Data é OPCIONAL: mídia sem EXIF (ex.: baixada do zap) entra sem
    // dcterms:date e ainda assim deve aparecer na galeria — no grupo
    // "sem-data", no fim (DESC(?d) põe ?d não-ligado por último). Facetas de
    // data continuam excluindo essas (FILTER sobre ?d não-ligado = falso).
    W.push('OPTIONAL { ?m dcterms:date ?d }');

    if (facets.lists && facets.lists.length) {
      W.push(valuesBlock('list', facets.lists));
      W.push('?m schema:isPartOf ?list .');
    }
    if (facets.authors && facets.authors.length) {
      W.push(valuesBlock('author', facets.authors));
      W.push('?m prov:wasAttributedTo ?author .');
    }
    if (facets.uploaders && facets.uploaders.length) {
      W.push(valuesBlock('uploader', facets.uploaders));
      W.push('?m pav:providedBy ?uploader .');
    }
    if (facets.tours && facets.tours.length) {
      W.push(valuesBlock('ftour', facets.tours));
      W.push('?m ph:capturedDuring ?ftour .');
    }
    // Datas pelo DIA-calendário gravado na mídia (o AAAA-MM-DD do
    // dcterms:date, no fuso dela — como o agrupamento por dia e o dia da
    // semana). Era ?d >= "…T00:00:00"^^xsd:dateTime: um limite SEM fuso, que
    // o Comunica resolve pelo fuso do navegador e com o sinal invertido — em
    // São Paulo a janela do dia ia de 18h da véspera a 17h59 (medido: "de
    // 25/09 até 25/09" achava 0 das 67 mídias do PH 113, um pedal noturno).
    if (facets.dateFrom) {
      W.push('FILTER(SUBSTR(STR(?d), 1, 10) >= ' + sparqlStr(facets.dateFrom) + ')');
    }
    if (facets.dateTo) {
      W.push('FILTER(SUBSTR(STR(?d), 1, 10) <= ' + sparqlStr(facets.dateTo) + ')');
    }
    if (facets.kjMin != null || facets.kjMax != null) {
      W.push('?m ph:capturedDuring ?et . ?et ph:energyEstimate ?kj .');
      if (facets.kjMin != null) W.push('FILTER(?kj >= ' + (+facets.kjMin) + ')');
      if (facets.kjMax != null) W.push('FILTER(?kj <= ' + (+facets.kjMax) + ')');
    }
    if (facets.weekdays && facets.weekdays.length && facets.weekdays.length < 7) {
      var names = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
      W.push('# dia da semana aplicado no cliente: [' +
        facets.weekdays.slice().sort().map(function (n) { return names[n]; }).join(', ') + ']');
    }

    // Chave de grupo (?group).
    var g = facets.group || 'tour';
    if (g === 'tour') {
      W.push('OPTIONAL { ?m ph:capturedDuring ?gt }');
      W.push('BIND(COALESCE(?gt, "sem-passeio") AS ?group)');
    } else if (g === 'year') {
      W.push('BIND(COALESCE(STR(YEAR(?d)), "sem-data") AS ?group)');
    } else if (g === 'month') {
      W.push('BIND(COALESCE(CONCAT(STR(YEAR(?d)), "-", IF(MONTH(?d) < 10, "0", ""), STR(MONTH(?d))), "sem-data") AS ?group)');
    } else if (g === 'day') {
      W.push('BIND(COALESCE(SUBSTR(STR(?d), 1, 10), "sem-data") AS ?group)');
    } else {
      W.push('BIND("" AS ?group)');
    }

    // O ORDER BY documenta a ordem (data desc, desempate pelo IRI), mas a
    // galeria NÃO confia nele pro desempate: este Comunica não aplica a 2ª
    // chave de forma confiável (medido — mídias com a mesma data, ou sem
    // data, saem embaralhadas). A ordem total é imposta no cliente
    // (canonicalRowOrder em imagens.html) e espelhada no backend
    // (_album_sequence) — é ela que numera /imagens/lista/<slug>/<n>.
    return P.join('\n') + '\n\nSELECT DISTINCT ?m ?group WHERE {\n  ' +
      W.join('\n  ') + '\n}\nORDER BY DESC(?d) ?m';
  }

  // ── facetas → linhas em JS (sem Comunica) ─────────────────────────────────
  // As MESMAS linhas {m, group} que runQuery(store, buildQueryFromFacets(f))
  // devolve (SELECT DISTINCT ?m ?group), calculadas direto de model.records —
  // a galeria renderiza a visão padrão e cada faceta sem baixar/compilar o
  // Comunica nem consultar o catálogo inteiro. Mesma semântica da consulta
  // (mudou uma, mude a outra): listas/autoras/quem subiu/passeios = "qualquer
  // um de"; datas pelo dia-calendário gravado; kJ pela estimativa do passeio
  // (sem passeio/estimativa → fora); grupo = passeio | dia | mês | ano |
  // nenhum. Dia da semana fica com quem chama (não existe em SPARQL). Sem
  // ordem: quem chama ordena (canonicalRowOrder na galeria).
  var DATE_RE = /^(\d{4})-(\d{2})-(\d{2})/;
  function facetGroup(rec, g) {
    if (g === 'tour') {
      return rec.tourIri ? { value: rec.tourIri, termType: 'NamedNode' } : { value: 'sem-passeio', termType: 'Literal' };
    }
    if (g !== 'year' && g !== 'month' && g !== 'day') return { value: '', termType: 'Literal' };
    var m = DATE_RE.exec(rec.datetime || '');
    var v = !m ? 'sem-data' : (g === 'year' ? m[1] : (g === 'month' ? m[1] + '-' + m[2] : m[0]));
    return { value: v, termType: 'Literal' };
  }
  function facetRows(model, facets) {
    facets = facets || {};
    var asSet = function (a) { return (a && a.length) ? new Set(a) : null; };
    var lists = asSet(facets.lists), authors = asSet(facets.authors),
      uploaders = asSet(facets.uploaders), tours = asSet(facets.tours);
    var anyIn = function (vals, set) {
      for (var i = 0; vals && i < vals.length; i++) if (set.has(vals[i])) return true;
      return false;
    };
    var kjMin = facets.kjMin, kjMax = facets.kjMax;
    var hasKj = kjMin != null || kjMax != null;
    var g = facets.group || 'tour';
    var seen = new Set(), rows = [];
    ((model && model.records) || []).forEach(function (r) {
      if (seen.has(r.iri)) return;
      if (lists && !anyIn(r.lists, lists)) return;
      if (authors && !anyIn(r.authorIris, authors)) return;
      if (uploaders && !anyIn(r.uploaderIris, uploaders)) return;
      if (tours && !(r.tourIri && tours.has(r.tourIri))) return;
      if (facets.dateFrom || facets.dateTo) {
        var dm = DATE_RE.exec(r.datetime || '');
        if (!dm) return;   // sem data: fora de qualquer faixa (como o FILTER)
        if (facets.dateFrom && dm[0] < facets.dateFrom) return;
        if (facets.dateTo && dm[0] > facets.dateTo) return;
      }
      if (hasKj) {
        if (r.energyKj == null) return;
        if (kjMin != null && !(r.energyKj >= +kjMin)) return;
        if (kjMax != null && !(r.energyKj <= +kjMax)) return;
      }
      seen.add(r.iri);
      rows.push({ m: { value: r.iri, termType: 'NamedNode' }, group: facetGroup(r, g) });
    });
    return rows;
  }

  // Consulta simples de pertencimento (default do mapa): membros de uma lista.
  function listMembershipQuery(listIri) {
    return 'PREFIX schema: <' + NS.schema + '>\n' +
      'SELECT DISTINCT ?m WHERE { ?m schema:isPartOf <' + listIri + '> }';
  }

  global.PhidroMediaQuery = {
    NS: NS,
    PADRAO_IRI: PADRAO_IRI,
    ensureEngine: ensureEngine,
    makeStore: makeStore,
    runQuery: runQuery,
    queryMediaIris: queryMediaIris,
    buildMediaRecords: buildMediaRecords,
    buildQueryFromFacets: buildQueryFromFacets,
    facetRows: facetRows,
    listMembershipQuery: listMembershipQuery,
    weekdayOf: weekdayOf,
  };
})(window);
