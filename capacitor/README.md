# Amora — shell nativo (Capacitor)

Empacota o **mesmo** app web (`web/`) num app nativo iOS/Android cujo único
ganho sobre o PWA é **localização em segundo plano**: a *Localização ao vivo*
continua transmitindo com a tela apagada / app em segundo plano — o cenário que
nenhum navegador cobre (no iOS o `watchPosition` é suspenso segundos após o
bloqueio; no Android a página é congelada).

> O app web segue 100% utilizável no navegador. Este shell é um empacotamento
> adicional, não um substituto. Só instale-o quem precisa transmitir com a tela
> apagada.

## Como funciona

- **Carrega o site remoto.** `capacitor.config.json` aponta `server.url` para
  `https://amora.pedalhidrografi.co`. A WebView carrega o app publicado, então
  `location.origin` continua sendo `amora` — todas as URLs relativas e os
  endpoints `/live-*` funcionam **sem CORS e sem refatorar nada**.
  Atualizações do site chegam ao app sem rebuild nativo.
- **Service worker só com App-Bound Domains (iOS).** A WKWebView de um app
  comum vem com o service worker DESLIGADO; o WebKit só o liga quando a
  WebView limita a navegação aos *App-Bound Domains* do app. Por isso a config
  traz `ios.limitsNavigationsToAppBoundDomains: true` e o `run-ios.sh` põe o
  `WKAppBoundDomains` no Info.plist (ver "Config nativa"). Com isso o shell
  ganha o mesmo SW do PWA: shell em cache (abre sem sinal depois da primeira
  visita) e o cache de blocos dos FlatGeobuf (sem ele, cada pan no viário /
  Morros e Águas rebaixa as mesmas faixas pelo 4G). No Android o SW funciona
  direto.
- **Sem rede, uma tela local.** `server.errorPath` aponta para
  `www/index.html`, que vai empacotada no app: se a navegação principal falha
  (abrir sem sinal antes de o SW ter o shell, a WebView recarregada pelo
  sistema sem rede), aparece "Sem conexão com o Amora" com **Tentar de novo**
  — e a própria página volta pro mapa sozinha quando alcança o servidor. Antes
  disso era tela em branco.
- **A ponte de background vive em `web/app.js`.** As funções
  `startNativeBackgroundWatch()` / `stopNativeBackgroundWatch()` acessam o
  plugin pelo global injetado `window.Capacitor.Plugins.BackgroundGeolocation`
  (sem `import`), guardadas por `liveIsNative()`. Como já fazem parte do site,
  rodam inalteradas: no shell, o watcher de background dirige o envio (chama
  `window.phidroLivePush` a cada fix, inclusive com a tela apagada); num
  navegador comum o plugin não existe e caímos no `watchPosition`. O projeto
  nativo só precisa **registrar o plugin** — nenhum código JS extra aqui.
- **Envio de fotos e vídeos em segundo plano (Android; iOS planejado).** O
  plugin local `plugins/amora-upload/` (dependência `file:` no
  `package.json`, entra no `npx cap sync` como qualquer plugin) dá ao
  `/subir` uma galeria nativa — no Android, o seletor de DOCUMENTOS do
  sistema, que entrega o original COM o GPS (o Photo Picker zera; medido) — e
  uma fila de envio do sistema (WorkManager + notificação de progresso) que segue com a tela apagada, o app fechado e a
  rede caindo. O lado web está em `web/subir.html` (seção "Shell nativo") e só
  liga quando `AmoraUpload.info()` responde: navegador e app antigo seguem no
  caminho de sempre. Contrato, decisões e o que falta testar em aparelho:
  `docs/PLAN-native-upload.md`. Permissões (mescladas pelo Gradle a partir do
  manifesto do plugin — nada a colar no `android/`): só
  `POST_NOTIFICATIONS` (pedida no primeiro "Escolher imagens") e
  `FOREGROUND_SERVICE_DATA_SYNC` — nenhuma permissão de mídia.

## Pré-requisitos

- Node ≥ 18 (`@capacitor/cli`).
- **iOS:** macOS + Xcode + CocoaPods (`sudo gem install cocoapods` — o
  `npx cap sync ios` roda `pod install`) + uma conta Apple Developer
  (US$ 99/ano) para distribuir. Simulador não dá GPS de verdade — teste em
  device físico.
- **Android:** Android Studio + SDK; conta Google Play Developer (US$ 25, único)
  para publicar.

## Setup (uma vez)

