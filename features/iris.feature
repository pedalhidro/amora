# language: pt
@backend @nao-verificado
Funcionalidade: IRIs dereferenciáveis (Linked Data, httpRange-14)
  id.pedalhidrografi.co/<path> → 303 (Cloudflare) → resolvers Flask no amora,
  com content negotiation: Accept text/turtle (ou ?format=ttl) → triples;
  senão página/redirect humano.

  @auto
  Esquema do Cenário: Content negotiation por tipo de recurso
    Quando eu peço GET <path> com Accept: text/turtle
    Então recebo turtle com as triples do recurso
    Quando eu peço GET <path> sem Accept de turtle
    Então recebo <resposta_humana>

    Exemplos:
      | path              | resposta_humana                     |
      | /terms            | página HTML de documentação         |
      | /pessoas/<slug>   | pessoas.html                        |
      | /passeio/<slug>   | 303 para /?tour=<slug>              |
      | /passeio/BP/4     | 303 para o passeio realizador       |
      | /serie/BP         | HTML da série, edições recentes 1º  |
      | /midia/<hash>     | 303 para /imagens.html?pick=        |
      | /listas/<slug>    | 303 para /imagens.html              |

  @auto
  Cenário: Alias de deep link numérico antigo
    Quando eu peço GET /?tour=<id-numérico-antigo>
    Então recebo 303 para /?tour=<slug> via tour-iri-map

  @auto
  Cenário: index() responde em / E /index.html
    # o worker da Cloudflare reescreve / → /index.html antes da origem
    Quando eu peço GET /index.html com ?tour=<id>
    Então o SSR por passeio roda igual ao GET /

  @auto
  Cenário: SSR mínimo por passeio
    Quando eu peço GET /?tour=<slug> como crawler (sem JS)
    Então o HTML tem title/OG/canonical do passeio + JSON-LD + <article>
    E se a renderização falhar, degrada pro index estático

  @auto
  Cenário: Links de mídia com prefixo legado
    Quando eu peço /midia/image_<hash>
    Então resolve igual a /midia/<hash> (prefixo tirado na leitura)

  @auto
  Cenário: Guid do feed é estável pra passeios migrados
    Quando eu leio /feed.xml
    Então passeios migrados usam o guid legado phd:tour_<numid>
