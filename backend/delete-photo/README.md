# delete-photo — função que apaga uma foto do acervo

Endpoint HTTP protegido por token. Recebe `POST {"id": "<id>"}`, apaga
`photos/<id>.jpg`, `thumbs/<id>.jpg` e `items/<id>.json` em
`gs://telhas/fotos/` e reconstrói `photos.jsonld`.

**A remoção é definitiva — não há lixeira.** O `id` é o campo `id` da foto
no `photos.jsonld` (o app o envia automaticamente pelo botão "Apagar foto").

## Pré-requisitos
- As funções `sign-upload` e `process-upload` já deployadas.
- A service account `phidro-processor` já existe e tem `objectAdmin` em
  `gs://telhas` (criada para a `process-upload`) — esta função a reaproveita.

## 1. Variáveis

```sh
PROJECT=pedal-hidrografico
REGION=southamerica-east1
SA=phidro-processor@$PROJECT.iam.gserviceaccount.com
SECRET=<o MESMO UPLOAD_SECRET usado na sign-upload>
```

## 2. Deploy

Rode a partir desta pasta (`backend/delete-photo/`). Da raiz do repositório,
use `--source=backend/delete-photo`.

```sh
gcloud functions deploy delete-photo \
  --project=$PROJECT --region=$REGION --gen2 \
  --runtime=python312 --source=. --entry-point=delete_photo \
  --trigger-http --allow-unauthenticated \
  --service-account=$SA \
  --set-env-vars="OUT_BUCKET=telhas,OUT_PREFIX=fotos,UPLOAD_SECRET=$SECRET,ALLOWED_ORIGIN=*"
```

`UPLOAD_SECRET` deve ser **o mesmo token** da `sign-upload` — assim o app usa
um único token para enviar e apagar. (Aspas duplas: o `*` senão vira glob.)

A SA `phidro-processor` já pode listar/ler/criar/apagar em `gs://telhas`
(`objectAdmin`), então não há novo IAM a conceder.

## 3. Ligar no app

```sh
gcloud functions describe delete-photo --region=$REGION --gen2 \
  --format='value(serviceConfig.uri)'
```

Ponha essa URL na constante `DELETE_PHOTO_URL` em `public/app.js`. Aí o botão
"Apagar foto" aparece no popup de cada foto do acervo. Sem a URL, o botão não
aparece — a função fica desligada.

## Notas de segurança

- O endpoint é público mas exige o token em todo `POST` — sem token → `403`.
  O token é digitado em runtime e guardado só no `localStorage` do aparelho;
  nunca vai no código publicado.
- O `id` é validado contra `[A-Za-z0-9._-]+` (sem `/` nem `..`), então não dá
  para sair do prefixo `fotos/`.
- Como a remoção é definitiva, o app pede confirmação antes de chamar a função.
- Para um histórico recuperável, troque o `delete()` por uma cópia para um
  prefixo `trash/` antes de apagar — mas, como combinado, esta versão apaga
  de vez.
