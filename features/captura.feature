# language: pt
@dados @backend
Funcionalidade: Captura de dados e passe de coleta de mídia
  O catálogo registra o que foi capturado de cada passeio nos três funis
  (chamado, censo, mídia) e — o ponto do modelo — distingue "ninguém
  compartilhou nada" de "ninguém foi buscar".

  Contexto:
    Dado o backend rodando com STORAGE_BACKEND=local

  # ── O modelo do passe ──────────────────────────────────────────────────

  @auto
  Cenário: A existência do nó é o marcador do passe
    Dado um passeio sem ph:mediaSweep
    Então o painel mostra o passe como "nunca feito"
    E a auditoria o lista em "passe de coleta nunca feito"

  @auto
  Cenário: Passe feito e vazio é diferente de passe não feito
    Dado um passeio com um ph:MediaSweep de ph:collectedFileCount 0
    Então o painel mostra "∅" (feito, ninguém compartilhou)
    E NÃO mostra "?" (nunca feito)
    E a auditoria não o cobra como pendente

  @auto
  Cenário: O nó do passe é derivado do passeio
    Quando eu gravo um passe de coleta no passeio pas:<slug>
    Então o nó é exatamente pas:<slug>_sweep
    E excluir o passeio purga o passe junto (aritmética de prefixo)

  @auto
  Cenário: O nó do passe não é inferido como ph:Tour
    Dado que o validador roda com inference="rdfs"
    Quando um ph:MediaSweep é validado
    Então ele é tipado ph:MediaSweep e prov:Activity
    E NÃO é tipado ph:Tour
    # Os predicados do passe têm rdfs:domain ph:MediaSweep. Se tivessem
    # domain ph:Tour, a inferência RDFS tiparia o nó do passe como passeio,
    # jogando-o na ph:TourShape (que exige título e data) → Violation.

  @auto
  Cenário: Contribuintes ficam como literal, não como IRI de pessoa
    Quando um passe registra quem compartilhou
    Então cada contribuinte é um ph:sweepContributor com o slug cru
    E o passe é gravado mesmo que nenhum slug resolva pra uma pessoa
    # O slug é o dado bruto e sempre existe; a resolução pra pessoa é um
    # join via schema:alternateName que pode ainda não ter acontecido.

  # ── A auditoria ────────────────────────────────────────────────────────

  @auto
  Cenário: Auditoria cruza as três fontes
    Quando eu rodo scripts/audit-captura.py
    Então ela reporta, por passeio, o funil ANTES (do tours.ttl)
    E o funil DEPOIS (do tours.ttl)
    E a mídia do amora (do images.ttl)
    E o passe de coleta (do tours.ttl)

  @auto
  Cenário: --sync grava pelo backend, nunca no arquivo
    Quando eu rodo audit-captura.py --sync
    Então cada passe entra por POST /upload-tour com mode=patch
    E nenhum arquivo de web/data/ é escrito pelo script
    E os predicados que o script não conhece sobrevivem ao patch

  @auto
  Cenário: --dry-run não envia nada
    Quando eu rodo audit-captura.py --sync --dry-run
    Então o script mostra o que gravaria
    E nenhum POST é feito

  @manual
  Cenário: O acervo do Drive é lido só em metadados
    Quando a auditoria varre a Biblioteca Hidrográfica
    Então ela usa apenas scandir/stat (nome, tamanho, mtime)
    E NUNCA abre o conteúdo de um arquivo
    E nada é escrito, movido ou apagado no Drive
    # Os arquivos são stubs do Google Drive: abrir um força o download.
    # Ler os 8 mil puxaria ~13 GiB pela rede.

  @auto
  Cenário: A pasta de mídia tem mais de um nome no acervo
    Dado que o acervo usa "midia", "midia zap", "midias", "Midia Danilo" e "fotos"
    Quando a auditoria varre uma pasta de passeio
    Então ela reconhece todas essas variações
    E reporta qualquer imagem achada FORA de uma pasta reconhecida
    # Fixar a string "midia" perdia 9 passeios e ~430 arquivos, calado.

  # ── O painel ───────────────────────────────────────────────────────────

  @manual
  Cenário: Cada lacuna leva à ferramenta que a preenche
    Dado o Painel de Captura aberto
    Quando eu clico num campo vermelho do funil ANTES
    Então vou pro upload_tour.html daquele passeio
    Quando eu clico num campo vermelho de saída/chegada/energia
    Então vou pro backfill_tours.html

  @auto
  Cenário: Arte apontando pra host local conta como lacuna
    Dado um passeio com schema:image em http://localhost:8080/...
    Então o painel mostra a arte como AUSENTE
    E o aviso explica que a IRI não resolve fora da máquina de quem subiu
    # A arte existe, mas aponta pra lugar nenhum — confundir isso com "nunca
    # preencheu" faria alguém procurar uma arte que já foi feita.

  @auto
  Cenário: O badge da aba ignora a gravação GPS
    Dado que ph:linkActivity falta em TODOS os passeios
    Então o badge de pendências não conta essa lacuna
    E a gravação GPS aparece como métrica própria em destaque
    # Um badge que sinaliza 109 de 109 não sinaliza nada.

  # ── Sync de rota (efeito colateral do patch) ───────────────────────────

  @auto
  Cenário: Patch que não mexe na rota não rebusca a geometria
    Dado um passeio cuja rota já tem geometria no routes.json
    Quando eu faço um patch de qualquer outro predicado
    Então o backend REUSA a geometria em cache
    E não faz nenhuma chamada ao RideWithGPS
    E não reescreve o routes.json
    # Sem isso, os 87 passes em lote viravam 87 fetches de GPX + 87 rewrites
    # de um JSON de 2 MB — e, com Object Versioning, 87 gerações noncurrent
    # paradas no bucket por 90 dias.

  @auto
  Cenário: Rota trocada rebusca a geometria
    Dado um passeio com ph:linkRoute apontando pra outra rota
    Quando o patch é salvo
    Então o backend busca a geometria nova no RideWithGPS

  # ── Ingestão do acervo ─────────────────────────────────────────────────

  @auto
  Cenário: Só entra no mapa o que tem GPS de verdade
    Dado um arquivo do acervo vindo do WhatsApp (EXIF removido)
    Quando ele é ingerido
    Então ele NÃO recebe o mixin ph:GeoreferencedImage
    E NÃO vira marcador no mapa
    E nenhuma coordenada é inventada pra ele

  @auto
  Cenário: pHash do script bate com o pHash do navegador
    Dado uma mídia já em images.ttl com o blob original em web/photos/
    Quando o script recalcula o pHash em Python
    Então ele é idêntico ao hash que está na IRI med:<phash16>
    # O pHash É a identidade da mídia. Um bit de diferença cria um IRI novo
    # pra mesma foto e mata a deduplicação do acervo inteiro.
