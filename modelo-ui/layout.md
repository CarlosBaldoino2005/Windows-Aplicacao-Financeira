# Layout Padrao

## Estrutura geral

```
+--------------------------------------------------+
|  Cabecalho (titulo + acoes principais)           |
+--------------------------------------------------+
|  [Opcional] Barra lateral |  Area de conteudo    |
|                           |                      |
|                           |  Secoes / cards      |
+--------------------------------------------------+
|  [Opcional] Rodape (status, versao)              |
+--------------------------------------------------+
```

## Regras

- Largura maxima do conteudo principal: ~1200px em telas grandes; centralizar.
- Padding externo da area util: `espacamento.lg` (24px).
- Gap entre secoes: `espacamento.md` a `espacamento.lg`.
- Cabecalho fixo ou sticky quando houver muitas acoes ou navegacao.
- Formularios: labels acima dos campos; agrupar campos relacionados em cards.
- Listagens: toolbar com busca/filtro acima da tabela ou grid.
- Mobile/responsivo: sidebar vira menu; colunas empilham; botoes full-width quando necessario.

## Hierarquia visual

1. Titulo da pagina (maior peso).
2. Acoes primarias alinhadas a direita do titulo ou abaixo em mobile.
3. Conteudo em cards com `superficie`, borda suave e `sombra.card`.
4. Texto secundario com cor `textoSecundario`.

## Formularios Delphi / desktop

- Form centralizado (`poScreenCenter`), borda fixa (`bsSingle`) — ver regra de formularios.
- Margem interna minima 16px; botoes de acao no rodape do form, alinhados a direita.
- Botao primario a direita; cancelar/fechar a esquerda do primario.
