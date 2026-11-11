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
 * Carregado como <script> clássico (NÃO módulo) por index.html, imagens.html,
 * georef.html e memoria.html, e por importScripts no lib/gallery-worker.js;
 * publica window.PhidroMediaQuery (self.… no worker). Requer N3 já carregado
 * na hora de CHAMAR o que parseia ou monta store. A galeria e o worker dela
 * carregam `media-query.js?api=N` — suba o N (nos dois) quando passarem a
 * usar um nome novo daqui (mesmo motivo do `?api=` do lib/utils.js).
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

  // ── data EFETIVA da mídia ─────────────────────────────────────────────────
  // dcterms:date de mídia tem três estados:
  //   xsd:dateTime — o instante real (EXIF / moov);
  //   xsd:date     — só o DIA é conhecido (mídia do zap: o dia é o do passeio,
  //                  a hora ninguém sabe — e não se inventa uma);
  //   ausente      — vale o dia do passeio (ph:capturedDuring), se houver.
  // Nos dois últimos a mídia vale pelo dia, às 23:59 de São Paulo: na ordem
  // "mais novas primeiro" fica ACIMA das fotos com hora do mesmo dia. Leitores
  // usam `datetime` (sempre um instante ISO com fuso, ou null) pra ordenar,
  // filtrar e agrupar, e `dateOnly` pra NÃO mostrar o 23:59 como se fosse a
  // hora da foto. `raw` é o literal gravado (null = veio do passeio).
  //
  // Um 4º caso, por cima dos dois "sem hora": a mídia tem uma HORA ESTIMADA
  // (ph:estimatedCaptureTime — o instante em que a gravação do passeio passou
  // pelo ponto onde ela foi posicionada à mão). Aí `datetime` é a estimativa
  // (ordena no lugar certo do dia, em vez do 23:59) e `estimated` manda
  // mostrar a hora com ≈. Um xsd:dateTime de verdade sempre ganha dela.
  // Espelhos: _media_instant (backend/main.py). Mudou aqui, mude lá.
  var DAY_ONLY_RE = /^(\d{4}-\d{2}-\d{2})(?:Z|[+-]\d{2}:\d{2})?$/;
  var UNTIMED_SUFFIX = 'T23:59:00-03:00';
  function effectiveDate(raw, tourDate, estimated) {
    raw = raw ? String(raw) : '';
    var m = DAY_ONLY_RE.exec(raw);
    if (raw && !m) return { datetime: raw, dateOnly: false, estimated: false, raw: raw };
    if (estimated) return { datetime: String(estimated), dateOnly: false, estimated: true, raw: raw || null };
    if (m) return { datetime: m[1] + UNTIMED_SUFFIX, dateOnly: true, estimated: false, raw: raw };
    var t = /^\d{4}-\d{2}-\d{2}/.exec(tourDate ? String(tourDate) : '');
    if (t) return { datetime: t[0] + UNTIMED_SUFFIX, dateOnly: true, estimated: false, raw: null };
    return { datetime: null, dateOnly: false, estimated: false, raw: null };
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

  // ── índice leve do catálogo (sem N3.Store) ───────────────────────────────
  // O que buildMediaRecords lê do catálogo são ~20 predicados. Um N3.Store
  // indexa TUDO (os 126 mil quads de 11/2026, mais da metade nunca lida: nós
  // _geo/_hash, os env: de cada envio…) em três índices — medido com o catálogo
  // de produção, montar o store + ler os records dele custava mais que o
  // próprio parse (0,6 s num desktop, 2,7 s num celular) e travava a página
  // a cada abertura e a cada recarga depois de uma edição. O índice guarda só
  // sujeito → predicado → valores dos predicados de RECORD_PREDICATES e os
  // sujeitos de cada rdf:type, na ordem do documento. O N3.Store continua
  // sendo o que a consulta SPARQL (Avançado, filtro do mapa) precisa.
  var RECORD_PREDICATES = [
    NS.dcterms + 'title', NS.dcterms + 'date',
    NS.ph + 'energyEstimate', NS.ph + 'inSeriesEdition', NS.ph + 'inEventSeries',
    NS.ph + 'sequenceInSeries', NS.ph + 'capturedDuring', NS.ph + 'estimatedCaptureTime',
    NS.ph + 'video360p', NS.ph + 'video720p', NS.ph + 'audio',
    NS.schema + 'name', NS.schema + 'alternateName', NS.schema + 'isPartOf',
    NS.schema + 'locationCreated', NS.schema + 'encodingFormat', NS.schema + 'thumbnail',
    NS.schema + 'duration',
    NS.prov + 'wasAttributedTo', NS.pav + 'providedBy',
  ];
  var RDF_TYPE = NS.rdf + 'type';
  function makeIndex() {
    var want = new Set(RECORD_PREDICATES);
    var sp = new Map();       // sujeito → Map(predicado → [valores])
    var byType = new Map();   // classe → Set(sujeitos)
    return {
      _phIndex: true, sp: sp, byType: byType, preds: want,
      add: function (q) {
        var p = q.predicate.value;
        if (p === RDF_TYPE) {
          var set = byType.get(q.object.value);
          if (!set) byType.set(q.object.value, set = new Set());
          set.add(q.subject.value);
          return;
        }
        // Só sujeito IRI, como o store é consultado (namedNode(s)).
        if (!want.has(p) || q.subject.termType !== 'NamedNode') return;
        var s = q.subject.value;
        var byP = sp.get(s);
        if (!byP) sp.set(s, byP = new Map());
        var vals = byP.get(p);
        if (!vals) byP.set(p, vals = []);
        var v = q.object.value;
        if (vals.indexOf(v) < 0) vals.push(v);   // triple repetida em dois dumps
      },
    };
  }
  function indexQuads(quads) {
    var idx = makeIndex();
    for (var i = 0; i < (quads ? quads.length : 0); i++) idx.add(quads[i]);
    return idx;
  }
  // Turtle → Promise<índice>, sem guardar os quads: o parser entrega um a um
  // (com callback o N3 tokeniza num microtask — por isso a Promise; o último
  // callback vem sem quad).
  function parseToIndex(text) {
    return new Promise(function (resolve, reject) {
      var idx = makeIndex(), done = false;
      new global.N3.Parser().parse(text, function (e, quad) {
        if (done) return;
        if (e) { done = true; reject(e); return; }
        if (quad) idx.add(quad);
        else { done = true; resolve(idx); }
      });
    });
  }
  // Leitura uniforme das duas fontes (N3.Store | índice leve).
  var NO_VALUES = [];
  function sourceReader(src) {
    if (src && src._phIndex) {
      return {
        objs: function (s, p) {
          if (!src.preds.has(p)) throw new Error('predicado fora de RECORD_PREDICATES: ' + p);
          var byP = src.sp.get(s);
          return (byP && byP.get(p)) || NO_VALUES;
        },
        ofType: function (cls) { var set = src.byType.get(cls); return set ? Array.from(set) : []; },
      };
    }
    var DF = global.N3.DataFactory;
    var nn = function (iri) { return DF.namedNode(iri); };
    var RDFT = nn(RDF_TYPE);
    return {
      objs: function (s, p) {
        return src.getObjects(nn(s), nn(p), null).map(function (t) { return t.value; });
      },
      ofType: function (cls) {
        return src.getQuads(null, RDFT, nn(cls), null).map(function (q) { return q.subject.value; });
      },
    };
  }

  // Rótulo do passeio: "<série nº> — <título>". Função à parte porque o model
  // que vem do worker (structured clone) não carrega funções — quem recebe
  // refaz a dele com isto.
  function makeTourLabel(tours) {
    return function (t) {
      var o = tours[t]; if (!o) return short(t);
      return o.code ? (o.code + ' — ' + o.title) : o.title;
    };
  }

  // ── records (dados dos tiles + catálogos de facetas) ──────────────────────
  // `src` = N3.Store ou o índice leve (indexQuads / parseToIndex). Predicado
  // novo lido aqui entra em RECORD_PREDICATES (o índice recusa o que não tem).
  function buildMediaRecords(src) {
    var reader = sourceReader(src);
    var objs = reader.objs, ofType = reader.ofType;
    function obj1(s, p) { var a = objs(s, p); return a.length ? a[0] : null; }

    // Passeios: rótulo (série + título) + energia (kJ) pra faceta quilojaules.
    var tours = {};
    ofType(NS.ph + 'Tour').forEach(function (t) {
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
    var tourLabel = makeTourLabel(tours);

    // Pessoas e listas (catálogos p/ opções de faceta).
    var people = {};
    ofType(NS.schema + 'Person').forEach(function (p) {
      people[p] = obj1(p, NS.schema + 'name') || obj1(p, NS.schema + 'alternateName') || short(p);
    });
    var lists = {};
    ofType(NS.schema + 'Collection').forEach(function (l) {
      lists[l] = obj1(l, NS.schema + 'name') || short(l);
    });

    var records = [];
    [['StillImage', 'image'], ['MotionImage', 'video']].forEach(function (pair) {
      var cls = pair[0], kind = pair[1];
      ofType(NS.ph + cls).forEach(function (iri) {
        var tourIri = obj1(iri, NS.ph + 'capturedDuring');
        var when = effectiveDate(obj1(iri, NS.dcterms + 'date'),
          (tourIri && tours[tourIri]) ? tours[tourIri].date : null,
          obj1(iri, NS.ph + 'estimatedCaptureTime'));
        var authorIris = objs(iri, NS.prov + 'wasAttributedTo').slice();
        var uploaderIris = objs(iri, NS.pav + 'providedBy').slice();
        var rec = {
          iri: iri, kind: kind,
          // Data EFETIVA (ver effectiveDate): instante ISO ou null. dateOnly =
          // só o dia é conhecido (não mostrar hora); dateRaw = o literal gravado.
          datetime: when.datetime,
          dateOnly: when.dateOnly,
          dateEstimated: when.estimated,   // hora ESTIMADA pela posição: mostrar com ≈
          dateRaw: when.raw,
          tourIri: tourIri,
          tourLabel: tourIri ? tourLabel(tourIri) : null,
          energyKj: (tourIri && tours[tourIri]) ? tours[tourIri].energyKj : null,
          authorIris: authorIris,
          uploaderIris: uploaderIris,
          authors: authorIris.map(function (p) { return people[p] || short(p); }),
          uploaders: uploaderIris.map(function (p) { return people[p] || short(p); }),
          lists: objs(iri, NS.schema + 'isPartOf').slice(),
          weekday: weekdayOf(when.datetime),
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

  // ── carga do catálogo (manifesto VoID → dumps) ───────────────────────────
  // Texto Turtle de todos os grafos, concatenado: segue cada void:dataDump do
  // manifesto (URL relativa a ele); sem manifesto, os dumps conhecidos. Os
  // dumps baixam em PARALELO e entram na ordem do manifesto. `base` = a URL
  // contra a qual ./data/… resolve (document.baseURI — NÃO location.href, que
  // ignora o <base> das páginas servidas em /imagens/lista/…). Roda na página
  // e no worker da galeria (lib/gallery-worker.js): só fetch + N3.
  async function fetchCatalogText(base) {
    var VOID_DUMP = 'http://rdfs.org/ns/void#dataDump';
    var urls = null;
    try {
      var manifestUrl = new URL('./data/data_graphs.ttl', base).href;
      var res = await fetch(manifestUrl, { cache: 'no-cache' });
      if (!res.ok) throw new Error('data_graphs.ttl HTTP ' + res.status);
      var mQuads = new global.N3.Parser().parse(await res.text());
      urls = [];
      mQuads.forEach(function (q) {
        if (q.predicate.value === VOID_DUMP) urls.push(new URL(q.object.value, manifestUrl).href);
      });
      if (!urls.length) throw new Error('manifesto sem void:dataDump');
    } catch (e) {
      console.warn('[media-query] manifesto indisponível, usando fallback:', e.message);
      urls = ['tours.ttl', 'images.ttl', 'identities.ttl', 'lists.ttl'].map(function (f) {
        return new URL('./data/' + f, base).href;
      });
    }
    var parts = await Promise.all(urls.map(function (u) {
      return fetch(u, { cache: 'no-cache' })
        .then(function (r) {
          if (!r.ok) { console.warn('[media-query] ' + u + ': HTTP ' + r.status); return null; }
          return r.text();
        })
        .catch(function (err) { console.warn('[media-query] ' + u + ': ' + err.message); return null; });
    }));
    return parts.filter(function (t) { return t != null; }).join('\n\n');
  }
  // Catálogo → model da galeria, pelo índice leve. Devolve só DADOS (records,
  // tours, people, lists): atravessa o postMessage do worker; quem recebe põe
  // o tourLabel (makeTourLabel).
  async function loadMediaModel(base) {
    var idx = await parseToIndex(await fetchCatalogText(base));
    var m = buildMediaRecords(idx);
    return { records: m.records, tours: m.tours, people: m.people, lists: m.lists };
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
    // Data EFETIVA (?d), como o effectiveDate dos records: a da própria mídia
    // (xsd:dateTime, ou xsd:date quando só o dia é conhecido) e, na falta
    // dela, a do passeio. Só mídia sem data E sem passeio datado fica com ?d
    // não-ligado — vai pro grupo "sem-data", no fim, e fora das facetas de
    // data (FILTER sobre ?d não-ligado = falso).
    // Ordem de preferência, igual à do effectiveDate: hora de verdade
    // (xsd:dateTime) → hora ESTIMADA (ph:estimatedCaptureTime) → só o dia →
    // o dia do passeio. O IF fica não-ligado quando não há nem uma nem outra.
    W.push('OPTIONAL { ?m dcterms:date ?dm }');
    W.push('OPTIONAL { ?m ph:estimatedCaptureTime ?de }');
    W.push('OPTIONAL { ?m ph:capturedDuring ?dtour . ?dtour a ph:Tour ; dcterms:date ?dt }');
    W.push('BIND(IF(BOUND(?dm) && DATATYPE(?dm) = xsd:dateTime, ?dm, ?de) AS ?dh)');
    W.push('BIND(COALESCE(?dh, ?dm, ?dt) AS ?d)');

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
      // Pelo texto gravado, não YEAR()/MONTH(): essas só valem pra
      // xsd:dateTime, e ?d também pode ser xsd:date.
      W.push('BIND(COALESCE(SUBSTR(STR(?d), 1, 4), "sem-data") AS ?group)');
    } else if (g === 'month') {
      W.push('BIND(COALESCE(SUBSTR(STR(?d), 1, 7), "sem-data") AS ?group)');
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
    indexQuads: indexQuads,
    parseToIndex: parseToIndex,
    makeTourLabel: makeTourLabel,
    fetchCatalogText: fetchCatalogText,
    loadMediaModel: loadMediaModel,
    buildQueryFromFacets: buildQueryFromFacets,
    facetRows: facetRows,
    listMembershipQuery: listMembershipQuery,
    weekdayOf: weekdayOf,
    effectiveDate: effectiveDate,
  };
// `self` no worker da galeria (lá não há window).
})(typeof window !== 'undefined' ? window : self);
