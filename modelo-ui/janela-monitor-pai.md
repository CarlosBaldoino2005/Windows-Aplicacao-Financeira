# Janelas Filhas No Mesmo Monitor Do Pai

Problema comum no Windows com varios monitores: ao maximizar uma janela filha sem posiciona-la antes, o sistema abre no **monitor principal** (`+0+0`), mesmo com o app no segundo monitor.

## Regra

1. Detectar a janela que abriu a tela (pai / owner / parent).
2. Posicionar a filha sobre o pai (`rootx`, `rooty`, largura e altura iniciais).
3. So entao maximizar (`state("zoomed")`, `wsMaximized`, `showMaximized()`, etc.).
4. Em fallback manual de geometry, usar coordenadas e dimensoes do **monitor do pai**, nunca `+0+0` fixo.

## Python — arquivo canonico

Copie para o projeto:

```text
modelo-ui/templates/janela_helper.py  →  src/Tool/janela_helper.py
```

Funcoes principais:

| Funcao | Uso |
|--------|-----|
| `configurar_janela_maximizada(janela)` | Tela principal ou filha; detecta pai automaticamente |
| `configurar_janela_maximizada(janela, janela_pai=pai)` | Quando o master Tk nao e o pai logico |
| `posicionar_janela_no_monitor_referencia(janela, pai)` | So reposicionar sem maximizar |
| `maximizar_janela(janela, referencia=pai)` | Maximizar no monitor do pai |

Toda `CTkToplevel` do projeto deve usar `configurar_janela_maximizada` no `__init__`, apos montar a interface.

## Delphi

Antes de exibir form filho maximizado:

- Copiar `Left` e `Top` do `Owner` (ou form chamador).
- Depois `WindowState := wsMaximized`.
- Dialogs pequenos: preferir `poOwnerFormCenter` em vez de `poScreenCenter` quando houver owner em outro monitor.

## Sincronizacao

Ao alterar o helper global, atualize:

1. `C:\Users\Carlos\.cursor\modelo-ui\templates\janela_helper.py`
2. `src/Tool/janela_helper.py` deste projeto
