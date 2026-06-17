# backend — Pedal Hidrográfico auto-hospedado

Um único serviço Flask que **serve o app do mapa, valida uploads RDF/imagem e
persiste tudo em arquivos**, sem SQLite. Roda igual num host local (macOS ou
Linux) e no Cloud Run — `STORAGE_BACKEND` escolhe onde vive o estado.

```text
host local  (ou Cloud Run — mesmo main.py, STORAGE_BACKEND escolhe storage)
  └─ gunicorn → main.py (Flask)
        ├─ GET  /                       → web/index.html (o app)
        ├─ GET  /health                 → "ok" (liveness)
        ├─ GET  /<path>                 → estáticos de web/ (app.js,
        │                                 data/*.ttl estáticos, …)
        ├─ GET  /data/<filename>        → uploads.ttl / data_graphs.ttl
        │                                 (bucket-first, container fallback)
        ├─ GET  /routes.json            → geometria das rotas (mutável,
        │                                 bucket-first; upsert incremental)
        ├─ GET  /feed.xml               → RSS 2.0 dos passeios (tours.ttl)
        ├─ GET  /photos|/clips|/tour_assets/<path>
        │                                 → blobs (302 pro bucket em modo gcs)
        ├─ POST /upload-image           → multipart: ttl + variantes;
        │                                 valida com pyshacl, grava em web/
        ├─ POST /upload-video           → multipart: ttl + audio.webm +
        │                                 (opcional) video360/720.webm +
        │                                 thumb.jpg; valida via VideoShape
        ├─ POST /upload-tour            → upsert de 1 ph:Tour em tours.ttl
        │                                 (+ anúncio opcional em tour_assets/)
        ├─ POST /delete-image/<phash>   → apaga arquivos + triples
        ├─ POST /delete-video/<vhash>   → apaga clipes + thumb + triples
        ├─ POST /delete-tour/<tour_id>  → apaga triples do tour + assets
        └─ POST /reload                 → invalida caches in-memory
  └─ cloudflared → túnel HTTPS público (local) ou Cloud Run domain mapping
```

Arquivos: `main.py`, `storage.py`, `rwgps.py`, `requirements.txt`,
`phidro.plist` (launchd, macOS).

## O estado vive em `web/` (local) ou no bucket GCS (Cloud Run)

Não há SQLite. Os uploads — imagens E vídeos — viram triples no mesmo
**`web/data/uploads.ttl`** (Turtle). Os blobs (foto/vídeo/áudio/thumb)
vivem em `web/photos/` e `web/clips/` em modo local, ou no bucket
GCS no Cloud Run.

**No Cloud Run o container é magrinho**: `.gcloudignore` exclui
`web/photos/` e `web/clips/` inteiros, então nada de mídia local é
empacotado na imagem. Os handlers `/photos/<path>` e `/clips/<path>`
redirecionam pro bucket via 302 (storage público leitura).

Um manifesto em **`web/data/data_graphs.ttl`** registra cada dump
(`void:dataDump`), e é ele que o app consulta no boot pra descobrir
quais grafos carregar.

```text
web/                            (no container do Cloud Run: só o que NÃO está excluído)
├─ index.html, app.js, style.css, sw.js, manifest.json, icons…
├─ upload_images.html           formulário unificado (imagens + vídeos)
├─ upload_videos.html           redirect stub → upload_images.html
├─ lib/                         utils.js + n3.min.js + energy-worker.js +
│                               tom-select.* + leaflet/ + locatecontrol/ +
│                               qrcode.js (deps vendored)
├─ data/                        TTLs estáticos vão no container; mutáveis no bucket
│   ├─ shapes.ttl               SHACL — ph:ImageShape + ph:VideoShape (no container)
│   ├─ ontology.ttl             vocabulário ph:                       (no container)
│   ├─ tours.ttl                catálogo de passeios                  (no container)
│   ├─ uploads.ttl              triples de TODA mídia                 (bucket-only)
│   └─ data_graphs.ttl          manifesto void:                       (bucket-only)
├─ photos/<phash>/              { original.* | large.jpg | thumb.jpg }    (bucket-only no CR)
└─ clips/                       clipes de vídeo curtos (Animação + galleries) (bucket-only no CR)
    ├─ <stem>.{360p,720p}.mp4   transcodes de build-clips.py (raw → otimizado)
    ├─ <stem>.thumb.jpg         miniatura pro marker no mapa
    ├─ audio/<stem>.m4a         trilha de áudio extraída (loop ambiente)
    ├─ <vhash>.{360p,720p}.webm transcodes do upload form (browser-side,
    │                           áudio opus EMBUTIDO no webm de vídeo)
    ├─ <vhash>.audio.webm       opus avulso pro audio loop (não baixa o vídeo)
    └─ <vhash>.thumb.jpg
```

