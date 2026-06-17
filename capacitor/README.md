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
  `location.origin` continua sendo `amora` — todas as URLs relativas, o service
  worker e os endpoints `/live-*` funcionam **sem CORS e sem refatorar nada**.
  Atualizações do site chegam ao app sem rebuild nativo.
- **A ponte de background vive em `web/app.js`.** As funções
  `startNativeBackgroundWatch()` / `stopNativeBackgroundWatch()` acessam o
  plugin pelo global injetado `window.Capacitor.Plugins.BackgroundGeolocation`
  (sem `import`), guardadas por `liveIsNative()`. Como já fazem parte do site,
  rodam inalteradas: no shell, o watcher de background dirige o envio (chama
  `window.phidroLivePush` a cada fix, inclusive com a tela apagada); num
  navegador comum o plugin não existe e caímos no `watchPosition`. O projeto
  nativo só precisa **registrar o plugin** — nenhum código JS extra aqui.

## Pré-requisitos

- Node ≥ 18 (`@capacitor/cli`).
- **iOS:** macOS + Xcode + uma conta Apple Developer (US$ 99/ano) para
  distribuir. Simulador não dá GPS de verdade — teste em device físico.
- **Android:** Android Studio + SDK; conta Google Play Developer (US$ 25, único)
  para publicar.

## Setup (uma vez)

```sh
cd capacitor
npm install
npx cap add ios
npx cap add android
npx cap sync
```

`cap add` gera os projetos `ios/` e `android/` (gitignorados — recriáveis).
`cap sync` instala os plugins nativos e copia a config/`www/`.

> Versões em `package.json` são um ponto de partida. Se o `npm install` reclamar
> de incompatibilidade, alinhe tudo na mesma major: `npm install @capacitor/core@latest
> @capacitor/cli@latest @capacitor/ios@latest @capacitor/android@latest
> @capacitor-community/background-geolocation@latest` e rode `npx cap sync`.

## Config nativa obrigatória

O plugin `@capacitor-community/background-geolocation` exige permissões e modos
de background declarados à mão.

### iOS — `ios/App/App/Info.plist`

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Mostra sua posição no mapa e a compartilha ao vivo enquanto você usa o app.</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Mantém o compartilhamento da sua localização ao vivo durante o pedal, mesmo com a tela apagada. Você liga e desliga quando quiser.</string>
<key>UIBackgroundModes</key>
<array>
  <string>location</string>
</array>
```

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

## Rodar em device

Pela GUI:

```sh
npx cap sync          # após qualquer mudança de config/plugins
npx cap open ios      # abre o Xcode → Run num iPhone físico
npx cap open android  # abre o Android Studio → Run num device
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
site remoto (`server.url`), edições só de `web/` dispensam rebuild nativo — basta
publicar o `web/` e dar pull-to-refresh no celular.

## Teste de aceitação (o que importa: tela apagada)

1. Instale em um device físico e conceda localização **"Sempre"**.
2. Em Configurações → *Localização ao vivo*, ligue *Transmitir minha localização*
   e ponha um apelido.
3. **Bloqueie o telefone e ponha no bolso.** De outro aparelho (ou navegador),
   confirme que o marcador continua se movendo.
4. Confirme a notificação persistente (Android).
5. Desligue o toggle → as atualizações param e o marcador some em ~2 min (TTL do
   servidor) ou na hora (o `/live-location/stop` é disparado no desligar).

## Publicação (resumo)

- **iOS:** assine com a conta Apple Developer, archive no Xcode, suba pelo App
  Store Connect, preencha o questionário de privacidade (coleta de localização
  precisa, em background, não vinculada a identidade — é pseudônima e efêmera).
- **Android:** gere um AAB assinado, suba no Play Console, preencha a declaração
  de localização em background com a justificativa do caso de uso.

Custo real desse caminho: contas de loja, ciclos de revisão e manutenção nativa
contínua. Por isso o substrato web (Partes A/B do plano) já entrega a feature
para uso em foreground antes deste investimento.
