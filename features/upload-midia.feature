# language: pt
@backend @nao-verificado
Funcionalidade: Upload unificado de mídia (fotos e vídeos)
  upload_images.html aceita image/* e video/* num só picker; o backend
  valida com SHACL e persiste em web/data/images.ttl + blobs.

  Contexto:
    Dado o backend rodando com STORAGE_BACKEND=local

  @auto
  Cenário: Foto válida é aceita e catalogada
    Quando eu envio uma foto com EXIF completo (data, GPS)
    Então a resposta é de sucesso
    E images.ttl ganha um ph:StillImage com IRI med:<phash16>
    E os blobs original/large/thumb existem em photos/<phash>/

  @auto
  Cenário: Vídeo válido é aceito com variantes e áudio
    Quando eu envio um vídeo transcodificado (360p, áudio embutido, thumbnail)
    Então images.ttl ganha um ph:MotionImage com schema:duration e schema:thumbnail

  @auto
  Cenário: Dedup por hash perceptual no servidor
    Dado uma foto já catalogada com phash "abcd1234abcd1234"
    Quando eu envio outra foto com o mesmo phash
    Então o envio é tratado como re-upload (mesmo IRI, sem duplicata)

  @auto
  Cenário: Guarda cross-type de hash
    Dado um vídeo já catalogado com vhash "abcd1234abcd1234"
    Quando eu envio uma FOTO cujo phash é "abcd1234abcd1234"
    Então o upload é rejeitado (os dois virariam o mesmo IRI med:)

  @auto
  Cenário: TTL inválido contra o SHACL é rejeitado
    Quando eu envio uma foto cujo fragmento TTL viola ph:StillImageShape
    Então o upload é rejeitado com o relatório de validação
    E images.ttl não é modificado

  @auto
  Cenário: Validação enxerga instâncias declaradas na ontologia
    Quando eu envio mídia com schema:provider ph:rwgps
    Então a checagem sh:class de Organization passa
    # gotcha: exige merge manual da ontologia, ont_graph do pyshacl não basta

  @frontend @manual
  Cenário: Auto-detecção de passeio na hora do upload
    Dado um passeio com saída dentro da janela −2h/+12h da data da mídia
    Quando eu adiciono o arquivo no formulário
    Então o passeio vem pré-selecionado no card

  @frontend @manual
  Cenário: Data de gravação de vídeo iOS com fuso
    Quando eu adiciono um .MOV com com.apple.quicktime.creationdate
    Então a data usada é a Apple (com TZ), não o mvhd

  @frontend @manual
  Cenário: Card "Apenas áudio"
    Quando eu marco "Apenas áudio" num card de vídeo
    Então o catálogo resultante não tem ph:video360p/ph:video720p
    E o clip participa do loop de áudio mas é pulado pelo ghost-video

  @auto
  Cenário: upload_videos.html redireciona permanentemente
    Quando eu acesso /upload_videos.html
    Então recebo redirect permanente para upload_images.html