```sh
cd capacitor
npm install
npx cap add ios
npx cap add android
./run-ios.sh --prepare   # cap sync ios + as chaves do Info.plist
npx cap sync android
```

`cap add` gera os projetos `ios/` e `android/` (gitignorados — recriáveis).
`cap sync` instala os plugins nativos e copia a config e o `www/` (a tela sem
conexão). O `www/` é versionado — é o `webDir` e guarda só essa tela.

> Versões em `package.json` são um ponto de partida. Se o `npm install` reclamar
> de incompatibilidade, alinhe tudo na mesma major: `npm install @capacitor/core@latest
> @capacitor/cli@latest @capacitor/ios@latest @capacitor/android@latest
> @capacitor-community/background-geolocation@latest` e rode `npx cap sync`.
> As chaves da config abaixo foram conferidas no código do Capacitor 6.2.

### Ícones e splash

As artes-fonte ficam versionadas em `assets/`: `icon.png` (1024×1024) e
`splash.png` (2732×2732, ícone centralizado no fundo escuro `#0f1721`). O
splash é escuro por identidade visual, mas **o app é claro** (barra branca):
a WebView tem fundo branco (`ios.backgroundColor`) e a barra de status usa
ícones escuros (`UIStatusBarStyleDarkContent`) — no instante do splash eles
somem no fundo escuro, e é só isso. `splash-dark.png` hoje é idêntico ao
`splash.png`; só vale mantê-lo se um dia for genuinamente distinto. Gere os
ícones e telas nativos com:

```sh
npm run icons   # capacitor-assets generate
```

Rode depois do `npx cap add` (e sempre que trocar as artes), seguido de
`npx cap sync`. Trocar o ícone/splash exige rebuild nativo — não basta
republicar o `web/`.

## Config nativa obrigatória

### iOS — `ios/App/App/Info.plist`

**O `run-ios.sh` aplica tudo isto sozinho a cada execução** (`plutil -replace`,
idempotente): o `ios/` é gerado e o template do Capacitor não traz NENHUMA
destas chaves, então todo `npx cap add ios` as perde. Pelo Xcode, rode
`./run-ios.sh --prepare` antes do `npx cap open ios`. Os textos moram no
`run-ios.sh` — mude lá e aqui juntos.

```xml
<!-- Localização ao vivo (plugin background-geolocation) -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>Mostra sua posição no mapa e a compartilha ao vivo enquanto você usa o app.</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Mantém o compartilhamento da sua localização ao vivo durante o pedal, mesmo com a tela apagada. Você liga e desliga quando quiser.</string>
<key>UIBackgroundModes</key>
<array>
  <string>location</string>
</array>

<!-- Câmera/microfone do seletor de arquivos e gravação nas Fotos -->
<key>NSCameraUsageDescription</key>
<string>Tira fotos e grava vídeos na hora, quando você escolhe a câmera para enviar imagens ao acervo do pedal.</string>
<key>NSMicrophoneUsageDescription</key>
<string>Grava o som dos vídeos que você filma pela câmera do app para enviar ao acervo do pedal.</string>
<key>NSPhotoLibraryAddUsageDescription</key>
<string>Salva nas suas Fotos as imagens que você pedir para guardar, como a colagem do álbum.</string>

<!-- Ícones escuros na barra de status (a barra do app é branca) -->
<key>UIStatusBarStyle</key>
<string>UIStatusBarStyleDarkContent</string>

<!-- Service worker na WKWebView — só junto com ios.limitsNavigationsToAppBoundDomains -->
<key>WKAppBoundDomains</key>
<array>
  <string>amora.pedalhidrografi.co</string>
  <string>localhost</string>
</array>
```

- **Câmera, microfone e Fotos não são opcionais.** Sem a descrição de uso, o
  iOS **encerra o app** no instante em que o recurso é pedido — perdendo o
  envio em andamento e a transmissão ao vivo. Todo `<input type=file>` que
  aceita imagem (📤 enviar imgs, formulários, arte do passeio, até o seletor de
  DEM — `.tif` é imagem pro iOS) ganha "Tirar Foto" no menu do WebKit, e os de
  vídeo, "Gravar Vídeo" (microfone). "Salvar nas Fotos" (toque longo numa
  imagem) e "Salvar Imagem" (folha de compartilhar da colagem do `/subir`)
  gravam nas Fotos. Escolher da fototeca NÃO pede permissão (o WebKit usa o
  PHPicker, fora do processo) — por isso não há `NSPhotoLibraryUsageDescription`.
