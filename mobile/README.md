# Financeiro — App Android (Fase 1)

App instalavel em Flutter que consome a **API FastAPI local** do projeto (`api/`).

**API Render desativada** — desktop e mobile usam apenas API local (`executar_api.bat`).

Interface segue tokens em `../modelo-ui/design-tokens.json` (cores em `lib/tema/cores.dart`).

## Fase 2 (atual)

- Painel com seletor: **Ações**, **Cripto**, **FIIs** e **Índices**
- Gráfico de histórico com periodos (dia, semana, mês, 3 anos, 5 anos, etc.)
- **Mais detalhes**: empresa, indicadores, dividendos e resultados
- Busca por tipo de ativo
- Favoritos por tipo (salvos no celular)
- Carteira de investimentos

## Requisitos

1. **Flutter SDK** — `scripts\instalar_flutter.ps1`
2. **Android Studio** — para gerar APK
3. **API local** rodando no PC: `executar_api.bat` (raiz do projeto)

## 1. Subir a API no PC

```powershell
cd "c:\Users\Carlos\OneDrive\Windows\Financeiro"
.\executar_api.bat
```

A API escuta em `http://0.0.0.0:8000` (acessivel na rede local).

## 2. Celular fisico (Wi-Fi)

1. Copie `mobile\celular_api_url.example.bat` para `mobile\celular_api_url.bat`
2. Ajuste o IP do PC (mesma rede Wi-Fi), ex.: `set API_CELULAR_URL=http://192.168.0.10:8000`
3. Execute `mobile\gerar_apk.bat`
4. Instale `mobile\Financeiro.apk` no celular

O PC precisa estar ligado com `executar_api.bat` em execucao.

## 3. Emulador no PC

1. `executar_api.bat`
2. `mobile\gerar_apk_emulador.bat`
3. `mobile\testar_apk.bat`

## 4. Gerar projeto Android (primeira vez)

```powershell
cd mobile\financeiro_app
flutter create . --project-name financeiro_app --org br.com.financeiro
flutter pub get
```

## Desktop

O app desktop (`executar.bat`) **nao usa** a API HTTP nem o Render — acessa Yahoo/Brapi direto em Python.
