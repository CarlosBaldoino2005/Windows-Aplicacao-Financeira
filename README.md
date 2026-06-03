# Financeiro - Painel de Mercado (100% Python)

Aplicacao **desktop** em Python para acompanhar o mercado financeiro: acoes em alta, graficos por periodo e comparacao entre ativos.

Toda a interface e logica estao em Python (CustomTkinter + Matplotlib). Nao e necessario navegador.

## Funcionalidades

- **Painel**: abas **Em alta**, **Em queda** e **Todas**; quantidades em `dados/painel.ini` (modelo em `dados/painel.example.ini`).
- **Pesquisar acao** e **Acoes favoritas**: telas dedicadas; favoritos gravados em `dados/favoritos.json` (ate 40 acoes).
- **Grafico da acao**: abre em janela dedicada (periodo dia/mes/ano etc.); duplo clique no painel ou nos favoritos.
- **Comparar acoes**: ate 6 tickers com indice base 100 (desempenho relativo em nova janela).

## Requisitos

- Windows 10/11 (ou SO com Python e interface grafica)
- Python 3.10+
- Conexao com a internet

## Como executar

### Opcao 1 — Mais simples (recomendado)

Duplo clique em **`ABRIR_FINANCEIRO.bat`** (nao precisa ativar o venv no PowerShell).

### Opcao 2 — Arquivo na raiz

```powershell
python executar.py
```

### Opcao 3 — Script PowerShell

```powershell
cd "c:\Users\Carlos\OneDrive\Windows\Financeiro"
.\scripts\desenvolver.ps1
```

> Se aparecer erro de `Activate.ps1` / politica de execucao, use o `.bat` ou `executar.py`.
> O projeto usa `venv\Scripts\python.exe` direto, sem `Activate.ps1`.

### Opcao 4 — Modulo principal (venv)

```powershell
cd "c:\Users\Carlos\OneDrive\Windows\Financeiro"
$env:PYTHONPATH = (Get-Location).Path
.\venv\Scripts\python.exe -m src.main
```

## Arquivos principais

| Arquivo | Funcao |
|---------|--------|
| `executar.py` | Atalho na raiz para abrir o programa |
| `src/main.py` | Ponto de entrada da aplicacao |
| `src/View/interface_app.py` | Janela e telas (GUI) |
| `src/Controller/controlador_mercado.py` | Liga interface ao servico |
| `src/Service/mercado_servico.py` | Cotacoes via yfinance |
| `scripts/desenvolver.ps1` | Instala deps e inicia o app |

## Estrutura MVC

```text
src/
├── Model/          # CotacaoResumo, SerieHistorica
├── View/           # interface_app, tema, formatadores
├── Controller/     # controlador_mercado
├── Service/        # mercado_servico (yfinance)
└── Tool/           # log, validadores pt-BR
```

## Codigos de acoes

- **B3**: `PETR4`, `VALE3` (sufixo `.SA` automatico).
- **EUA**: `AAPL`, `MSFT`, `NVDA`, etc.

## Dependencias

- `yfinance` — dados de mercado
- `customtkinter` — interface moderna
- `matplotlib` — graficos

## Configuracao do painel (INI)

Arquivo: `dados/painel.ini` (criado automaticamente na primeira execucao).

Modelo: `dados/painel.example.ini`

```ini
[PAINEL]
quantidade_acoes = 10
```

- **quantidade_acoes**: maximo de linhas nas abas Em alta, Em queda e Todas (1 a 100).

Ao clicar em **Atualizar cotacoes**, o valor do campo na tela e gravado no INI.

## Logs

`log\log-dd-mm-aaaa.log` (pasta ignorada pelo Git).

## Interface visual

Segue tokens em `modelo-ui/design-tokens.json` (cores, zebrado em tabelas).

## Aviso

Dados publicos do Yahoo Finance. Uso educacional; nao constitui recomendacao de investimento.
