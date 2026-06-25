# Financeiro - Painel de Mercado (100% Python)

Aplicacao **desktop** em Python para acompanhar o mercado financeiro: acoes em alta, graficos por periodo e comparacao entre ativos.

Toda a interface e logica estao em Python (CustomTkinter + Matplotlib). Nao e necessario navegador.

## Funcionalidades

- **Painel**: abas **Em alta**, **Em queda** e **Todas**; configuracoes em `dados/painel.ini` (quantidades e tema claro/escuro).
- **Pesquisar acao**, **Acoes favoritas**, **Comparar acoes**, **Noticias do mercado** e **Criptomoedas**: botoes na tela principal; favoritos de acoes em `dados/favoritos.json` e de criptos em `dados/favoritos_cripto.json` (ate 40 cada).
- **Grafico da acao**: abre em janela dedicada (periodo dia/mes/ano etc.); duplo clique no painel ou nos favoritos; **linha laranja tracejada** com evolucao em 100% CDI no grafico (acoes em reais); selecao de dois pontos com quantidade mostra valor pago, valor final, lucro/prejuizo e comparacao CDI no painel; botao **Desvalorizacao** abre tela com a ultima queda (pico → fundo) no periodo e lista outras quedas do intervalo; botao **Mais detalhes** com perfil da empresa, indicadores, DRE/balanco/fluxo e concorrentes (yfinance).
- **Comparar acoes** (`janela_comparar_acoes.py`): ate 6 tickers, periodo configuravel; grafico em nova janela com indice base 100, linha **100% CDI** e desempenho relativo.
- **Noticias do mercado** (`janela_noticias_mercado.py`): manchetes Brasil e EUA via Yahoo Finance; **Pesquisar** abre tela para buscar por acao, empresa ou assunto; listbox **Original** / **Portugues (traduzido)** em ambas as telas (`deep-translator`).
- **Criptomoedas** (`janela_hub_criptomoedas.py`): painel com abas Em alta / Em queda / Todas, pesquisa, favoritos, comparacao, graficos e noticias (pares `BTC-USD`, `ETH-USD`, etc. no Yahoo Finance).
- **Fundos imobiliarios** (`janela_hub_fundos_imobiliarios.py`): mesmo painel de acoes, filtrando somente FIIs da B3 (HGLG11, MXRF11, etc.).

## Requisitos

- Windows 10/11 (ou SO com Python e interface grafica)
- Python 3.10+
- Conexao com a internet

## App Android (Fase 1)

Versao mobile instalavel (Flutter). Detalhes em [`mobile/README.md`](mobile/README.md).

| Componente | Como rodar |
|------------|------------|
| Desktop | `executar.bat` — nao usa API HTTP nem Render (dados direto via Python) |
| App Android (celular) | `liberar_api_rede.bat` + `executar_api.bat` + `mobile\gerar_apk.bat` (API local na Wi-Fi) |
| App Android (emulador) | `executar_api.bat` + `gerar_apk_emulador.bat` + `testar_apk.bat` |

> A API na nuvem (Render) esta **desativada** — mobile e desktop usam apenas fontes locais.

Endpoints iniciais: `/api/saude`, `/api/mercado/painel`, `/api/mercado/cotacao/{simbolo}`, `/api/busca/acoes?q=`.

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

## Provedores de dados (fallback automatico)

Cotacoes, historico e parte dos detalhes tentam fontes nesta ordem:

1. **Yahoo Finance** (`yfinance`) — principal  
2. **Brapi** (`https://brapi.dev`) — backup para acoes **B3** (sem token obrigatorio)  
3. **Yahoo Chart API** — backup REST direto (B3 e EUA)

Se o Yahoo falhar, o sistema troca sozinho para a proxima fonte e registra no `log\log-dd-mm-aaaa.log` qual provedor respondeu.

Token opcional da Brapi (mais limite): variavel `BRAPI_TOKEN` no arquivo `.env` (modelo em `config.example.env`).

### Analise com IA (tela Agora)

Opcional. **Nao existe IA gratuita so de mercado financeiro** — o app envia preco, variacao e metricas do ativo para um modelo de linguagem com prompt especializado.

**Pela tela (recomendado):** na janela **Analise** (Agora), clique em **Configurar IA**, escolha o provedor e informe a chave. A configuracao e salva automaticamente no arquivo `.env` na raiz do projeto.

