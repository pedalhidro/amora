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
    //
    // A PILHA de um campo de dados é curta: o que conta é a soma das variáveis
    // locais de todas as funções abertas ao mesmo tempo. A 1ª versão do radar
    // morreu de "Stack Overflow Error" no simulador com uma função de ~45
    // locais chamada por outra de ~18, chamada pelo onUpdate (~20). Por isso o
    // desenho é uma FILA de funções pequenas, chamadas uma depois da outra, e o
    // que elas compartilham (cores, centro/raio/escala do radar, a pessoa mais
    // próxima) mora em campos do objeto — não em argumentos nem em locais.
    // Ao mexer aqui: função nova e curta, nunca mais locais numa que já existe.

    private var _fg as Graphics.ColorType = Graphics.COLOR_WHITE;
    private var _gray as Graphics.ColorType = Graphics.COLOR_LT_GRAY;
    private var _now as Number = 0;
    private var _best as Array? = null;       // a mais próxima: [nome, lat, lng, idade]
    private var _bestDist as Float = -1.0;    // m (< 0 = não há)
    private var _bestBrg as Float = 0.0;      // rumo até ela, graus
    private var _rcx as Number = 0;           // radar: centro (px)…
    private var _rcy as Number = 0;
    private var _rr as Number = 0;            // …raio (px)…
    private var _rRange as Float = 500.0;     // …alcance (m)…
    private var _rScale as Float = 1.0;       // …e escala (px por metro)
    private var _rMini as Boolean = false;

    function onUpdate(dc as Graphics.Dc) as Void {
        var bg = getBackgroundColor();
        _fg = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_WHITE : Graphics.COLOR_BLACK;
        _gray = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_DK_GRAY;
        _now = Time.now().value();
        dc.setColor(_fg, bg);
        dc.clear();
        findNearest();
        var w = dc.getWidth();
        var h = dc.getHeight();
        if (w >= RADAR_MIN_W && h >= RADAR_MIN_H) {
            // Radar completo: linha de cima + radar com nomes + estado.
            _client.wantRoute = true;
            drawStatus(dc, true);
            drawTopLine(dc);
            layoutFull(dc);
            drawRadar(dc);
        } else if (w >= MINI_MIN_W && h >= MINI_MIN_H) {
            // Radar mini: círculo à esquerda, distância e idade ao lado.
            _client.wantRoute = true;
            drawStatus(dc, false);
            layoutMini(dc);
            drawRadar(dc);
            drawMiniText(dc);
        } else {
            drawStatus(dc, h >= 70);
            drawCompact(dc);
        }
    }

    // ── A pessoa mais próxima ───────────────────────────────────────────

    private function findNearest() as Void {
        _best = null;
        _bestDist = -1.0;
        var peers = _client.peers;
        for (var i = 0; i < peers.size(); i++) {
            var p = peers[i];
            if (!(p instanceof Lang.Array) || p.size() < 4) {
                continue;
            }
            var geo = peerGeo(p);
            if (geo != null && (_bestDist < 0.0 || geo[0] < _bestDist)) {
                _best = p;
                _bestDist = geo[0];
                _bestBrg = geo[1];
            }
        }
    }

    //! [distância, rumo] até a pessoa `p`, ou null (sem a minha posição).
    private function peerGeo(p as Array) as Array<Float>? {
        var la = p[1];
        var lo = p[2];
        if (!(la instanceof Lang.Float || la instanceof Lang.Double || la instanceof Lang.Number)
                || !(lo instanceof Lang.Float || lo instanceof Lang.Double || lo instanceof Lang.Number)) {
            return null;
        }
        return toPeer(la, lo);
    }

    //! Idade (s) da posição de uma pessoa da lista, agora.
    private function peerAge(p as Array?) as Number {
        if (p != null && p[3] instanceof Lang.Number) {
            return (p[3] as Number) + (_now - _client.peersAt);
        }
        return 0;
    }

    private function bestName() as String {
        var b = _best;
        return (b != null && b[0] instanceof Lang.String) ? b[0] as String : "?";
    }

    // ── Peças comuns ────────────────────────────────────────────────────

    //! Faixa de estado na base (verde = transmitindo) e, se couber, o texto.
    private function drawStatus(dc as Graphics.Dc, withText as Boolean) as Void {
        var w = dc.getWidth();
        var h = dc.getHeight();
        dc.setColor((_share && _running) ? Graphics.COLOR_DK_GREEN : Graphics.COLOR_DK_GRAY,
                    Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(0, h - 3, w, 3);
        dc.setColor(_fg, Graphics.COLOR_TRANSPARENT);
        if (withText) {
            dc.drawText(w / 2, h - 3 - dc.getFontHeight(Graphics.FONT_XTINY), Graphics.FONT_XTINY,
                        statusLine(_now), Graphics.TEXT_JUSTIFY_CENTER);
        }
    }

    //! Linha de cima do radar completo: quem, a quanto, há quanto tempo.
    private function drawTopLine(dc as Graphics.Dc) as Void {
        var w = dc.getWidth();
        var small = Graphics.FONT_XTINY;
        var line = "";
        if (_bestDist >= 0.0) {
            var dist = distLabel(_bestDist);
            var ago = ageLabel(peerAge(_best));
            line = bestName() + " · " + dist + " · " + ago;
            if (dc.getTextWidthInPixels(line, small) > w - 4) {
                line = dist + " · " + ago;
            }
            if (dc.getTextWidthInPixels(line, small) > w - 4) {
                line = dist;
            }
        } else if (_client.peers.size() == 0) {
            line = (_client.peersAt == 0) ? "..." : "ninguém ao vivo";
        } else {
            line = _client.total.format("%d") + " ao vivo";
        }
        dc.setColor(_fg, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w / 2, 2, small, line, Graphics.TEXT_JUSTIFY_CENTER);
    }

    // ── Radar ───────────────────────────────────────────────────────────
    //
    // Você no centro, com o SUL SEMPRE PRA CIMA (a agulha do coletivo aponta
    // pro sul; o radar não gira com o seu rumo — quem gira é a seta do centro).
    // Na tela: x = centro − leste·escala, y = centro + norte·escala. As pessoas
    // são pontos na posição relativa de verdade; dois anéis dão a escala (o de
    // fora é o alcance, escolhido pra caber a pessoa mais próxima); quem está
    // além do alcance vira um anel oco na borda. A linha laranja é o traçado
    // do próximo passeio. Não é o mapa do aparelho — um campo de dados não tem
    // acesso a ele.

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

    private function setScale() as Void {
        _rRange = (_bestDist >= 0.0) ? radarRange(_bestDist) : 500.0;
        _rScale = (_rr > 0 ? _rr : 1).toFloat() / _rRange;
    }

    //! Radar completo: entre a linha de cima e a barra de estado.
    private function layoutFull(dc as Graphics.Dc) as Void {
        var w = dc.getWidth();
        var smallH = dc.getFontHeight(Graphics.FONT_XTINY);
        var top = 2 + smallH + 2;
        var bottom = dc.getHeight() - 3 - smallH - 2;
        _rr = ((w < bottom - top) ? w : (bottom - top)) / 2 - 6;
        _rcx = w / 2;
        _rcy = (top + bottom) / 2;
        _rMini = false;
        setScale();
    }

    //! Radar mini: o círculo ocupa a altura do campo, à esquerda se sobrar
    //! uma coluna de texto (≥ 36 px), senão no meio.
    private function layoutMini(dc as Graphics.Dc) as Void {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var d = h - 8;
        if (d > w - 4) {
            d = w - 4;
        }
        _rr = d / 2;
        _rcx = (w - d - 8 >= 36) ? 3 + _rr : w / 2;
        _rcy = (h - 3) / 2;
        _rMini = true;
        setScale();
    }

    private function drawRadar(dc as Graphics.Dc) as Void {
        if (_rr < 18) {
            return;
        }
        radarRings(dc);
        if (_lat == null || _lng == null) {
            dc.setColor(_fg, Graphics.COLOR_TRANSPARENT);
            dc.drawText(_rcx, _rcy - dc.getFontHeight(Graphics.FONT_XTINY) / 2, Graphics.FONT_XTINY,
                        _rMini ? "GPS?" : "sem GPS", Graphics.TEXT_JUSTIFY_CENTER);
            return;
        }
        radarRoute(dc);
        radarPeers(dc);
        radarMe(dc);
    }

    //! Anéis; no radar completo, também o alcance e o "S" no topo.
    private function radarRings(dc as Graphics.Dc) as Void {
        dc.setColor(_gray, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(1);
        dc.drawCircle(_rcx, _rcy, _rr);
        dc.drawCircle(_rcx, _rcy, _rr / 2);
        if (_rMini) {
            return;
        }
        var small = Graphics.FONT_XTINY;
        dc.drawText(_rcx, _rcy + _rr - dc.getFontHeight(small) - 1, small, distLabel(_rRange),
                    Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(_rcx, _rcy - _rr, small, "S",
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    //! Traçado do próximo passeio (LiveClient.routeE/N, em metros).
    private function radarRoute(dc as Graphics.Dc) as Void {
        var re = _client.routeE;
        var rn = _client.routeN;
        var myLat = _lat;
        var myLng = _lng;
        if (re.size() < 2 || myLat == null || myLng == null) {
            return;
        }
        var meE = ((myLng - _client.routeLng0) * _client.routeKx).toFloat();
        var meN = ((myLat - _client.routeLat0) * 110540.0d).toFloat();
        var lim2 = 9.0 * _rr * _rr;                 // trecho todo além de 3 raios: pula
        dc.setColor(Graphics.COLOR_ORANGE, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(_rMini ? 2 : 3);
        var ax = (meE - re[0]) * _rScale;           // tela, a partir do centro
        var ay = (rn[0] - meN) * _rScale;
        for (var i = 1; i < re.size(); i++) {
            var bx = (meE - re[i]) * _rScale;
            var by = (rn[i] - meN) * _rScale;
            if (ax * ax + ay * ay <= lim2 || bx * bx + by * by <= lim2) {
                dc.drawLine(_rcx + ax.toNumber(), _rcy + ay.toNumber(),
                            _rcx + bx.toNumber(), _rcy + by.toNumber());
            }
            ax = bx;
            ay = by;
        }
        dc.setPenWidth(1);
    }

    //! As pessoas: ponto (a mais próxima, azul e maior), cinza se a posição é
    //! velha, anel oco na borda se está além do alcance.
    private function radarPeers(dc as Graphics.Dc) as Void {
        var myLat = _lat;
        var myLng = _lng;
        if (myLat == null || myLng == null) {
            return;
        }
        var peers = _client.peers;
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
            var px = ((myLng - lo.toDouble()) * kx).toFloat() * _rScale;
            var py = ((la.toDouble() - myLat) * 110540.0d).toFloat() * _rScale;
            var dpx = Math.sqrt(px * px + py * py).toFloat();
            var nearest = (p == _best);
            dc.setColor((peerAge(p) > STALE_S) ? _gray : (nearest ? Graphics.COLOR_BLUE : _fg),
                        Graphics.COLOR_TRANSPARENT);
            if (dpx > _rr) {
                dc.drawCircle(_rcx + (px * _rr / dpx).toNumber(), _rcy + (py * _rr / dpx).toNumber(),
                              _rMini ? 3 : 4);
                continue;
            }
            dc.fillCircle(_rcx + px.toNumber(), _rcy + py.toNumber(),
                          _rMini ? (nearest ? 5 : 3) : (nearest ? 7 : 5));
            if (!_rMini && (nearest || labels < 3)) {
                peerLabel(dc, p, _rcx + px.toNumber() + 10, _rcy + py.toNumber());
                labels += 1;
            }
        }
    }

    //! Nome (até 8 letras) ao lado do ponto de uma pessoa.
    private function peerLabel(dc as Graphics.Dc, p as Array, x as Number, y as Number) as Void {
        var label = p[0];
        if (!(label instanceof Lang.String)) {
            return;
        }
        if (label.length() > 8) {
            var cut = label.substring(0, 8);
            if (cut != null) {
                label = cut;
            }
        }
        dc.drawText(x, y - dc.getFontHeight(Graphics.FONT_XTINY) / 2, Graphics.FONT_XTINY, label,
                    Graphics.TEXT_JUSTIFY_LEFT);
    }

    //! Você: seta no SEU rumo (com o sul pra cima, rumo norte = seta pra
    //! baixo — por isso os 180°); sem rumo, um ponto.
    private function radarMe(dc as Graphics.Dc) as Void {
        var hd = _heading;
        dc.setColor(_fg, Graphics.COLOR_TRANSPARENT);
        if (hd != null) {
            drawArrow(dc, _rcx, _rcy, _rMini ? 7 : 11, hd.toFloat() + 180.0);
        } else {
            dc.fillCircle(_rcx, _rcy, _rMini ? 3 : 5);
        }
    }

    //! Texto ao lado do radar mini: distância e idade da mais próxima (ou
    //! quantas pessoas há). Só desenha se sobrar uma coluna de ≥ 36 px.
    private function drawMiniText(dc as Graphics.Dc) as Void {
        var h = dc.getHeight();
        var colW = dc.getWidth() - 2 * _rr - 8;
        if (colW < 36) {
            return;
        }
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);
        var tx = 3 + 2 * _rr + 5;
        var first = "";
        var second = "";
        if (_bestDist >= 0.0) {
            first = distLabel(_bestDist);
            second = ageShort(peerAge(_best));
        } else if (_client.peers.size() == 0) {
            first = (_client.peersAt == 0) ? "..." : "0";
        } else {
            first = _client.total.format("%d");
        }
        var two = second.length() > 0 && h - 6 >= 2 * smallH;
        var y = (h - 3 - (two ? 2 : 1) * smallH) / 2;
        dc.setColor(_fg, Graphics.COLOR_TRANSPARENT);
        if (dc.getTextWidthInPixels(first, small) <= colW + 3) {
            dc.drawText(tx, y, small, first, Graphics.TEXT_JUSTIFY_LEFT);
        }
        if (two && dc.getTextWidthInPixels(second, small) <= colW + 3) {
            dc.setColor(_gray, Graphics.COLOR_TRANSPARENT);   // a idade, mais apagada
            dc.drawText(tx, y + smallH, small, second, Graphics.TEXT_JUSTIFY_LEFT);
        }
    }

    // ── Resumo (campo pequeno demais pro radar) ─────────────────────────

    private function drawCompact(dc as Graphics.Dc) as Void {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);
        if (_client.peers.size() == 0 || _bestDist < 0.0) {
            // Ninguém — ou há gente, mas ainda não sei onde EU estou.
            var msg = (_client.peers.size() > 0) ? _client.total.format("%d") + " ao vivo"
                : ((_client.peersAt == 0) ? "..." : "ninguém ao vivo");
            dc.drawText(w / 2, (h - dc.getFontHeight(Graphics.FONT_SMALL)) / 2 - (h >= 70 ? smallH / 2 : 0),
                        Graphics.FONT_SMALL, msg, Graphics.TEXT_JUSTIFY_CENTER);
            return;
        }
        // Em cima: quem é, quantas mais e HÁ QUANTO TEMPO é essa posição — na
        // forma mais longa que couber no campo.
        var age = peerAge(_best);
        var line = compactTopLine(dc, age);
        dc.drawText(w / 2, 2, small, line, Graphics.TEXT_JUSTIFY_CENTER);

        var bodyTop = 2 + smallH;
        var bodyH = h - 3 - bodyTop - (h >= 70 ? smallH : 0);
        var text = distLabel(_bestDist);
        if (age > STALE_S) {
            dc.setColor(_gray, Graphics.COLOR_TRANSPARENT);   // a pessoa pode não estar mais ali
        }
        var font = pickFont(dc, text, w - bodyH - 8, bodyH);
        var ty = bodyTop + (bodyH - dc.getFontHeight(font)) / 2;
        var arrowR = (bodyH < 40 ? bodyH : 40) / 2 - 2;
        var hd = _heading;
        if (arrowR >= 6 && hd != null) {
            var x0 = (w - (dc.getTextWidthInPixels(text, font) + 6 + 2 * arrowR)) / 2;
            drawArrow(dc, x0 + arrowR, bodyTop + bodyH / 2, arrowR, _bestBrg - hd.toFloat());
            dc.drawText(x0 + 2 * arrowR + 6, ty, font, text, Graphics.TEXT_JUSTIFY_LEFT);
        } else {
            dc.drawText(w / 2, ty, font, text, Graphics.TEXT_JUSTIFY_CENTER);
        }
    }

    private function compactTopLine(dc as Graphics.Dc, age as Number) as String {
        var w = dc.getWidth();
        var small = Graphics.FONT_XTINY;
        var ago = ageLabel(age);
        var line = bestName() + " · " + ago;
        if (_client.total > 1) {
            var withCount = bestName() + " +" + (_client.total - 1).format("%d") + " · " + ago;
            if (dc.getTextWidthInPixels(withCount, small) <= w - 4) {
                line = withCount;
            }
        }
        if (dc.getTextWidthInPixels(line, small) > w - 4) {
            line = ago;
        }
        return line;
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
