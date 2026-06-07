# Interacao De Grids — Hover, Clique E Duplo Clique

Padrao global para listas e tabelas em projetos Python (CustomTkinter + `ttk.Treeview`).

## Comportamento obrigatorio

| Acao | Comportamento |
|------|----------------|
| **Hover** | Linha sob o cursor fica azul (`selecao` / `selecaoTexto`), exceto se ja estiver selecionada |
| **Clique simples** | Alterna selecao da linha (liga/desliga o azul); permite **multiplas linhas** |
| **Duplo clique** | Acao na **linha sob o cursor** (`identify_row`), nunca na linha errada por selecao antiga |
| **Visual** | Hover e selecao usam **o mesmo azul** (tags + `style.map` do Treeview) |

## Implementacao

### Treeview (`ttk`)

1. Copie `templates/grid_interacao_treeview_helper.py` para `src/View/`.
2. Ao criar a grid, chame `configurar_interacao_treeview` com cores do tema.
3. No estilo, chame `aplicar_destaque_estilo_treeview`.
4. Ao preencher linhas, guarde tag zebrada em `tabela._tags_zebra[iid]` e chame `sincronizar_tags_selecao_treeview` apos reload.
5. Handlers de duplo clique devem usar `obter_iid_linha_evento_treeview` ou `obter_iid_duplo_clique_treeview`.

```python
configurar_interacao_treeview(
    tabela,
    cor_fundo_destaque=CORES["selecao"],
    cor_texto_destaque=CORES["selecaoTexto"],
    ao_duplo_clique=self._abrir_detalhe,
)
```

### Tabela zebrada (CustomTkinter)

- Hover: Enter/Leave com contador (evita flicker entre celulas).
- Duplo clique: bind em linha + rotulos; callback sem depender de selecao previa.
- Ordenacao: regra `padrao-grid-ordenacao-python`.

## Robustez

- Verifique `treeview_ainda_ativa(tabela)` antes de atualizar apos threads ou `after`.
- Delay ~280 ms no clique simples evita conflito com duplo clique (toggle cancelado no `<Double-1>`).

## Referencia

Projeto modelo: **Financeiro** — `src/View/grid_interacao_treeview_helper.py`, `tabela_mercado_helper.py`, `tabela_detalhes_helper.py`.

Regra Cursor: `padrao-grid-interacao-python.mdc`.
