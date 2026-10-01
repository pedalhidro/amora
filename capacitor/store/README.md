# Lojas — kit da distribuição para testers

Tudo o que o **TestFlight (iOS, teste externo)** e o **teste fechado do Google
Play** pedem, campo a campo, pronto pra colar. Os textos de loja são em pt-BR
(o app é em português); as notas pra revisão da Apple vão em inglês.

Contas: o coletivo não tem CNPJ, então as duas são **pessoais**, no nome de
quem publica — na App Store o "vendedor" aparece com o nome civil; no Play dá
pra escolher o nome de desenvolvedor exibido ("Pedal Hidrográfico"), mas a
identidade é verificada. Conta pessoal nova do Play **precisa** de um teste
fechado com **≥ 12 testers inscritos por 14 dias seguidos** antes de poder ir
pra produção — é exatamente este kit.

## Pendências (só a pessoa responsável resolve)

- [x] **E-mail de contato** público (lojas + política de privacidade):
      `contato@abiru.to`.
- [x] **Pessoa responsável** pelos dados (LGPD): Danilo Lessa Bernardineli.
- [ ] **Telefone** pra revisão da Apple (não é público).
- [x] `web/privacidade.html` no ar (v423):
      `https://amora.pedalhidrografi.co/privacidade.html`.
- [ ] Contas: Play Console (US$ 25, uma vez) — em verificação desde
      01/10/2026; Apple Developer (US$ 99/ano) — a criar.
- [ ] Chave de assinatura do Android (upload key) — gerar UMA vez e guardar com
      backup; perder a chave = não conseguir mais atualizar o app (o Play App
      Signing permite trocar a de upload, com pedido ao suporte).

## Textos comuns

| Campo | Texto | Limite |
|---|---|---|
| Nome do app | `Amora — Pedal Hidrográfico` | 30 |
| Subtítulo (iOS) | `Pedais seguindo as águas de SP` | 30 |
| Descrição curta (Play) | `Mapa dos passeios do Pedal Hidrográfico: águas escondidas, fotos e traçados.` | 80 |
| Palavras-chave (iOS) | `bicicleta,ciclismo,pedal,são paulo,rios,córregos,hidrografia,relevo,mapa,gpx,rota,coletivo` | 100 |
| Categoria | Play: **Mapas e navegação** · iOS: **Navegação** (secundária: Esportes) | |
| Site | `https://amora.pedalhidrografi.co/` | |
| URL de suporte | `https://github.com/pedalhidro/amora/issues` | |
| Política de privacidade | `https://amora.pedalhidrografi.co/privacidade.html` | |
| E-mail de contato | `contato@abiru.to` | |

### Descrição completa (Play ≤ 4000 · App Store ≤ 4000)

```
O amora é o mapa do Pedal Hidrográfico, coletivo de ciclismo urbano que planeja seus passeios seguindo as águas de São Paulo — os rios e córregos que a cidade canalizou e cobriu, e o relevo que eles desenharam.

NO MAPA
• As rotas de todos os passeios do coletivo, com data, narrativa, energia estimada e fotos.
• Fotos e vídeos dos pedais no lugar onde foram feitos.
• Camadas de hidrografia, relevo, a enchente de 1929, metrô e trens, ciclovias e infraestrutura.
• A Memória Hidrográfica, com a história de cada passeio.

PARA PEDALAR
• Editor de traçado: desenhe uma rota, veja o perfil de relevo e a energia (kJ) que ela pede, e exporte em GPX.
• Localização ao vivo (opcional): durante o passeio, quem está pedalando se vê no mapa — no app, mesmo com a tela apagada.

PARA O ACERVO
• Envie fotos e vídeos direto da galeria; data, lugar e passeio saem do próprio arquivo.
• No app, o envio continua em segundo plano: dá pra apagar a tela ou ficar sem sinal no meio, que ele termina sozinho.
• Tudo o que é enviado vira acervo público e aberto (licença CC BY-SA 4.0).

O amora é software livre (GNU AGPL v3.0), feito por voluntários do coletivo: github.com/pedalhidro/amora. Não tem conta, anúncio nem rastreador.
```

## Google Play — teste fechado

Play Console → criar app (idioma padrão **Português (Brasil)**, app, gratuito).

**Painel → Configurar o app** (todos obrigatórios antes do 1º envio pra teste):

