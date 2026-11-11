import Toybox.Activity;
import Toybox.Application;
import Toybox.FitContributor;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;

//! Campo de dados "Quilojaules".
//!
//!   em cima   est. 269 kJ | med. 382 kJ   (energia do modelo | medida)
//!   no meio   142 W                        (potência ESTIMADA, média de 30 s)
//!   embaixo   faltam 31 kJ                 (do orçamento; 300 kJ por padrão)
//!
//! A potência estimada é a do MODELO do amora — o que o terreno pede de quem
//! pedala, sem medidor: a energia por aresta dos últimos 30 s dividida pelo
//! tempo. "med." só aparece com medidor de potência (∫P·dt). A barra da base
//! tem a cor da faixa de intensidade do censo.
//!
//! Grava no .fit, como campos de desenvolvedor: kJ do modelo e potência
//! estimada a cada registro, kJ do modelo e medidos POR VOLTA e no total. A
//! volta é o que marca a janela do passeio: aperte Lap ao chegar no ponto de
//! encontro e de novo na chegada — a volta do meio é o pedal, sem o trajeto
//! de casa.
class QuilojaulesField extends WatchUi.DataField {
    // Ids dos campos FIT — batem com resources/fitcontributions.
    private const FIELD_MODEL = 0;
    private const FIELD_LAP_MODEL = 1;
    private const FIELD_LAP_MEASURED = 2;
    private const FIELD_TOTAL_MODEL = 3;
    private const FIELD_TOTAL_MEASURED = 4;
    private const FIELD_EST_POWER = 5;

    private const STORE_KEY = "estado";
    private const SAVE_EVERY_S = 300;
    private const PW_WINDOW = 31;          // 31 amostras de 1 s = janela de 30 s
    private const PW_MIN_MS = 5000;        // menos que isso: ainda sem estimativa

    private var _model as KjModel;
    private var _budget as Float = 300.0;

    private var _measuredKj as Float = 0.0;
    private var _lapMeasuredKj as Float = 0.0;
    private var _hasPower as Boolean = false;
    private var _lastTimerMs as Number = -1;

    private var _running as Boolean = false;
    private var _restoreChecked as Boolean = false;
    private var _startTime as Number = 0;
    private var _sinceSave as Number = 0;

    // Potência estimada: anel de (relógio do timer, energia por aresta).
    private var _pwT as Array<Number>;
    private var _pwE as Array<Float>;
    private var _pwI as Number = 0;
    private var _pwN as Number = 0;
    private var _estPower as Number? = null;

    private var _recField as FitContributor.Field;
    private var _estPowerField as FitContributor.Field;
    private var _lapModelField as FitContributor.Field;
    private var _lapMeasuredField as FitContributor.Field;
    private var _totalModelField as FitContributor.Field;
    private var _totalMeasuredField as FitContributor.Field;

    function initialize() {
        DataField.initialize();
        _model = new KjModel();
        loadSettings();
        _pwT = [] as Array<Number>;
        _pwE = [] as Array<Float>;
        for (var i = 0; i < PW_WINDOW; i++) {
            _pwT.add(0);
            _pwE.add(0.0);
        }

        _recField = createField("kj_model", FIELD_MODEL, FitContributor.DATA_TYPE_FLOAT,
            { :mesgType => FitContributor.MESG_TYPE_RECORD, :units => "kJ" });
        _lapModelField = createField("lap_kj_model", FIELD_LAP_MODEL, FitContributor.DATA_TYPE_FLOAT,
            { :mesgType => FitContributor.MESG_TYPE_LAP, :units => "kJ" });
        _lapMeasuredField = createField("lap_kj_measured", FIELD_LAP_MEASURED, FitContributor.DATA_TYPE_FLOAT,
            { :mesgType => FitContributor.MESG_TYPE_LAP, :units => "kJ" });
        _totalModelField = createField("total_kj_model", FIELD_TOTAL_MODEL, FitContributor.DATA_TYPE_FLOAT,
            { :mesgType => FitContributor.MESG_TYPE_SESSION, :units => "kJ" });
        _totalMeasuredField = createField("total_kj_measured", FIELD_TOTAL_MEASURED, FitContributor.DATA_TYPE_FLOAT,
            { :mesgType => FitContributor.MESG_TYPE_SESSION, :units => "kJ" });
        _estPowerField = createField("est_power", FIELD_EST_POWER, FitContributor.DATA_TYPE_UINT16,
            { :mesgType => FitContributor.MESG_TYPE_RECORD, :units => "W" });
        writeFit();
    }

