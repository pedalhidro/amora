import Toybox.Application;
import Toybox.Lang;
import Toybox.Math;
import Toybox.System;

//! O que o app e o glance compartilham: servidor, código de pareamento,
//! o "próximo passeio" guardado e os textos de erro.
(:glance)
module Api {
    const DEFAULT_SERVER = "https://amora.pedalhidrografi.co";
    //! Sorteio do código sem 0/1 (o servidor trata O→0 e I/L→1, mas melhor
    //! nem dar chance de confundir na hora de digitar no celular).
    const CODE_ALPHABET = "23456789abcdefghjkmnpqrstvwxyz";

    //! Base das URLs, sem barra no fim. Só https (o Connect IQ recusa http).
    function server() as String {
        try {
            var s = Application.Properties.getValue("server");
            if (s instanceof Lang.String && s.find("https://") == 0) {
                var len = s.length();
                var trimmed = s.substring(0, len - 1);
                var last = s.substring(len - 1, len);
                if (trimmed != null && last != null && last.equals("/")) {
                    return trimmed;
                }
                return s;
            }
        } catch (e) {
        }
        return DEFAULT_SERVER;
    }

    //! Código de pareamento do aparelho (6 caracteres), sorteado uma vez. É
    //! o que a pessoa digita no amora pra "Enviar pro Garmin".
    function code() as String {
        try {
            var saved = Application.Storage.getValue("code");
            if (saved instanceof Lang.String && saved.length() == 6) {
                return saved;
            }
        } catch (e) {
        }
        Math.srand(System.getTimer());
        var c = "";
        var n = CODE_ALPHABET.length();
        for (var i = 0; i < 6; i++) {
            var k = (Math.rand() & 0x7FFFFFFF) % n;
            c += CODE_ALPHABET.substring(k, k + 1);
        }
        try {
            Application.Storage.setValue("code", c);
        } catch (e) {
        }
        return c;
    }

    //! "abc234" → "ABC 234", pra ler na tela.
    function codeLabel() as String {
        var c = code().toUpper();
        return c.substring(0, 3) + " " + c.substring(3, 6);
    }

    //! Guarda o próximo passeio (nome + linha de fatos) pro glance mostrar
    //! sem rede. `item` = um item da lista ({n, s, …}) ou null.
    function rememberNext(item as Object?) as Void {
        try {
            if (item instanceof Lang.Dictionary && item["n"] instanceof Lang.String) {
                Application.Storage.setValue("nextN", item["n"] as String);
                var s = item["s"];
                Application.Storage.setValue("nextS", (s instanceof Lang.String) ? s : "");
            } else {
                Application.Storage.deleteValue("nextN");
                Application.Storage.deleteValue("nextS");
            }
        } catch (e) {
        }
    }

    function errorText(code as Number) as String {
        if (code == -104) {
            return "Sem conexão com o celular";
        } else if (code == -1001) {
            return "O servidor precisa ser https";
        } else if (code == -402 || code == -403) {
            return "Resposta grande demais";
        } else if (code == -2) {
            return "Celular sem resposta";
        } else if (code == 404) {
            return "Não encontrado";
        }
        return "Erro " + code.format("%d");
    }
}
