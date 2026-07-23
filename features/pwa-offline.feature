# language: pt
@nao-verificado
Funcionalidade: PWA, service worker e eficiência de rede
  O app funciona offline via sw.js; ETags + compressão evitam re-downloads.

  @ops @auto
  Cenário: VERSION do sw.js acompanha mudanças em web/
    Quando qualquer arquivo servido de web/ muda num commit
    Então o VERSION (phidro-vN) foi incrementado no mesmo commit
    # verificável com um check de git diff no CI/pre-commit

  @frontend @manual
  Cenário: App funciona offline
    Dado uma visita prévia com o SW instalado
    Quando eu fico offline e recarrego
    Então mapa, rotas e catálogos carregam do cache

  @backend @auto
  Cenário: Respostas condicionais com ETag
    Dado que já baixei /routes.json
    Quando eu repito o GET com If-None-Match
    Então recebo 304 (idem /data/<ttl>)

  @backend @auto
  Cenário: Compressão em respostas de arquivo
    Quando eu peço /app.js com Accept-Encoding: gzip
    Então a resposta vem comprimida
    # COMPRESS_STREAMS=True é load-bearing pro send_from_directory

  @frontend @manual
  Cenário: Preload de routes.json coalesce com o fetch do app
    Quando a página carrega
    Então o <link rel="preload"> e o fetch do app.js geram UMA requisição
    # o fetch NÃO usa cache:'no-cache' — manter casados

  @frontend @manual
  Cenário: Changelog acompanha mudanças visíveis
    Quando uma mudança visível ao usuário é lançada
    Então o <details class="help-changelog"> do modal Ajuda ganha entrada datada
