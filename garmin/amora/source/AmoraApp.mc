import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

//! App "Amora": passeios e rotas do amora no aparelho.
//!
//!   glance  → o próximo passeio
//!   início  → código de pareamento + abre a lista
//!   lista   → enviadas por você · próximos · recentes · rotas salvas
//!   ficha   → dados da rota, mapa, "Baixar percurso"
//!   baixado → entrega o percurso à navegação nativa (System.exitTo)
class AmoraApp extends Application.AppBase {

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
    }

    function onStop(state as Dictionary?) as Void {
    }

    //! Nunca roda no processo do glance (lá o sistema chama getGlanceView),
    //! então pode usar as classes que não são (:glance).
    (:typecheck(disableGlanceCheck))
    function getInitialView() as [Views] or [Views, InputDelegates] {
        var view = new HomeView();
        return [view, new HomeDelegate(view)];
    }

    function getGlanceView() as [GlanceView] or [GlanceView, GlanceViewDelegate] or Null {
        return [new AmoraGlance()];
    }
}
