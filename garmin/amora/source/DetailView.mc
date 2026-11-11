import Toybox.Communications;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.PersistedContent;
import Toybox.System;
import Toybox.WatchUi;

//! Ficha de um passeio ou rota.
//!
//!   Select / toque ........ baixa o percurso; de novo, abre na navegação
//!   Página seguinte / deslizar ... mapa do traçado
//!   Voltar ................ lista (cancela um download em curso)
//!
//! O percurso baixado fica salvo nos Percursos do aparelho mesmo que a
//! pessoa não abra a navegação agora — o app só é preciso uma vez por rota.
class DetailView extends WatchUi.View {
    private var _kind as String;
    private var _ref as String;
    private var _name as String;

    private var _info as Dictionary?;
    private var _status as String = "Carregando...";
    private var _requested as Boolean = false;
    private var _busy as Boolean = false;
    private var _course as PersistedContent.Content?;

    function initialize(kind as String, ref as String, name as String) {
        View.initialize();
        _kind = kind;
        _ref = ref;
        _name = name;
    }

    function onShow() as Void {
        if (_requested) {
            return;
        }
        _requested = true;
        _busy = true;
        Communications.makeWebRequest(
            Api.server() + "/garmin/item/" + _kind + "/" + _ref, null, {
                :method => Communications.HTTP_REQUEST_METHOD_GET,
                :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
            }, method(:onItem));
    }

    function onItem(code as Number, data as Dictionary or String or Null) as Void {
        _busy = false;
        if (code == 200 && data instanceof Lang.Dictionary) {
            _info = data;
            _status = "Select: baixar percurso";
        } else {
            _status = Api.errorText(code);
        }
        WatchUi.requestUpdate();
    }

    function isBusy() as Boolean {
        return _busy;
    }

    //! Select: baixa; com o percurso já baixado, entrega à navegação nativa.
    function primary() as Void {
        if (_busy) {
            return;
        }
        var course = _course;
        if (course != null) {
            System.exitTo(course.toIntent());
            return;
        }
        var info = _info;
        if (info == null) {
            _requested = false;      // a ficha falhou: tenta de novo
            _status = "Carregando...";
            WatchUi.requestUpdate();
            onShow();
            return;
        }
        var fit = info["fit"];
        if (!(fit instanceof Lang.String)) {
            return;
        }
        _busy = true;
        _status = "Baixando percurso...";
        WatchUi.requestUpdate();
        // FIT (não GPX): é o formato de percurso que o Edge E o Forerunner
        // aceitam de um app Connect IQ.
        Communications.makeWebRequest(Api.server() + fit, null, {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_FIT
        }, method(:onCourse));
    }

    function onCourse(code as Number,
                      data as Dictionary or String or PersistedContent.Iterator or Null) as Void {
        _busy = false;
        if (code == 200 && data instanceof PersistedContent.Iterator) {
            var course = data.next();
            if (course != null) {
                _course = course;
                _status = "Salvo. Select: navegar";
            } else {
                _status = "O aparelho recusou o percurso";
            }
        } else if (code == 200) {
            _status = "O aparelho recusou o percurso";
        } else {
            _status = Api.errorText(code);
        }
        WatchUi.requestUpdate();
    }

    //! Mapa do traçado (≤ 60 pontos, vindos na ficha).
    function showMap() as Void {
        var info = _info;
        if (info == null) {
            return;
        }
        var pts = info["pts"];
        if (pts instanceof Lang.Array && pts.size() >= 2) {
            var map = new RouteMap(pts);
            WatchUi.pushView(map, new RouteMapDelegate(map), WatchUi.SLIDE_UP);
        }
    }

    // ── Tela ────────────────────────────────────────────────────────────

    private function bandColor(kj as Numeric) as Graphics.ColorType {
        if (kj < 150) {
            return Graphics.COLOR_GREEN;
        } else if (kj < 300) {
            return Graphics.COLOR_DK_GREEN;
        } else if (kj < 500) {
            return Graphics.COLOR_YELLOW;
        } else if (kj < 1000) {
            return Graphics.COLOR_ORANGE;
        }
        return Graphics.COLOR_RED;
    }

