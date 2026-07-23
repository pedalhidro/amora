# Captura de dados — o que se coleta de cada pedal, e como saber o que falta

Cada passeio do Pedal Hidrográfico deixa três rastros, e eles vivem em lugares
diferentes. Este documento é sobre garantir que os três sejam colhidos — e,
principalmente, sobre **saber quando não foram**.

    ANTES  ─ o chamado ──────  narrativa, arte, rota planejada, post do Instagram
    DEPOIS ─ o censo ────────  comparecimento, saída, chegada, movimento, energia
    MÍDIA  ─ as fotos ───────  as que sobem no amora  +  as que ficam no grupo do zap

O problema nunca foi coletar. Foi **perceber que não coletou**. Um passeio sem
foto no catálogo era ambíguo: ninguém compartilhou nada, ou ninguém foi buscar?
Sem responder isso, não dá pra cobrar nada de ninguém — nem de si mesmo.

## O modelo: o passe de coleta (`ph:MediaSweep`)

O amora enxerga `images.ttl` (o que subiu por upload) e não enxerga a
**Biblioteca Hidrográfica** no Drive (onde as fotos do WhatsApp são
arquivadas). O passe de coleta é o marcador que traz esse fato pra dentro do
catálogo:

```turtle
pas:<slug> ph:mediaSweep pas:<slug>_sweep .

pas:<slug>_sweep a ph:MediaSweep ;
    dcterms:date "2025-10-29T09:56:03-03:00"^^xsd:dateTime ;   # quando o passe foi feito
    prov:wasAssociatedWith pes:1fhkjnba ;                       # quem foi buscar
    ph:archiveFolder "2025-09-02 53 Contornar Antonico" ;       # a pasta no Drive
    ph:collectedFileCount 40 ;                                  # quantos arquivos vieram
    ph:sweepContributor "alef", "chiara", "dandanlessa" .       # quem compartilhou
```

**A existência do nó é o marcador.** Daí saírem três estados bem distintos, e
essa distinção é o ponto do modelo inteiro:

| No painel | Significa |
|---|---|
| `n` | o passe foi feito e trouxe **n** arquivos |
| `∅` | o passe foi feito e **ninguém compartilhou nada** |
| `?` | o passe **nunca foi feito** — ninguém foi buscar |

Os contribuintes ficam como **literal** (o slug cru do nome do arquivo), não
como IRI de pessoa. É deliberado: o slug é o dado bruto e sempre existe;
resolvê-lo pra uma pessoa é um join via `schema:alternateName` no
`identities.ttl`, que pode não ter acontecido ainda. Assim o registro do passe
nunca fica travado esperando alguém ser cadastrado.

O nó segue a convenção da casa (IRI derivada do pai, `pas:<slug>_sweep`), então
a purga do backend — que é aritmética de prefixo — o leva junto com o passeio,
de graça.

> `ph:mediaCount` era a versão anterior disso: um inteiro solto, sem
> procedência, que ninguém escrevia e ninguém lia. Está marcado
> `owl:deprecated` na ontologia. Não escreva nele.

## As ferramentas

| | |
|---|---|
| **Painel de Captura** | Aba no Censo (`censo.html#captura`). Uma linha por passeio, uma coluna por campo. Cada lacuna é **clicável** e leva na ferramenta que a preenche. É o rosto do sistema. |
| `scripts/audit-captura.py` | O motor. Cruza `tours.ttl` + `images.ttl` + o acervo do Drive e diz o que falta. `--sync` grava os passes de coleta no catálogo; `--slug-map` emite o mapa slug→pessoa pra revisão. |
| `scripts/backfill-activities.py` | Casa cada passeio com a gravação GPS no RideWithGPS, grava `ph:linkActivity` e backfilla saída/chegada/movimento/energia medida. |
| `scripts/ingest-drive.py` | Sobe pro amora os originais do acervo que têm EXIF/GPS (fase 1 — ver abaixo). |
| `scripts/migrate-captura-fixes.py` | Reparos pontuais de catálogo (arte em host local, datatype de sequência). Idempotente. |

O acervo do Drive é lido em **modo estritamente somente-leitura**, e só os
metadados (nome, tamanho, mtime). Os arquivos são *stubs* do Google Drive: abrir
um força o download. Ler os 8 mil puxaria ~13 GiB pela rede.

## O ritual

O pedal é semanal. O ritual acompanha:

**Antes (quando o chamado sai)** — cadastre o passeio no `upload_tour.html`:
título, data, narrativa, arte do anúncio, rota planejada, post do Instagram.
Cinco minutos, e é o que alimenta o site, o feed RSS e o Instagram.

