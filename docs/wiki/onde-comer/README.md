# Onde comer — fontes do wiki

A página [Onde comer](https://pedalhidrografi.co/wiki/Onde_comer) do wiki
(Miraheze) é a **fonte única** dos lugares para comer. O amora não guarda
cópia: a camada "Onde comer (wiki)" lê os pontos ao vivo pela API do
Kartographer. Estes arquivos são as fontes versionadas do que mora no wiki —
editar aqui e publicar lá (ou o contrário, e trazer de volta).

| Arquivo | Página no wiki |
|---|---|
| `Modulo-Onde_comer.lua` | `Módulo:Onde comer` |
| `Predefinicao-Lugar_para_comer.wiki` | `Predefinição:Lugar para comer` |
| `Predefinicao-Mapa_onde_comer.wiki` | `Predefinição:Mapa onde comer` |
| `Onde_comer.wiki` | `Onde comer` (conteúdo inicial; depois a página vive no wiki) |
| `MediaWiki-Common.js` | `MediaWiki:Common.js` (exige interface-admin) |
| `MediaWiki-Mobile.js` | `MediaWiki:Mobile.js` (idem) |

## Como funciona

- Cada lugar é um `{{Lugar para comer | nome = … | coordenadas = lat, lon | … }}`
  sob uma seção `== Região ==`. A predefinição chama `Módulo:Onde comer`, que
  desenha a ficha e um `<maplink>` com o ponto.
- `{{Mapa onde comer}}` lê o wikitexto **salvo** da própria página, junta todas
  as fichas (região = a seção `==` onde estão) e desenha um `<mapframe>`.
  Não dá pra usar `group`/`show` do Kartographer: só existem no "modo
  Wikivoyage", desligado nesta instalação.
- `MediaWiki:Common.js` entra no hook `wikipage.maps` de todo mapa do
  Kartographer e (1) põe a Topografia colorida por cima do OSM, a partir de
  `storage.googleapis.com/telhas/rmsampa-v2` (o CSP do Miraheze libera esse
  host em `img-src`, não `telhas.pedalhidrografi.co`); (2) troca os pinos por
  bolinhas — o servidor de mapas configurado (`tile.openstreetmap.org`) não
  tem `/v4/marker`, então sem o script todo marcador vira imagem quebrada.
  O mapa estático (snapshot) também 400a pelo mesmo motivo; com JS o Leaflet
  substitui a imagem.

## Contrato com o amora

O amora (`web/app.js`, seção "Onde comer") busca
`https://pedalhidrografi.co/w/api.php?action=query&prop=mapdata&titles=Onde_comer&mpdlimit=max&format=json&formatversion=2&origin=*`
e lê das feições `Point`:

`id` (slug, também a âncora `<h3 id>` na página e o `/#comer=<id>` do amora),
`nome` (texto cru; `title` passa pelo wikitexto→HTML do Kartographer), `regiao` (só no grupo do mapframe), `endereco`, `metro`, `tipo`,
`bicicleta`, `instagram` (perfil sem @), `site`, `aproximado` (bool).

Cada lugar aparece em dois grupos (maplink da ficha + mapframe) — o amora junta
por `id`. Renomear/remover uma propriedade aqui = mudar `comerPlaces` /
`comerPopupHtml` lá.

## Publicar

Com `WIKI_USER`/`WIKI_PASSWORD` (senha de robô) no `.env` do amora, via API
(`action=edit`). O namespace MediaWiki precisa dos grants "Editar o espaço
nominal MediaWiki…" e "Editar CSS/JS de todo o site e de usuários" na senha de
robô, e o usuário no grupo interface-admin.
