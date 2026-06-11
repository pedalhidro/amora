#!/usr/bin/env bash
#
# Guarda anti-clobber pros arquivos de estado mutável sincronizados entre o
# repo local e o bucket GCS: uploads.ttl, data_graphs.ttl, tours.ttl,
# routes.json. Os dois lados são escritos de forma independente (uploads e
# Tour CRUD mutam o bucket server-side; builds e edições locais mutam o
# repo), então um cp cego em qualquer direção descarta silenciosamente o
# outro lado — o mesmo lost update do gunicorn multi-worker, só que no
# nível do deploy.
#
# Mecânica: .sync-state/<basename>.md5 (gitignored) guarda o MD5 (base64,
# mesmo formato do md5_hash do GCS) do conteúdo no último sync bem-sucedido
# — o último momento em que local == bucket. Antes de copiar, compara
# origem (S), destino (D) e baseline (B):
#
#   S == D            → insync   (só rebaseia o stash, sem copiar)
#   D == B            → ok       (destino não mudou desde o último sync)
#   D != B, D != S    → conflict (os dois lados mudaram — copiar perderia
#                                 o destino; reconcilie ou use --force)
#
# Sem baseline (primeiro uso) qualquer divergência vira conflict: confira
# manualmente qual lado está certo e rode com --force pra estabelecer o
# baseline.
#
# Pra ser source-ado por deploy-cloudrun.sh / pull-cloudrun.sh. Espera
# REPO_ROOT e PROJECT definidos pelo caller; SYNC_GUARD_DRY=1 pula a
# escrita do stash (dry-run).

SYNC_STATE_DIR="$REPO_ROOT/.sync-state"

# MD5 em base64 de um arquivo local. Vazio se o arquivo não existe.
sync_guard_local_md5() {
  local path="$1"
  if [[ -f "$path" ]]; then
    openssl dgst -md5 -binary "$path" | base64
  else
    echo ""
  fi
}

# md5_hash do objeto no bucket. Vazio se o objeto não existe.
sync_guard_remote_md5() {
  local url="$1"
  gcloud storage objects describe "$url" --project="$PROJECT" \
    --format="value(md5_hash)" 2>/dev/null || echo ""
}

sync_guard_stash_read() {
  local name="$1"
  cat "$SYNC_STATE_DIR/$name.md5" 2>/dev/null || echo ""
}

sync_guard_stash_write() {
  local name="$1" md5="$2"
  [[ "${SYNC_GUARD_DRY:-0}" == 1 ]] && return 0
  mkdir -p "$SYNC_STATE_DIR"
  printf '%s\n' "$md5" > "$SYNC_STATE_DIR/$name.md5"
}

# Veredito pra uma cópia DESTINO ← ORIGEM (ver tabela no cabeçalho).
# Args: <nome-do-stash> <md5-origem> <md5-destino>. Imprime insync|ok|conflict.
sync_guard_verdict() {
  local name="$1" src="$2" dst="$3"
  local base
  base="$(sync_guard_stash_read "$name")"
  if [[ -z "$dst" ]]; then echo ok; return; fi
  if [[ "$src" == "$dst" ]]; then echo insync; return; fi
  if [[ -n "$base" && "$dst" == "$base" ]]; then echo ok; return; fi
  echo conflict
}
