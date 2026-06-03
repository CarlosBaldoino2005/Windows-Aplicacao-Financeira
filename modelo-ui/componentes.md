# Componentes Padrao

Valores referem-se a `design-tokens.json`.

## Botoes

| Tipo | Fundo | Texto | Uso |
|------|-------|-------|-----|
| Primario | primaria | textoInverso | Acao principal (Salvar, Confirmar) |
| Secundario | superficie + borda | texto | Acao alternativa (Cancelar) |
| Perigo | erro | textoInverso | Excluir, acoes destrutivas |
| Ghost | transparente | primaria | Acoes terciarias, links de acao |

- Altura minima: 36px; padding horizontal: `espacamento.md`.
- Border-radius: `borda.raioMd`.
- Hover: escurecer 1 tom; disabled: opacidade ~50%, cursor not-allowed.

## Campos de entrada

- Altura ~36–40px; borda `borda.largura` cor `borda`; raio `borda.raioMd`.
- Focus: borda `primaria` + outline sutil.
- Label acima; mensagem de erro abaixo em `erro`, tamanho `legenda`.
- Placeholder em `textoSecundario`.

## Cards

- Fundo `superficie`, padding `espacamento.lg`, raio `borda.raioLg`, sombra `sombra.card`.
- Titulo da secao com `tituloSecao`; conteudo com gap `espacamento.md`.

## Tabelas / grids

- Cabecalho neutro (sem zebra).
- Linhas zebradas: `zebraClara` / `zebraEscura`.
- Linha selecionada: fundo `selecao`, texto `selecaoTexto`.
- Hover de linha: leve destaque antes da selecao.

## Mensagens (toast / alert)

- Sucesso, aviso, erro, info: usar pares cor/fundo do tokens.
- Icone + texto curto; auto-dismiss opcional para sucesso/info.

## Modais / dialogs

- Overlay escuro ~40% opacidade.
- Painel central `superficie`, max-width ~480px (confirmacao) ou ~720px (formulario).
- Titulo, corpo, acoes no rodape (secundario + primario).
