# Amora no Garmin (Connect IQ)

Três apps Connect IQ pro **Edge 1040** e o **Forerunner 955**, mais o que eles
pedem do backend. Código em Monkey C; nada daqui vai pro container do amora.

| Pasta | Tipo | O que faz |
|---|---|---|
| `quilojaules/` | campo de dados | kJ do modelo do amora ao vivo, faixa do censo, "faltam N de 300"; grava kJ por volta no `.fit` |
| `pessoas/` | campo de dados | pessoa mais próxima entre as que estão ao vivo no amora; opcionalmente transmite a sua posição |
| `amora/` | app + glance | lista passeios e rotas salvas, baixa o percurso e entrega à navegação nativa |
| `tools/` | — | testes e conferências que rodam no computador |

> **Estado:** os três apps compilam pro Edge 1040 e pro Forerunner 955 com o
> SDK 9.3.0 no nível mais estrito de checagem de tipos (`-l 3`). O
> **Quilojaules** rodou no simulador (Edge 1040) tocando um `.fit`, e os
> números bateram com o esperado; falta um pedal de verdade no aparelho e
> conferir os campos gravados no `.fit`. **Pessoas** e **Amora** nunca
> rodaram — dependem dos endpoints `/garmin/…` no ar.

## Compilar e instalar

