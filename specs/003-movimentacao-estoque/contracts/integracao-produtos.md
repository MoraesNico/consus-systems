# Contrato: integração com as páginas de produto (002) e eventos (001/004)

**Requisitos**: FR-013, FR-015, FR-017, FR-025, FR-032 | **Pesquisa**: R9, R12

## 1. Inclusion tags (`apps/movimentacoes/templatetags/movimentacoes_tags.py`)

### `{% acoes_rapidas produto origem %}`

- `produto`: instância de `Produto`; `origem`: `"lista"` ou `"detalhe"`.
- Template: `movimentacoes/partials/acoes_rapidas.html`.
- Saída (para `#0001 Parafuso`, origem `lista`):

```html
<a class="…botão compacto secundário (001)…"
   href="/movimentacoes/nova/?produto=1&amp;tipo=ENTRADA"
   hx-get="/movimentacoes/nova/?produto=1&amp;tipo=ENTRADA&amp;origem=lista"
   hx-target="#dialogo" hx-swap="innerHTML"
   aria-label="Registrar entrada de #0001 Parafuso">+ Entrada</a>
<a … tipo=SAIDA … aria-label="Registrar saída de #0001 Parafuso">− Saída</a>
```

- Sem HTMX, o `href` leva à página Nova movimentação com produto e tipo pré-selecionados
  (FR-013). O `hx-get` explícito tem precedência sobre o `hx-boost` do `<body>`.
- O sinal de "− Saída" é U+2212. As ações continuam disponíveis com saldo 0 (a prévia e a
  recusa explicam a situação).

### `{% historico_produto produto %}`

- Consulta `historico_do_produto(produto.pk, limite=10)`.
- Template: `movimentacoes/partials/historico_produto.html`, raiz
  `<section id="produto-<id>-historico" aria-labelledby="produto-<id>-historico-titulo">`
  (aceita `oob=True` para emitir `hx-swap-oob="true"`).
- Conteúdo: título "Histórico", tabela com Data/hora, Tipo, Quantidade (com sinal), Saldo
  (anterior → posterior), Observação (linhas de `partials/linha_movimentacao.html` sem a coluna
  Produto), link "Ver histórico completo" → `/movimentacoes/?produto=<id>`; estado vazio
  "Nenhuma movimentação registrada.".

## 2. Alterações nos templates da feature 002

| Arquivo | Alteração |
|---------|-----------|
| `apps/produtos/templates/produtos/partials/linha_produto.html` | raiz `<tr id="produto-{{ produto.id }}"{% if oob %} hx-swap-oob="true"{% endif %}>`; na célula de ações, `{% load movimentacoes_tags %}{% acoes_rapidas produto "lista" %}` |
| `apps/produtos/templates/produtos/partials/resumo_produto.html` | bloco de saldo/mínimo/situação com raiz `<section id="produto-{{ produto.id }}-resumo"{% if oob %} hx-swap-oob="true"{% endif %}>` (extraído do detalhe se a 002 ainda não o tiver como partial) |
| `apps/produtos/templates/produtos/detalhe.html` | `{% acoes_rapidas produto "detalhe" %}` no cabeçalho; `{% include "produtos/partials/resumo_produto.html" %}`; `{% historico_produto produto %}` |

As views da 002 não mudam.

## 3. Resposta OOB de sucesso (`movimentacoes/partials/sucesso_dialogo.html`)

| `origem` | Fragmentos | Contexto |
|----------|------------|----------|
| `lista` | `<template>{% include "produtos/partials/linha_produto.html" with produto=produto oob=True %}</template>` | `produto = Produto.objects.com_situacao().get(pk=…)` (situação de alerta atualizada) |
| `detalhe` | `{% include "produtos/partials/resumo_produto.html" with oob=True %}` + `{% historico_produto produto oob=True %}` | idem |

Enviada com `HX-Reswap: none`, para que só os OOB sejam aplicados e o diálogo seja fechado pelo
evento `fechar-dialogo`.

## 4. Eventos

| Evento | Emissor | Carga útil | Ouvinte | Efeito esperado |
|--------|---------|------------|---------|-----------------|
| `estoque-alterado` | toda movimentação bem-sucedida via HTMX (003) | `{produto_id, saldo_anterior, saldo_posterior}` | badge de alertas e painel (004), `hx-trigger="estoque-alterado from:body"` | recarregam `/alertas/contador/` e KPIs em ≤ 1 s (SC-005) |
| `toast` | idem | `{nivel: "sucesso", texto: "<mensagem de confirmação>"}` | contêiner de toasts (001, `aria-live`) | exibe "Entrada registrada: #0001 … — saldo 10 → 15" |
| `fechar-dialogo` | sucesso no diálogo (003) | `{}` | `static/js/consus.js` (001) — **proposta ao contrato** | fecha o `<dialog>` e devolve o foco à ação que o abriu |
| `estoque-alterado` | cadastro de produto bem-sucedido via HTMX (view da 002) — **proposta ao contrato** | `{produto_id, saldo_anterior: 0, saldo_posterior}` | idem 004 | o novo produto entra na contagem de alertas, se nascer em alerta |

Sem HTMX (PRG), o recarregamento completo da página já exibe saldo, badge e mensagem
(`django.contrib.messages`, renderizado pela 001) atualizados.

## 5. Dependências assumidas

- **001**: `<dialog id="dialogo">` em `base.html`, aberto após o *swap* de conteúdo em
  `#dialogo`; contêiner de toasts que escuta `toast` e renderiza `messages`; HTMX configurado para
  trocar respostas 422; componentes de botão, selo, tabela, campo e estado vazio; navegação com
  item "Movimentações".
- **002**: `Produto` com `CheckConstraint(quantidade_atual >= 0)`, `Produto.codigo`,
  `ProdutoQuerySet.com_situacao()`, `cadastrar_produto`, partials acima.
- **004**: ouvintes de `estoque-alterado`.
