# Plano: verificação e completude do inventário Gherkin

Objetivo: transformar os `.feature` semeados (escritos a partir do
`CLAUDE.md`, todos marcados `@nao-verificado`) num inventário **conferido
contra o código real** e **completo**, e então bootstrapar a suíte
automatizada. Desenhado pra execução por agentes (Workflow com opus/sonnet),
mas cada fase funciona como tarefa manual também.

## Insumos

- `features/*.feature` (este diretório) — a hipótese
- Código-fonte: `backend/main.py` (~3.3k linhas), `backend/storage.py`,
  `backend/rwgps.py`, `web/app.js` (~12k linhas), `web/upload_images.html`,
  `web/upload_tour.html`, `web/backfill_tours.html`, `web/sw.js`,
  `scripts/*.sh`, `scripts/build-*.py`
- `web/data/shapes.ttl` — pra decidir "isso é SHACL, não Gherkin"

## Fase 1 — Verificar (paralelo por arquivo .feature)

Um agente por `.feature`. Prompt de cada um:

> Leia `features/<X>.feature` e o código que implementa esse fluxo
> (arquivos listados no cabeçalho da tarefa). Para CADA cenário decida:
> **confirmado** (o código faz isso — cite arquivo:linha), **divergente**
> (o comportamento real é outro — descreva o real), ou **não-encontrado**.
> NÃO edite nada; retorne JSON `{scenario, verdict, evidence, correction?}`.

Mapeamento feature → código:

| feature | código principal |
|---|---|
| upload-midia | main.py (upload/validate), upload_images.html |
| tour-crud | main.py (upload-tour, synthesize_tour_patch, rwgps.py) |
| exclusao | main.py (_derived_subjects, _purge_subject, delete-*) |
| iris | main.py (resolvers /terms /pessoas /passeio /serie /midia /listas, SSR) |
| localizacao-ao-vivo | main.py (_live_*), app.js (applyLiveLocation), capacitor/ |
| mapa | app.js (só leitura estática — sem browser nesta fase) |
| pwa-offline | sw.js, main.py (_conditional, flask-compress), index.html |
| estado-ops | scripts/sync-guard.sh, deploy-cloudrun.sh, state-history.sh, storage.py, Dockerfile |

## Fase 2 — Completar (varredura de lacunas, paralelo por fonte)

Agentes varrendo na direção OPOSTA — do código pro inventário:

- um agente sobre `backend/main.py`: liste TODO endpoint/comportamento
  observável e diga qual cenário o cobre; o que sobrar vira cenário novo.
- um agente sobre `web/app.js` (em 3–4 fatias de ~3k linhas): recursos de UI
  com comportamento testável (trace editor, camadas, ajustes, i18n de deep
  link, energia) sem cenário.
- um agente sobre `scripts/` + `Dockerfile` + `.gcloudignore`.

Saída: lista de cenários faltantes, com evidência.

## Fase 3 — Sintetizar (1 agente, barreira)

Com os veredictos das fases 1–2: editar os `.feature` — corrigir divergentes,
adicionar faltantes, remover `@nao-verificado` dos confirmados, mover pro
`shapes.ttl`-território o que for invariante de dados (anotar no README).
Cenários divergentes onde a DOC parecia mais correta que o código →
listar como possíveis bugs em `features/FINDINGS.md` (não "corrigir" o
cenário silenciosamente).

## Fase 4 — Bootstrapar a automação (depois, sessão própria)

- `tests/` com pytest-bdd; `conftest.py` sobe o Flask com
  `STORAGE_BACKEND=local` num tmpdir + catálogos-fixture mínimos.
- Implementar primeiro os steps dos cenários `@auto` de
  `tour-crud` + `exclusao` (maior risco de regressão: patch semantics e
  purga) e depois `upload-midia`, `iris`, `localizacao-ao-vivo`.
- `@manual` vira checklist (o próprio arquivo, filtrado por tag).
- Rodar com `pytest` normal; sem CI por ora (padrão do repo).

## Regras pros agentes

- Idioma dos cenários: português (`# language: pt`); tags e nomes de arquivo
  como estão.
- Comportamento ≠ invariante de dados: se dá pra expressar em SHACL, sai
  do Gherkin.
- Um comportamento por cenário; passos por intenção, não mecânica.
- Nada de tocar em `web/` (não é app servido — sem bump de sw.js) nem nos
  catálogos TTL.
