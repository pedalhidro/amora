# Achados da revisão adversarial — `backfill-activities.py` e `ingest-drive.py`

Os dois scripts foram escritos nesta leva e **passaram por revisão adversarial
independente, que achou bugs críticos**. Ambos ficam com `--dry-run` como
default e **NÃO devem rodar com `--apply` contra produção** até os itens
CRÍTICOS abaixo estarem corrigidos.

O resto do sistema de captura (`audit-captura.py`, o Painel, o modelo
`ph:MediaSweep`, `import-activities-censo.py`, `migrate-captura-fixes.py`) foi
verificado e **está em uso** — estes dois é que ficaram para trás.

---

## `backfill-activities.py`

Deriva saída/chegada/movimento/energia da gravação GPS. A ideia está certa e a
heurística foi medida contra os valores humanos; a implementação é que tem
buracos.

### CRÍTICO

1. **Falha de rede num candidato AUMENTA a confiança** e faz gravar o trip
   errado como "alta" (`:717-719`, `:738`). O `continue` num 429/timeout tira o
   candidato da lista, e a detecção de empate usa `len(avaliados)` (os que
   sobreviveram ao fetch) em vez de quantos candidatos existiam. Dois trips
   plausíveis viram um só porque o outro deu timeout.
2. **`confianca == "baixa"` não bloqueia escrita nenhuma**, e a linha
   "REVISÃO HUMANA" é impressa **depois** do POST (`:650-676`). O rótulo de
   confiança é decorativo.
3. **Fallback silencioso pro `tours.ttl` local obsoleto** (`:285-290`,
   `:233-236`): `_baixar` engole qualquer exceção e o script segue lendo o
   disco. Como o local pode estar velho, isso **sobrescreve dado humano** — a
   regra que o script diz respeitar.

### ALTO

4. **Potência ausente é integrada como 0 W** (`:400-401`, `:626`): "sem canal de
   potência" e "pedalando a 0 W" viram a mesma coisa, e a `ph:measuredEnergy`
   sai subestimada **em silêncio**, e é gravada assim mesmo.

### MÉDIO

5. Os números de precisão do docstring são **otimistas por vazamento**: a
   seleção do trip já usa a janela humana, então o `--validar` mede a heurística
   contra dados que ela viu.
6. O resumo "GRAVOU" conta escritas **antes** de o POST acontecer (`:855-857` vs
   `:870-872`) — 30 falhas de rede ainda imprimem sucesso.

### Correção de premissa

7. O docstring afirma que o campo `work` do trip é ∫potência·dt em kJ. **Não é
   bem assim**: `work` só existe na LISTAGEM (`/users/<id>/trips.json`), não no
   detalhe, e diverge >15% do ∫p·dt em 3 dos 91 trips medidos.

### E o mais importante, que a revisão não pegou

O `ph:linkActivity` **já foi importado** (87/109) pelo
`import-activities-censo.py`, direto da planilha do censo, que é fonte curada à
mão. O valor que sobra pro backfill é só o dos campos derivados — e ele mesmo
estima que preencheria **9 das 42** `measuredEnergy` faltantes. Vale mais
consertar o script do que rodá-lo com pressa.

---

## `ingest-drive.py`

Fase 1 da ingestão (os originais com EXIF). O **pHash está correto** — isto foi
verificado de forma independente e é o que mais importava (ver abaixo).

### CONFIRMADO

1. **Foto com GPS = 0/0 vira marcador na Ilha Nula** (`:612-614`): a checagem só
   rejeita ausência (`is None`), nunca o zero. Câmera que grava a tag sem ter
   fix escreve exatamente `0, 0` — e o marcador vai parar no Golfo da Guiné.
2. **`large.jpg` e `thumb.jpg` saem com pixels Display P3 e sem perfil ICC**
   (~90% das fotos): o pHash converte P3→sRGB de propósito (é o que o canvas
   faz), mas o codificador das variantes ignora isso. As cores saem lavadas.
3. **A prova de paridade do pHash não existe como artefato** no repo — o número
   estava só na cabeça do agente. **Isto foi resolvido**: ver
   `scripts/phash-browser.mjs`, que roda o JS verbatim do `upload_images.html`
   no Chromium de verdade e serve de régua.
4. Menor: a dedup mistura os conjuntos de hash de foto e de vídeo (o formulário
   os mantém separados).

### Não é achado (verificado)

- **Não escreve nada no Drive** — 100% somente-leitura, confirmado.
- `--dry-run` é o default de verdade.
- Não baixa os 13 GiB sem avisar.

---

## O pHash: o que a investigação achou (e vale guardar)

Isto contraria a intuição e custou caro pra descobrir, então fica registrado.

**O hash guardado no acervo não é reproduzível — nem pelo próprio navegador.**
Medido em 352 fotos de `web/photos/<hash>/original.*`, onde o nome da pasta é o
hash que o navegador de quem subiu calculou:

| | paridade exata |
|---|---|
| Chromium rodando o JS verbatim do form **vs. o acervo** | **~76%** |
| O port em Python **vs. o acervo** | ~78% |
| **O port em Python vs. o Chromium** | **100%** (Hamming 0, na amostra medida) |

Ou seja: o port está **bit-exato contra o motor de verdade**. Os ~24% que não
batem com o acervo vieram de **outros aparelhos** — rasterização por GPU dá um
hash até 8 bits diferente da rasterização por CPU pra mesma foto.

Dois detalhes que decidem o port, e que qualquer reimplementação futura vai
errar se não souber:

1. **O canvas NÃO faz média de área.** Ao desenhar uma foto de 12 MP num canvas
   32×32, o Skia lê **4 texels** ao redor do ponto amostrado e ignora os outros
   doze milhões de pixels. Parece bug, não é. Por isso `NEAREST` chega mais
   perto do resultado real que `LANCZOS` (32% vs 1%), e média de área dá 1%.
2. **Foto de iPhone é Display P3**, e o navegador converte pra sRGB ao desenhar.
   Sem converter, 28% dos hashes mudam.

**Consequência prática, que vale pro sistema todo:** como o hash é
dependente do aparelho, a dedup **nunca** foi por igualdade — é por
**distância de Hamming ≤ 5** (`PHASH_DUP_THRESHOLD`, `upload_images.html:797`),
tanto contra o lote quanto contra o servidor. É isso que faz o acervo funcionar
apesar da variação. E é isso que torna a ingestão segura: 2 bits de resíduo
cabem sobrando em 5.

Corolário incômodo (pré-existente, não introduzido pela ingestão): como a
distância entre aparelhos chega a 8 bits, **mesmo o navegador de verdade
falharia em deduplicar ~12% das fotos históricas** numa re-subida.
