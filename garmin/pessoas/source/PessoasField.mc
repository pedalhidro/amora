import Toybox.Activity;
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.Time;
import Toybox.WatchUi;

//! Campo de dados "Pessoas ao vivo".
//!
//! Mostra a pessoa mais próxima entre as que transmitem a posição no amora
//! (distância, seta de direção relativa ao seu rumo, apelido) e quantas mais
//! há. Com "Transmitir minha posição" ligado nas configurações — e SÓ com a
//! atividade rodando — manda a sua, sem depender da tela do celular.
//!
//! Privacidade, como no amora: transmitir nasce desligado; ver não manda
//! posição nenhuma; a barra de estado diz sempre se está transmitindo.
class PessoasField extends WatchUi.DataField {
    private const STALE_S = 180;          // posição velha: distância em cinza

    private var _client as LiveClient;
    private var _share as Boolean = false;

    private var _lat as Double?;
    private var _lng as Double?;
    private var _heading as Number?;      // graus, 0 = norte
    private var _running as Boolean = false;
    private var _recording as Boolean = false;
    private var _visible as Boolean = false;

    function initialize() {
        DataField.initialize();
        _client = new LiveClient();
        loadSettings();
    }

    function loadSettings() as Void {
        _share = false;
        try {
            var s = Application.Properties.getValue("share");
            _share = (s instanceof Lang.Boolean) && s;
            var n = Application.Properties.getValue("name");
            _client.name = (n instanceof Lang.String && n.length() > 0) ? n : "Garmin";
            var ttl = Application.Properties.getValue("ttl");
            if (ttl instanceof Lang.Number && ttl >= 1 && ttl <= 24) {
                _client.ttlS = ttl * 3600;
            }
            var iv = Application.Properties.getValue("interval");
            if (iv instanceof Lang.Number && iv >= 10 && iv <= 120) {
                _client.interval = iv;
            }
            var srv = Application.Properties.getValue("server");
            if (srv instanceof Lang.String && srv.find("https://") == 0) {
                // sem barra no fim: os caminhos são concatenados
                var len = srv.length();
                var trimmed = srv.substring(0, len - 1);
                var last = srv.substring(len - 1, len);
                _client.server = (trimmed != null && last != null && last.equals("/"))
                    ? trimmed : srv;
            }
        } catch (e) {
            // propriedade ausente: transmitir fica desligado
        }
    }

    function onShow() as Void {
        _visible = true;
    }

    function onHide() as Void {
        _visible = false;
    }

    function onTimerStart() as Void {
        _running = true;
        _recording = true;
    }

    function onTimerResume() as Void {
        _running = true;
    }

    function onTimerPause() as Void {
        _running = false;
    }

    function onTimerStop() as Void {
        _running = false;
    }

    function onTimerReset() as Void {
        _running = false;
        _recording = false;
    }

    function compute(info as Activity.Info) as Void {
        var state = info.timerState;
        if (state != null) {
            _running = (state == Activity.TIMER_STATE_ON);
            _recording = (state != Activity.TIMER_STATE_OFF);
        }
        var loc = info.currentLocation;
        if (loc != null) {
            var deg = loc.toDegrees();
            _lat = deg[0];
            _lng = deg[1];
        }
        var hd = info.currentHeading;
        if (hd != null) {
            var d = Math.toDegrees(hd).toNumber() % 360;
            _heading = d < 0 ? d + 360 : d;
        }
        // Transmite só com a configuração ligada E o timer andando; lê
        // enquanto há atividade gravando ou o campo está na tela.
        _client.tick(Time.now().value(), _lat, _lng, _heading,
                     _share && _running, _recording || _visible);
    }

    // ── Geometria (equiretangular: sobra pra distâncias de pedal) ───────

