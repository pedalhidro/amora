import Toybox.Communications;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;

//! Tela de início: mostra o CÓDIGO do aparelho (o que se digita no amora pra
//! "Enviar pro Garmin") e abre a lista. Na primeira vez carrega sozinha;
//! depois, Select/toque recarrega e abre de novo. Voltar sai do app.
class HomeView extends WatchUi.View {
    var status as String = "Carregando...";
    private var _loading as Boolean = false;
    private var _first as Boolean = true;

    function initialize() {
        View.initialize();
    }

    function onShow() as Void {
        if (_first) {
            _first = false;
            loadList();
        }
    }

    function loadList() as Void {
        if (_loading) {
            return;
        }
        _loading = true;
        status = "Carregando...";
        WatchUi.requestUpdate();
        // POST com o código no corpo: além de trazer a lista, é o que registra
        // este aparelho como "visto" no servidor (um GET lá nunca grava).
        Communications.makeWebRequest(Api.server() + "/garmin/list", { "code" => Api.code() }, {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => { "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        }, method(:onList));
    }

    function onList(code as Number, data as Dictionary or String or Null) as Void {
        _loading = false;
        if (code == 200 && data instanceof Lang.Dictionary) {
            status = "Select: abrir a lista";
            var next = data["next"];
            Api.rememberNext((next instanceof Lang.Array && next.size() > 0) ? next[0] as Object? : null);
            var menu = new WatchUi.Menu2({ :title => "Amora" });
            var n = addItems(menu, data["sent"] as Object?, "Enviada");
            n += addItems(menu, data["next"] as Object?, null);
            n += addItems(menu, data["recent"] as Object?, null);
            n += addItems(menu, data["routes"] as Object?, "Rota");
            if (n > 0) {
                WatchUi.pushView(menu, new ListDelegate(), WatchUi.SLIDE_LEFT);
            } else {
                status = "Nada pra mostrar ainda";
            }
        } else {
            status = Api.errorText(code);
        }
        WatchUi.requestUpdate();
    }

    //! Uma seção da resposta ([{k, id, n, s}, …]) → linhas do menu. O id da
    //! linha é [tipo, id, nome], que a ficha usa pra buscar os detalhes.
    private function addItems(menu as WatchUi.Menu2, items as Object?, prefix as String?) as Number {
        if (!(items instanceof Lang.Array)) {
            return 0;
        }
        var n = 0;
        for (var i = 0; i < items.size(); i++) {
            var it = items[i];
            if (!(it instanceof Lang.Dictionary)) {
                continue;
            }
            var k = it["k"];
            var id = it["id"];
            var name = it["n"];
            var sub = it["s"];
            if (!(k instanceof Lang.String) || !(id instanceof Lang.String)
                    || !(name instanceof Lang.String)) {
                continue;
            }
            var line = (sub instanceof Lang.String) ? sub : "";
            if (prefix != null) {
                line = (line.length() > 0) ? prefix + " · " + line : prefix;
            }
            menu.addItem(new WatchUi.MenuItem(name, line, [k, id, name], null));
            n++;
        }
        return n;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
        var w = dc.getWidth();
        var h = dc.getHeight();
        var cx = w / 2;
        var tiny = Graphics.FONT_XTINY;
        var tinyH = dc.getFontHeight(tiny);
        var big = Graphics.FONT_LARGE;
        var bigH = dc.getFontHeight(big);
        var titleH = dc.getFontHeight(Graphics.FONT_MEDIUM);

        var blockH = titleH + tinyH + bigH + tinyH * 2 + 12;
        var y = (h - blockH) / 2;
        dc.drawText(cx, y, Graphics.FONT_MEDIUM, "Amora", Graphics.TEXT_JUSTIFY_CENTER);
        y += titleH + 6;
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, y, tiny, "código deste aparelho", Graphics.TEXT_JUSTIFY_CENTER);
        y += tinyH;
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, y, big, Api.codeLabel(), Graphics.TEXT_JUSTIFY_CENTER);
        y += bigH + 6;
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, y, tiny, "digite no amora:", Graphics.TEXT_JUSTIFY_CENTER);
        y += tinyH;
        dc.drawText(cx, y, tiny, "Enviar pro Garmin", Graphics.TEXT_JUSTIFY_CENTER);

        dc.setColor(Graphics.COLOR_YELLOW, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, h - tinyH - (h / 12), tiny, status, Graphics.TEXT_JUSTIFY_CENTER);
    }
}

class HomeDelegate extends WatchUi.BehaviorDelegate {
    private var _view as HomeView;

    function initialize(view as HomeView) {
        BehaviorDelegate.initialize();
        _view = view;
    }

    function onSelect() as Boolean {
        _view.loadList();
        return true;
    }
}

//! Lista de passeios e rotas: escolher abre a ficha.
class ListDelegate extends WatchUi.Menu2InputDelegate {

    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item as WatchUi.MenuItem) as Void {
        var id = item.getId();
        if (id instanceof Lang.Array && id.size() == 3) {
            var view = new DetailView(id[0] as String, id[1] as String, id[2] as String);
            WatchUi.pushView(view, new DetailDelegate(view), WatchUi.SLIDE_LEFT);
        }
    }

    function onBack() as Void {
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
    }
}
