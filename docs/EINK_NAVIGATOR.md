# Navegador e-ink de guidão (DIY) 🚲

Um display e-ink no guidão mostrando o mapa do amora: rotas do coletivo,
hidrografia, e as pessoas compartilhando **Localização ao vivo** — legível sob
sol a pino, consumindo quase nada de bateria.

Este guia assume **zero experiência com eletrônica**. Spoiler: o caminho mais
fácil não solda nem um fio.

## A grande ideia (leia isto primeiro)

Placas DIY de e-ink são **péssimas em rodar mapas** (pouca memória, sem
navegador de verdade) mas **ótimas em desenhar uma imagem pronta**. Então
invertemos o problema:

```
telefone da ciclista                 servidor amora                dispositivo e-ink
┌──────────────────┐   Localização  ┌──────────────┐   GET /eink/  ┌─────────────┐
│ amora (PWA/app)  │ ──── ao vivo ─▶│  renderiza o │ ◀─ map.png ── │ blita e     │
│ = o GPS da bike  │                │  quadro 1-bit│ ── PNG/raw ──▶│ dorme 30 s  │
└──────────────────┘                └──────────────┘               └─────────────┘
         ▲                                                                ▲
         └────────────── hotspot Wi-Fi do próprio telefone ───────────────┘
```

- **O telefone é o GPS.** A ciclista liga o *Localização ao vivo* no amora
  (funciona com a tela apagada no app nativo). O dispositivo no guidão não
  precisa de chip GPS: ele pede o mapa com `?follow=<apelido>`.
- **O servidor renderiza tudo** (`GET /eink/map.png`): tiles OSM ditherizados
  pra 1-bit, rotas do acervo, POIs, quem está ao vivo, rastro, seta de rumo,
  hora, escala. O dispositivo só faz um GET e desenha.
- **O dispositivo é burro de propósito**: acorda, GET, blita, dorme. Cabe em
  40 linhas de código.

## A API (o que o dispositivo pede)

`GET https://amora.pedalhidrografi.co/eink/map.png` com:

| Parâmetro | O quê |
|---|---|
| `follow=<apelido>` | centraliza na pessoa ao vivo (rastro pontilhado + seta de rumo) |
| `route=<slug>` | visão geral daquela rota (enquadra sozinho; POIs como losangos) |
| `lat=&lng=&z=` | enquadramento manual |
| `w=&h=` | tamanho do painel em px (default 400×300) |
| `fmt=png` \| `fmt=raw` | PNG (qualquer cliente) ou framebuffer cru (ESP32) |
| `base=osm` \| `hydro` \| `none` | ruas / raster de hidrografia / só vetores |
| `invert=1` | preto↔branco |

Modos combinam: `?route=X&follow=Y` = traçado da rota X, centrado na pessoa Y.
**`fmt=raw`**: sem header — cada linha são `ceil(w/8)` bytes, MSB primeiro,
bit 1 = branco (o layout dos buffers Waveshare/GxEPD2). Dimensões nos headers
HTTP `X-EPD-Width`/`X-EPD-Height`. Um quadro 400×300 = 15 000 bytes.

**Simulador no navegador:** `https://amora.pedalhidrografi.co/eink.html` —
brinque com os modos, copie a URL pronta.

## Hardware — do mais fácil pro mais capaz

### Nível 0 — "já tenho em casa": um Kindle velho (R$ 0)

Sério. Qualquer Kindle com o navegador experimental (ou tablet e-ink com
browser) já é o dispositivo:

1. Telefone: liga o hotspot + o *Localização ao vivo* no amora.
2. Kindle: conecta no hotspot, abre o navegador em
   `https://amora.pedalhidrografi.co/eink.html?kiosk=1&follow=SEUAPELIDO&w=600&h=800&interval=30`
3. Pronto — a página vira só o quadro, atualizando a cada 30 s.

Prende no guidão com suporte de celular + saquinho ziploc se chover. Zero
eletrônica, zero código. É o jeito certo de **testar se a ideia agrada** antes
de comprar qualquer coisa.

### Nível 1 — o painel NFC que você já comprou (2.7" NFC-Powered, 264×176)