    //! [distância em m, rumo em graus] de mim até (lat, lng), ou null.
    private function toPeer(lat as Numeric, lng as Numeric) as Array<Float>? {
        var myLat = _lat;
        var myLng = _lng;
        if (myLat == null || myLng == null) {
            return null;
        }
        var dy = (lat.toDouble() - myLat) * 110540.0d;
        var dx = (lng.toDouble() - myLng) * 111320.0d * Math.cos(Math.toRadians(myLat));
        var dist = Math.sqrt(dx * dx + dy * dy).toFloat();
        var brg = Math.toDegrees(Math.atan2(dx, dy)).toFloat();
        if (brg < 0.0) {
            brg += 360.0;
        }
        return [dist, brg] as Array<Float>;
    }

    private function distLabel(m as Float) as String {
        if (m < 1000.0) {
            return (((m / 10.0) + 0.5).toNumber() * 10).format("%d") + " m";
        } else if (m < 10000.0) {
            return (m / 1000.0).format("%.1f") + " km";
        }
        return (m / 1000.0).format("%.0f") + " km";
    }

    // ── Tela ────────────────────────────────────────────────────────────

    function onUpdate(dc as Graphics.Dc) as Void {
        var bg = getBackgroundColor();
        var fg = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_WHITE : Graphics.COLOR_BLACK;
        dc.setColor(fg, bg);
        dc.clear();
        dc.setColor(fg, Graphics.COLOR_TRANSPARENT);

        var w = dc.getWidth();
        var h = dc.getHeight();
        var cx = w / 2;
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);
        var now = Time.now().value();

        // Barra de estado na base: sempre diz se está transmitindo.
        var status = statusLine(now);
        var sharing = _share && _running;
        dc.setColor(sharing ? Graphics.COLOR_DK_GREEN : Graphics.COLOR_DK_GRAY,
                    Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(0, h - 3, w, 3);
        dc.setColor(fg, Graphics.COLOR_TRANSPARENT);
        if (h >= 70) {
            dc.drawText(cx, h - 3 - smallH, small, status, Graphics.TEXT_JUSTIFY_CENTER);
        }

        // A pessoa mais próxima.
        var best = null as Array?;
        var bestGeo = null as Array<Float>?;
        var peers = _client.peers;
        for (var i = 0; i < peers.size(); i++) {
            var p = peers[i];
            if (!(p instanceof Lang.Array) || p.size() < 4) {
                continue;
            }
            var la = p[1];
            var lo = p[2];
            if (!(la instanceof Lang.Float || la instanceof Lang.Double || la instanceof Lang.Number)
                    || !(lo instanceof Lang.Float || lo instanceof Lang.Double || lo instanceof Lang.Number)) {
                continue;
            }
            var geo = toPeer(la, lo);
            if (geo != null && (bestGeo == null || geo[0] < bestGeo[0])) {
                best = p;
                bestGeo = geo;
            }
        }

        if (peers.size() == 0) {
            var msg = (_client.peersAt == 0) ? "..." : "ninguém ao vivo";
            dc.drawText(cx, (h - dc.getFontHeight(Graphics.FONT_SMALL)) / 2 - (h >= 70 ? smallH / 2 : 0),
                        Graphics.FONT_SMALL, msg, Graphics.TEXT_JUSTIFY_CENTER);
            return;
        }
        if (best == null || bestGeo == null) {
            // Há pessoas, mas ainda não sei onde EU estou.
            dc.drawText(cx, (h - dc.getFontHeight(Graphics.FONT_SMALL)) / 2,
                        Graphics.FONT_SMALL, _client.total.format("%d") + " ao vivo",
                        Graphics.TEXT_JUSTIFY_CENTER);
            return;
        }

        var name = (best[0] instanceof Lang.String) ? best[0] as String : "?";
        var age = (best[3] instanceof Lang.Number) ? (best[3] as Number) + (now - _client.peersAt) : 0;
        var top = 2;
        // Em cima: quem é, quantas mais e HÁ QUANTO TEMPO é essa posição — na
        // forma mais longa que couber no campo.
        var ago = ageLabel(age);
        var line1 = name + " · " + ago;
        if (_client.total > 1) {
            var withCount = name + " +" + (_client.total - 1).format("%d") + " · " + ago;
            if (dc.getTextWidthInPixels(withCount, small) <= w - 4) {
                line1 = withCount;
            }
        }
        if (dc.getTextWidthInPixels(line1, small) > w - 4) {
            line1 = ago;
        }
        dc.drawText(cx, top, small, line1, Graphics.TEXT_JUSTIFY_CENTER);

        var bodyTop = top + smallH;
        var bodyH = h - 3 - bodyTop - (h >= 70 ? smallH : 0);
        var text = distLabel(bestGeo[0]);
        if (age > STALE_S) {
            // Posição velha: a pessoa pode não estar mais ali.
            dc.setColor(bg == Graphics.COLOR_BLACK ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_DK_GRAY,
                        Graphics.COLOR_TRANSPARENT);
        }
        var font = pickFont(dc, text, w - bodyH - 8, bodyH);
        var fh = dc.getFontHeight(font);
        var tw = dc.getTextWidthInPixels(text, font);
        var arrowR = (bodyH < 40 ? bodyH : 40) / 2 - 2;
        var gap = 6;
        var x0 = (w - (tw + gap + 2 * arrowR)) / 2;
        if (arrowR >= 6 && _heading != null) {
            drawArrow(dc, x0 + arrowR, bodyTop + bodyH / 2, arrowR,
                      bestGeo[1] - (_heading as Number).toFloat());
            dc.drawText(x0 + 2 * arrowR + gap, bodyTop + (bodyH - fh) / 2, font, text,
                        Graphics.TEXT_JUSTIFY_LEFT);
        } else {
            dc.drawText(cx, bodyTop + (bodyH - fh) / 2, font, text, Graphics.TEXT_JUSTIFY_CENTER);
        }
    }

