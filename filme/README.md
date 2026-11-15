# Filme — retrospectiva do Pedal Hidrográfico

Vídeo de 4 min 07 s que percorre todos os passeios do mais novo ao mais antigo,
montado no CapCut a partir da mídia do amora. Esta pasta guarda as ferramentas
que geram e editam as peças do filme e o diário do que foi feito. A mídia, os
renders e os projetos do CapCut **não** ficam no repositório.

## Estrutura do filme

Tudo anda numa grade de 60 BPM (um tempo = 1 s); os cortes caem em segundo inteiro.

| Trecho | Tempo | O que é |
|---|---|---|
| Mapa de abertura | 0–20 s | relevo 3D de São Paulo; 120 rotas desenhadas, 6 por segundo |
| Passeios | 20–226 s | um mosaico de fotos e vídeos por passeio, do mais novo ao mais antigo, com legenda |
| Mural de artes | 226–236 s | todas as artes de anúncio, andando em 5 deslizes (1, 3, 5, 7, 9 s) |
| Mural de números | 236–246 s | um parágrafo com os totais e uma célula por passeio, em 2 deslizes (4 e 7 s) |
| Logo | 246–247 s | |

Há dois projetos no CapCut: `bicicultura-pedalhidro` (16:9, 1920×1080) e
`bicicultura-pedalhidro-4x5` (retrato, 1080×1350, gerado a partir do primeiro).
A trilha é a mesma nos dois.

## Onde as coisas ficam (fora do repositório)

- **Projetos:** `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`.
- **Mídia de edição:** `~/Downloads/1110-midia/` — cópias locais do que o amora serve
  (fotos originais, vídeos em 360p). O projeto lia de uma montagem WebDAV do bucket e
  travava; `repoint.py` troca os caminhos pelas cópias locais.
- **Originais dos vídeos:** `~/Downloads/1110-midia-original/` (Fotos da Apple e Drive),
  pra trocar no fim, quando a edição estiver fechada.
- **Renders:** `~/Downloads/1110-*.mp4` (mapa, murais). O **prefixo do nome importa**: o
  metrônomo e as trilhas reconhecem `1110-intro`, `1110-mural-10s-60bpm` e `1110-numeros-10s`.
- **Áudio:** `~/Downloads/metronomo-catraca-60bpm-v*.wav` e `~/Downloads/bicicultura-musica*/`.
- **Cópia de trabalho destas ferramentas:** `~/Movies/amora-capcut-tools/`. O repositório mora
  num compartilhamento de rede que cai; por isso as ferramentas rodam de lá e `ferramentas/`
  é um retrato delas (`cp ~/Movies/amora-capcut-tools/*.py filme/ferramentas/`).

## Regras pra mexer num projeto do CapCut por script

O rascunho é um JSON (`draft_info.json`) com quatro cópias que têm de ficar idênticas
(`draft_info.json`, `template-2.tmp` e as duas dentro de `Timelines/<id>/`).

1. **CapCut fechado.** Todo script que grava confere e se recusa a gravar com ele aberto.
2. **Backup antes** (zip da pasta do projeto).
3. **Ensaio antes de gravar:** sem `--apply` nada é escrito.
4. **Conferência embutida:** cada script desfaz a própria mudança em memória e exige que
   sobre exatamente o projeto original — se mexeu em mais alguma coisa, não grava.
5. **Nada é confirmado até o CapCut abrir o projeto.** Não dá pra ver o render dele daqui;
   `capcut_layout.py` desenha um quadro pelo modelo de posicionamento, que foi conferido contra
   uma exportação de verdade (posição, escala, recorte, rotação).

## Ferramentas (`ferramentas/`)