    // ── Configurações ───────────────────────────────────────────────────

    //! Lê as propriedades (Garmin Connect) e recalcula os coeficientes.
    function loadSettings() as Void {
        _budget = prop("budget", 300.0);
        _model.setParams(
            prop("mass", 75.0), prop("crr", 0.008), prop("cda", 0.5), prop("rho", 1.1),
            prop("keff", 0.97), prop("pflat", 50.0), prop("climbthr", 2.0) / 100.0,
            prop("deadband", 2.0), prop("step", 30.0));
    }

    private function prop(key as String, dflt as Float) as Float {
        try {
            var v = Application.Properties.getValue(key);
            if (v instanceof Lang.Float) {
                return v;
            }
            if (v instanceof Lang.Number || v instanceof Lang.Long || v instanceof Lang.Double) {
                return v.toFloat();
            }
            if (v instanceof Lang.String) {
                var f = v.toFloat();
                if (f != null) {
                    return f;
                }
            }
        } catch (e) {
            // propriedade ausente/corrompida: fica o padrão
        }
        return dflt;
    }

    // ── Cálculo (1×/s) ──────────────────────────────────────────────────

    function compute(info as Activity.Info) as Void {
        if (!_restoreChecked) {
            _restoreChecked = true;
            tryRestore(info);
        }
        var st = info.startTime;
        if (st != null) {
            _startTime = st.value();
        }
        var running = _running;
        var state = info.timerState;
        if (state != null) {
            running = (state == Activity.TIMER_STATE_ON);
        }
        if (running) {
            var dist = info.elapsedDistance;
            if (dist != null) {
                _model.feed(dist, info.altitude);
            }
            accumulatePower(info);
            updateEstPower(info);
            _sinceSave += 1;
            if (_sinceSave >= SAVE_EVERY_S) {
                saveState();
            }
        } else {
            // Parado: o relógio do timer não anda; não deixa um dt gigante
            // entrar na integral quando ele voltar.
            _lastTimerMs = -1;
            if (_estPower != null) {
                _estPower = 0;           // parado: o terreno não pede nada
            }
        }
        writeFit();
    }

    //! Potência estimada (W): energia por aresta dos últimos 30 s ÷ tempo,
    //! pelo relógio do timer (pausas não contam).
    private function updateEstPower(info as Activity.Info) as Void {
        var t = info.timerTime;
        if (t == null) {
            return;
        }
        _pwT[_pwI] = t;
        _pwE[_pwI] = _model.liveEdge();
        _pwI = (_pwI + 1) % PW_WINDOW;
        if (_pwN < PW_WINDOW) {
            _pwN += 1;
        }
        var newest = (_pwI - 1 + PW_WINDOW) % PW_WINDOW;
        var oldest = (_pwI - _pwN + PW_WINDOW) % PW_WINDOW;
        var dt = _pwT[newest] - _pwT[oldest];
        if (dt < PW_MIN_MS) {
            _estPower = null;
            return;
        }
        // kJ → J (×1000) e ms → s (×1000)
        var p = (_pwE[newest] - _pwE[oldest]) * 1000000.0 / dt.toFloat();
        if (p < 0.0) {
            p = 0.0;
        } else if (p > 3000.0) {
            p = 3000.0;
        }
        _estPower = (p + 0.5).toNumber();
    }