- **Barra de status:** o padrão do Capacitor é automático — ícones brancos no
  Modo Escuro, invisíveis sobre a barra branca do app. `UIStatusBarStyleDarkContent`
  fixa ícones escuros (o `CAPBridgeViewController` lê essa chave).
- **`WKAppBoundDomains` anda junto com `ios.limitsNavigationsToAppBoundDomains`
  — nunca um sem o outro.** A flag sem a chave é inofensiva (o SW só não
  registra). A chave SEM a flag marca TODA navegação como fora do domínio, e o
  WebKit passa a bloquear os scripts injetados e o `evaluateJavaScript`: a
  ponte do Capacitor — e com ela a localização em segundo plano — morre. O
  `run-ios.sh` deriva a lista da config (host do `server.url` + `localhost`, a
  tela sem conexão em `capacitor://localhost`) e REMOVE a chave se a flag
  estiver desligada; quem desligar a flag e buildar pelo Xcode sem passar pelo
  script tem que apagar a chave à mão. O WebKit casa pelo domínio registrável
  (`amora.pedalhidrografi.co` cobre todo `*.pedalhidrografi.co`) e aceita até 10
  entradas. O que muda com isso: navegação **principal** para fora da lista é
  bloqueada — mas o Capacitor já manda todo link externo (Instagram, RWGPS…)
  pro Safari antes dessa checagem, então nada muda na prática; tiles, R2
  (`fabdem.`), `telhas.`, jsDelivr e as APIs são sub-recursos e não passam por
  ela.

> A App Store revisa "Always location" com rigor. Justifique com o caso real
> (compartilhar posição ao vivo durante pedais em grupo), deixe claro que é
> opt-in e que para na hora ao desligar. Tenha um vídeo/print do toggle pronto.

### Android — `android/app/src/main/AndroidManifest.xml`

```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
```

O plugin sobe um *foreground service* com notificação persistente enquanto o
watcher está ativo (requisito do Android 10+ para localização em background).
O texto da notificação vem de `backgroundTitle`/`backgroundMessage` no
`addWatcher(...)` em `web/app.js`. O Play Console exige uma **declaração de uso
de localização em background** + revisão.

## `capacitor.config.json` — o que cada chave faz

Mudar a config exige `cap sync` + rebuild nativo (ela vai empacotada no app).

- `server.url` — o app carregado (o site publicado).
- `server.errorPath: "index.html"` — a tela sem conexão, relativa ao `webDir`
  (`www/`). O Capacitor a serve do pacote: `capacitor://localhost/index.html`
  no iOS, `https://localhost/index.html` no Android. No iOS ela entra em
  qualquer falha da navegação principal (inclusive CANCELAMENTO — ver
  Limitações); no Android, em erro de rede e também em erro HTTP (4xx/5xx) da
  página principal, e lá ela não enxerga os plugins. O arquivo tem de existir
  (os `run-*.sh` conferem): se faltar, a falha ao carregar a própria tela de
  erro dispara outro load dela, em laço.
- `ios.limitsNavigationsToAppBoundDomains: true` — liga o service worker (ver
  acima; anda junto com o `WKAppBoundDomains`).
- `ios.zoomEnabled: true` — o Capacitor bloqueia a pinça de zoom da página por
  padrão (desliga o gesto no primeiro zoom). Com isso o shell segue a mesma
  regra do Safari: quem decide é o `<meta name="viewport">` do `web/` (a
  WKWebView respeita `user-scalable=no`/`maximum-scale`, o Safari não). O
  Android segue no padrão do Capacitor (sem zoom); `android.zoomEnabled`
  liga lá, se um dia fizer falta.
- `ios.backgroundColor: "#ffffff"` — fundo da WebView enquanto a página
  carrega. O padrão é a cor do sistema, que vira preto no Modo Escuro — um
  flash escuro entre o splash e o app, que é claro.

## Rodar em device

Pela GUI:

```sh
./run-ios.sh --prepare   # sync + Info.plist — sempre, antes do Xcode
npx cap open ios         # abre o Xcode → Run num iPhone físico
npx cap sync android
npx cap open android     # abre o Android Studio → Run num device
```

Sem abrir a GUI (sync + build + install + launch num device conectado):

```sh
./run-ios.sh --list           # lista devices e UDIDs
./run-ios.sh <UDID>           # ou IOS_UDID=<UDID> ./run-ios.sh
./run-android.sh <serial>     # ou ANDROID_SERIAL=<serial> ./run-android.sh
```