**Depois (no dia seguinte)** — edite o mesmo passeio
(`upload_tour.html?id=<slug>`) e preencha: quantos vieram, quantos estreando, e
**cole a URL da gravação GPS** no campo *Atividades gravadas*. Essa URL é a
peça mais barata e mais valiosa do fluxo inteiro: com ela, saída, chegada,
tempo em movimento e energia medida saem sozinhos do
`backfill-activities.py`. Sem ela, os quatro só entram na mão — e é por isso
que faltavam em 30–40 passeios.

**Uma vez por mês (ou quando der)** — passe o zap: baixe o que o pessoal
compartilhou pra pasta do passeio na Biblioteca Hidrográfica, e registre o
passe:

```sh
python scripts/audit-captura.py --sync
```

Depois, é só abrir o painel e olhar o que ficou vermelho:

```sh
python scripts/audit-captura.py            # o mesmo relatório, no terminal
```

## Fase 2 — os 7.658 do WhatsApp

O acervo tem **8.174 arquivos** (13,0 GiB). Deles:

- **516 são originais** (AirDrop, cabo, upload direto pro Drive) e preservam o
  EXIF completo: GPS, data de captura, câmera. Esses viram mídia de primeira
  classe no amora, com marcador no mapa — é a **fase 1** (`ingest-drive.py`).
- **7.658 vieram do WhatsApp**, que **remove todo o EXIF no envio**. Não têm
  GPS, não têm data de captura, não têm câmera. O único carimbo de tempo que
  resta é o do nome do arquivo — e ele é a hora do *compartilhamento*, não da
  captura (as fotos do pedal de 2025-09-09 aparecem como "2025-09-10 at
  00.46").

**Esses 7.658 nunca serão marcadores no mapa**, e não há truque que conserte
isso: qualquer coordenada atribuída a eles seria GPS inventado. O que eles
podem ser é **memória** — mídia ligada ao passeio (`ph:capturedDuring`) e a
quem compartilhou, navegável na galeria e no modal do passeio.

O modelo já suporta isso sem termo novo: o mixin `ph:GeoreferencedImage` é o
que faz o mapa desenhar um marcador. Mídia sem GPS entra como `ph:StillImage`
**sem** o mixin — e some do mapa sozinha, sem nenhum caso especial no
`app.js`. O SHACL também já aceita (`schema:locationCreated` é `sh:Warning`).

Ordem importa, e é de graça: **ingira os 516 originais primeiro**. Como o pHash
*é* o IRI e o WhatsApp só recomprime a imagem, uma cópia de zap e o original
colidem no mesmo IRI — então, com os originais já lá, as cópias deduplicam
contra eles e **a versão com GPS vence**.

Antes de rodar a fase 2, resolva a autoria: `scripts/whatsapp-slug-map.json`
(gerado por `--slug-map`) tem 19 slugs que já resolvem pra uma pessoa e ~130
que precisam de revisão humana — incluindo quase-homônimos que são a mesma
pessoa com um typo (`fabiotarantes`/`fabioarantes`).

## O retrato de hoje (2026-07-12)

109 passeios no catálogo.

| | |
|---|---|
| Passeios completos (fora a gravação GPS) | **41/109** |
| Com gravação GPS (`ph:linkActivity`) | **0/109** ← a lacuna que trava as outras |
| Com passe de coleta registrado | **87/109** |
| Sem passe *e* sem mídia nenhuma | os 22 restantes |
| Arquivos contabilizados nos passes | **7.998** |
| Mídia no amora | 355 |

O passe de coleta **parou em 2026-02-24**. Entre 2026-03-04 e 2026-06-23 há um
bloco contínuo de passeios sem mídia em lugar nenhum — nem Drive, nem amora. Em
vários deles a pasta do Drive foi criada, com a arte do chamado na raiz, e a
`midia/` ficou vazia: o ritual de criar a pasta sobreviveu, o de coletar não.

Esse é o buraco pra fechar primeiro, porque é o único ainda recuperável —
enquanto a memória (e o WhatsApp) das pessoas aguentar.

## Cinco eventos existem no Drive e não no catálogo

Não são lacunas de captura; são buracos de catálogo. Os dois primeiros ainda
por cima duplicam a numeração de passeios que já existem:

| Pasta no Drive | Arquivos |
|---|---|
| `2025-04-29 35 Braço Morto do Tietê` | 112 |
| `2025-05-17 SN Avistar25` | 64 |
| `2025-03-18 28 Lavapés Aclimação 2` | 0 |
| `2025-03-29 SN Bicipassarinhada Raposo` | 0 |
| `2026-01-29 Oficina Hidro Cartografia Bordada SESC Consolação` | 0 |

Cadastre-os pelo `upload_tour.html` (ou decida que não são passeios). Enquanto
não forem, `audit-captura.py` os lista como órfãos a cada rodada.
