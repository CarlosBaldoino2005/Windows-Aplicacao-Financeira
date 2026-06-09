# Financeiro — App Android (Fase 1)

App instalavel em Flutter que consome a **API FastAPI** do projeto (`api/`).

Interface segue tokens em `../modelo-ui/design-tokens.json` (cores em `lib/tema/cores.dart`).

## Fase 2 (atual)

- Painel com seletor: **Ações**, **Cripto**, **FIIs** e **Índices**
- Gráfico de histórico com periodos (dia, semana, mês, etc.)
- **Mais detalhes**: empresa, indicadores, dividendos e resultados
- Busca por tipo de ativo
- Favoritos por tipo (salvos no celular)

## Fase 1

- Painel: Em alta / Em queda / Todas
- Busca de acoes
- Favoritos salvos no celular (SharedPreferences)
- Conexao com API na nuvem (Render); celular nao depende do PC ligado

## Requisitos

1. **Flutter SDK** — ja pode instalar com o script do projeto:
   ```powershell
   powershell -ExecutionPolicy Bypass -File "scripts\instalar_flutter.ps1"
   ```
   (instala em `C:\src\flutter` e adiciona ao PATH do usuario)
2. **Android Studio** — obrigatorio para gerar APK ([download](https://developer.android.com/studio))
3. API no Render: `https://windows-aplicacao-financeira.onrender.com` (ja configurada em `api_config.dart`)

## 1. Subir a API

### Local (testes no emulador Android)

```powershell
cd "c:\Users\Carlos\OneDrive\Windows\Financeiro"
.\executar_api.bat
```

### Render (celular fisico — padrao)

O APK gerado por `gerar_apk.bat` usa **sempre** a API na nuvem:

`https://windows-aplicacao-financeira.onrender.com`

O PC pode estar desligado; basta internet no celular (Wi-Fi ou dados moveis).

Para publicar outra URL, altere `urlRender` em `lib/config/api_config.dart` e rode `gerar_apk.bat` de novo.

Se definiu `FINANCEIRO_API_KEY` no Render, coloque o mesmo valor em `chaveApi`.

### Emulador no PC (opcional, API local)

Use `gerar_apk_emulador.bat` + `testar_apk.bat` com `executar_api.bat` no PC.

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

## 4. Gerar APK para o celular

```powershell
cd mobile
gerar_apk.bat
```

APK em: `mobile\Financeiro.apk` — conecta na API Render (nuvem).

Copie para o celular e instale (habilite "fontes desconhecidas" se necessario).

**Importante:** se o app ainda mostrar erro com `127.0.0.1`, o APK instalado e antigo. Gere e instale de novo com `gerar_apk.bat`.

## Proximas fases

- Comparar ativos, noticias, tema escuro, empresas pagadoras de dividendos
