import Toybox.Application;
import Toybox.Communications;
import Toybox.Lang;
import Toybox.Math;
import Toybox.System;
import Toybox.Time;

//! Conversa com o amora pela localização ao vivo.
//!
//! Um ciclo a cada `interval` segundos, SEMPRE uma requisição por vez (o
//! Connect IQ limita as requisições em paralelo e o enlace é o Bluetooth do
//! celular): se a transmissão está ligada, POST /live-location com a posição
//! (e a fila do que não subiu); depois POST /garmin/live pra ler quem está
//! no mapa. A segunda só parte no retorno da primeira.
//!
//! Ver nunca manda a posição: o servidor devolve lat/lng de cada pessoa e a
//! distância é calculada aqui.
class LiveClient {
    private const QUEUE_MAX = 40;        // fixes guardados sem conexão
    private const QUEUE_GAP_S = 20;      // espaçamento mínimo entre eles
    private const WATCHDOG_S = 90;       // retorno que nunca veio
    //! Uma leitura que volta VAZIA não apaga na hora quem estava na tela: a
    //! lista do servidor vive em memória e some quando ele reinicia (ou a
    //! pessoa passa um tempo sem sinal). Segura a última lista por 5 min — a
    //! idade de cada posição continua contando na tela.
    private const HOLD_S = 300;

    var server as String = "https://amora.pedalhidrografi.co";
    var name as String = "";
    var ttlS as Number = 10800;
    var interval as Number = 15;

    //! Pessoas da última leitura: [[nome, lat, lng, idade_s], …]
    var peers as Array = [];
    var total as Number = 0;
    var peersAt as Number = 0;           // quando a lista chegou (epoch s)
    var lastOkAt as Number = 0;          // último envio aceito (epoch s)
    var lastError as Number = 0;         // código da última falha (0 = nenhuma)

    private var _token as String;
    private var _busy as Boolean = false;
    private var _busySince as Number = 0;
    private var _lastCycleAt as Number = 0;
    private var _queue as Array = [];    // [[lat, lng, epoch_s], …]
    private var _sentQueue as Number = 0;
    private var _pendingFix as Array?;
    private var _thenRead as Boolean = false;   // ler as pessoas depois do envio

    // Traçado do próximo passeio, pro radar (só é buscado se o campo pedir).
    // Em metros a partir do 1º ponto: routeE = leste, routeN = norte.
    var wantRoute as Boolean = false;
    var routeE as Array<Float> = [] as Array<Float>;
    var routeN as Array<Float> = [] as Array<Float>;
    var routeLat0 as Double = 0.0d;
    var routeLng0 as Double = 0.0d;
    var routeKx as Double = 0.0d;               // metros por grau de longitude ali
    private var _routeState as Number = 0;      // 0 = nada, 1 = sei qual passeio, 2 = pronto
    private var _routeId as String = "";
    private var _routeRetryAt as Number = 0;

    function initialize() {
        _token = loadToken();
    }

    //! Token pseudônimo do aparelho: 32 hex (o backend só aceita hex e
    //! hífen), sorteado uma vez e guardado.
    private function loadToken() as String {
        try {
            var saved = Application.Storage.getValue("token");
            if (saved instanceof Lang.String && saved.length() == 32) {
                return saved;
            }
        } catch (e) {
        }
        Math.srand(System.getTimer());
        var t = "";
        for (var i = 0; i < 8; i++) {
            t += (Math.rand() & 0xFFFF).format("%04x");
        }
        try {
            Application.Storage.setValue("token", t);
        } catch (e) {
        }
        return t;
    }

    //! Chamado 1×/s. `lat`/`lng` null = sem posição. `share` = transmitir
    //! AGORA (configuração ligada E atividade rodando). `view` = ler.
    function tick(now as Number, lat as Double?, lng as Double?, heading as Number?,
                  share as Boolean, view as Boolean) as Void {
        if (_busy) {
            if (now - _busySince < WATCHDOG_S) {
                return;
            }
            _busy = false;
        }
        if (now - _lastCycleAt < interval) {
            return;
        }
        if (!share && !view) {
            return;
        }
        if (!System.getDeviceSettings().phoneConnected) {
            lastError = -104;            // BLE_CONNECTION_UNAVAILABLE
            if (share && lat != null && lng != null) {
                enqueue(lat, lng, now);
            }
            _lastCycleAt = now;
            return;
        }
        _lastCycleAt = now;
        if (share && lat != null && lng != null) {
            sendPosition(now, lat, lng, heading, view);
        } else if (view) {
            readPeers(now);
        }
    }

    private function enqueue(lat as Double, lng as Double, now as Number) as Void {
        if (_queue.size() > 0) {
            var last = _queue[_queue.size() - 1] as Array;
            if (now - (last[2] as Number) < QUEUE_GAP_S) {
                return;
            }
        }
        _queue.add([lat, lng, now]);
        if (_queue.size() > QUEUE_MAX) {
            _queue = _queue.slice(_queue.size() - QUEUE_MAX, null);
        }
    }

