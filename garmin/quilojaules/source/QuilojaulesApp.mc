import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

class QuilojaulesApp extends Application.AppBase {
    private var _field as QuilojaulesField?;

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
    }

    function onStop(state as Dictionary?) as Void {
    }

    function getInitialView() as [Views] or [Views, InputDelegates] {
        var field = new QuilojaulesField();
        _field = field;
        return [field];
    }

    //! Configuração mudada no celular: vale dali pra frente, sem zerar nada.
    function onSettingsChanged() as Void {
        var field = _field;
        if (field != null) {
            field.loadSettings();
        }
        WatchUi.requestUpdate();
    }
}
