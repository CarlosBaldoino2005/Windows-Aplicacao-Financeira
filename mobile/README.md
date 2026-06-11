# Financeiro — App Android (Fase 1)

App instalavel em Flutter que consome a API FastAPI local do projeto (`api/`).

- **Celular fisico:** API local no PC (`executar_api.bat`) na mesma Wi-Fi — **sem Render**.
- **Emulador no PC:** API local (`executar_api.bat` + `127.0.0.1:8000`).

Interface segue tokens em `../modelo-ui/design-tokens.json` (cores em `lib/tema/cores.dart`).

## Fase 2 (atual)

- Painel com seletor: **Ações**, **Cripto**, **FIIs** e **Índices**
- Gráfico de histórico com periodos (dia, semana, mês, 3 anos, 5 anos, etc.)
- **Mais detalhes**: empresa, indicadores, dividendos e resultados
- Busca por tipo de ativo
- Favoritos por tipo (salvos no celular)
- Carteira de investimentos (várias compras do mesmo ativo em datas/preços diferentes)

## Requisitos

1. **Flutter SDK** — `scripts\instalar_flutter.ps1`
2. **Android Studio** — para gerar APK
3. **API local** — `executar_api.bat` (celular e emulador)

## 1. Celular fisico

1. Execute `liberar_api_rede.bat` **como administrador** (uma vez, libera porta 8000 no firewall)
2. Deixe `executar_api.bat` aberto no PC
3. Opcional: copie `celular_api_url.example.bat` para `celular_api_url.bat` e ajuste o IP do PC
4. Execute `mobile\gerar_apk.bat` (detecta o IP da rede ou usa `celular_api_url.bat`)
5. Instale `mobile\Financeiro.apk` no celular na **mesma Wi-Fi** do PC

Em cada posição da carteira, use **Nova compra** para registrar outra aquisição do mesmo ativo.

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

O app desktop (`executar.bat`) **nao usa** API HTTP nem Render — acessa Yahoo/Brapi direto em Python.

A API Render (`onrender.com`) esta **desativada** em todo o projeto.
