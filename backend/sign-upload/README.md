# sign-upload — função de URLs assinadas para upload de fotos

Permite que o app estático envie fotos direto para um bucket do GCS **sem
nunca expor credenciais no navegador**. A função, rodando com sua própria
service account, assina uma URL de `PUT` de validade curta; o navegador
envia o arquivo direto ao GCS com essa URL.

```
navegador  ──POST {filename, contentType, token}──▶  função sign-upload
navegador  ◀──{ uploadUrl assinada }──────────────────────────┘
navegador  ──PUT bytes da foto──▶  bucket gs://pedalhidro-uploads
```

Arquivos: `main.py` (a função), `requirements.txt`, `cors.json`.

## Pré-requisitos
- `gcloud` autenticado no projeto `pedal-hidrografico`.
- APIs ligadas: Cloud Functions, Cloud Run, Cloud Build, Artifact Registry,
  IAM, Cloud Storage.

## 1. Variáveis (ajuste ao seu ambiente)

```sh
PROJECT=pedal-hidrografico
REGION=southamerica-east1
BUCKET=pedalhidro-uploads
SITE_ORIGIN=https://telhas.pedalhidrografi.co
SECRET=$(openssl rand -hex 16)        # GUARDE este token — é a senha de envio
SA=phidro-uploader@$PROJECT.iam.gserviceaccount.com
echo "Token de upload: $SECRET"
```

## 2. Bucket de uploads — separado do bucket do site

```sh
gcloud storage buckets create gs://$BUCKET \
  --project=$PROJECT --location=$REGION --uniform-bucket-level-access
```

Mantenha-o **privado** (não dê leitura pública). O `build-photos.py` lê dele
com suas próprias credenciais; o site nunca lê esse bucket direto.

## 3. CORS no bucket

`cors.json` libera qualquer origem (`"origin": ["*"]`) — sem manutenção por
domínio. Isso é seguro aqui: o `PUT` no bucket exige uma URL assinada de uso
único, e o CORS `*` só permite que uma página *tente* o pedido.

```sh
gcloud storage buckets update gs://$BUCKET --cors-file=cors.json
```

## 4. Service account dedicada para a função

```sh
gcloud iam service-accounts create phidro-uploader \
  --project=$PROJECT --display-name="Pedal Hidrografico uploader"

# pode CRIAR objetos no bucket de uploads (e nada além disso)
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
  --member=serviceAccount:$SA --role=roles/storage.objectCreator

# pode assinar URLs em nome de si mesma (IAM signBlob)
gcloud iam service-accounts add-iam-policy-binding $SA \
  --member=serviceAccount:$SA \
  --role=roles/iam.serviceAccountTokenCreator
```

## 5. Deploy da função (2ª geração)

Rode a partir desta pasta (`backend/sign-upload/`) — `--source=.` envia o
diretório atual. Da raiz do repositório, use `--source=backend/sign-upload`.

```sh
gcloud functions deploy sign-upload \
  --project=$PROJECT --region=$REGION --gen2 \
  --runtime=python312 --source=. --entry-point=sign_upload \
  --trigger-http --allow-unauthenticated \
  --service-account=$SA \
  --set-env-vars="UPLOAD_BUCKET=$BUCKET,UPLOAD_SECRET=$SECRET,ALLOWED_ORIGIN=*"
```

As aspas duplas são necessárias: sem elas o zsh tenta expandir o `*` como
glob e aborta com `no matches found`. Aspas duplas evitam o glob e ainda
deixam `$BUCKET`/`$SECRET` expandirem.

`ALLOWED_ORIGIN=*` faz a função aceitar qualquer origem — o token continua
sendo o portão. Para restringir a domínios específicos, troque por uma lista
separada por vírgulas (ex.: `ALLOWED_ORIGIN=https://telhas.pedalhidrografi.co`).

`--allow-unauthenticated` deixa o endpoint público, mas todo `POST` exige o
token `UPLOAD_SECRET`. Sem token correto → `403`.

## 6. Ligar no app

Pegue a URL da função:

```sh
gcloud functions describe sign-upload --region=$REGION --gen2 \
  --format='value(serviceConfig.uri)'
```

Em `public/app.js`, ponha essa URL na constante `SIGN_UPLOAD_URL`. Aí o botão
"Enviar ao acervo" aparece no app. Na primeira vez o app pede o token
(`UPLOAD_SECRET`) e o guarda no `localStorage` **daquele aparelho** — o token
nunca vai no código-fonte publicado.

## 7. Trazer os uploads para o mapa

Os arquivos caem em `gs://pedalhidro-uploads/uploads/`. Para que apareçam no
mapa publicado, sincronize-os e rode o pipeline normal:

```sh
gcloud storage rsync -r gs://$BUCKET/uploads ./_uploads_baixados
python3 scripts/build-photos.py --photos-root ./_uploads_baixados
./scripts/deploy.sh
```

## Notas de segurança

- **O token vai para o navegador de quem envia.** Por isso ele NÃO fica em
  `app.js`; é digitado em runtime e guardado só no `localStorage` local.
  Para uso público de verdade, troque o token por login real (Firebase Auth
  / Identity Platform) — o token compartilhado só barra abuso casual.
- A URL assinada **fixa o Content-Type**; só `image/jpeg|png|heic|heif` passam.
- A URL assinada de `PUT` **não limita o tamanho** do arquivo. O cliente
  checa ~25 MB antes de enviar, mas isso não é barreira de segurança. Para
  limite imposto pelo servidor, use uma *signed POST policy*.
- Considere uma regra de *lifecycle* no bucket (apagar uploads crus após N
  dias) e um alerta de orçamento, já que o endpoint é público.
- O bucket de uploads é **separado** do bucket do site e nunca é público.
