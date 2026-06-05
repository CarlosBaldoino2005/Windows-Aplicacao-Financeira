# Financeiro — App Android (Fase 1)

App instalavel em Flutter que consome a **API FastAPI** do projeto (`api/`).

Interface segue tokens em `../modelo-ui/design-tokens.json` (cores em `lib/tema/cores.dart`).

## Fase 1 (atual)

- Painel: Em alta / Em queda / Todas
- Busca de acoes
- Favoritos salvos no celular (SharedPreferences)
- Conexao com API na nuvem ou local

## Requisitos

1. [Flutter SDK](https://docs.flutter.dev/get-started/install) (canal stable)
2. Android Studio ou SDK Android (para gerar APK)
3. API rodando (local ou Render)

## 1. Subir a API

### Local (testes no emulador Android)

```powershell
cd "c:\Users\Carlos\OneDrive\Windows\Financeiro"
.\executar_api.bat
```

URL no emulador: `http://10.0.2.2:8000` (ja configurada em `lib/config/api_config.dart`).

### Render (nuvem gratuita)

1. Conta em [render.com](https://render.com)
2. Conecte o repositorio GitHub
3. Crie **Web Service** com **Docker** (usa `Dockerfile` na raiz)
4. Health check: `/api/saude`
5. Copie a URL gerada (ex.: `https://financeiro-api.onrender.com`)
6. Em `lib/config/api_config.dart`, altere `urlBasePadrao`
7. Se definiu `FINANCEIRO_API_KEY` no Render, coloque o mesmo valor em `chaveApi`

## 2. Gerar projeto Android (primeira vez)

Flutter nao esta no repositorio (pasta `android/`). Gere uma vez:

```powershell
cd mobile\financeiro_app
flutter create . --project-name financeiro_app --org br.com.financeiro
flutter pub get
```

## 3. Executar no emulador ou celular

```powershell
flutter devices
flutter run
```

## 4. Gerar APK instalavel

```powershell
flutter build apk --release
```

APK em: `build\app\outputs\flutter-apk\app-release.apk`

Copie para o celular e instale (habilite "fontes desconhecidas" se necessario).

## Celular fisico + API local

O celular nao alcanca `127.0.0.1` do PC. Use:

- API no **Render** (recomendado), ou
- IP da rede local do PC, ex.: `http://192.168.0.10:8000` em `api_config.dart` (mesma Wi-Fi)

## Proximas fases

- Graficos, comparar, detalhes, noticias, cripto, FIIs (novas rotas na API + telas Flutter)