**Recomendado (gratuito, sem cartao): Google Gemini** — chave em [Google AI Studio](https://aistudio.google.com/apikey)

**Alternativa gratuita: Groq** — [console.groq.com](https://console.groq.com)

**OpenAI** (pago / exige creditos): [platform.openai.com](https://platform.openai.com/api-keys)

Edicao manual no `.env` (opcional):

```env
IA_PROVEDOR=gemini
GEMINI_API_KEY=sua_chave_gemini
GEMINI_MODEL=gemini-2.5-flash
```

Com `IA_PROVEDOR=auto`, o app tenta **Gemini → Groq → OpenAI**, usando a primeira chave encontrada.

Na tela **Agora**, use **Analise** → **Analisar com IA**. Conteudo informativo — nao e recomendacao de investimento.

**Ja gratuito no app (sem IA):** aba **Analistas** usa dados reais do Yahoo Finance (recomendacoes e precos-alvo).

## Configuracao do painel (INI)

Arquivo: `dados/painel.ini` (criado automaticamente na primeira execucao).

Modelo: `dados/painel.example.ini`

```ini
[PAINEL]
quantidade_acoes = 10
quantidade_cotas_grafico = 100
modo_aparencia = claro
fotos_noticias = medio
fonte_grid = medio

[JANELA]
monitor_dispositivo = DISPLAY2
```

- **quantidade_acoes**: maximo de linhas nas abas Em alta, Em queda e Todas (1 a 100).
- **quantidade_cotas_grafico**: quantidade padrao na janela do grafico para simular compra (1 a 9.999.999).
- **modo_aparencia**: `claro` ou `escuro` (tambem alteravel no canto superior direito da tela principal).
- **fotos_noticias**: `nenhum`, `pequeno`, `medio` ou `grande` — tamanho das miniaturas nas telas de noticias (tambem alteravel no combo **Fotos**).
- **fonte_grid**: `pequeno`, `medio` ou `grande` — tamanho da fonte nas grids de cotacoes (painel, favoritos, cripto e tabelas de Mais detalhes); alteravel no combo **Fonte grid**.
- **quantidade_cripto**: maximo de linhas no painel de criptomoedas (1 a 80).
- **provedor_noticias**: servidor de noticias de mercado (`geral`, `brasil_ibovespa`, `brasil_blue_chips`, `eua_wall_street`, `eua_tecnologia`, `europa`, `asia`, `commodities`, etc.). Alteravel no combo **Servidor** nas telas de noticias; todas as buscas usam essa fonte.
- **provedor_noticias_cripto**: servidor para noticias de criptomoedas (`cripto_geral`, `cripto_top3`, `cripto_bitcoin`, etc.).
- **monitor_dispositivo** (secao `[JANELA]`): monitor da janela principal (`DISPLAY1`, `DISPLAY2`, ...). Gravado automaticamente ao mover a janela para outro monitor ou ao fechar o app. Na proxima abertura, abre maximizado nesse monitor; se ele nao existir mais, usa o monitor principal.

## Empresa + dividendos

Botao **Empresa + dividendos** na tela principal abre um painel com a mesma estrutura das acoes (Em alta, Em queda, Todas, pesquisa, favoritos, comparar e noticias), listando **somente empresas que pagam dividendos** (lista curada B3/EUA + validacao no Yahoo Finance).

Em **Mais detalhes** do grafico, a aba **Dividendos** mostra data e valor por acao de cada pagamento registrado na fonte.

Favoritos do painel: `dados/favoritos_dividendos.json` (ignorado pelo Git).

## Fundos imobiliarios

Botao **Fundos imobiliarios** (entre Empresa + dividendos e Acoes por periodo) abre painel com a mesma estrutura, listando **somente FIIs da B3** (lista curada + validacao de ticker 11).

Inclui pesquisa, favoritos, comparacao, graficos, noticias e proventos em **Mais detalhes**.

Favoritos do painel: `dados/favoritos_fiis.json` (ignorado pelo Git).

## Acoes por periodo

Botao **Acoes por periodo** abre um painel com a mesma estrutura (Em alta, Em queda, Todas, pesquisa, favoritos, comparar e noticias), mas a variacao e calculada no **periodo selecionado** (Dia, Semana, Mes, Trimestre, Semestre, Ano ou Personalizado com datas), e nao apenas no dia atual.

Use **Atualizar painel** apos mudar o periodo. O carregamento pode levar mais tempo porque consulta o historico de cada acao.

Ao clicar em **Atualizar cotacoes**, a quantidade do painel e gravada no INI. No grafico, o valor e gravado ao clicar em **Atualizar grafico** ou ao fechar a janela. A troca de tema e salva no INI ao selecionar **Claro** ou **Escuro**.

## Logs

`log\log-dd-mm-aaaa.log` (pasta ignorada pelo Git).

## Interface visual

Segue tokens em `modelo-ui/design-tokens.json` (paletas `claro` e `escuro` na secao `modos`, zebrado em tabelas).

## Aviso

Dados publicos (Yahoo Finance, Brapi e APIs relacionadas). Uso educacional; nao constitui recomendacao de investimento.
