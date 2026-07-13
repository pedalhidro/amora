# language: pt
@backend @nao-verificado
Funcionalidade: Exclusão e purga por aritmética de IRIs derivados
  Purgar um sujeito = remover (sujeito,*,*) + os IRIs <sujeito>_*.
  Sem caminhada de blank nodes; o sufixo "_" evita prefix-match entre irmãos.

  Contexto:
    Dado o backend rodando com STORAGE_BACKEND=local

  @auto
  Cenário: Excluir foto purga triples, derivados e blobs
    Dado uma foto catalogada com nós _geo e _hash
    Quando eu chamo POST /delete-image/<phash>
    Então med:<phash>, med:<phash>_geo e med:<phash>_hash somem de images.ttl
    E photos/<phash>/ é apagado do storage

  @auto
  Cenário: Excluir vídeo purga o mesmo padrão
    Quando eu chamo POST /delete-video/<vhash>
    Então as triples e blobs do vídeo somem

  @auto
  Cenário: Purga não vaza para IRIs irmãos
    Dado passeios pas:abc e pas:abcd (um prefixo do outro)
    Quando eu excluo pas:abc
    Então pas:abcd e seus derivados permanecem intactos

  @auto
  Cenário: Excluir tour preserva pessoas e séries
    Dado um passeio que referencia pessoas e uma série
    Quando eu chamo POST /delete-tour/<tour_id>
    Então o passeio e tour_assets/<tour_id>/ somem
    Mas as pessoas e a série continuam no catálogo
    E a entrada do passeio some de routes.json

  @frontend @manual
  Cenário: Botão Excluir tem confirmação
    Quando eu clico em Excluir no popup de uma mídia
    Então um confirm() precede a chamada de delete
