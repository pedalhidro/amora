import Toybox.Application;
import Toybox.Communications;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;

//! Glance: o próximo passeio (nome + "sáb 14/11 · 8h · 42 km · 310 kJ").
//!
//! Mostra na hora o que ficou guardado da última vez e pede a versão nova
//! (GET /garmin/list?glance=1 — resposta de ~200 bytes; o glance tem 64 KB).
//! Em aparelhos que só atualizam o glance em segundo plano a requisição pode
//! não voltar a tempo: fica o guardado, que o app também atualiza ao abrir.
(:glance)
class AmoraGlance extends WatchUi.GlanceView {
    private var _name as String = "";
    private var _facts as String = "";
    private var _asked as Boolean = false;

    function initialize() {
        GlanceView.initialize();
        readStored();
    }

    private function readStored() as Void {
        _name = "";
        _facts = "";
        try {
            var n = Application.Storage.getValue("nextN");
            var s = Application.Storage.getValue("nextS");
            if (n instanceof Lang.String) {
                _name = n;
            }
            if (s instanceof Lang.String) {
                _facts = s;
            }
        } catch (e) {
        }
    }

    function onShow() as Void {
        if (_asked) {
            return;
        }
        _asked = true;
        Communications.makeWebRequest(Api.server() + "/garmin/list", { "glance" => "1" }, {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        }, method(:onNext));
    }

    function onNext(code as Number, data as Dictionary or String or Null) as Void {
        if (code == 200 && data instanceof Lang.Dictionary) {
            Api.rememberNext(data["next"] as Object?);
            readStored();
            WatchUi.requestUpdate();
        }
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        var h = dc.getHeight();
        var top = Graphics.FONT_GLANCE;
        var topH = dc.getFontHeight(top);
        if (_name.length() == 0) {
            dc.drawText(0, (h - topH) / 2, top, "Amora", Graphics.TEXT_JUSTIFY_LEFT);
            return;
        }
        var sub = Graphics.FONT_XTINY;
        var subH = dc.getFontHeight(sub);
        var y = (h - topH - subH) / 2;
        dc.drawText(0, y, top, _name, Graphics.TEXT_JUSTIFY_LEFT);
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(0, y + topH, sub, _facts, Graphics.TEXT_JUSTIFY_LEFT);
    }
}
