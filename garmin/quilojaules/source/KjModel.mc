import Toybox.Lang;

//! Energia do MODELO do amora, em fluxo (amostra a amostra).
//!
//! É a receita que o site usa pra estimar os kJ de uma rota (`simulateRide`
//! em web/app.js): perfil reamostrado a passo FIXO (30 m), deadband de 2 m na
//! altitude, rolamento em toda a distância, arrasto só fora das subidas,
//! gravidade com a recuperação de descida ε ponderada pela queda (− 0,13).
//!
//! Por que não somar amostra a amostra direto: o barômetro mexe a cada
//! segundo e o modelo é não linear na descida — a 5 m sem deadband a conta
//! cobra ~10 % a mais (medido num pedal de 363 km gravado num Edge 1040; ver
//! garmin/tools/kj_parity.mjs). Passo fixo + deadband é o que mantém o número
//! comparável ao rótulo de kJ do passeio.
//!
//! ESPELHO: `class KjModel` em garmin/tools/kj_parity.mjs repete este arquivo
//! linha a linha e é conferido contra o código real do amora. Mude os dois.
class KjModel {
    //! Coeficientes em kJ por metro (o Float do Monkey C tem 32 bits; em kJ
    //! os acumuladores ficam longe do limite de precisão — 0,03 % em 363 km).
    var aRoll as Float = 0.0;
    var aAero as Float = 0.0;
    var beta as Float = 0.0;
    var abRatio as Float = 0.0;
    var climbThr as Float = 0.02;
    var tau as Float = 2.0;
    var step as Float = 30.0;

    //! Acumuladores: [x, wRoll, wAero, wClimb, hPlus, hMinus, epsNum, epsDen]
    var total as Array<Float>;
    var lap as Array<Float>;

    var started as Boolean = false;
    var lastS as Float = 0.0;   // distância da última amostra
    var lastH as Float = 0.0;   // altitude da última amostra
    var nodeS as Float = 0.0;   // distância do último nó do perfil
    var y as Float = 0.0;       // altitude com deadband no último nó

    //! Soma POR ARESTA (o custo do roteamento do amora, GraphEngine.stepCost,
    //! com o ε local de cada trecho). Fecha com o total acima em ~0,1 %, mas
    //! só cresce e é local — é dela que sai a potência estimada: o total usa
    //! um ε ponderado no pedal inteiro, então a diferença dele entre dois
    //! instantes mistura o passado e pode até ser negativa.
    var edge as Float = 0.0;

    function initialize() {
        total = newAcc();
        lap = newAcc();
    }

    //! Dobra os parâmetros físicos nos coeficientes (o `readCost` do amora).
    //! `climbThrGrade` é fração (0.02 = 2 %). Pode ser chamado no meio de uma
    //! atividade: vale dali pra frente, os acumuladores ficam.
    function setParams(mass as Float, crr as Float, cda as Float, rho as Float,
                       kEff as Float, powerFlat as Float, climbThrGrade as Float,
                       deadbandM as Float, stepM as Float) as Void {
        var g = 9.81;
        if (kEff > 1.0) {
            kEff = 1.0;
        } else if (kEff < 0.1) {
            kEff = 0.1;
        }
        if (mass < 1.0) {
            mass = 1.0;
        }
        var vf = flatSpeed(powerFlat, mass, crr, cda, rho);
        var aero = 0.5 * rho * cda * vf * vf;       // J por metro, antes do k_eff
        aRoll = (crr * mass * g) / kEff / 1000.0;
        aAero = aero / kEff / 1000.0;
        beta = (mass * g) / kEff / 1000.0;
        abRatio = crr + aero / (mass * g);
        climbThr = climbThrGrade;
        tau = deadbandM < 0.0 ? 0.0 : deadbandM;
        step = stepM < 5.0 ? 5.0 : stepM;
    }

    //! Velocidade de equilíbrio no plano (Newton na cúbica) — o
    //! solveSpeedAtGradient do amora com gradiente 0.
    function flatSpeed(power as Float, mass as Float, crr as Float, cda as Float,
                       rho as Float) as Float {
        var a = 0.5 * rho * cda;
        var b = mass * 9.81 * crr;
        var v = 5.0;
        for (var i = 0; i < 60; i++) {
            var fv = a * v * v * v + b * v - power;
            var fp = 3.0 * a * v * v + b;
            if (fp < 0.000000000001 && fp > -0.000000000001) {
                break;
            }
            var dv = fv / fp;
            v -= dv;
            if (v < 0.1) {
                v = 0.1;
            }
            if (dv < 0.0000001 && dv > -0.0000001) {
                break;
            }
        }
        return v < 0.5 ? 0.5 : v;
    }

