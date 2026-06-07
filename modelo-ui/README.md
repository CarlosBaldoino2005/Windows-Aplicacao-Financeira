# Modelo UI Global

Referencia visual unificada para todos os projetos. A IA e desenvolvedores devem seguir estes arquivos ao criar ou alterar interfaces.

## Arquivos

| Arquivo | Conteudo |
|---------|----------|
| `design-tokens.json` | Cores, tipografia, espacamentos, bordas, sombras |
| `layout.md` | Estrutura de paginas, grids e areas da tela |
| `componentes.md` | Padroes de botoes, campos, cards, tabelas e feedback |
| `estados-feedback.md` | Loading, erro, sucesso, vazio e confirmacoes |
| `versao.txt` | Versao atual do modelo (incrementar em mudancas relevantes) |
| `config.ini.example` | Modelo INI: `[Interface]` → `Tema=claro\|escuro` |
| `tema-interface.md` | Tema claro e escuro via config.ini |
| `janela-monitor-pai.md` | Filhas no mesmo monitor do pai (multi-monitor) |
| `grid-interacao-treeview.md` | Hover, clique com toggle e duplo clique em grids |
| `templates/janela_helper.py` | Helper Python Tk/CTk (copiar para `src/Tool/`) |
| `templates/grid_interacao_treeview_helper.py` | Interacao de `ttk.Treeview` (copiar para `src/View/`) |

## Uso em projetos

1. Copie esta pasta para `<projeto>/modelo-ui/` ao iniciar um projeto com interface.
2. Em projetos Python com Tk/CustomTkinter, copie `templates/janela_helper.py` para `src/Tool/janela_helper.py`.
3. Copie `templates/grid_interacao_treeview_helper.py` para `src/View/` e ligue as cores do tema (regra `padrao-grid-interacao-python`).
4. Traduza tokens para a tecnologia do projeto (CSS variables, QSS, VCL, etc.).
5. Nao invente paleta ou espacamento fora deste modelo sem ordem explicita do usuario.

## Atualizacao

Mudancas visuais globais entram aqui primeiro; depois replique em projetos ativos.