- **Acesso ao app:** todas as funções disponíveis sem acesso especial.
- **Anúncios:** não contém anúncios.
- **Classificação do conteúdo** (questionário IARC, categoria "Todos os outros
  tipos de app"): violência, sexo, linguagem, drogas, apostas → **não**.
  Interação: **os usuários podem interagir ou trocar conteúdo → sim** (fotos e
  vídeos públicos); **compartilha a localização atual com outros usuários →
  sim** (localização ao vivo); compras digitais → não. Resultado esperado:
  Livre, com os avisos "Interação entre usuários" e "Compartilha localização".
- **Público-alvo:** **18 anos ou mais** (evita as exigências da política de
  famílias; o app não é feito pra crianças).
- **App de notícias:** não. **App governamental:** não. **Serviços
  financeiros / saúde:** não.
- **Segurança dos dados** — ver a seção abaixo.
- **Permissões de serviço em primeiro plano** — ver abaixo.

**Detalhes da página (Presença na loja → Página principal):** nome, descrição
curta e completa (acima), ícone `icon-512.png`, gráfico de destaque
`feature-graphic.png`, capturas `screenshots/android-*.jpg` (mín. 2; ordem = número do arquivo), e-mail
de contato, site e política de privacidade.

**Testers:** Testes → Teste fechado → criar faixa → lista de e-mails (ou um
Grupo do Google, ex.: `amora-testers@googlegroups.com`) → enviar o AAB
assinado → mandar o **link de inscrição** pro grupo do coletivo. Contam só
quem abre o link e aceita. **12 inscritos por 14 dias seguidos** → aí aparece
"Solicitar acesso à produção".

### Segurança dos dados (Data safety)

Coleta ou compartilha algum dos tipos obrigatórios? **Sim.** Criptografados em
trânsito? **Sim** (HTTPS). Os usuários podem pedir exclusão? **Sim** (pelo
e-mail de contato; cada imagem também pode ser excluída no próprio app).

| Tipo de dado | Coletado | Compartilhado | Opcional? | Finalidade |
|---|---|---|---|---|
| Localização → **exata** | sim | não¹ | sim | Funcionalidade do app (localização ao vivo; local das fotos) |
| Fotos e vídeos → **fotos**, **vídeos** | sim | não¹ | sim | Funcionalidade do app (acervo) |
| Informações pessoais → **nome** | sim | não¹ | sim | Funcionalidade do app (autoria, apelido ao vivo) |
| IDs de dispositivo ou outros | sim² | não | sim | Funcionalidade do app (localização ao vivo) |

¹ O conteúdo fica **público** por escolha explícita de quem envia — o Play não
conta isso como "compartilhamento com terceiros". ² Um identificador aleatório
gerado pelo app ao ligar a localização ao vivo (não é o ID do aparelho).
Nada é usado pra publicidade, análise ou personalização.

### Permissões de serviço em primeiro plano

Para cada tipo, descrição + **link de vídeo** (YouTube não listado serve)
mostrando o uso:

- **`location`** — *Compartilhamento de localização ao vivo iniciado pela
  pessoa durante passeios em grupo. Ela liga explicitamente (Camadas → Pessoas
  ao vivo → 📍), vê uma notificação permanente enquanto transmite e desliga
  quando quiser. Sem o serviço, a posição para de ser enviada quando a tela
  apaga — e o grupo perde quem está no pedal.* Vídeo: ligar a transmissão,
  bloquear a tela, mostrar a notificação, desligar.
- **`dataSync`** — *Envio de fotos e vídeos escolhidos pela pessoa para o
  acervo do coletivo. O envio, iniciado por ela, continua em segundo plano com
  notificação de progresso, para não se perder quando a tela apaga ou o sinal
  cai.* Vídeo: 📤 enviar imgs → escolher → bloquear a tela → notificação de
  progresso → "arquivo enviado".

(Não há `ACCESS_BACKGROUND_LOCATION` no app — o formulário de localização em
segundo plano **não** se aplica. Nem permissão de fotos: a galeria é o seletor
de documentos do sistema.)

## TestFlight — teste externo

App Store Connect → Apps → novo app (iOS, nome, idioma principal Português
(Brasil), bundle ID `co.pedalhidrografi.amora`, SKU `amora`).

**TestFlight → Informações de teste:**

- **Descrição do beta:**
  ```
  Versão de teste do amora, o mapa do Pedal Hidrográfico — coletivo de ciclismo urbano de São Paulo que pedala seguindo os rios e córregos escondidos da cidade. Nesta fase, testamos principalmente o envio de fotos e vídeos pelo app e a localização ao vivo com a tela apagada.
  ```
- **E-mail para feedback:** `contato@abiru.to`
- **URL de marketing:** `https://amora.pedalhidrografi.co/` · **Política de
  privacidade:** `https://amora.pedalhidrografi.co/privacidade.html`
- **O que testar** (por build):
  ```
  1. 📤 enviar imgs → Escolher imagens: escolha fotos E vídeos da galeria. Eles sobem sozinhos; confira no mapa se apareceram no lugar certo.
  2. No meio de um envio, bloqueie a tela, troque de app ou ligue o modo avião e volte: o envio tem que terminar sozinho.
  3. Camadas → Pessoas ao vivo → 📍: ligue a transmissão, bloqueie a tela por alguns minutos e veja, em outro aparelho, se você continua aparecendo.
  Atenção: o que você envia entra no acervo público de verdade do coletivo. Use imagens que você topa publicar — ou exclua depois com 🗑.
  ```
- **Grupo externo** com **link público** (até 10.000 pessoas) — o 1º build de
  cada versão passa pela Beta App Review (~1 dia).

**Informações para a revisão (Beta App Review)** — contato: nome, e-mail,
telefone; login: **não necessário**. Notas:

```
Amora is the map app of Pedal Hidrográfico, a volunteer cycling collective in São Paulo, Brazil. The interface is in Portuguese. No sign-in is needed: every feature works without an account.

What the app adds over the website:
1. Live location during group rides — off by default. To try it: tap "camadas", enable "Pessoas ao vivo", tap the 📍 on that row, type a nickname and allow location. It uses background location (UIBackgroundModes: location) so riders keep appearing on the shared map with the screen locked; it stops when the user turns it off. Positions are kept only in server memory and deleted after the retention the user picks (3 h by default, 24 h at most).
2. Native photo/video picker and background upload — tap "enviar imgs", then "Escolher imagens". The system photo picker is used without photo-library permission; uploads continue in a background URLSession if the app is closed.
3. An offline page and a cached copy of the map.

User-generated content: uploaded photos and videos join the collective's public archive (CC BY-SA 4.0). Any item can be deleted from its popup (🗑), and removal can be requested at contato@abiru.to. Privacy policy: https://amora.pedalhidrografi.co/privacidade.html
```

**Para a App Store (depois do beta):** capturas de iPhone 6,9" (1320×2868) e,
se o app continuar universal, de iPad 13"; questionário de Privacidade do App
(mesmo conteúdo da tabela de Segurança dos dados: localização exata, fotos/
vídeos, nome, identificador — tudo "não vinculado a identidade" e "sem
rastreamento"); classificação etária 4+ com "conteúdo gerado por usuários" e
"compartilhamento de localização" sinalizados. **Atenção à diretriz 1.2
(conteúdo gerado por usuários):** a App Store exige um jeito de **denunciar**
conteúdo e de **bloquear** quem abusa, além do contato publicado. O amora hoje
não tem denúncia nem login — o TestFlight tolera; a App Store provavelmente
não. Resolver antes de enviar pra produção.

## Imagens

| Arquivo | Uso | Medidas |
|---|---|---|
| `icon-512.png` | Ícone do Play | 512×512, PNG 32 bits |
| `feature-graphic.png` | Gráfico de destaque do Play | 1024×500, sem transparência |
| `screenshots/android-*.jpg` | Capturas do Play (telefone): mapa, passeio, traçado, galeria, camadas | 1080×1920 (9:16) |

O ícone do iOS sai do `assets/icon.png` (1024×1024) via `npm run icons` — o
TestFlight não pede capturas.

As capturas são do app de verdade apontado pra produção (emulador Android 15
com a tela em 1080×1920 — o Play recusa proporção acima de 2:1, e a padrão
1080×2400 passa — e a barra de status em modo demo). Mostram fotos do acervo
com gente do coletivo: são públicas (CC BY-SA), mas vale conferir se ninguém
se opõe a aparecer na loja. Pra refazer: ver `docs/PLAN-native-upload.md`
(emulador + CDP no WebView).