> O host local serve `web/clips/` e `web/photos/` diretamente do disco —
> o `build-clips.py` roda localmente (precisa de `ffmpeg` + `exiftool`).
> Pra subir essas mídias pro Cloud Run, rode
> `scripts/deploy-cloudrun.sh --state-only`.

A validação SHACL acontece contra `web/data/shapes.ttl` mesclado com
`web/data/ontology.ttl`. Imagens validam contra `ph:ImageShape` (24 triples,
exige date/location/license/author etc.); vídeos contra `ph:VideoShape`
(NÃO subclasse de `ph:Image` — não exige bearing/focal-35), que adiciona
`schema:duration`, `ph:availableResolution`, `ph:audio`, opcionalmente
`ph:video360p`/`ph:video720p`/`schema:thumbnail`.

Passeios (`ph:Tour`) seguem a mesma mecânica, mas gravam em
**`web/data/tours.ttl`**: `POST /upload-tour` faz upsert de exatamente 1
tour (mais quaisquer `phd:pessoa*`/`phd:assoc_*` novos que ele referencie)
e, se vier um campo `announcement`, salva a arte em
`tour_assets/<tour_id>/` e injeta `schema:image`. `POST /delete-tour/<id>`
remove os triples do tour + seus assets (mas NÃO as pessoas/séries, que
podem ser referenciadas por outros tours). O form é `web/upload_tour.html`;
`web/censo.html` mostra métricas agregadas + roster editável.

**Backup é copiar `web/data/` + `web/photos/` + `web/clips/`** — não há
mais nada de estado. (`web/routes.json` é regenerado por
`scripts/build-routes.py`; clipes transcodados podem ser re-gerados de
`web/clips/raw/` com `scripts/build-clips.py`.)

No Cloud Run o bucket tem **Object Versioning** ligado (pelo
`deploy-cloudrun.sh`, idempotente), então cada sobrescrita de um arquivo de
estado guarda a geração anterior — rede de segurança contra clobber/purga
ruim. Listar/diff/restaurar gerações: `scripts/state-history.sh
list|diff|restore <arquivo>`. `restore` é não-destrutivo (cria nova geração
corrente); rode `POST /reload` depois pro backend reler o catálogo. Uma
regra de lifecycle expira versões não-correntes em 90 dias. Em modo local
não há versioning — o backup ali é cópia de diretório / git.

## 1. Repositório e ambiente

```sh
git clone <seu-repo> pedalhidrografico
cd pedalhidrografico/backend
python -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 2. Teste local

```sh
./venv/bin/python main.py        # sobe em http://0.0.0.0:8000
```

Abra `http://localhost:8000/` — o mapa deve carregar. Para testar o fluxo
de upload, abra `http://localhost:8000/upload_images.html`. `Ctrl-C` para
parar.

Variáveis úteis: `PORT` (padrão `8000`) e `PHIDRO_WEB` (padrão
`../web`, sibling do diretório do `main.py`).

## 3. Serviço no boot (launchd, macOS)

Use o `phidro.plist` desta pasta. Edite-o trocando o usuário e os
caminhos, depois:

```sh
sudo cp phidro.plist /Library/LaunchDaemons/co.pedalhidrografi.phidro.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/co.pedalhidrografi.phidro.plist
sudo launchctl enable system/co.pedalhidrografi.phidro
# parar / recarregar:
#   sudo launchctl bootout system/co.pedalhidrografi.phidro
```

(Em macOS antigos, o equivalente é `sudo launchctl load -w <plist>`.)
Logs vão para `/tmp/phidro.log` e `/tmp/phidro.err`. O serviço escuta só
em `127.0.0.1:8000` — quem o expõe é o túnel (passo 4).

