# language: pt
@backend @nao-verificado
Funcionalidade: CRUD de passeios e sync incremental do routes.json
  POST /upload-tour upserta exatamente um ph:Tour em tours.ttl;
  o backend mantém routes.json incrementalmente a cada mutação.

  Contexto:
    Dado o backend rodando com STORAGE_BACKEND=local

  @auto
  Cenário: Criação em modo replace
    Quando eu envio um TTL com um novo ph:Tour (mode=replace)
    Então tours.ttl contém o passeio com o slug informado
    E o SHACL validou o documento final

  @auto
  Cenário: Edição em modo patch preserva predicados não enviados
    Dado um passeio existente com schema:description preenchida
    Quando eu envio um patch só com ph:energyEstimate
    Então a energia é atualizada E a description sobrevive

  @auto
  Cenário: Campo remove apaga predicados no patch
    Dado um passeio existente com ph:energyEstimate
    Quando eu envio um patch com remove="ph:energyEstimate" e sem esse predicado
    Então o passeio fica sem ph:energyEstimate

  @auto
  Cenário: Patch é validado no estado FINAL
    Dado um passeio válido existente
    Quando eu envio um patch que tornaria o estado final inválido pelo SHACL
    Então o patch é rejeitado e tours.ttl não muda

  @auto
  Cenário: Arte de anúncio é salva e ligada
    Quando eu envio um tour com arquivo announcement
    Então o arquivo vai para tour_assets/<tour_id>/announcement.<ext>
    E o passeio ganha schema:image apontando pra URL

  @auto
  Cenário: Slug com underscore é rejeitado
    Quando eu envio um tour cujo slug contém "_"
    Então o upload é rejeitado (colidiria com nós derivados _route etc.)

  @auto
  Cenário: Sync de routes.json com ph:linkRoute
    Dado RWGPS acessível
    Quando eu salvo um tour com ph:linkRoute para uma rota RideWithGPS
    Então routes.json ganha/atualiza a entrada keyed por tourIri

  @auto
  Cenário: Falha do RWGPS não falha o save
    Dado RWGPS inacessível
    Quando eu salvo um tour com ph:linkRoute
    Então o save do tour tem sucesso
    E a entrada em routes.json fica com latlngs:null + error

  @auto
  Cenário: Tour sem linkRoute remove a entrada
    Dado um tour presente em routes.json
    Quando eu salvo o tour sem ph:linkRoute
    Então a entrada dele some de routes.json

  @auto
  Cenário: Numeração de série resolvida do catálogo persistido
    Dado edições ph:SeriesEdition existentes fora do fragmento enviado
    Quando eu salvo um tour de uma série
    Então a numeração usa o tours.ttl persistido, não só o fragmento

  @auto
  Cenário: Feed e sitemap refletem o CRUD
    Quando eu crio um passeio
    Então /feed.xml passa a listar o passeio (cache invalidado por hash)
    E /sitemap.xml inclui /?tour=<id>

  @frontend @manual
  Cenário: Censo abre em iframe e edição não estranda o usuário
    Quando eu abro Censo, navego pro form de edição, fecho e reabro
    Então o iframe volta pra censo.html, não pro form