    //! "há 30 s", "há 2 min", "há 1 h".
    private function ageLabel(s as Number) as String {
        if (s < 0) {
            s = 0;
        }
        if (s < 60) {
            return "há " + s.format("%d") + " s";
        } else if (s < 3600) {
            return "há " + (s / 60).format("%d") + " min";
        }
        return "há " + (s / 3600).format("%d") + " h";
    }

    private function statusLine(now as Number) as String {
        if (_client.lastError == -104) {
            return "sem celular";
        }
        if (_share && _running) {
            if (_client.queued() > 0) {
                return "transmitindo (" + _client.queued().format("%d") + " na fila)";
            }
            if (_client.lastOkAt > 0 && now - _client.lastOkAt > 60) {
                return "sem enviar há " + ((now - _client.lastOkAt) / 60).format("%d") + " min";
            }
            return "transmitindo";
        }
        if (_client.lastError != 0) {
            return "erro " + _client.lastError.format("%d");
        }
        return _share ? "transmite ao iniciar" : "só vendo";
    }

    //! Seta apontando `relDeg` graus à direita do topo do campo (0 = em frente).
    private function drawArrow(dc as Graphics.Dc, cx as Number, cy as Number, r as Number,
                               relDeg as Float) as Void {
        var a = Math.toRadians(relDeg);
        var sin = Math.sin(a);
        var cos = Math.cos(a);
        // Triângulo com a ponta pra cima, girado: (x, y) → (x·cos − y·sin, x·sin + y·cos)
        var pts = [[0.0, -1.0], [0.7, 0.8], [0.0, 0.4], [-0.7, 0.8]];
        var out = [] as Array<Graphics.Point2D>;
        for (var i = 0; i < pts.size(); i++) {
            var px = pts[i][0] * r;
            var py = pts[i][1] * r;
            out.add([cx + px * cos - py * sin, cy + px * sin + py * cos] as Graphics.Point2D);
        }
        dc.fillPolygon(out);
    }

    private function pickFont(dc as Graphics.Dc, text as String, maxW as Number,
                              maxH as Number) as Graphics.FontDefinition {
        var fonts = [Graphics.FONT_LARGE, Graphics.FONT_MEDIUM, Graphics.FONT_SMALL,
                     Graphics.FONT_TINY] as Array<Graphics.FontDefinition>;
        for (var i = 0; i < fonts.size(); i++) {
            var dims = dc.getTextDimensions(text, fonts[i]);
            if (dims[0] <= maxW && dims[1] <= maxH) {
                return fonts[i];
            }
        }
        return Graphics.FONT_XTINY;
    }
}
