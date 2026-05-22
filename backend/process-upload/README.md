# process-upload — função que processa fotos enviadas

Dispara automaticamente quando um arquivo novo chega em
`gs://pedalhidro-uploads`. Gera versão de exibição + thumbnail, grava
metadados e reconstrói `gs://telhas/fotos/photos.jsonld` — o manifesto que
o app do mapa consome.

```
gs://pedalhidro-uploads/uploads/foto.heic
        │  (evento "object finalized")
        ▼
   process-upload  ──▶  gs://telhas/fotos/photos/<id>.jpg   (exibição ~1600px)
                   ──▶  gs://telhas/fotos/thumbs/<id>.jpg   (thumbnail ~400px)
                   ──▶  gs://telhas/fotos/items/<id>.json   (metadados)
                   ──▶  gs://telhas/fotos/photos.jsonld     (manifesto recriado)
```

Arquivos: `main.py`, `requirements.txt`.

## Pré-requisitos
- A função `sign-upload` já deployada (deposita fotos em `uploads/`).
- APIs ligadas: Cloud Functions, Cloud Run, Cloud Build, Eventarc, Pub/Sub,
  Cloud Storage.

## 1. Variáveis

```sh
PROJECT=pedal-hidrografico
REGION=southamerica-east1
SA=phidro-processor@$PROJECT.iam.gserviceaccount.com
```

## 2. Service account dedicada

```sh
gcloud iam service-accounts create phidro-processor \
  --project=$PROJECT --display-name="Pedal Hidrografico processor"

# lê o bucket de uploads
gcloud storage buckets add-iam-policy-binding gs://pedalhidro-uploads \
  --member=serviceAccount:$SA --role=roles/storage.objectViewer

# escreve o acervo processado no bucket do site
gcloud storage buckets add-iam-policy-binding gs://telhas \
  --member=serviceAccount:$SA --role=roles/storage.objectAdmin
```

> **Atenção de segurança:** `objectAdmin` em `gs://telhas` dá à função
> escrita em **todo** o bucket do site, não só em `fotos/`. O código só
> mexe no prefixo `fotos/`, mas um bug poderia tocar `rota_app/`. Para
> isolar de verdade, a opção limpa é usar um **bucket separado** só do
> acervo (ex.: `gs://telhas-fotos`) e apontar `OUT_BUCKET`/`PUBLIC_BASE`
> para ele. Alternativamente, restrinja a permissão com uma *IAM Condition*
> em `resource.name.startsWith(".../objects/fotos/")` (ciente de que a
> listagem de objetos não é coberta pela condição).

## 3. Eventarc — permissões do gatilho

```sh
# o agente de serviço do GCS precisa publicar eventos no Pub/Sub
GCS_SA=$(gcloud storage service-agent --project=$PROJECT)
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:$GCS_SA --role=roles/pubsub.publisher

# a SA da função precisa RECEBER eventos do Eventarc
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:$SA --role=roles/eventarc.eventReceiver

# e ser invocável pelo Eventarc (funções gen2 = Cloud Run por baixo)
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:$SA --role=roles/run.invoker
```

> As permissões de IAM levam ~1 min para propagar. Se o deploy falhar com
> `eventarc.events.receiveEvent denied` logo após o grant, espere e repita.

## 4. Deploy (gatilho de bucket)

Rode a partir desta pasta (`backend/process-upload/`) — `--source=.` envia o
diretório atual. Da raiz do repositório, use `--source=backend/process-upload`.

```sh
gcloud functions deploy process-upload \
  --project=$PROJECT --region=$REGION --gen2 \
  --runtime=python312 --source=. --entry-point=process_upload \
  --trigger-bucket=pedalhidro-uploads \
  --service-account=$SA \
  --memory=512Mi --timeout=120s \
  --set-env-vars=OUT_BUCKET=telhas,OUT_PREFIX=fotos,PUBLIC_BASE=https://telhas.pedalhidrografi.co/fotos,ROUTES_URL=https://telhas.pedalhidrografi.co/rota_app/routes.json
```

`--trigger-bucket` cria o gatilho de *object finalized* no bucket de
uploads. Nenhum dos valores acima tem vírgula, então o `--set-env-vars`
padrão funciona; se algum dia precisar de vírgulas, use `--env-vars-file`.

## 5. Conferir

Envie uma foto pelo app (ou copie um arquivo para `uploads/`) e veja:

```sh
gcloud functions logs read process-upload --region=$REGION --gen2 --limit=20
gcloud storage ls gs://telhas/fotos/
gcloud storage cat gs://telhas/fotos/photos.jsonld | head
```

O app lê `https://telhas.pedalhidrografi.co/fotos/photos.jsonld`
automaticamente (com queda para o `photos.json` local).

## Notas

- **HEIC:** o processamento usa `pillow-heif`, cujas *wheels* já trazem o
  libheif embutido — funciona no builder do Cloud Functions sem libs de
  sistema. Ainda assim, teste com um HEIC real após o primeiro deploy.
- **Sem GPS:** fotos sem coordenadas no EXIF não entram no manifesto (o
  original continua arquivado em `pedalhidro-uploads`).
- **Concorrência:** o `photos.jsonld` é recriado da lista completa de
  `items/` a cada disparo — uploads simultâneos convergem por consistência
  eventual.
- **Cache:** thumbnails e fotos vão com cache longo e imutável; o
  `photos.jsonld` vai com `no-cache` para o CDN/app verem as atualizações.
- **Foto ↔ pedal:** a associação usa `routes.json` e casa pela data (com
  janela de madrugada). Se `ROUTES_URL` falhar, a foto fica com `ride: null`.
