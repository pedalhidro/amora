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
        _busy = false;
        if (code == 200 && data instanceof Lang.Dictionary) {
            var p = data["p"];
            var n = data["n"];
            if (p instanceof Lang.Array) {
                peers = p;
                total = (n instanceof Lang.Number) ? n : p.size();
                peersAt = Time.now().value();
                lastError = 0;
                return;
            }
        }
        lastError = (code == 200) ? -1 : code;
    }

    private function start(now as Number) as Void {
        _busy = true;
        _busySince = now;
    }

    function queued() as Number {
        return _queue.size();
    }
}
