import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

class PessoasApp extends Application.AppBase {
    private var _field as PessoasField?;

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
    }

    function onStop(state as Dictionary?) as Void {
    }

    function getInitialView() as [Views] or [Views, InputDelegates] {
        var field = new PessoasField();
        _field = field;
        return [field];
    }

    //! Ligar/desligar a transmissão no celular vale na hora.
    function onSettingsChanged() as Void {
        var field = _field;
        if (field != null) {
            field.loadSettings();
        }
        WatchUi.requestUpdate();
    }
}
