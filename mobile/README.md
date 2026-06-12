# Financeiro — App Android (Fase 1)

App instalavel em Flutter que consulta **Yahoo Finance e Brapi diretamente**, como o desktop — **sem depender do PC** nem de `executar_api.bat`.

Interface segue tokens em `../modelo-ui/design-tokens.json` (cores em `lib/tema/cores.dart`).

## Fase 2 (atual)

- Painel com seletor: **Ações**, **Cripto**, **FIIs** e **Índices**
- Gráfico de histórico com periodos (dia, semana, mês, 3 anos, 5 anos, etc.)
- **Mais detalhes**: empresa, indicadores, dividendos e resultados
- Busca por tipo de ativo
- Favoritos por tipo (salvos no celular)
- Carteira de investimentos (várias compras do mesmo ativo em datas/preços diferentes)

## Provedores de mercado

| Dado | Fonte |
|------|-------|
| Cotações B3 | Brapi → Yahoo Chart |
| Cotações EUA / cripto / índices | Yahoo Chart |
| Histórico | Brapi (B3) → Yahoo Chart |
| Busca | Listas locais + Yahoo Search |
| Detalhes | Yahoo Quote Summary → Brapi → Yahoo Chart |

A carteira e os favoritos ficam no celular (`SharedPreferences`). Só precisam de internet para **cotações, gráficos, busca e detalhes**.

## Requisitos

1. **Flutter SDK** — `scripts\instalar_flutter.ps1`
2. **Android Studio** — para gerar APK
3. **Internet no celular** — para dados de mercado (Wi-Fi ou dados móveis)

## Gerar e instalar APK

```powershell
cd mobile
gerar_apk.bat
```

Instale `mobile\Financeiro.apk` no celular. **Não é mais necessário** configurar IP do PC nem manter `executar_api.bat` aberto.

O script `gerar_apk.bat` ainda aceita `celular_api_url.bat` por compatibilidade, mas o app **não usa** essa URL para cotações.

## Emulador no PC

```powershell
mobile\gerar_apk_emulador.bat
mobile\testar_apk.bat
```

## Modo offline

Sem internet, o app abre normalmente. A **carteira local** continua disponível; painel, busca, gráficos e detalhes exibem aviso até a conexão voltar (toque em **Atualizar** na tela inicial).

## Desktop

O app desktop (`executar.bat`) usa a mesma lógica de provedores em Python (`src/Service/`).

A API FastAPI (`executar_api.bat`) permanece opcional para integrações futuras; o mobile **não depende** dela.

## Estrutura mobile

```
financeiro_app/lib/
  servicos/
    api_cliente.dart          # fachada usada pelas telas
    mercado_servico.dart      # painel, cotacao, historico
    busca_mercado_servico.dart
    detalhes_mercado_servico.dart
    provedores/               # Yahoo Chart, Brapi, busca
  dados/universo_mercado.dart # listas de ativos monitorados
```
