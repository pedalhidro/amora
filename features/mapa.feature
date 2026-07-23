# language: pt
@frontend @manual @nao-verificado
Funcionalidade: Mapa, camadas, rotas e animação
  app.js carrega data_graphs.ttl → segue os void:dataDump → renderiza
  marcadores Leaflet por ph:Image/ph:MotionImage e as rotas de routes.json.

  Cenário: Mídia vira marcador no mapa
    Quando o app carrega os catálogos
    Então cada mídia com GPS vira um marcador (vídeos com borda .photo-dot-video)
    E marcadores densos são relaxados pelo clustering

  Cenário: Painel de camadas persiste estado
    Quando eu mudo visibilidade/opacidade/ordem de camadas e recarrego
    Então o estado volta como estava (localStorage)

  Cenário: Destacar rota
    Quando eu clico ★ no modal de uma rota
    Então uma cópia ~1.5× mais grossa aparece
    E a camada "Rota destacada" se materializa (🗑 limpa e a esconde)

  Cenário: Fontes de dados em Configurações
    Quando eu troco entre Servidor / CDN / Local (kit ZIP)
    Então o app resolve os catálogos e imagens da fonte escolhida
    E o valor legado 'pi' é migrado pra 'server' no load

  Cenário: Animação (ghost-video)
    Quando eu ligo Animação
    Então clips tocam em ordem aleatória com o handoff de 5 estados no marcador
    E clips audioOnly são pulados pelo player mas entram no loop de áudio

  Cenário: Deep link abre o modal do passeio
    Quando eu abro /?tour=<slug>
    Então o modal da rota abre e o <article> SSR é removido do DOM

  Cenário: Editor de traçado — biblioteca de rotas salvas
    Quando eu salvo um traçado (POST /save-route) e clico 📂 Carregar
    Então a lista vem mais novas primeiro e o estado completo restaura