**Impedir o Mac de dormir** — um servidor não pode hibernar:

```sh
sudo pmset -a sleep 0          # desktop
sudo pmset -a disablesleep 1   # notebook (impede dormir com a tampa)
```

> Em Linux, o equivalente é uma unit do systemd chamando o mesmo gunicorn
> single-worker (`--workers 1` é obrigatório: o lock global de mutação é
> per-processo; 2+ workers = lost updates nos catálogos TTL).

## 4. HTTPS público — Cloudflare Tunnel

O app é um PWA (service worker, geolocalização) e **exige HTTPS**. A forma
mais simples, sem abrir portas no roteador nem IP fixo, é o Cloudflare
Tunnel (gratuito; `brew install cloudflared` no macOS):

```sh
cloudflared tunnel login
cloudflared tunnel create phidro
# aponte um (sub)domínio seu para o túnel:
cloudflared tunnel route dns phidro pedalhidrografi.co
```

No arquivo de config do túnel (`~/.cloudflared/config.yml`), aponte o
serviço para `http://localhost:8000`, e rode o `cloudflared` como serviço
(`sudo cloudflared service install`). A Cloudflare cuida do HTTPS.

> Alternativa sem Cloudflare: encaminhar uma porta no roteador + DNS
> dinâmico + um proxy reverso (Caddy faz HTTPS automático via Let's
> Encrypt). É mais trabalho; o túnel é o caminho mais curto.

## 5. O app já está pronto

`web/app.js` e `web/upload_images.html` usam caminhos relativos
(`./data/data_graphs.ttl`, `./data/uploads.ttl`, `./photos/<phash>/large.jpg`,
`./upload-image`, `./delete-image/<phash>`). Como o backend serve o app e a
API na **mesma origem**, funciona sem CORS e sem configurar URLs.

## Limitações e notas

- **Camada de topografia colorida:** os tiles `rmsampa-v2` estavam no GCS.
  Sem a nuvem, essa sobreposição não carrega. O mapa-base do OpenStreetMap
  (externo, gratuito) continua funcionando; só o relevo colorido some até
  você hospedar esses tiles em algum lugar (o backend pode servi-los como
  arquivos estáticos, se você tiver a pirâmide de tiles).
- **Segurança:** não há autenticação — presume-se que quem alcança o
  servidor é de confiança. Qualquer um que abrir a URL pode enviar e apagar
  fotos. Se isso deixar de valer, restrinja o acesso na borda (regra do
  Cloudflare Tunnel, lista de IPs, VPN) ou reintroduza um token.
- **HEIC:** o servidor não decodifica imagem — `upload_images.html` converte
  HEIC para JPEG no browser (via `heic2any`) e envia variantes prontas.
  Servidor não precisa de `pillow-heif`.

## Rodar no Cloud Run

`main.py` é o mesmo container; só a camada de storage muda. Em vez de
filesystem, `STORAGE_BACKEND=gcs` faz tudo passar por
`google-cloud-storage` num bucket (default `phidro-state`). A leitura usa
`bucket.get_blob(key)` (e não `bucket.blob(key)` puro) pra evitar um bug
silencioso onde o blob retorna conteúdo de uma geração desatualizada
mesmo com uma única geração corrente — ver
`GCSStateStore.read_text` em `backend/storage.py`.

Deploy completo (build + push + rota + bucket bootstrap):

```sh
scripts/deploy-cloudrun.sh                # build + deploy
scripts/deploy-cloudrun.sh --state        # idem + sync uploads.ttl/photos/clips
scripts/deploy-cloudrun.sh --state-only   # só sync, sem rebuild
scripts/deploy-cloudrun.sh --dry-run      # preview
```

O sync push `web/photos/` e `web/clips/` (excluindo `raw/`) e os TTLs
mutáveis (`uploads.ttl`, `data_graphs.ttl`) pro bucket via
`gcloud storage rsync`. Os TTLs estáticos (shapes/ontology/tours) já
vão em todo deploy, independente das flags. No fim, faz `POST /reload`
pra invalidar caches in-memory do validador + manifesto.