`run-ios.sh` ainda exige o Xcode instalado e a **assinatura configurada uma
vez** (time de desenvolvimento — ver acima; conta Apple grátis serve, mas o app
expira em 7 dias). `npx cap run` passa pelo xcodebuild e instala no device
(devicectl no iOS 17+/Xcode 15+; ios-deploy no iOS ≤16). Como o app carrega o
site remoto (`server.url`), edições só de `web/` dispensam rebuild nativo —
basta publicar o `web/` (ver abaixo quando a versão nova aparece).

## Limitações do shell

- **Sem voltar, sem recarregar, sem barra de endereço.** O Capacitor desliga o
  "quique" da rolagem (então não há pull-to-refresh) e não liga o gesto de
  voltar. Para recarregar: feche o app no seletor de apps e abra de novo.
- **Quando um deploy do `web/` aparece:** como no PWA — o service worker serve
  a cópia em cache e busca a nova em segundo plano, então a versão nova entra
  na abertura seguinte. Um shell que fica dias aberto (transmitindo em segundo
  plano) segue com o código velho até ser fechado e reaberto.
- **`target=_blank` e `window.open` abrem no Safari — até os do próprio
  amora** (🕰 memória, custos, "Abrir rota salva no editor ↗", link do álbum):
  o Capacitor entrega toda janela nova ao sistema. Volta-se pelo "◀ Amora" do
  canto da tela.
- **Uma navegação no lugar pra algo que não é o app não tem volta** (ex.: o
  link do `feed.xml` no changelog da Ajuda mostra o XML cru): só fechando e
  reabrindo.
- **A tela sem conexão também aparece em navegação CANCELADA (iOS).** O
  Capacitor não distingue: um link same-origin que redireciona pra outro host
  (ex.: um download que o backend manda pro bucket) é aberto no Safari e a
  WebView cai na tela "Sem conexão". Ela sonda o servidor e volta pro mapa
  sozinha — mas o mapa recarrega do zero. Por isso links de download no shell
  não devem navegar a página principal.
- **Toda recarga da página desliga a transmissão ao vivo.** Qualquer navegação
  zera as chamadas guardadas da ponte (o watcher nativo para de entregar
  posições) e o app sempre abre com a transmissão desligada: depois de uma
  recarga — ou da tela sem conexão — é preciso ligar de novo.

## Teste de aceitação (o que importa: tela apagada)

1. Instale em um device físico e conceda localização **"Sempre"**.
2. Em Configurações → *Localização ao vivo*, ligue *Transmitir minha localização*
   e ponha um apelido.
3. **Bloqueie o telefone e ponha no bolso.** De outro aparelho (ou navegador),
   confirme que o marcador continua se movendo.
4. Confirme a notificação persistente (Android).
5. Desligue o toggle → as atualizações param na hora. O marcador e o rastro
   **permanecem visíveis até expirar a retenção** escolhida no modal (default
   3 h) — desligar só interrompe novos envios. O `/live-location/stop` (apagar
   o rastro na hora) existe mas **não** é disparado automaticamente.

E o resto do shell (iOS):

6. **📤 enviar imgs → Tirar Foto**: aparece o pedido de acesso à câmera (e não
   o app fechando). Idem **toque longo numa imagem → Salvar nas Fotos**.
7. **Modo Escuro**: relógio e bateria visíveis (escuros) sobre a barra branca.
8. **Service worker**: no Safari do Mac (Desenvolvedor → o iPhone → Amora),
   `navigator.serviceWorker.controller` não é `null` a partir da 2ª abertura.
9. **Sem sinal**: com o SW já instalado, modo avião + fechar + abrir → o mapa
   abre do cache. Na primeira abertura da vida sem sinal → tela "Sem conexão";
   ao sair do modo avião ela volta pro mapa sozinha.

## Publicação (resumo)

- **iOS:** assine com a conta Apple Developer, archive no Xcode, suba pelo App
  Store Connect, preencha o questionário de privacidade (coleta de localização
  precisa, em background, não vinculada a identidade — é pseudônima e efêmera).
  Câmera, microfone e Fotos só são usados quando a pessoa escolhe tirar/salvar
  uma imagem.
- **Android:** gere um AAB assinado, suba no Play Console, preencha a declaração
  de localização em background com a justificativa do caso de uso.

Custo real desse caminho: contas de loja, ciclos de revisão e manutenção nativa
contínua. Por isso o substrato web (Partes A/B do plano) já entrega a feature
para uso em foreground antes deste investimento.
