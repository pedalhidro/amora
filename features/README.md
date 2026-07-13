# Inventário de funcionalidades e comportamentos (Gherkin)

Catálogo verificável do comportamento do amora, em Gherkin (`# language: pt`).
Fonte inicial: `CLAUDE.md` (2026-07). **Ainda não verificado contra o código** —
ver `PLAN.md` para o passe de verificação.

## Convenções

- Um arquivo por fluxo; um comportamento por Cenário.
- Passos descrevem intenção, não mecânica (o POST/seletor fica na implementação).
- Tags de camada: `@backend` `@frontend` `@ops` `@dados`
- Tags de status:
  - `@auto` — automatizável já (pytest-bdd contra o Flask, rdflib/pyshacl)
  - `@manual` — checklist humano por ora (browser, iOS, Capacitor)
  - `@nao-verificado` — cenário escrito a partir da doc, ainda não conferido
    contra o código (removida pelo passe de verificação do PLAN.md)
- Invariantes de DADOS não entram aqui — pertencem ao SHACL
  (`web/data/shapes.ttl`). Aqui ficam só comportamentos (transições de estado,
  fluxos, efeitos colaterais).

## Arquivos

- `upload-midia.feature` — upload unificado de fotos e vídeos, dedup, validação
- `tour-crud.feature` — upsert/patch/delete de passeios, sync do routes.json
- `captura.feature` — passe de coleta (ph:MediaSweep), auditoria dos três
  funis, Painel de Captura, ingestão do acervo. Ver `docs/CAPTURA.md`.
- `exclusao.feature` — purga de mídia/passeios (aritmética de IRIs derivados)
- `iris.feature` — dereferenciamento Linked Data, content negotiation, aliases
- `localizacao-ao-vivo.feature` — transmissão/visualização, retenção, CORS
- `mapa.feature` — camadas, rotas, destaque, animação/clips (frontend)
- `pwa-offline.feature` — service worker, VERSION, ETags/compressão
- `estado-ops.feature` — sync-guard, Object Versioning, workers=1, reload
