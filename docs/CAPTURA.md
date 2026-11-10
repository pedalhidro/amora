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

**A data é só o dia.** Do arquivo do zap sabemos em que passeio foi, não a que
horas. Ele entra com `dcterms:date "AAAA-MM-DD"^^xsd:date` — o dia do passeio,
sem hora. (Até 11/2026 o `ingest-whatsapp.py` gravaria a data **e a hora** da
saída como `xsd:dateTime`: uma hora inventada, indistinguível de um EXIF de
verdade. Nunca chegou a rodar em produção.) Os leitores tratam o dia sozinho
como 23:59 daquele dia — a mídia aparece no fim do dia, depois das fotos com
hora — e mídia sem data nenhuma herda o dia do `ph:capturedDuring`. A regra
está em `effectiveDate` (`web/lib/media-query.js`); ver "Data de mídia tem
três estados" no `CLAUDE.md`.

Ordem importa, e é de graça: **ingira os 516 originais primeiro**. Como o pHash
*é* o IRI e o WhatsApp só recomprime a imagem, uma cópia de zap e o original
colidem no mesmo IRI — então, com os originais já lá, as cópias deduplicam
contra eles e **a versão com GPS vence**.

## O livro-razão: como saber que o amora reflete o acervo

`scripts/media_ledger.py` guarda, **fora dos catálogos e fora do git**
(`.sync-state/`, por máquina), o que foi feito de cada arquivo do acervo:
subiu (`med:<hash>`), era duplicata (de qual mídia), ficou retido, foi
excluído à mão. A chave é o id do arquivo no Google Drive — sobrevive a
renomear a pasta.

```sh
python scripts/media_ledger.py status     # por pasta: pendente / subiu / duplicata / retida…
python scripts/media_ledger.py retidos    # o que parece mídia apagada no amora
python scripts/media_ledger.py liberar drive:<id>    # pode subir
python scripts/media_ledger.py excluir drive:<id>    # nunca sobe
```

Três promessas, testadas ponta a ponta num backend de teste:

- **Apagou no amora, fica apagado.** O arquivo de origem tem registro, então
  não é reenviado. E uma *outra* cópia da mesma foto (a do zap, recomprimida,
  com outro id) bate numa **lápide** — um hash que o amora já teve e não tem
  mais — e fica retida até alguém liberar.
- **Sumiu do Drive, nada acontece no amora.** Só aparece no `status`.
- **Sem livro, não sobe nada.** Num clone novo, rode `media_ledger.py semear`
  (monta as lápides a partir dos blobs que já existiram, no disco e nas versões
  antigas do bucket — em 11/2026 eram 26) e a primeira ingestão com
  `--iniciar-livro`. Se o livro existe em outra cópia do repo, copie o
  `.sync-state/` de lá em vez de começar outro.

**O original substitui a cópia.** Se o amora já tem a foto numa versão pior (a
do zap: sem GPS, só com o dia) e chega o original, ele toma o lugar dela — no
MESMO endereço (`/midia/<hash>`), com os álbuns, o crédito e o passeio que a
cópia tinha, mais a hora e a coordenada do EXIF. A ordem de ingestão deixa de
importar: zap primeiro e original depois dá no mesmo que o contrário. Só fotos
(vídeo duplicado fica como duplicata). `--sem-substituir` desliga.

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

**Mídia solta na raiz da pasta (11/2026).** Nas pastas mais novas, criadas por
quem colabora, não há subpasta `midia/`: os arquivos do pedal foram largados na
raiz, ao lado da arte do chamado. A auditoria e as duas ingestões só olhavam
dentro de `midia*/` e não viam 317 arquivos (246 do zap + 71 originais de
câmera, quase todos em `2026-10-24 Pedal pela Democracia` e no PH 117). Agora
um arquivo da raiz conta como mídia quando tem **nome** de mídia — do WhatsApp,
ou de câmera/celular (`IMG_…`, `DSC…`, `PA243145.JPG`…; `_midia_solta` em
`audit-captura.py`). O resto da raiz segue sendo arte. Fica de fora, por não
dar pra saber pelo nome, uma vintena de arquivos com nome de UUID (PH 7, PH 8,
PH 76). O casamento pasta↔passeio é por DATA (±1 dia): pasta com data errada
se conserta renomeando a pasta no Drive, não no código.

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
