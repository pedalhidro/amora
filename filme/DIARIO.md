# Diário do filme

Registro do que foi feito e decidido, em ordem. Datas de 2026.

## 13/11

- **Som nivelado:** volume ajustado em 48 clipes; a diferença entre grupos caiu de ~42 dB pra ~11 dB.
- **Grade de 60 BPM:** todos os cortes levados pra segundo inteiro; o mapa de abertura desenha
  6 rotas por segundo (120 em 20 s).
- **Metrônomo de catraca:** um único clique tirado de uma gravação de roda livre
  (`74792__timkahn__bike_freewheel`, do Freesound), escolhido por ser o mais limpo.
- **Mural de artes** refeito em 10 s com os deslizes nos tempos.
- **Título removido** do mapa de abertura.
- **Flashes de rota** (a rota de cada passeio por 0,5 s a 70 % quando ele entra) — feitos e
  depois **retirados** do projeto por quem edita.

## 14/11

- **Reinicialização do Mac apagou a pasta temporária** com os scripts e os caches. Daí em
  diante as ferramentas moram em `~/Movies/amora-capcut-tools/`. Ficou perdido o renderizador
  do mapa 3D (em recuperação a partir do registro da sessão).
- **Mídia local:** o projeto lia de uma montagem WebDAV do bucket e travava. A mídia usada foi
  copiada pra `~/Downloads/1110-midia/` e os caminhos trocados (`repoint.py`), em três rodadas.
  Ler pela montagem do macOS chegou a devolver arquivos de tamanho errado; a cópia passou a
  buscar direto do servidor local.
- **Legendas:** criadas pra todos os passeios que não tinham (31, depois mais 44). O texto é um
  resumo do título do passeio — falta revisão de quem edita.
- **Mapa de abertura:** testado em 12 s (10 rotas/s) e **voltou pra 20 s** — rápido demais no som.
- **Regras do metrônomo** (decisão de quem edita): forte em toda transição, médio no tempo
  anterior, forte nos deslizes do mural, fraco por rota no mapa com acento no segundo inteiro.
- **Trilha em camadas.** Objetivo: dar a quem ouve noção de continuidade e de quanto falta.
  Quatro níveis: seção, ano, trimestre, passeio. Versões, na ordem, e o que se achou delas:
  1. ré maior, kalimba, sinos, gotas — cumpre a função, mas "fofa/relaxante demais";
  2. eletrônica — distrai demais e soa otimista; descartada como direção;
  3. com o som dos próprios vídeos (trem, córregos, vento, ato) — ainda "clara, otimista,
     transcendental"; a versão escura continua "espacial";
  4. seca e mínima: só notas com começo e fim.
  O tom pedido: **neutro e contemplativo**, nem otimista nem pessimista, com estrutura — mas
  não mais estrutura do que precisa. A mixagem final foi feita no CapCut com as várias faixas.
- **Mural de números** (10 s): parágrafo com os totais + uma célula por passeio, em IBM Plex
  Mono, só texto, em dois deslizes. O texto original citava "CC BY-ND-SA 4.0", que não existe;
  ficou CC BY-SA 4.0, que é a licença de toda a mídia do catálogo. Os dois passeios Pedalula
  (2.000 e 500 participantes) respondem por mais da metade das presenças somadas.
- **Trilha estendida pra 247 s** (mural de números + logo) sem tocar no que já estava mixado:
  cada faixa fica idêntica até 225 s e ganha só o final novo (`estende.py`).
- **Originais dos vídeos:** 226 de 234 baixados (112 das Fotos da Apple, quase todos 4K; 6
  arquivos de câmera e 108 cópias de WhatsApp do Drive; 8 sem origem conhecida). As fotos do
  projeto já são os originais. A troca no projeto fica pro fim da edição.
- **Projeto em retrato (4:5)**, gerado por `make_4x5.py`:
  - cada cena vira um mosaico de fileiras justificadas, sem sobreposição;
  - quando um passeio entra ou sai no meio da cena, os clipes são cortados ali e a tela é
    re-ladrilhada (no tempo forte);
  - legendas centralizadas no pé do bloco de cada passeio;
  - mural de artes e mural de números refeitos em retrato, nos mesmos tempos;
  - mapa de abertura: primeiro uma composição com dois mapas (geral + detalhe) — **recusada**;
    ficou, de quebra-galho, o render 16:9 recortado no centro. Falta o render de verdade em
    retrato, com a câmera repensada (girar o mapa, se precisar).

## 14/11, noite, e 15/11

- **Vídeos em qualidade original no projeto 16:9 e no retrato** (`troca_originais.py`): só troca o
  clipe que confere em duração, proporção e no próprio quadro. Ficaram como estavam os sem
  original e um clipe cujo corte passa do fim do original. Os originais ganharam um nome com o
  prefixo do passeio, porque as outras ferramentas leem o passeio do nome do arquivo.
- **"Mídia não suportada" no CapCut:** eram dois vídeos 720p em WebM do amora; convertidos pra MP4.
- **Espaços em branco no 16:9** (`preenche.py`): cada clipe cresce só na direção do vazio vizinho,
  sem refazer a composição feita à mão. A tela em branco caiu de 0,9 % pra 0 % na média.
- **Bordas suaves** (`mascaras.py`): máscara retangular em todos os clipes dos dois projetos, com os
  valores de uma máscara-modelo feita à mão no CapCut; o desfoque foi depois cortado pela metade
  (0,05). Os seis clipes compostos ficaram sem.
- **Renderizador do mapa 3D recuperado** do registro da sessão; reproduz o quadro do vídeo original.
- **Mapa de abertura em retrato**, decidido em várias voltas: um mapa só (a composição com dois
  foi recusada); câmera olhando pra 285° (entre o norte-em-cima e o oeste-em-cima), inclinação de
  35°, zoom de 1,25×, a Cratera de Colônia quase na borda esquerda; a imagem esticada na vertical
  (corta em cima e embaixo) e 5 % mais chão à direita. Só o mapa colorido aparece: além da
  cobertura dele a cor é calculada da altitude e da declividade, pela regra aprendida onde ele
  existe.
- **Projeto em retrato editado à mão** por quem edita (uma cena 2 s mais curta). Ganhou trilha
  própria: as mixagens com os mesmos 2 s retirados e o metrônomo refeito.
- **Mural de artes e mural de números em 3 colunas no retrato.** Com menos colunas o conteúdo fica
  mais comprido; pra nada ser pulado o mural de artes dá um passo a cada meio segundo (19) e o de
  números um por segundo (6). O metrônomo e as trilhas marcam os passos que caem no segundo inteiro.
- **Arquivo:** tudo o que não é do repositório foi pra `~/Movies/2026-bicicultura/video-pedalhidro/`
  e os dois projetos passaram a ler de lá.
- **No filme:** 494 mídias distintas (257 fotos e 237 vídeos) de 104 passeios.

## Em aberto

- Rever o texto das legendas geradas.
- Decidir se o parágrafo do mural de números conta os dois Pedalula.
- Máscara nos seis clipes compostos (153–156 s e 166–169 s no 16:9).
- Três fotos do projeto em retrato ainda são lidas da montagem do amora (`~/AmoraPhotos`).