O [Waveshare 2.7" NFC-Powered](https://www.waveshare.com/wiki/2.7inch_NFC-Powered_e-Paper_Module)
é uma criatura curiosa: **não tem bateria, não tem processador acessível, não
tem Wi-Fi**. Ele é alimentado pelo campo NFC do telefone durante os ~6 s da
gravação (pelo app Android da Waveshare — atenção: o app **não funciona em
Samsung/Google/Sony**; há app iOS) e depois segura a imagem PRA SEMPRE, sem
energia nenhuma.

Ou seja: **ele não consegue se atualizar sozinho → não faz navegação ao
vivo.** Mas faz uma coisa ótima:

**Cartão de rota de energia zero.** Antes do pedal (ou em cada parada):

1. No telefone, abra
   `https://amora.pedalhidrografi.co/eink/map.png?route=<slug>&w=264&h=176`
   (o tamanho exato do painel) e salve a imagem na galeria.
2. App da Waveshare → escolher imagem → encostar o telefone no painel.
3. O traçado do dia fica no guidão, imune a chuva de bateria, o pedal inteiro.

É genuinamente útil (overview + POIs sempre à vista) e usa o mesmo endpoint.
Só não espere a bolinha andando no mapa.

### Nível 2 — navegador ao vivo de verdade, sem solda (~US$ 45–60)

**LilyGO T5 4.7" (ESP32-S3)** — a recomendação pra noobs que querem o
"de verdade": display 960×540, ESP32 (Wi-Fi), gestão de bateria e USB-C
**tudo numa placa só**. Compra, pluga uma bateria LiPo (conector, sem solda),
carrega o sketch abaixo via USB, prende no guidão.

Alternativa mais mastigada: **Inkplate 6** (~US$ 99) — tela de Kindle
reciclada + ESP32, documentação excelente, Arduino/MicroPython.

### Nível 3 — o clássico modular (~R$ 250 total)

**ESP32 DevKit** (~R$ 40) + **Waveshare 4.2" SPI, 400×300** (~R$ 200) — o
módulo vem com cabo de 8 vias com terminais fêmea: encaixa direto nos pinos
do DevKit (compre um com os pinos já soldados). 400×300 é o **default do
endpoint** — nenhum parâmetro de tamanho necessário. Biblioteca GxEPD2.

| | Kindle velho | NFC 2.7" | LilyGO T5 4.7" | ESP32+4.2" |
|---|---|---|---|---|
| Ao vivo? | ✅ 30 s | ❌ (tap manual) | ✅ 30–60 s | ✅ 30–60 s |
| Solda | zero | zero | zero | zero* |
| Código | zero | zero | sketch pronto | sketch pronto |
| Bateria | a do Kindle (dias) | **nenhuma!** | LiPo, ~1 semana | LiPo/powerbank |
| Custo | R$ 0 | já comprado | ~US$ 60 | ~R$ 250 |

\* com DevKit de pinos pré-soldados.

## O sketch (ESP32 + GxEPD2, nível 3)

Instale a IDE do Arduino + suporte a ESP32 + biblioteca GxEPD2. Ajuste
`WIFI_*`, `FOLLOW` e a linha do display pro seu painel:

```cpp
// Navegador e-ink amora — ESP32 + Waveshare 4.2" (400x300) via GxEPD2.
// Acorda, baixa o framebuffer cru do amora, blita, dorme 30 s. Só isso.
#include <WiFi.h>
#include <HTTPClient.h>
#include <GxEPD2_BW.h>

#define WIFI_SSID  "hotspot-do-telefone"
#define WIFI_PASS  "senha"
#define FOLLOW     "dandan"          // seu apelido no Localização ao vivo
#define REFRESH_S  30

// Waveshare 4.2" no pinout padrão do exemplo GxEPD2 p/ ESP32:
GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT>
    display(GxEPD2_420_GDEY042T81(/*CS*/5, /*DC*/17, /*RST*/16, /*BUSY*/4));

static uint8_t fb[400 / 8 * 300];    // 15 000 bytes — cabe folgado na RAM

void setup() {
  display.init();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("https://amora.pedalhidrografi.co/eink/map.png"
               "?follow=" FOLLOW "&w=400&h=300&fmt=raw");
    if (http.GET() == 200 &&
        http.getStream().readBytes(fb, sizeof fb) == sizeof fb) {
      display.setFullWindow();
      display.firstPage();
      do { display.drawBitmap(0, 0, fb, 400, 300, GxEPD_BLACK, GxEPD_WHITE); }
      while (display.nextPage());
    }
    http.end();
  }
  // Deep sleep economiza MUITO mais que delay() — o e-ink segura a imagem.
  esp_sleep_enable_timer_wakeup((uint64_t)REFRESH_S * 1000000ULL);
  esp_deep_sleep_start();
}
```

Notas:
- Pro **LilyGO T5 4.7"** troque GxEPD2 pela lib `epd47` da LilyGO (a tela é
  paralela, não SPI) e peça `w=960&h=540`; o resto é igual.
- `fmt=raw` já vem no layout que `drawBitmap` espera (bit 1 = branco). Se a
  sua imagem sair invertida, acrescente `&invert=1` na URL e pronto.
- Deep sleep entre refreshes: um 18650 dura dias pedalando fins de semana.

## Montagem e uso no pedal

- **Hotspot**: deixe o hotspot do telefone ligado com nome/senha fixos; o
  ESP32 reconecta sozinho. (iPhone: manter a tela do hotspot aberta na
  primeira conexão.)
- **Suporte**: braçadeira de guidão pra GoPro + case impresso, ou a boa e
  velha braçadeira de velcro. E-ink não esquenta e o vidro é fino — proteja
  de pancada.
- **Chuva**: os painéis não são vedados. Ziploc resolve; e-ink continua
  legível através do plástico (sem reflexo!).
- **Etiqueta OSM**: o quadro com `base=osm` usa tiles do OpenStreetMap (a
  atribuição já vai desenhada no canto). Refresh de 30–60 s é tranquilo;
  não desça de 10 s por educação com os servidores deles.

## Ideias pra depois (contribuições bem-vindas)

- Rotação heading-up (mapa gira com o rumo, marcador fixo).
- Zoom automático por velocidade (parado = perto, descendo = longe).
- Painel de "quem vem aí": lista de distâncias até cada pessoa ao vivo.
- Partial refresh no ESP32 (só o marcador, sem flash) entre full refreshes.
- Botõezinhos no guidão (zoom −/+) — o ESP32 tem GPIO de sobra.
