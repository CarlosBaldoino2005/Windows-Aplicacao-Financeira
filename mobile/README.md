# Financeiro — App Android (Fase 1)

App instalavel em Flutter que consome a API FastAPI do projeto (`api/`).

- **Celular fisico:** API na nuvem (Render) — PC pode estar desligado.
- **Emulador no PC:** API local (`executar_api.bat`).

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
3. **Emulador apenas:** API local com `executar_api.bat`

## 1. Celular fisico

1. Execute `mobile\gerar_apk.bat`
2. Instale `mobile\Financeiro.apk` no celular
3. Use Wi-Fi ou dados moveis — nao precisa do PC na mesma rede

A primeira conexao no plano gratuito do Render pode levar ate 1 minuto.

## 2. Emulador no PC

1. `executar_api.bat` (deixe a janela aberta)
2. `mobile\gerar_apk_emulador.bat`
3. `mobile\testar_apk.bat`

## 3. Gerar projeto Android (primeira vez)

```powershell
cd mobile\financeiro_app
flutter create . --project-name financeiro_app --org br.com.financeiro
flutter pub get
```

## Desktop

O app desktop (`executar.bat`) **nao usa** a API HTTP nem o Render — acessa Yahoo/Brapi direto em Python.
