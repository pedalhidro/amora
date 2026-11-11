import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Position;
import Toybox.System;
import Toybox.WatchUi;

//! Mapa nativo com o traçado da rota (uma polilinha) e um alfinete na saída.
//! Select entra no modo de navegar o mapa (arrastar/zoom); Voltar sai dele e,
//! de novo, volta pra ficha.
class RouteMap extends WatchUi.MapView {

    //! `pts` = [[lat, lng], …] (o `pts` de GET /garmin/item).
    function initialize(pts as Array) {
        MapView.initialize();
        setMapMode(WatchUi.MAP_MODE_PREVIEW);

        var line = new WatchUi.MapPolyline();
        line.setColor(Graphics.COLOR_RED);
        line.setWidth(4);
        var minLat = 90.0d;
        var maxLat = -90.0d;
        var minLng = 180.0d;
        var maxLng = -180.0d;
        var first = null as Position.Location?;
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
            var loc = new Position.Location({ :latitude => lat, :longitude => lng, :format => :degrees });
            line.addLocation(loc);
            if (first == null) {
                first = loc;
            }
            if (lat < minLat) { minLat = lat; }
            if (lat > maxLat) { maxLat = lat; }
            if (lng < minLng) { minLng = lng; }
            if (lng > maxLng) { maxLng = lng; }
        }
        MapView.setPolyline(line);

        if (first != null) {
            var marker = new WatchUi.MapMarker(first);
            marker.setIcon(WatchUi.MAP_MARKER_ICON_PIN, 0, 0);
            marker.setLabel("Saída");
            MapView.setMapMarker([marker] as Array<WatchUi.MapMarker>);

            // Enquadra o traçado com ~8 % de margem.
            var padLat = (maxLat - minLat) * 0.08d + 0.0005d;
            var padLng = (maxLng - minLng) * 0.08d + 0.0005d;
            MapView.setMapVisibleArea(
                new Position.Location({ :latitude => maxLat + padLat, :longitude => minLng - padLng, :format => :degrees }),
                new Position.Location({ :latitude => minLat - padLat, :longitude => maxLng + padLng, :format => :degrees }));
        }
        var ds = System.getDeviceSettings();
        MapView.setScreenVisibleArea(0, 0, ds.screenWidth, ds.screenHeight);
    }
}

class RouteMapDelegate extends WatchUi.BehaviorDelegate {
    private var _view as RouteMap;

    function initialize(view as RouteMap) {
        BehaviorDelegate.initialize();
        _view = view;
    }

    function onBack() as Boolean {
        if (_view.getMapMode() == WatchUi.MAP_MODE_PREVIEW) {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
        } else {
            _view.setMapMode(WatchUi.MAP_MODE_PREVIEW);
        }
        return true;
    }

    function onSelect() as Boolean {
        _view.setMapMode(WatchUi.MAP_MODE_BROWSE);
        return true;
    }
}
