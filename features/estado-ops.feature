# language: pt
@ops @nao-verificado
Funcionalidade: Estado, sincronização e proteção contra lost updates
  Arquivos dual-writer (tours.ttl, images.ttl, routes.json) mutam local
  e no bucket; o sync-guard e o Object Versioning são a rede de segurança.

  @auto
  Cenário: sync-guard recusa clobber
    Dado um baseline MD5 em .sync-state/
    E o destino mudou desde o baseline E difere da origem
    Quando eu rodo deploy-cloudrun.sh --state (ou pull-cloudrun.sh)
    Então a cópia é recusada com exit 3 e instruções de reconciliação
    E --force sobrepõe e restabelece o baseline

  @auto
  Cenário: Deploy garante Versioning + lifecycle idempotentes
    Quando eu rodo deploy-cloudrun.sh
    Então o bucket fica com Object Versioning ligado
    E lifecycle usa daysSinceNoncurrentTime=90 (NUNCA age)

  @auto
  Cenário: state-history restaura sem destruir
    Quando eu rodo state-history.sh restore <file>
    Então uma NOVA geração corrente é escrita (as antigas ficam)
    E POST /reload faz o backend reler o catálogo

  @backend @auto
  Cenário: Leitura GCS usa get_blob
    # bucket.blob()+download_as_text() serviu conteúdo stale no Cloud Run
    Quando o backend lê estado do bucket
    Então usa bucket.get_blob(key)

  @auto
  Cenário: gunicorn com exatamente 1 worker (e 1 instância no Cloud Run)
    Quando eu inspeciono Dockerfile, phidro.plist e o deploy
    Então --workers 1 e min=max=1 instância
    # o _state_lock é por processo; 2+ workers = lost update silencioso

  @backend @auto
  Cenário: Mutações concorrentes no mesmo processo são serializadas
    Quando dois uploads chegam simultaneamente
    Então o catálogo final contém os dois (read-modify-write sob _state_lock)

  @auto
  Cenário: Container magrinho
    Quando eu inspeciono .gcloudignore/.dockerignore
    Então web/photos/, web/clips/ e eink/ ficam fora do build context
    E em modo gcs, /photos|/clips|/tour_assets fazem 302 pro bucket
