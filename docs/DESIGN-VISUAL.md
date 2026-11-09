# Design visual do amora

Como as cores e a ordem de empilhamento do app são organizadas e como mudar alguma
coisa sem quebrar o resto. O sistema vem do [Bici Busão Sampa](https://github.com/pedalhidro/bicibusaosampa)
(PRs 1 a 3, do Andrei), adaptado para o amora. (`docs/DESIGN.md` é outro assunto: o
modelo RDF.)

**Toda cor e todo `z-index` do app são tokens.** Os tokens ficam em JSON no padrão
[DTCG 2025.10](https://www.designtokens.org/tr/2025.10/), em `design/tokens/`. Um script
sem dependências gera deles o CSS e o JS que o site carrega. O site continua sem build
no deploy: os arquivos gerados são commitados.

```
design/tokens/                a fonte (você edita aqui)
  ref.tokens.json             a paleta
  ui.tokens.json              interface: ordem de empilhamento, sombra composta
  themes/light.tokens.json    cores da interface
  map.tokens.json             a simbologia do mapa
  brand.tokens.json           o app fora da página (PWA)
  amora.resolver.json         como os arquivos se combinam
        │
        ▼  npm run build:tokens   (scripts/build-tokens.mjs)
        │
  web/lib/tokens.css          variáveis CSS                 (gerado)
  web/lib/tokens.js           os mesmos valores para o JS   (gerado)
  este documento, tabelas     a lista de tokens             (gerado)
```

## Como funciona

**Duas camadas.** A paleta (`ref.color.*`) guarda os valores. Os papéis (`ui.*`, `map.*`,
`brand.*`) dizem para que serve cada um e sempre apontam para a paleta. O código só lê
papéis.

**Três domínios.** `ui` é a interface. `map` é a simbologia do mapa, que não muda com o
esquema de cor. `brand` é a barra do navegador e a tela de abertura.

**Nomes.** `<domínio>.<papel>[.<variante>]`, em minúsculas. Vira `--ui-surface-panel` no
CSS e `tokens.ui.surface.panel` no JS (hífens viram camelCase).

## Tarefas comuns

**Mudar uma cor.** Troque o valor em `ref.tokens.json` ou aponte o papel para outro tom.
Rode `npm run build:tokens`, suba o `VERSION` do `web/sw.js` e rode `npm test`.

**Criar um papel.** Acrescente em `themes/light.tokens.json` (interface) ou
`map.tokens.json` (mapa), com `$description` e `usage` (o que é: `text`, `background`,
`border`, `line`, `fill`, `shadow`…). Use em CSS com `var(--ui-…)` e em JS com
`tokens.map.…`.

## Regras (`npm test`)

- Os gerados batem com a fonte.
- Nenhum literal de cor em `web/style.css`, `web/index.html` e `web/app.js`.
- Nenhum `z-index` numérico no `style.css`.
- O código só lê tokens que existem e nunca a paleta direto.
- Papéis apontam para a paleta e têm descrição e `usage`.
- Pares de contraste declarados passam.
- Todo ícone usado está no vocabulário, e todo ícone do vocabulário é usado.
- Nenhum emoji ou glifo como ícone nos botões do `index.html`.

## Ícones

Os botões do `index.html` e o painel de camadas usam o [Tabler Icons](https://tabler.io/icons)
(MIT), por significado: o código pede `uiIcon('swap')`, nunca o nome na biblioteca. Cada
entrada de `design/icons/vocabulary.json` diz o significado e o desenho. Só os SVGs usados
ficam copiados em `design/icons/tabler/`, na versão fixada e com a licença. O ícone segue
a cor do texto e o tamanho da fonte em volta (`.icon`).

```sh
# acrescentar um ícone: o significado e o name em vocabulary.json, depois
npm run icons:fetch   # copia o SVG (a única etapa que precisa de internet)
npm run build:icons   # escreve web/lib/icons.js e os ícones do index.html
```

No `index.html`: `<i data-icon="swap"></i>`, que o build troca pelo `<svg>`, então o ícone
aparece antes de qualquer script. Num botão que liga e desliga, os dois estilos ficam dentro
de `.icon-swap`, e o preenchido aparece com `aria-pressed="true"`. No JS:
`import { icon as uiIcon } from './lib/icons.js'`.

## Exceções

- **Cores que são dados.** As paletas do OpenInfraMap (`OIM_THEMES` e vizinhas) e a cor
  calculada de cada pessoa ao vivo não são papéis do amora. Ficam entre os comentários
  `cores-de-dados: início` e `cores-de-dados: fim` no `app.js`.
- **Cores de linhas que vêm dos dados** (metrô, bici-busão) também ficam nos dados.

## Decisões

1. **Paleta herdada, sem redesenho.** A migração não mudou nenhuma cor: cada literal
   virou um papel de valor idêntico. Por isso a paleta tem nomes pelo próprio valor
   (`ref.color.orange.c2410c`) e não é uma escala. Consolidar tons é trabalho de
   redesenho.
2. **Sem modo escuro.** O amora não tem. A estrutura (`themes/`) aceita um `dark` quando
   houver.
3. **Script do Bici Busão, adaptado**, sem dependências. A fonte é o padrão DTCG.
4. **Água não é azul** (`map.water.fill`): decisão do coletivo.

## O que falta

- **Páginas embutidas** (`imagens`, `censo`, `upload_*`, `subir`, `pessoas`, `memoria`,
  `custos`, `backfill_tours`) ainda têm literais próprios e leem os nomes curtos (`--bg`,
  `--text`…), que o `tokens.css` gera como aliases.
- **`web/lib/poster.js`**: as cores de rótulo são padrões da arte, ainda literais.
- **Emojis fora dos botões do `index.html` e do painel de camadas**: popups, toasts, o seletor
  de símbolos de POI (que são dados: viram `<sym>` no GPX) e as páginas embutidas.
- **Grade de 4 px e texto base de 16 px** (o PR 2 do Bici Busão): muda o visual de
  propósito e esbarra em tamanhos que o `CLAUDE.md` registra como necessários (alvos de
  toque, campos de 16 px no iPhone). Fica para uma mudança própria, revisada com
  capturas de antes e depois. Espaço, raio, tipo e movimento ainda não são tokens.

## Tokens

### Interface
<!-- tokens:ui -->
| Token | Valor | Para quê |
|---|---|---|
| `ui.layer.modal` | `5000` | Modais. |
| `ui.layer.inner-top` | `30` | Bolinhas de fechar, dentro do componente. |
| `ui.layer.inner-header` | `20` | Cabeçalho que fica preso, dentro do modal. |
| `ui.layer.sheet` | `5500` | Sidebar e painel de camadas como folhas. |
| `ui.layer.inner-fade` | `25` | Degradê "tem mais", dentro do modal. |
| `ui.layer.overlay` | `6000` | Toasts, setas da foto, popovers. |
| `ui.layer.ghost-video` | `400` | Vídeo sobre o mapa, abaixo dos popups do Leaflet. |
| `ui.layer.tooltip` | `6500` | Dica da rota. |
| `ui.layer.overlay-raised` | `6100` | Toasts com ação. |
| `ui.layer.modal-raised` | `5001` | Modal aberto sobre outro modal (o QR). |
| `ui.layer.map-control` | `1000` | Controles presos ao mapa. |
| `ui.layer.map-control-raised` | `1100` | Busca de endereço, sobre os controles. |
| `ui.layer.marker-hover` | `1000` | Bolinha com o ponteiro em cima. |
| `ui.layer.inner-close` | `10` | Fechar do popup. |
| `ui.layer.marker-active` | `1001` | Bolinha em destaque. |
| `ui.layer.inner-back` | `1` | Fundo, dentro do componente. |
| `ui.layer.inner-front` | `2` | Frente, dentro do componente. |
| `ui.layer.inner-actions` | `5` | Ações presas no pé. |
| `ui.layer.poster-art` | `650` | Arte do editor. |
| `ui.layer.poster-ui` | `700` | Alças de edição sobre a arte. |
| `ui.layer.poster-panel` | `1500` | Painel do editor. |
| `ui.shadow.elevated` | `0px 4px 16px rgb(16 24 32 / 0.14)` | Sombra de elevação comum. |
| `ui.surface.page` | `#fafbfc` | Fundo da página. |
| `ui.surface.panel` | `#ffffff` | Painéis, folhas e modais. |
| `ui.surface.control` | `#eef1f4` | Fundo de campos e botões: um pouco mais escuro que o painel. |
| `ui.surface.paper` | `#ffffff` | Fundo branco de verdade, para conteúdo que precisa dele: o QR, o iframe dos formulários. |
| `ui.surface.map-button` | `#ffffff` | Botões soltos sobre o mapa. |
| `ui.surface.map-button-hover` | `#f4f4f4` | Botão sobre o mapa com o ponteiro em cima. |
| `ui.surface.map-button-pressed` | `#d8ecff` | Botão sobre o mapa ligado. |
| `ui.surface.scrim` | `rgb(0 0 0 / 0.55)` | Véu atrás de um modal. |
| `ui.surface.scrim-light` | `rgb(16 24 32 / 0.22)` | Véu leve, atrás do modal de envio. |
| `ui.surface.tint-faint` | `rgb(0 0 0 / 0.02)` | Agrupa uma seção sem separar do painel. |
| `ui.surface.tint` | `rgb(0 0 0 / 0.03)` | Fundo de uma faixa dentro do painel. |
| `ui.surface.tint-strong` | `rgb(0 0 0 / 0.05)` | Campo ou item levemente destacado. |
| `ui.surface.button-tint` | `rgb(0 0 0 / 0.08)` | Botão discreto sobre um chip. |
| `ui.surface.button-tint-hover` | `rgb(0 0 0 / 0.15)` | Botão discreto com o ponteiro em cima. |
| `ui.surface.neutral-soft` | `rgb(127 127 127 / 0.15)` | Botões e código na ficha da foto. |
| `ui.surface.neutral-hover` | `rgb(127 127 127 / 0.25)` | Botões da ficha da foto com o ponteiro em cima. |
| `ui.surface.fade` | `rgb(255 255 255 / 0)` | Início do degradê "tem mais abaixo" no modal. |
| `ui.surface.video` | `#000000` | Fundo atrás do vídeo. |
| `ui.content.primary` | `#101820` | Texto principal. |
| `ui.content.muted` | `#4a5867` | Texto secundário. |
| `ui.content.on-color` | `#ffffff` | Texto e símbolos sobre fundo colorido: botões primários, toasts, bolinhas. |
| `ui.content.plain` | `#333333` | Texto dos botões sobre o mapa e destaque nos popups. |
| `ui.content.popup-heading` | `#444444` | Cabeçalho das tabelas de popup. |
| `ui.content.popup-soft` | `#666666` | Texto secundário nos popups do mapa. |
| `ui.content.popup-note` | `#888888` | Observação em popup. |
| `ui.content.chip-shadow` | `rgb(0 0 0 / 0.6)` | Sombra do texto nos chips de linha. |
| `ui.content.media-shadow` | `rgb(0 0 0 / 0.8)` | Sombra do texto sobre foto ou vídeo. |
| `ui.accent.default` | `#c2410c` | A cor de ação do app: links, seleção, botão primário. |
| `ui.accent.hover` | `#9a3412` | A cor de ação com o ponteiro em cima. |
| `ui.border.default` | `#c6ced6` | Bordas de painel, campo e botão. |
| `ui.border.dashed` | `#cccccc` | Separador tracejado dentro de um formulário. |
| `ui.border.input` | `rgb(0 0 0 / 0.2)` | Borda de campo sobre popover. |
| `ui.border.popover` | `rgb(0 0 0 / 0.15)` | Borda de popover. |
| `ui.border.popover-divider` | `rgb(0 0 0 / 0.1)` | Divisor dentro de popover. |
| `ui.border.neutral-soft` | `rgb(127 127 127 / 0.3)` | Borda dos botões da ficha da foto. |
| `ui.state.hover` | `rgb(45 169 255 / 0.18)` | Hover de botão secundário. |
| `ui.state.hover-soft` | `rgb(45 169 255 / 0.12)` | Hover em ações de configuração. |
| `ui.state.hover-faint` | `rgb(45 169 255 / 0.08)` | Hover de item de lista. |
| `ui.state.selected` | `rgb(45 169 255 / 0.16)` | Item de lista ou navegação escolhido. |
| `ui.state.hover-bar` | `rgb(255 140 46 / 0.18)` | Hover e estado ligado dos botões da barra. |
| `ui.state.filter-active` | `#0e7490` | Filtro personalizado aplicado. |
| `ui.status.ok` | `#1a7f4b` | Deu certo. |
| `ui.status.ok-border` | `#2f7d43` | Borda do botão de salvar. |
| `ui.status.ok-border-hover` | `#2f9e44` | Borda do botão de salvar com o ponteiro em cima. |
| `ui.status.ok-tint` | `rgb(26 127 75 / 0.12)` | Hover do botão de salvar. |
| `ui.status.warn` | `#9c6a10` | Atenção. |
| `ui.status.error` | `#b3261e` | Erro. |
| `ui.status.danger` | `#b3431e` | Ação que apaga, em botão discreto. |
| `ui.action.delete` | `#ff5722` | Botão de excluir mídia. |
| `ui.action.delete-hover` | `#e74c1c` | Botão de excluir mídia com o ponteiro em cima. |
| `ui.action.view` | `#1d5c96` | Botão de alternar a vista do traçado. |
| `ui.action.view-border` | `#2d6ea8` | Borda do botão de alternar a vista do traçado. |
| `ui.dot.close` | `#ff5f57` | Bolinha vermelha de fechar. |
| `ui.dot.maximize` | `#28c840` | Bolinha verde de maximizar. |
| `ui.dot.border` | `rgb(0 0 0 / 0.22)` | Borda das bolinhas de janela. |
| `ui.dot.shine` | `rgb(255 255 255 / 0.35)` | Brilho das bolinhas de janela. |
| `ui.dot.glyph-shadow` | `rgb(0 0 0 / 0.35)` | Sombra do × nas bolinhas de janela. |
| `ui.dot.maximize-glyph` | `rgb(0 0 0 / 0.55)` | Símbolo dentro da bolinha de maximizar. |
| `ui.tooltip.surface` | `rgb(15 23 33 / 0.92)` | Dica escura sobre o mapa. |
| `ui.tooltip.surface-label` | `rgb(15 23 33 / 0.9)` | Rótulo de ponto do traçado. |
| `ui.tooltip.surface-live` | `rgb(15 23 33 / 0.82)` | Rótulo de pessoa ao vivo. |
| `ui.tooltip.content` | `#ffffff` | Texto das dicas escuras. |
| `ui.tooltip.content-soft` | `#97a3b1` | Texto secundário das dicas escuras. |
| `ui.tooltip.border` | `rgb(255 255 255 / 0.18)` | Borda das dicas escuras. |
| `ui.photo.nav-bg` | `rgb(15 15 15 / 0.42)` | Setas de anterior/próxima sobre a foto. |
| `ui.photo.nav-bg-hover` | `rgb(15 15 15 / 0.72)` | Setas sobre a foto com o ponteiro em cima. |
| `ui.poster.handle` | `#ffffff` | Alças e contornos de edição da arte. |
| `ui.poster.backdrop` | `#24282c` | Fundo atrás da arte no editor. |
| `ui.poster.panel-shadow` | `rgb(0 0 0 / 0.25)` | Sombra do painel do editor. |
| `ui.poster.selected` | `#fff7ed` | Item escolhido no editor. |
| `ui.poster.selected-border` | `#fdba74` | Borda do item escolhido no editor. |
| `ui.poster.placeholder` | `#fde68a` | Marca de texto a preencher. |
| `ui.poster.ok` | `#15803d` | Passo pronto. |
| `ui.poster.todo` | `#b45309` | Passo pendente. |
| `ui.poster.error` | `#b91c1c` | Erro no editor. |
| `ui.shadow.color-panel` | `rgb(16 24 32 / 0.18)` | Sombra de painéis e modais. |
| `ui.shadow.color-control` | `rgb(16 24 32 / 0.15)` | Sombra de controles. |
| `ui.shadow.color-label` | `rgb(16 24 32 / 0.16)` | Sombra de rótulos sobre o mapa. |
| `ui.shadow.color-tooltip` | `rgb(0 0 0 / 0.5)` | Sombra das dicas escuras. |
| `ui.shadow.color-stage` | `rgb(0 0 0 / 0.55)` | Sombra da arte no editor. |
<!-- /tokens:ui -->

### Mapa
<!-- tokens:map -->
| Token | Valor | Para quê |
|---|---|---|
| `map.route.accent` | `#ff5b3a` | Destaque de rota nos elementos da interface. |
| `map.route.hover-ui` | `#ffd03a` | Rota com o ponteiro em cima, nos elementos da interface. |
| `map.route.casing` | `#1a1a1a` | Contorno escuro das rotas e do traçado. |
| `map.route.line` | `#ffffff` | Linha branca das rotas e do traçado. |
| `map.route.hit` | `#000000` | Faixa de toque invisível sobre a rota. |
| `map.route.hover` | `#ffb547` | Rota com o ponteiro em cima. |
| `map.route.saved` | `#7c3aed` | Rotas salvas no Traçar. |
| `map.route.number` | `#111111` | Número da rota no mapa. |
| `map.route.number-halo` | `#ffffff` | Halo do número da rota. |
| `map.thumb.outline` | `#ffffff` | Contorno na miniatura de rota. |
| `map.thumb.start` | `#2e8b57` | Início do traçado na miniatura. |
| `map.thumb.end` | `#b3431e` | Fim do traçado na miniatura. |
| `map.trace.point` | `#ffffff` | Ponto do traçado. |
| `map.trace.point-border` | `#1a1a1a` | Borda do ponto do traçado. |
| `map.trace.point-halo` | `rgb(255 255 255 / 0.6)` | Halo do ponto do traçado. |
| `map.trace.poi-bg` | `rgb(255 255 255 / 0.92)` | Fundo do ponto de interesse. |
| `map.trace.poi-shadow` | `rgb(0 0 0 / 0.45)` | Sombra do ponto de interesse. |
| `map.marker.outline` | `#ffffff` | Contorno claro de marcadores. |
| `map.marker.outline-stale` | `rgb(255 255 255 / 0.6)` | Contorno de pessoa com localização antiga. |
| `map.marker.shadow` | `rgb(0 0 0 / 0.55)` | Sombra de marcadores. |
| `map.marker.shadow-soft` | `rgb(0 0 0 / 0.5)` | Sombra das bolinhas de foto. |
| `map.marker.shadow-video` | `rgb(0 0 0 / 0.35)` | Sombra extra das bolinhas de vídeo. |
| `map.marker.shadow-me` | `rgb(0 0 0 / 0.6)` | Sombra do marcador da própria pessoa. |
| `map.marker.text-halo` | `rgb(0 0 0 / 0.5)` | Sombra da inicial no marcador. |
| `map.photo.cone` | `#ffffff` | Cone de direção da foto. |
| `map.photo.active` | `#ffd23f` | Anel da foto em destaque. |
| `map.photo.active-glow` | `rgb(255 210 63 / 0.85)` | Brilho da foto em destaque. |
| `map.video.marker` | `#ff5722` | Borda da bolinha de vídeo. |
| `map.video.placeholder` | `rgb(255 87 34 / 0.35)` | Bolinha de vídeo sem miniatura. |
| `map.clip.intro` | `#4caf50` | Marcador do clipe na entrada da animação. |
| `map.live.me` | `#1e88e5` | A própria pessoa na localização ao vivo. |
| `map.line.casing` | `#ffffff` | Contorno branco de linhas sobre o relevo: metrô, ônibus, rotas salvas. |
| `map.rail.unknown` | `#555555` | Linha de trilho sem cor conhecida. |
| `map.rail.interchange` | `#222222` | Anel de estação de integração. |
| `map.rail.station` | `#ffffff` | Miolo da estação. |
| `map.bus.sptrans` | `#16a34a` | Itinerário SPTrans que leva bici. |
| `map.bus.emtu` | `#0e7490` | Itinerário EMTU seletivo. |
| `map.food.marker` | `#d9480f` | Lugar para comer. |
| `map.parking.livre` | `#16a34a` | Estacionamento de bici livre. |
| `map.parking.cadastro` | `#2563eb` | Estacionamento com cadastro. |
| `map.parking.pago` | `#db2777` | Estacionamento pago. |
| `map.parking.clientes` | `#78716c` | Estacionamento só para clientes. |
| `map.parking.closed` | `#dc2626` | Fechado agora. |
| `map.parking.ink` | `#1c1917` | Contorno do ícone de estacionamento. |
| `map.parking.symbol` | `#ffffff` | Símbolo dentro do ícone de estacionamento. |
| `map.road.viario` | `#ffffff` | Camada Viário OSM. |
| `map.water.fill` | `#867627` | Água: rio do interior carregado de sedimento (decisão do coletivo, não azul). |
| `map.water.outline` | `#4a4115` | Contorno sobre a cor de água. |
| `map.hidro.ridge` | `#ef7a30` | Morros e Águas: crista. |
| `map.hidro.river` | `#a6c045` | Morros e Águas: rio e canal. |
| `map.hidro.stream` | `#ddb84f` | Morros e Águas: córrego. |
| `map.hidro.other` | `#888888` | Morros e Águas: demais cursos. |
| `map.cicloinfra.line` | `#00bfa6` | Cicloinfra OSM. |
| `map.compass.north` | `#c0392b` | Ponta norte da bússola. |
| `map.compass.south` | `#999999` | Ponta sul da bússola. |
<!-- /tokens:map -->

### App
<!-- tokens:brand -->
| Token | Valor | Para quê |
|---|---|---|
| `brand.theme` | `#ffffff` | theme-color do index.html e do manifesto. |
| `brand.splash` | `#ffffff` | background_color do manifesto. |
<!-- /tokens:brand -->