| Script | Pra quê |
|---|---|
| `repoint.py` | aponta a mídia do projeto pras cópias locais |
| `baixa_originais.py` | baixa os vídeos originais (Fotos da Apple, senão Drive); só lê das origens, retomável |
| `labels_apply.py` | cria a legenda dos passeios que ainda não têm, no estilo das existentes |
| `intro_speed.py` | muda a duração do mapa de abertura (velocidade do clipe) e puxa o resto junto |
| `metronomo.py` | metrônomo de catraca em três níveis, lido da linha do tempo |
| `audio_swap.py` | troca um áudio da linha do tempo por outro, mantendo volume e trilha |
| `estende.py` | emenda um render novo no fim de um áudio sem tocar no que já estava mixado |
| `mural.py` / `mural45.py` | mural das artes de anúncio (deitado / retrato) |
| `numeros.py` / `numeros45.py` | mural de números (deitado / retrato) |
| `musica.py` | trilha em camadas, 1ª versão (ré maior, kalimba e sinos) |
| `musica2.py` | versão eletrônica |
| `musica3-claro.py` / `musica3.py` | versões feitas com o som dos próprios vídeos (clara / escura) |
| `musica4.py` | versão seca e mínima: só notas, sem reverberação |
| `capcut_layout.py` | modelo de como o CapCut posiciona os clipes; desenha um quadro |
| `previa45.py` | folha de contato de um projeto, com as legendas |
| `make_4x5.py` | gera o projeto em retrato a partir do deitado |

O renderizador do mapa 3D se perdeu numa reinicialização e está sendo recuperado do
registro da sessão; entra aqui (`mapa3d/`) quando voltar.

## Convenções do filme

- **Metrônomo:** um clique de catraca por segundo. *Forte* quando entra um passeio (ou a tela
  troca inteira) e em cada deslize dos murais; *médio* no tempo antes de um forte; *fraco* no
  resto. No mapa, um clique fraco por rota, com acento (médio) na que cai no segundo inteiro.
- **Trilha:** a estrutura é a mesma em todas as versões — o baixo desce um grau da escala a cada
  trimestre e chega na nota de casa quando entra o mural; a virada de cada ano é contada em
  3, 2, 1 golpes; cada passeio ganha uma nota. Serve pra dar noção de onde o vídeo está e de
  quanto falta.
- **Legendas:** `ph<N>` + nome curto, fonte Minuscule 6. A fonte não tem á/í/ó/ú/ã/õ/ç.
- **Números** (como no censo): intensidade pelas faixas de kJ; tempo coletivo = participantes ×
  tempo total; kJ coletivos = participantes × kJ; gasolina = kJ coletivos ÷ 34.200 kJ/L;
  incidentes = quantas anotações `ph:hadIncident` o passeio tem.
- **Licença:** toda a mídia do amora é CC BY-SA 4.0; o filme sai nos mesmos termos.

## Receitas

```sh
T=~/Movies/amora-capcut-tools
P=~/Movies/CapCut/User\ Data/Projects/com.lveditor.draft/bicicultura-pedalhidro

# metrônomo novo depois de mexer na linha do tempo (freewheel.f32 = o clique, mono 48 kHz float)
python3 $T/metronomo.py freewheel.f32 "$P/draft_info.json" ~/Downloads/metronomo-catraca-60bpm-vN.wav
python3 $T/audio_swap.py "$P" <antigo.wav> <novo.wav> --apply

# legendas dos passeios que faltam
python3 $T/labels_apply.py "$P" --apply

# mural de números (precisa de tours.ttl e images.ttl numa pasta)
python3 $T/numeros.py <pasta> ~/Downloads/1110-numeros-10s-60bpm.mp4

# projeto em retrato (cria) / refazer a linha do tempo dele (apaga edições feitas à mão nele)
python3 $T/make_4x5.py "$P" "$P-4x5" --apply
python3 $T/make_4x5.py "$P" "$P-4x5" --refaz
```

O que foi feito, em ordem, e as decisões: [DIARIO.md](DIARIO.md).
Notas de trabalho pra sessões com o Claude: [CLAUDE.md](CLAUDE.md).