    private function sendPosition(now as Number, lat as Double, lng as Double,
                                  heading as Number?, thenRead as Boolean) as Void {
        var body = {
            "id" => _token,
            "name" => name,
            "lat" => lat,
            "lng" => lng,
            "ttl" => ttlS
        } as Dictionary<Object, Object>;
        if (heading != null) {
            body["heading"] = heading;
        }
        if (_queue.size() > 0) {
            var points = [] as Array<Dictionary>;
            for (var i = 0; i < _queue.size(); i++) {
                var q = _queue[i] as Array;
                points.add({ "lat" => q[0], "lng" => q[1], "age" => now - (q[2] as Number) });
            }
            body["points"] = points;
        }
        _sentQueue = _queue.size();
        _pendingFix = [lat, lng, now];
        _thenRead = thenRead;
        start(now);
        Communications.makeWebRequest(server + "/live-location", body, {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => { "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        }, method(:onSent));
    }

    function onSent(code as Number, data as Dictionary or String or Null) as Void {
        var t = Time.now().value();
        if (code == 200) {
            lastError = 0;
            lastOkAt = t;
            // Só sai da fila o que foi junto neste envio.
            if (_sentQueue >= _queue.size()) {
                _queue = [];
            } else {
                _queue = _queue.slice(_sentQueue, null);
            }
        } else {
            lastError = code;
            var fix = _pendingFix;
            if (fix != null) {
                enqueue(fix[0] as Double, fix[1] as Double, fix[2] as Number);
            }
        }
        _pendingFix = null;
        _sentQueue = 0;
        if (_thenRead && code == 200) {
            readPeers(t);
        } else {
            _busy = false;
        }
    }

    private function readPeers(now as Number) as Void {
        start(now);
        Communications.makeWebRequest(server + "/garmin/live", { "id" => _token } as Dictionary<Object, Object>, {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => { "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        }, method(:onPeers));
    }

    function onPeers(code as Number, data as Dictionary or String or Null) as Void {
        var t = Time.now().value();
        if (code == 200 && data instanceof Lang.Dictionary) {
            var p = data["p"];
            var n = data["n"];
            if (p instanceof Lang.Array) {
                lastError = 0;
                // Leitura vazia não apaga a última lista na hora (ver HOLD_S).
                if (!(p.size() == 0 && peers.size() > 0 && t - peersAt < HOLD_S)) {
                    peers = p;
                    total = (n instanceof Lang.Number) ? n : p.size();
                    peersAt = t;
                }
                if (wantRoute && _routeState < 2 && t >= _routeRetryAt) {
                    fetchRoute(t);       // segue ocupado: uma requisição por vez
                    return;
                }
                _busy = false;
                return;
            }
        }
        _busy = false;
        lastError = (code == 200) ? -1 : code;
    }

    // ── Traçado do próximo passeio ──────────────────────────────────────
    // Dois GETs em sequência, encadeados na leitura das pessoas: qual é o
    // próximo passeio (/garmin/list?glance=1) e o traçado dele
    // (/garmin/item/t/<id>). Falhou: tenta de novo em 5 min; sem passeio
    // próximo: olha de novo em 30 min.

    private function fetchRoute(now as Number) as Void {
        start(now);
        var opts = {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };
        if (_routeState == 0) {
            Communications.makeWebRequest(server + "/garmin/list",
                { "glance" => "1" } as Dictionary<Object, Object>, opts, method(:onNextTour));
        } else {
            Communications.makeWebRequest(server + "/garmin/item/t/" + _routeId,
                { "pts" => "200" } as Dictionary<Object, Object>, opts, method(:onRoute));
        }
    }

    function onNextTour(code as Number, data as Dictionary or String or Null) as Void {
        var t = Time.now().value();
        if (code == 200 && data instanceof Lang.Dictionary) {
            var next = data["next"];
            if (next instanceof Lang.Dictionary && next["id"] instanceof Lang.String) {
                _routeId = next["id"] as String;
                _routeState = 1;
                fetchRoute(t);
                return;
            }
            _routeRetryAt = t + 1800;
        } else {
            _routeRetryAt = t + 300;
        }
        _busy = false;
    }

    function onRoute(code as Number, data as Dictionary or String or Null) as Void {
        _busy = false;
        if (code == 200 && data instanceof Lang.Dictionary) {
            var pts = data["pts"];
            if (pts instanceof Lang.Array && setRoute(pts)) {
                _routeState = 2;
                return;
            }
        }
        _routeState = 0;
        _routeRetryAt = Time.now().value() + 300;
    }

    //! [[lat, lng], …] → metros a partir do 1º ponto (equiretangular).
    private function setRoute(pts as Array) as Boolean {
        var e = [] as Array<Float>;
        var n = [] as Array<Float>;
        var lat0 = 0.0d;
        var lng0 = 0.0d;
        var kx = 0.0d;
        for (var i = 0; i < pts.size(); i++) {
            var p = pts[i];
            if (!(p instanceof Lang.Array) || p.size() < 2) {
                continue;
            }
            var la = p[0];
            var lo = p[1];
            if (!(la instanceof Lang.Float || la instanceof Lang.Double)
                    || !(lo instanceof Lang.Float || lo instanceof Lang.Double)) {
                continue;
            }
            var lat = la.toDouble();
            var lng = lo.toDouble();
            if (e.size() == 0) {
                lat0 = lat;
                lng0 = lng;
                kx = 111320.0d * Math.cos(Math.toRadians(lat0));
            }
            e.add(((lng - lng0) * kx).toFloat());
            n.add(((lat - lat0) * 110540.0d).toFloat());
        }
        if (e.size() < 2) {
            return false;
        }
        routeE = e;
        routeN = n;
        routeLat0 = lat0;
        routeLng0 = lng0;
        routeKx = kx;
        return true;
    }

    private function start(now as Number) as Void {
        _busy = true;
        _busySince = now;
    }

    function queued() as Number {
        return _queue.size();
    }
}
