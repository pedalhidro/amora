# language: pt
@backend @nao-verificado
Funcionalidade: Localização ao vivo (efêmera, em memória)
  Estado por token pseudônimo em _live_positions; NUNCA toca os catálogos.

  @auto
  Cenário: Upsert de posição e leitura
    Quando eu envio POST /live-location {id, lat, lng}
    Então GET /live-locations retorna a posição com o rastro

  @auto
  Cenário: Retenção por token
    Dado um token com ttl de 60 segundos
    Quando o fix expira
    Então ele some de GET /live-locations
    E o ttl é limitado ao teto de 24h

  @auto
  Cenário: Rastro é podado
    Quando um token acumula fixes demais
    Então o rastro respeita o teto de 500 pontos/pessoa (e 500 pessoas)

  @auto
  Cenário: Stop apaga o rastro imediatamente
    Quando eu envio POST /live-location/stop com meu token
    Então meu token some na hora
    # e NÃO é chamado automaticamente — é o "apagar meu rastro" explícito

  @auto
  Cenário: CORS aberto SÓ nos endpoints live
    Quando a origem é capacitor:// ou http://localhost
    Então os endpoints /live-location* respondem com CORS
    Mas /upload-image e /upload-tour continuam same-origin

  @auto
  Cenário: /live-locations não é cacheável
    Quando eu peço GET /live-locations
    Então a resposta tem Cache-Control: no-store e sem ETag

  @frontend @manual
  Cenário: Ver e transmitir são independentes e privados por default
    Quando eu abro o app pela primeira vez
    Então a camada "Pessoas ao vivo" mostra os outros
    Mas minha transmissão NUNCA começa sozinha

  @frontend @manual
  Cenário: Shell nativo transmite com a tela apagada
    Dado o app Capacitor com transmissão ligada
    Quando a tela apaga
    Então os fixes continuam chegando (background-geolocation → phidroLivePush)