    function newAcc() as Array<Float> {
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] as Array<Float>;
    }

    //! Uma amostra: distância acumulada (m) e altitude (m, ou null).
    function feed(s as Float, h as Float?) as Void {
        var hh = (h == null) ? lastH : h;
        if (!started) {
            started = true;
            lastS = s;
            lastH = hh;
            nodeS = s;
            y = hh;
            return;
        }
        if (s > lastS) {
            while (nodeS + step <= s) {
                nodeS = nodeS + step;
                var frac = (nodeS - lastS) / (s - lastS);
                var hN = lastH + (hh - lastH) * frac;
                var yPrev = y;
                if (hN > y + tau) {
                    y = hN - tau;
                } else if (hN < y - tau) {
                    y = hN + tau;
                }
                addSegment(step, y - yPrev);
            }
            lastS = s;
        }
        lastH = hh;
    }

    function addSegment(seg as Float, dh as Float) as Void {
        addTo(total, seg, dh);
        addTo(lap, seg, dh);
        edge = edge + segCost(seg, dh);
    }

    function addTo(a as Array<Float>, seg as Float, dh as Float) as Void {
        a[0] = a[0] + seg;
        a[1] = a[1] + aRoll * seg;
        if (dh >= 0.0) {
            a[4] = a[4] + dh;
            a[3] = a[3] + beta * dh;
            if (dh < climbThr * seg) {
                a[2] = a[2] + aAero * seg;      // arrasto só fora das subidas
            }
        } else {
            var drop = -dh;
            a[5] = a[5] + drop;
            a[2] = a[2] + aAero * seg;
            var epsCoast = (abRatio * seg) / drop;
            if (epsCoast > 1.0) {
                epsCoast = 1.0;
            }
            a[6] = a[6] + epsCoast * drop;
            a[7] = a[7] + drop;
        }
    }

    //! kJ de UM trecho (distância d, desnível dh) com o ε local — a mesma
    //! conta do GraphEngine.stepCost do amora.
    function segCost(d as Float, dh as Float) as Float {
        if (dh >= 0.0) {
            var c = aRoll * d + beta * dh;
            if (dh < climbThr * d) {
                c += aAero * d;
            }
            return c;
        }
        var drop = -dh;
        var eps = (abRatio * d) / drop;
        if (eps > 1.0) {
            eps = 1.0;
        }
        eps -= 0.13;
        if (eps < 0.0) {
            eps = 0.0;
        }
        var e = aRoll * d + aAero * d - eps * beta * drop;
        return e < 0.0 ? 0.0 : e;
    }

    //! Soma por aresta + o trecho EM ANDAMENTO (do último nó até a última
    //! amostra). Sem isso a energia só anda de 30 em 30 m e a potência
    //! estimada viria aos trancos — numa subida a 2 m/s, um nó a cada 15 s.
    function liveEdge() as Float {
        var part = lastS - nodeS;
        if (!started || part <= 0.0) {
            return edge;
        }
        var yLive = y;
        if (lastH > y + tau) {
            yLive = lastH - tau;
        } else if (lastH < y - tau) {
            yLive = lastH + tau;
        }
        return edge + segCost(part, yLive - y);
    }

    //! kJ de um acumulador (o total ou o da volta).
    function energy(a as Array<Float>) as Float {
        var eps = 0.0;
        if (a[7] > 0.0) {
            eps = a[6] / a[7] - 0.13;
        }
        if (eps < 0.0) {
            eps = 0.0;
        } else if (eps > 1.0) {
            eps = 1.0;
        }
        var e = a[1] + a[2] + a[3] - eps * beta * a[5];
        return e < 0.0 ? 0.0 : e;
    }

    function kj() as Float {
        return energy(total);
    }

    function lapKj() as Float {
        return energy(lap);
    }

    function newLap() as Void {
        lap = newAcc();
    }

    function reset() as Void {
        total = newAcc();
        lap = newAcc();
        started = false;
        lastS = 0.0;
        lastH = 0.0;
        nodeS = 0.0;
        y = 0.0;
        edge = 0.0;
    }

    //! Estado inteiro num Array de Floats (cabe no Application.Storage) —
    //! pra retomar uma atividade depois que o campo é recarregado.
    function save() as Array<Float> {
        var out = [lastS, lastH, nodeS, y] as Array<Float>;
        out.addAll(total);
        out.addAll(lap);
        out.add(edge);
        return out;
    }

    function restore(data as Object?) as Boolean {
        if (!(data instanceof Lang.Array) || data.size() != 21) {
            return false;
        }
        for (var i = 0; i < 21; i++) {
            if (!(data[i] instanceof Lang.Float)) {
                return false;
            }
        }
        lastS = data[0] as Float;
        lastH = data[1] as Float;
        nodeS = data[2] as Float;
        y = data[3] as Float;
        total = data.slice(4, 12) as Array<Float>;
        lap = data.slice(12, 20) as Array<Float>;
        edge = data[20] as Float;
        started = true;
        return true;
    }
}
