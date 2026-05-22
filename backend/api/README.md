# phidro-api — backend único (Cloud Run + Firestore)

Substitui as três Cloud Functions (`sign-upload`, `process-upload`,
`delete-photo`) por **um serviço Flask** no Cloud Run, com rotas:

| rota              | método | o que faz                                  |
|-------------------|--------|--------------------------------------------|
| `/sign-upload`    | POST   | emite URL assinada para upload             |
| `/delete-photo`   | POST   | apaga uma foto do acervo                   |
| `/events`         | POST   | processa upload novo (alvo do Eventarc)    |
| `/`               | GET    | health check                               |

As fotos do acervo passam a viver no **Firestore** (coleção `photos`) — a
fonte da verdade. O `photos.jsonld` no GCS vira só um cache estático,
recriado a cada upload/remoção e servido pelo CDN ao app. Isso elimina a
corrida que havia ao reconstruir o manifesto a partir de sidecars `items/`.

Arquivos: `main.py`, `requirements.txt`, `Procfile`.

## Pré-requisitos
- A SA `phidro-processor` já existe, com `objectViewer` em
  `gs://pedalhidro-uploads` e `objectAdmin` em `gs://telhas`.
- APIs ligadas: Cloud Run, Cloud Build, Artifact Registry, Eventarc,
  Pub/Sub, Firestore, IAM.

## 1. Variáveis

```sh
PROJECT=pedal-hidrografico
REGION=southamerica-east1
SA=phidro-processor@$PROJECT.iam.gserviceaccount.com
SECRET=<o mesmo UPLOAD_SECRET de antes>
```

## 2. Banco Firestore (uma vez por projeto)

```sh
gcloud firestore databases create --project=$PROJECT --location=$REGION
```

Se já existir um banco `(default)`, o comando falha — pode ignorar.

## 3. IAM extra para a SA

A `phidro-processor` já lê o bucket de uploads e administra o `telhas`.
Faltam duas permissões:

```sh
# ler e gravar no Firestore
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:$SA --role=roles/datastore.user

# assinar URLs em nome de si mesma (a rota /sign-upload precisa)
gcloud iam service-accounts add-iam-policy-binding $SA \
  --member=serviceAccount:$SA --role=roles/iam.serviceAccountTokenCreator
```

`eventarc.eventReceiver`, `run.invoker` e o `pubsub.publisher` do agente do
GCS já foram concedidos para a antiga `process-upload` — continuam valendo.

## 4. Deploy do serviço

Rode a partir desta pasta (`backend/api/`). Da raiz, use `--source=backend/api`.

```sh
gcloud run deploy phidro-api \
  --project=$PROJECT --region=$REGION --source=. \
  --service-account=$SA \
  --allow-unauthenticated \
  --memory=512Mi --timeout=120 \
  --set-env-vars="UPLOAD_BUCKET=pedalhidro-uploads,OUT_BUCKET=telhas,OUT_PREFIX=fotos,PUBLIC_BASE=https://telhas.pedalhidrografi.co/fotos,UPLOAD_SECRET=$SECRET,ALLOWED_ORIGIN=*,ROUTES_URL=https://telhas.pedalhidrografi.co/rota_app/routes.json"
```

Aspas duplas no `--set-env-vars` (senão o zsh tenta expandir o `*`).
`--allow-unauthenticated`: as rotas `/sign-upload` e `/delete-photo` são
protegidas pelo token; `/events` aceita o evento do Eventarc (um evento
forjado, no pior caso, tenta processar um objeto inexistente e para).

## 5. Gatilho Eventarc para `/events`

```sh
gcloud eventarc triggers create phidro-uploads \
  --project=$PROJECT --location=$REGION \
  --destination-run-service=phidro-api \
  --destination-run-region=$REGION \
  --destination-run-path=/events \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=pedalhidro-uploads" \
  --service-account=$SA
```

## 6. Ligar no app

```sh
gcloud run services describe phidro-api --region=$REGION \
  --format='value(status.url)'
```

Em `public/app.js`, aponte para as rotas do novo serviço:

```js
const SIGN_UPLOAD_URL  = 'https://phidro-api-XXXX.run.app/sign-upload';
const DELETE_PHOTO_URL = 'https://phidro-api-XXXX.run.app/delete-photo';
```

## 7. Aposentar o antigo

Depois de testar (envie uma foto, veja `photos.jsonld` atualizar), remova as
três funções e o gatilho antigos:

```sh
gcloud functions delete sign-upload    --region=$REGION --gen2
gcloud functions delete process-upload --region=$REGION --gen2
gcloud functions delete delete-photo   --region=$REGION --gen2
gcloud eventarc triggers delete <gatilho-antigo-da-process-upload> --location=$REGION
```

As pastas `backend/sign-upload`, `backend/process-upload` e
`backend/delete-photo` ficam obsoletas — pode apagá-las do repositório.

## Migração de fotos já existentes

Fotos arquivadas antes desta mudança têm um sidecar em
`gs://telhas/fotos/items/` mas **não** estão no Firestore. Se houver alguma,
importe-as uma vez:

```sh
gcloud storage cat gs://telhas/fotos/items/*.json   # confira o que há
```

Para cada item, crie um documento na coleção `photos` com o `id` da foto.
Como o pipeline de upload é recente, isso provavelmente é uma ou nenhuma
foto — mais simples reenviar pelo app. Os sidecars `items/` podem ser
apagados depois.

## Notas

- **Firestore é a fonte da verdade.** Gravações são atômicas por documento,
  então uploads simultâneos não se perdem mais.
- O `photos.jsonld` é recriado por inteiro a cada mudança (consulta o
  Firestore). É um cache; o app continua lendo o arquivo estático no CDN.
- O serviço usa uma só configuração (512 MiB / 120 s) para todas as rotas —
  dimensionada pela mais pesada (`/events`, que decodifica HEIC).
