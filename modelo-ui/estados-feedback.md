# Estados e Feedback

## Carregamento

- Spinner ou skeleton na area afetada; nunca tela branca sem indicacao.
- Desabilitar botoes repetidos durante submit.
- Texto opcional: "Carregando..." em `textoSecundario`.

## Erro

- Mensagem clara em pt-BR: o que falhou e o que o usuario pode fazer.
- Destaque visual `erro` / `erroFundo`; manter campo invalido com borda erro.
- Erros de validacao: proximos ao campo; erros globais: banner no topo do formulario.

## Sucesso

- Confirmacao breve apos salvar/enviar (toast ou banner `sucesso`).
- Redirecionar ou atualizar lista somente apos feedback visivel.

## Estado vazio

- Ilustracao ou icone leve + titulo + texto orientando proximo passo.
- CTA primario quando fizer sentido ("Adicionar primeiro item").

## Confirmacao destrutiva

- Modal explicito; botao perigo para confirmar; secundario para cancelar.
- Mencionar consequencia ("Esta acao nao pode ser desfeita") quando aplicavel.

## Acessibilidade minima

- Contraste adequado texto/fundo.
- Foco visivel em elementos interativos.
- Labels associados a inputs; botoes com texto descritivo (evitar so icone sem aria-label).
