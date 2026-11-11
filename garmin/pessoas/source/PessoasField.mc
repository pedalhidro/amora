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
    // Campo com pelo menos RADAR_MIN vira o radar COMPLETO (linha de cima,
    // nomes, barra de estado). Entre MINI_MIN e isso — as telas de 8–10
    // campos — vira o radar MINI: o círculo à esquerda e, ao lado, distância
    // e idade da pessoa mais próxima. Menor que MINI_MIN, só o resumo.
    private const RADAR_MIN_W = 160;
    private const RADAR_MIN_H = 190;
    private const MINI_MIN_W = 90;
    private const MINI_MIN_H = 60;

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

        if (w >= RADAR_MIN_W && h >= RADAR_MIN_H) {
            _client.wantRoute = true;
            drawRadar(dc, fg, bg, now, best, bestGeo);
            return;
        }
        if (w >= MINI_MIN_W && h >= MINI_MIN_H) {
            _client.wantRoute = true;
            // A barra de estado de cima escreveu o texto dela; o mini usa o
            // campo todo, então limpa e deixa só a faixa colorida.
            dc.setColor(fg, bg);
            dc.clear();
            dc.setColor(sharing ? Graphics.COLOR_DK_GREEN : Graphics.COLOR_DK_GRAY,
                        Graphics.COLOR_TRANSPARENT);
            dc.fillRectangle(0, h - 3, w, 3);
            drawMiniRadar(dc, fg, bg, now, best, bestGeo);
            return;
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

    // ── Radar ───────────────────────────────────────────────────────────
    //
    // Você no centro, com o SUL SEMPRE PRA CIMA (a agulha do coletivo aponta
    // pro sul; o radar não gira com o seu rumo — quem gira é a seta do centro).
    // As pessoas são pontos na posição relativa de verdade; dois anéis dão a
    // escala (o de fora é o alcance, escolhido pra caber a pessoa mais
    // próxima); quem está além do alcance vira um anel oco na borda. A linha
    // laranja é o traçado do próximo passeio. Não é o mapa do aparelho — um
    // campo de dados não tem acesso a ele.

    //! Alcance "redondo" que contém a distância d (m).
    private function radarRange(d as Float) as Float {
        var steps = [250.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0, 25000.0, 50000.0] as Array<Float>;
        for (var i = 0; i < steps.size(); i++) {
            if (d * 1.15 <= steps[i]) {
                return steps[i];
            }
        }
        return 100000.0;
    }

    //! Radar completo: linha de cima + radar com nomes + barra de estado.
    private function drawRadar(dc as Graphics.Dc, fg as Graphics.ColorType, bg as Graphics.ColorType,
                               now as Number, best as Array?, bestGeo as Array<Float>?) as Void {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var cx = w / 2;
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);
        var peers = _client.peers;

        // Linha de cima: quem é a mais próxima, a quanto e há quanto tempo.
        var line = "";
        if (best != null && bestGeo != null) {
            var nm = (best[0] instanceof Lang.String) ? best[0] as String : "?";
            var age = (best[3] instanceof Lang.Number) ? (best[3] as Number) + (now - _client.peersAt) : 0;
            var dist = distLabel(bestGeo[0]);
            var ago = ageLabel(age);
            line = nm + " · " + dist + " · " + ago;
            if (dc.getTextWidthInPixels(line, small) > w - 4) {
                line = dist + " · " + ago;
            }
            if (dc.getTextWidthInPixels(line, small) > w - 4) {
                line = dist;
            }
        } else if (peers.size() == 0) {
            line = (_client.peersAt == 0) ? "..." : "ninguém ao vivo";
        } else {
            line = _client.total.format("%d") + " ao vivo";
        }
        dc.setColor(fg, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, 2, small, line, Graphics.TEXT_JUSTIFY_CENTER);

        // Área do radar: entre a linha de cima e a barra de estado.
        var top = 2 + smallH + 2;
        var bottom = h - 3 - smallH - 2;
        var r = ((w < bottom - top) ? w : (bottom - top)) / 2 - 6;
        if (r < 30) {
            return;
        }
        var range = (bestGeo != null) ? radarRange(bestGeo[0]) : 500.0;
        plotRadar(dc, cx, (top + bottom) / 2, r, range, fg, bg, now, best, false);
    }

    //! Radar mini (telas de muitos campos): o círculo ocupa a altura do campo,
    //! à esquerda; ao lado, a distância da pessoa mais próxima, a idade da
    //! posição e o alcance do anel. Sem nomes no círculo — não cabem.
    private function drawMiniRadar(dc as Graphics.Dc, fg as Graphics.ColorType, bg as Graphics.ColorType,
                                   now as Number, best as Array?, bestGeo as Array<Float>?) as Void {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);
        var gray = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_DK_GRAY;

        var d = h - 8;                     // diâmetro: a altura, menos a faixa e a folga
        if (d > w - 4) {
            d = w - 4;
        }
        var r = d / 2;
        if (r < 18) {
            return;
        }
        var colW = w - d - 8;              // coluna de texto à direita do círculo
        var cx = (colW >= 36) ? 3 + r : w / 2;
        var cy = (h - 3) / 2;
        var range = (bestGeo != null) ? radarRange(bestGeo[0]) : 500.0;
        plotRadar(dc, cx, cy, r, range, fg, bg, now, best, true);

        if (colW < 36) {
            return;                        // campo quase quadrado: só o círculo
        }
        var tx = 3 + d + 5;
        var lines = [] as Array<String>;
        if (best != null && bestGeo != null) {
            var age = (best[3] instanceof Lang.Number) ? (best[3] as Number) + (now - _client.peersAt) : 0;
            lines.add(distLabel(bestGeo[0]));
            lines.add(ageShort(age));
        } else if (_client.peers.size() == 0) {
            lines.add((_client.peersAt == 0) ? "..." : "0");
        } else {
            lines.add(_client.total.format("%d"));
        }
        var maxLines = (h - 6) / smallH;
        var y = (h - 3 - ((lines.size() < maxLines ? lines.size() : maxLines) * smallH)) / 2;
        dc.setColor(fg, Graphics.COLOR_TRANSPARENT);
        for (var i = 0; i < lines.size() && i < maxLines; i++) {
            if (i == 1) {
                dc.setColor(gray, Graphics.COLOR_TRANSPARENT);   // a idade, mais apagada
            }
            if (dc.getTextWidthInPixels(lines[i], small) <= colW + 3) {
                dc.drawText(tx, y, small, lines[i], Graphics.TEXT_JUSTIFY_LEFT);
            }
            y += smallH;
        }
    }

    //! O desenho do radar em si, centrado em (cx, cy) com raio r px e alcance
    //! `range` m. `mini` = sem nomes, sem rótulo de alcance, traços menores.
    private function plotRadar(dc as Graphics.Dc, cx as Number, cy as Number, r as Number,
                               range as Float, fg as Graphics.ColorType, bg as Graphics.ColorType,
                               now as Number, best as Array?, mini as Boolean) as Void {
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);
        var gray = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_DK_GRAY;
        var peers = _client.peers;
        var scale = r.toFloat() / range;            // px por metro

        // Anéis (+ alcance, no radar completo).
        dc.setColor(gray, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(1);
        dc.drawCircle(cx, cy, r);
        dc.drawCircle(cx, cy, r / 2);
        if (!mini) {
            dc.drawText(cx, cy + r - smallH - 1, small, distLabel(range), Graphics.TEXT_JUSTIFY_CENTER);
        }

        var myLat = _lat;
        var myLng = _lng;
        if (myLat == null || myLng == null) {
            dc.setColor(fg, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, cy - smallH / 2, small, mini ? "GPS?" : "sem GPS", Graphics.TEXT_JUSTIFY_CENTER);
            return;
        }

        // Sul pra cima, fixo: (leste, norte) → (x pra direita, y pra cima) com
        // uma rotação de 180° — o leste cai à esquerda, o oeste à direita.
        var hd = _heading;
        var cosT = -1.0;
        var sinT = 0.0;

        // "S" no topo do anel (no mini não cabe: fica só a convenção).
        if (!mini) {
            dc.drawText(cx, cy - r, small, "S",
                        Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        }

        // Traçado do próximo passeio.
        var re = _client.routeE;
        var rn = _client.routeN;
        if (re.size() >= 2) {
            var meE = ((myLng - _client.routeLng0) * _client.routeKx).toFloat();
            var meN = ((myLat - _client.routeLat0) * 110540.0d).toFloat();
            var lim = 3.0 * r;                      // trecho todo fora daqui: pula
            var lim2 = lim * lim;
            dc.setColor(Graphics.COLOR_ORANGE, Graphics.COLOR_TRANSPARENT);
            dc.setPenWidth(mini ? 2 : 3);
            var e0 = re[0] - meE;
            var n0 = rn[0] - meN;
            var ax = (e0 * cosT - n0 * sinT) * scale;
            var ay = (e0 * sinT + n0 * cosT) * scale;
            for (var i = 1; i < re.size(); i++) {
                var e1 = re[i] - meE;
                var n1 = rn[i] - meN;
                var bx = (e1 * cosT - n1 * sinT) * scale;
                var by = (e1 * sinT + n1 * cosT) * scale;
                if (ax * ax + ay * ay <= lim2 || bx * bx + by * by <= lim2) {
                    dc.drawLine(cx + ax.toNumber(), cy - ay.toNumber(),
                                cx + bx.toNumber(), cy - by.toNumber());
                }
                ax = bx;
                ay = by;
            }
            dc.setPenWidth(1);
        }

        // As pessoas.
        var kx = 111320.0d * Math.cos(Math.toRadians(myLat));
        var labels = 0;
        for (var j = 0; j < peers.size(); j++) {
            var p = peers[j];
            if (!(p instanceof Lang.Array) || p.size() < 4) {
                continue;
            }
            var la = p[1];
            var lo = p[2];
            if (!(la instanceof Lang.Float || la instanceof Lang.Double || la instanceof Lang.Number)
                    || !(lo instanceof Lang.Float || lo instanceof Lang.Double || lo instanceof Lang.Number)) {
                continue;
            }
            var pe = ((lo.toDouble() - myLng) * kx).toFloat();
            var pn = ((la.toDouble() - myLat) * 110540.0d).toFloat();
            var px = (pe * cosT - pn * sinT) * scale;
            var py = (pe * sinT + pn * cosT) * scale;
            var dpx = Math.sqrt(px * px + py * py).toFloat();
            var pAge = (p[3] instanceof Lang.Number) ? (p[3] as Number) + (now - _client.peersAt) : 0;
            var nearest = (p == best);
            var color = (pAge > STALE_S) ? gray : (nearest ? Graphics.COLOR_BLUE : fg);
            dc.setColor(color, Graphics.COLOR_TRANSPARENT);
            if (dpx > r) {
                // Além do alcance: anel oco na borda, na direção certa.
                var k = r.toFloat() / dpx;
                dc.drawCircle(cx + (px * k).toNumber(), cy - (py * k).toNumber(), mini ? 3 : 4);
                continue;
            }
            var sx = cx + px.toNumber();
            var sy = cy - py.toNumber();
            dc.fillCircle(sx, sy, mini ? (nearest ? 5 : 3) : (nearest ? 7 : 5));
            if (!mini && (nearest || labels < 3) && p[0] instanceof Lang.String) {
                var label = p[0] as String;
                if (label.length() > 8) {
                    var cutLabel = label.substring(0, 8);
                    label = (cutLabel != null) ? cutLabel : label;
                }
                dc.drawText(sx + 10, sy - smallH / 2, small, label, Graphics.TEXT_JUSTIFY_LEFT);
                labels += 1;
            }
        }

        // Você: seta no SEU rumo (com o sul pra cima, rumo norte = seta pra
        // baixo — por isso os 180°); sem rumo, um ponto.
        dc.setColor(fg, Graphics.COLOR_TRANSPARENT);
        if (hd != null) {
            drawArrow(dc, cx, cy, mini ? 7 : 11, hd.toFloat() + 180.0);
        } else {
            dc.fillCircle(cx, cy, mini ? 3 : 5);
        }
    }

    //! Idade curta pro radar mini: "30 s", "2 min", "1 h".
    private function ageShort(s as Number) as String {
        if (s < 0) {
            s = 0;
        }
        if (s < 60) {
            return s.format("%d") + " s";
        } else if (s < 3600) {
            return (s / 60).format("%d") + " min";
        }
        return (s / 3600).format("%d") + " h";
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