    //! Quebra `text` em até 2 linhas que caibam em `maxW`.
    private function wrap(dc as Graphics.Dc, text as String, font as Graphics.FontDefinition,
                          maxW as Number) as Array<String> {
        if (dc.getTextWidthInPixels(text, font) <= maxW) {
            return [text] as Array<String>;
        }
        var first = "";
        var rest = text;
        while (true) {
            var sp = rest.find(" ");
            if (sp == null) {
                break;
            }
            var word = rest.substring(0, sp) as String;
            var candidate = (first.length() > 0) ? first + " " + word : word;
            if (dc.getTextWidthInPixels(candidate, font) > maxW && first.length() > 0) {
                break;
            }
            first = candidate;
            rest = rest.substring(sp + 1, rest.length()) as String;
        }
        if (first.length() == 0) {
            return [text] as Array<String>;
        }
        return [first, rest] as Array<String>;
    }

    private function str(v as Object?) as String? {
        return (v instanceof Lang.String && v.length() > 0) ? v : null;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
        var w = dc.getWidth();
        var h = dc.getHeight();
        var cx = w / 2;
        var maxW = (w * 4) / 5;          // folga pra tela redonda
        var tiny = Graphics.FONT_XTINY;
        var small = Graphics.FONT_SMALL;
        var tinyH = dc.getFontHeight(tiny);
        var smallH = dc.getFontHeight(small);

        var info = _info;
        var title = _name;
        var lines = [] as Array<String>;       // linhas de fatos (fonte pequena)
        var kj = null as Number?;
        var band = null as String?;
        if (info != null) {
            var n = str(info["n"] as Object?);
            if (n != null) {
                title = n;
            }
            var when = str(info["when"] as Object?);
            if (when != null) {
                lines.add(when);
            }
            var place = str(info["place"] as Object?);
            if (place != null) {
                lines.add(place);
            }
            var km = info["km"];
            var up = info["up"];
            var geo = "";
            if (km instanceof Lang.Float || km instanceof Lang.Double || km instanceof Lang.Number) {
                geo = km.format(km instanceof Lang.Number ? "%d" : "%.1f") + " km";
            }
            if (up instanceof Lang.Number) {
                geo = geo + (geo.length() > 0 ? " · " : "") + "sobe " + up.format("%d") + " m";
            }
            if (geo.length() > 0) {
                lines.add(geo);
            }
            var e = info["kj"];
            if (e instanceof Lang.Number) {
                kj = e;
                band = str(info["band"] as Object?);
            }
        }

        var titleLines = wrap(dc, title, small, maxW);
        var chipH = (kj != null) ? smallH + 6 : 0;
        var blockH = titleLines.size() * smallH + 4 + lines.size() * tinyH + chipH;
        var y = (h - blockH) / 2 - tinyH / 2;
        if (y < h / 10) {
            y = h / 10;
        }

        for (var i = 0; i < titleLines.size(); i++) {
            dc.drawText(cx, y, small, titleLines[i], Graphics.TEXT_JUSTIFY_CENTER);
            y += smallH;
        }
        y += 4;
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        for (var j = 0; j < lines.size(); j++) {
            dc.drawText(cx, y, tiny, lines[j], Graphics.TEXT_JUSTIFY_CENTER);
            y += tinyH;
        }
        if (kj != null) {
            var label = kj.format("%d") + " kJ";
            if (band != null) {
                label = label + " · " + band;
            }
            y += 4;
            dc.setColor(bandColor(kj), Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, y, small, label, Graphics.TEXT_JUSTIFY_CENTER);
        }

        dc.setColor(Graphics.COLOR_YELLOW, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, h - tinyH - (h / 12), tiny, _status, Graphics.TEXT_JUSTIFY_CENTER);
    }
}

class DetailDelegate extends WatchUi.BehaviorDelegate {
    private var _view as DetailView;

    function initialize(view as DetailView) {
        BehaviorDelegate.initialize();
        _view = view;
    }

    function onSelect() as Boolean {
        _view.primary();
        return true;
    }

    function onNextPage() as Boolean {
        _view.showMap();
        return true;
    }

    function onPreviousPage() as Boolean {
        _view.showMap();
        return true;
    }

    function onMenu() as Boolean {
        _view.showMap();
        return true;
    }

    function onBack() as Boolean {
        if (_view.isBusy()) {
            Communications.cancelAllRequests();
        }
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        return true;
    }
}