    //! ∫P·dt em kJ, pelo relógio do timer (só anda com a atividade rodando).
    private function accumulatePower(info as Activity.Info) as Void {
        var t = info.timerTime;
        var p = info.currentPower;
        if (t == null) {
            return;
        }
        if (_lastTimerMs >= 0 && p != null) {
            var dt = t - _lastTimerMs;
            if (dt > 0 && dt <= 5000) {
                var kj = p.toFloat() * dt.toFloat() / 1000000.0;
                _measuredKj += kj;
                _lapMeasuredKj += kj;
                _hasPower = true;
            }
        }
        _lastTimerMs = t;
    }

    private function writeFit() as Void {
        var kj = _model.kj();
        _recField.setData(kj);
        var ep = _estPower;
        _estPowerField.setData(ep == null ? 0 : ep);
        _lapModelField.setData(_model.lapKj());
        _lapMeasuredField.setData(_lapMeasuredKj);
        _totalModelField.setData(kj);
        _totalMeasuredField.setData(_measuredKj);
    }

    // ── Eventos do timer ────────────────────────────────────────────────

    function onTimerStart() as Void {
        _running = true;
    }

    function onTimerResume() as Void {
        _running = true;
    }

    function onTimerPause() as Void {
        _running = false;
        saveState();
    }

    function onTimerStop() as Void {
        _running = false;
        saveState();
    }

    //! Volta: os campos de volta já têm o valor da que fechou (o sistema os
    //! grava neste evento); zera os acumuladores da próxima.
    function onTimerLap() as Void {
        _model.newLap();
        _lapMeasuredKj = 0.0;
    }

    //! Atividade encerrada (salva ou descartada): começa do zero.
    function onTimerReset() as Void {
        _running = false;
        _model.reset();
        _measuredKj = 0.0;
        _lapMeasuredKj = 0.0;
        _hasPower = false;
        _lastTimerMs = -1;
        _pwI = 0;
        _pwN = 0;
        _estPower = null;
        _startTime = 0;
        try {
            Application.Storage.deleteValue(STORE_KEY);
        } catch (e) {
        }
    }

    // ── Retomada (campo recarregado no meio da atividade) ───────────────

    private function saveState() as Void {
        _sinceSave = 0;
        if (_startTime == 0 || !_model.started) {
            return;
        }
        try {
            Application.Storage.setValue(STORE_KEY, {
                "t" => _startTime,
                "m" => _model.save(),
                "p" => [_measuredKj, _lapMeasuredKj]
            });
        } catch (e) {
            // sem espaço: segue sem retomada
        }
    }

    //! Só retoma se o estado guardado é DA MESMA atividade (mesmo instante
    //! de início) e a distância não andou pra trás.
    private function tryRestore(info as Activity.Info) as Void {
        var st = info.startTime;
        var dist = info.elapsedDistance;
        if (st == null || dist == null) {
            return;
        }
        try {
            var saved = Application.Storage.getValue(STORE_KEY);
            if (!(saved instanceof Lang.Dictionary)) {
                return;
            }
            var t = saved["t"];
            var m = saved["m"];
            var p = saved["p"];
            if (!(t instanceof Lang.Number) || t != st.value()) {
                return;
            }
            if (!(m instanceof Lang.Array) || !(p instanceof Lang.Array) || p.size() != 2) {
                return;
            }
            if (!(m[0] instanceof Lang.Float) || (m[0] as Float) > dist) {
                return;
            }
            if (_model.restore(m)) {
                if (p[0] instanceof Lang.Float && p[1] instanceof Lang.Float) {
                    _measuredKj = p[0] as Float;
                    _lapMeasuredKj = p[1] as Float;
                    _hasPower = _measuredKj > 0.0;
                }
            }
        } catch (e) {
        }
    }