1. Instale o [SDK Manager do Connect IQ](https://developer.garmin.com/connect-iq/sdk/),
   entre com uma conta Garmin, baixe um SDK (≥ 7) e os aparelhos **Edge 1040**
   e **Forerunner 955**. Precisa de Java 17+.
2. Gere uma chave de desenvolvedor (uma vez):
   `openssl genrsa -out developer_key.pem 4096 && openssl pkcs8 -topk8 -inform PEM -outform DER -in developer_key.pem -out developer_key.der -nocrypt`
3. Compile tudo (três apps × dois aparelhos, `-l 3`):

   ```sh
   CIQ_SDK=/caminho/do/sdk garmin/build.sh              # ou: garmin/build.sh quilojaules
   ```

   Sai em `garmin/<app>/bin/<app>-<aparelho>.prg`. A chave
   `garmin/developer_key.der` é gerada na primeira vez; `bin/` e a chave não
   entram no git. Numa máquina sem interface gráfica, basta copiar de outra
   as pastas `edge1040` e `fr955` de `~/.Garmin/ConnectIQ/Devices/`. A
   extensão **Monkey C** do VS Code (*Build for Device*) faz o mesmo.
4. Simulador: `connectiq` abre o simulador e `monkeydo bin/x.prg edge1040` roda.
5. No aparelho: copie o `.prg` pra `GARMIN/APPS/` por USB. As configurações
   (massa, transmitir posição…) são editadas no Garmin Connect / Connect IQ do
   celular, e isso costuma valer só pra app instalado pela loja (não
   conferido aqui): em sideload, teste pelo simulador ou publique como beta.

### Conferir sem aparelho

Sem `-d`, o compilador monta o app contra a API inteira — pega erro de sintaxe
e de tipo sem precisar das definições de aparelho (só Java + o zip do SDK):

```sh
monkeyc -f garmin/quilojaules/monkey.jungle -o /tmp/q.prg -y developer_key.der -l 3 -w
```

Não substitui o `-d edge1040` / `-d fr955`: não checa o teto de API do
Forerunner 955 (5.2) nem gera um `.prg` instalável.

## 1 · Quilojaules (campo de dados)

Mostra a energia do **modelo** do amora acumulada no pedal — a mesma conta que
dá os kJ de um passeio no site — a partir da distância e da altitude
barométrica. Não usa rede.

- **Tela:** em cima, `est. 269 kJ | med. 382 kJ` (energia do modelo e, com
  medidor de potência, a medida — ∫P·dt); no meio, a **potência estimada**
  em W, média de 30 s; embaixo, `faltam 31 kJ` do orçamento (300 kJ por
  padrão; `+N kJ` depois de passar). A barra da base tem a cor da faixa do
  censo (150 / 300 / 500 / 1000 kJ). Em campo estreito o texto de cima
  encurta até caber.
- **Potência estimada:** é o que o TERRENO pede segundo o modelo, não o que
  a pessoa faz — energia por aresta (o `GraphEngine.stepCost` do amora) dos
  últimos 30 s ÷ tempo. Como o modelo cobra o arrasto por metro a uma
  velocidade de plano fixa, andar mais rápido no plano só aumenta os watts em
  proporção à velocidade. Serve pra quem não tem medidor; com medidor, o
  interessante é comparar.
- **No `.fit`** (campos de desenvolvedor): `kj_model` e `est_power` a cada
  registro, `lap_kj_model` / `lap_kj_measured` por volta, `total_kj_model` /
  `total_kj_measured` na sessão.
- **Janela do passeio:** aperte **Lap** ao chegar no ponto de encontro e de
  novo na chegada. A volta do meio é o pedal, sem o trajeto de casa (no PH/81
  a gravação inteira dava 927 kJ contra 328 kJ do pedal).
- **Configurações:** orçamento, massa e os parâmetros do modelo. Os padrões
  são os `DEFAULT_PARAMS` do `web/app.js` — mudou lá, mude em
  `quilojaules/resources/settings/settings.xml` e no `tools/kj_parity.mjs`.

### A receita (não simplifique)

`KjModel.mc` reamostra o perfil a **passo fixo de 30 m** (interpolando a
altitude entre amostras), aplica **deadband de 2 m** e soma rolamento, arrasto
fora das subidas e gravidade com a recuperação ε ponderada pela queda — o
`simulateRide` do amora, em fluxo. Somar segundo a segundo a altitude crua
cobra a mais: num pedal de 363 km gravado num Edge 1040, 5 m sem deadband dá
**+10 %**; com o deadband a sensibilidade ao passo fica em ±2 % (5–50 m).

`class KjModel` em `tools/kj_parity.mjs` é o espelho linha a linha do
`KjModel.mc`: **mude os dois juntos**.

## 2 · Pessoas ao vivo (campo de dados)

- **Ver:** a pessoa mais próxima (distância, seta relativa ao seu rumo,
  apelido, há quanto tempo é aquela posição — "há 30 s", "há 2 min") e
  quantas mais estão no mapa. Posição com mais de 3 min fica em cinza. Se uma
  leitura volta vazia, a última lista fica na tela por 5 min antes de virar
  "ninguém ao vivo". Lê `POST /garmin/live` a cada 15 s,
  com a atividade gravando ou o campo na tela. Ver **não envia** a sua posição:
  o servidor devolve lat/lng de cada pessoa e a distância é calculada no
  aparelho.
- **Radar** (campo com pelo menos 160×190 px): você no centro com o seu rumo
  pra cima, as pessoas como pontos na posição relativa de verdade, dois anéis
  de escala (o alcance se ajusta à pessoa mais próxima; quem está além vira
  um anel oco na borda) e, em laranja, o traçado do próximo passeio — buscado
  uma vez em `/garmin/list?glance=1` + `/garmin/item/t/<id>?pts=200`. Não é o
  mapa do aparelho: um campo de dados não tem acesso a ele. Em campo menor
  fica o resumo (distância + seta).
- **Transmitir:** desligado por padrão. Ligando "Transmitir minha posição" nas
  configurações, o campo manda a posição pro `POST /live-location` — só com a
  atividade rodando, e a barra de estado diz "transmitindo". Sem conexão, até
  40 pontos ficam na fila e sobem juntos quando o celular volta.
- Uma requisição por vez, pelo Bluetooth do celular (o Garmin Connect precisa
  estar aberto em segundo plano).
- Token pseudônimo de 32 hex sorteado no aparelho; apelido e retenção do
  rastro nas configurações.

## 3 · Amora (app + glance)

1. **Glance:** o próximo passeio (nome, data, km, kJ).
2. **Início:** o **código do aparelho** (6 caracteres, sorteado uma vez) e o
   estado. Select/toque abre a lista.
3. **Lista:** enviadas por você · próximos passeios · passeios recentes ·
   rotas salvas mais novas.
4. **Ficha:** nome, quando, ponto de encontro, km, subida, kJ e faixa.
   Select baixa o percurso; página seguinte (ou deslizar) mostra o mapa.
5. **Baixado:** o percurso fica nos Percursos do aparelho; Select de novo
   abre na navegação nativa.

**No site:** o botão ⌚ no modal do passeio e em cada rota salva
(📂 Carregar). Sem aparelho pareado ele baixa o percurso em `.fit`, que o
Garmin Connect importa — funciona sem o app — e oferece "Parear aparelho".
Pareado (código de 6 caracteres, guardado em `localStorage
phidro:garminCode`), ele põe a rota no topo da lista do aparelho; "Trocar
código" com o campo vazio despareia.

## Backend (`backend/garmin.py`, `backend/fit_course.py`)

| Endpoint | Pra quê |
|---|---|
| `GET /garmin/list[?code=][&glance=1]` | lista enxuta (`{k, id, n, s}` por item); nunca grava |
| `POST /garmin/list` `{code}` | a mesma lista + registra o aparelho como visto (é o que o app usa) |
| `GET /garmin/item/<t\|r>/<slug>` | ficha + traçado em ≤ 60 pontos |
| `GET /garmin/course/<t\|r>/<slug>.fit` | percurso FIT (POIs viram pontos de percurso) |
| `POST /garmin/send` `{code, k, id}` | "Enviar pro Garmin" do site |
| `POST /garmin/live` `{id?}` | posições ao vivo sem rastro e sem tokens |

- A fila de envios é o `garmin_queue.json` no store (bucket em produção):
  até 10 itens por código, 30 dias. Em memória ela sumiria quando o Cloud Run
  escala pra zero entre o envio no celular e a abertura do app no aparelho.
- O percurso só tem a geometria cheia quando a rota está **hospedada no
  amora** (rota salva, ou passeio cuja rota é uma rota salva). Passeio com
  rota no RideWithGPS sai com o traçado do `routes.json` — ≤ 400 pontos, um a
  cada ~100 m num pedal de 40 km — e a ficha vem com `approx: true` (o app
  mostra "traçado aproximado"). O backend não busca nada no RideWithGPS: o
  endpoint é público e a busca usaria as credenciais do coletivo.
- Nenhum percurso tem altitude (o estado da rota salva e o `routes.json` não
  guardam elevação): o aparelho não mostra perfil de subida, e não há pontos
  de percurso com kJ por subida.

## O que está testado

```sh
python -m venv .venv && .venv/bin/pip install -r backend/requirements.txt garmin-fit-sdk
.venv/bin/python garmin/tools/check_fit_course.py    # FIT conferido com o decodificador oficial
.venv/bin/python garmin/tools/test_backend.py        # endpoints /garmin/…, sem rede
node garmin/tools/kj_parity.mjs                      # modelo × simulateRide do amora (sintético)
.venv/bin/python garmin/tools/fit_to_json.py pedal.fit > pedal.json
node garmin/tools/kj_parity.mjs pedal.json           # idem, num pedal de verdade
```

- **Percurso FIT:** decodificado pelo `garmin-fit-sdk` oficial (CRC, tipo
  `course`, registros, pontos de percurso, eventos). Não foi importado num
  aparelho nem no Garmin Connect.
- **Backend:** lista, ficha, percurso, pareamento, envio e ao vivo, com um
  passeio de data futura sintético.
- **Modelo de kJ:** o espelho do `KjModel.mc` contra o `simulateRide` real
  extraído do `web/app.js` — 0,005 % de diferença num pedal de 363 km de um
  Edge 1040; em float de 32 bits (o `Float` do Monkey C), 0,03 %.
- **Site:** os botões ⌚, em navegador headless (desktop e toque emulado).
- **Monkey C:** os três apps compilam pro Edge 1040 e pro Forerunner 955 com `-l 3`.
- **Simulador:** só o Quilojaules (Edge 1040, reprodução de `.fit`).
- **Não testado:** nada em aparelho; Pessoas e Amora nem em simulador (ver o aviso no topo).

## Limites conhecidos do Connect IQ (conferidos na documentação do SDK)

- Forerunner 955 = API 5.2: nada marcado "desde 6.0" (por isso o corpo da
  requisição vai em `parameters`, não em `:body`).
- Percurso baixado por app: **FIT** nos dois aparelhos; GPX só no Edge.
- Um app não lê a geometria nem o perfil do percurso carregado na navegação.
- Não há como pôr outras pessoas no mapa nativo; o campo "Pessoas" desenha a
  própria seta.
- Campo de dados: 128 KB de memória no Edge 1040 (256 KB no 955); até 32
  bytes de campos de desenvolvedor por mensagem FIT (o Quilojaules usa até 8).
- `Communications` num campo de dados em primeiro plano existe desde a API
  5.0. O manifesto do `pessoas/` NÃO pede `Background`: com essa permissão e
  sem código anotado, o compilador carrega o app inteiro também como processo
  de segundo plano. Se o aparelho recusar as requisições do campo, é o
  primeiro lugar a olhar (a tabela de permissões do SDK ainda cita
  `Background` pra `Communications` em campo de dados).
