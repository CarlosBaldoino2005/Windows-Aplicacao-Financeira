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
| `janela-monitor-pai.md` | Filhas no mesmo monitor do pai (multi-monitor) |
| `templates/janela_helper.py` | Helper Python Tk/CTk (copiar para `src/Tool/`) |

## Uso em projetos

1. Copie esta pasta para `<projeto>/modelo-ui/` ao iniciar um projeto com interface.
2. Copie `templates/janela_helper.py` para `src/Tool/janela_helper.py` em projetos Python desktop.
3. Traduza tokens para a tecnologia do projeto (CSS variables, QSS, VCL, etc.).
4. Nao invente paleta ou espacamento fora deste modelo sem ordem explicita do usuario.

## Atualizacao

Mudancas visuais globais entram aqui primeiro; depois replique em projetos ativos.