    // ── Tela ────────────────────────────────────────────────────────────

    //! Cor da faixa de intensidade do censo (mesmos cortes do
    //! backend/_intensity_for: 150 / 300 / 500 / 1000 kJ).
    private function bandColor(kj as Float) as Graphics.ColorType {
        if (kj < 150.0) {
            return Graphics.COLOR_GREEN;
        } else if (kj < 300.0) {
            return Graphics.COLOR_DK_GREEN;
        } else if (kj < 500.0) {
            return Graphics.COLOR_YELLOW;
        } else if (kj < 1000.0) {
            return Graphics.COLOR_ORANGE;
        }
        return Graphics.COLOR_RED;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        var bg = getBackgroundColor();
        var fg = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_WHITE : Graphics.COLOR_BLACK;
        dc.setColor(fg, bg);
        dc.clear();

        var w = dc.getWidth();
        var h = dc.getHeight();
        var cx = w / 2;
        var kj = _model.kj();
        var small = Graphics.FONT_XTINY;
        var smallH = dc.getFontHeight(small);

        // Barra da faixa de intensidade na base do campo.
        var barH = h >= 60 ? 5 : 3;
        dc.setColor(bandColor(kj), Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(0, h - barH, w, barH);
        dc.setColor(fg, Graphics.COLOR_TRANSPARENT);

        // Em cima: energia estimada | medida — na forma mais longa que couber.
        var est = kj.format("%.0f");
        var top = "est. " + est + " kJ";
        if (_hasPower) {
            var med = _measuredKj.format("%.0f");
            top = "est. " + est + " kJ | med. " + med + " kJ";
            if (dc.getTextWidthInPixels(top, small) > w - 4) {
                top = "est. " + est + " | med. " + med + " kJ";
            }
            if (dc.getTextWidthInPixels(top, small) > w - 4) {
                top = est + " | " + med + " kJ";
            }
        }
        dc.drawText(cx, 2, small, top, Graphics.TEXT_JUSTIFY_CENTER);

        // Embaixo: só o que falta do orçamento (se couber e houver orçamento).
        var bottom = null as String?;
        if (_budget > 0.0 && h >= 3 * smallH + 12) {
            var left = _budget - kj;
            bottom = (left >= 0.0)
                ? "faltam " + left.format("%.0f") + " kJ"
                : "+" + (-left).format("%.0f") + " kJ";
        }
        var bottomH = (bottom != null) ? smallH : 0;
        if (bottom != null) {
            dc.drawText(cx, h - barH - bottomH - 1, small, bottom, Graphics.TEXT_JUSTIFY_CENTER);
        }

        // No meio: potência estimada, média de 30 s.
        var ep = _estPower;
        var value = (ep == null) ? "--" : ep.format("%d");
        var unitW = dc.getTextWidthInPixels("W", small) + 3;
        var valueTop = 2 + smallH;
        var valueH = h - barH - bottomH - valueTop - 2;
        var font = pickFont(dc, value, w - 8 - 2 * unitW, valueH);
        var fh = dc.getFontHeight(font);
        var tw = dc.getTextWidthInPixels(value, font);
        var vy = valueTop + (valueH - fh) / 2;
        dc.drawText(cx, vy, font, value, Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx + tw / 2 + 3, vy + fh - smallH - (fh / 8), small, "W", Graphics.TEXT_JUSTIFY_LEFT);
    }

    //! A maior fonte em que o número cabe.
    private function pickFont(dc as Graphics.Dc, text as String, maxW as Number,
                              maxH as Number) as Graphics.FontDefinition {
        var fonts = [Graphics.FONT_NUMBER_THAI_HOT, Graphics.FONT_NUMBER_HOT,
                     Graphics.FONT_NUMBER_MEDIUM, Graphics.FONT_NUMBER_MILD,
                     Graphics.FONT_LARGE, Graphics.FONT_MEDIUM, Graphics.FONT_SMALL,
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
