# Contrato: integração com as páginas de produto (002) e eventos (001/004)

**Requisitos**: FR-013, FR-015, FR-017, FR-025, FR-032 | **Pesquisa**: R9, R12

## 1. Inclusion tags (`apps/movimentacoes/templatetags/movimentacoes_tags.py`)

### `{% acoes_rapidas produto origem %}`

- `produto`: instância de `Produto`; `origem`: `"lista"` ou `"detalhe"` (a 004 monta seus
  próprios links com `origem=alertas`). IDs em URLs e atributos com `|unlocalize` (contrato v1.1:
  evita `produto=1.234`).
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

## 2. Extensões nos templates da feature 002

Nomes e raízes do contrato `docs/arquitetura.md` v1.1, já entregues pela 002 (inclusive o
suporte a `oob` no contexto): `produtos/partials/linha.html` → `<tr id="produto-{{ produto.pk|unlocalize }}">`;
`produtos/partials/resumo.html` → `<section id="produto-{{ produto.pk|unlocalize }}-resumo">`;
região reservada `<section id="produto-{{ produto.pk|unlocalize }}-historico">` no detalhe.

| Arquivo (002) | Extensão feita pela 003 |
|---------------|-------------------------|
| `apps/produtos/templates/produtos/partials/linha.html` | nova última célula com `{% load movimentacoes_tags %}{% acoes_rapidas produto "lista" %}` (raiz e `oob` inalterados) |
| `apps/produtos/templates/produtos/partials/resultados.html` | cabeçalho `<th scope="col">Ações</th>` (não ordenável) correspondente à nova célula |
| `apps/produtos/templates/produtos/detalhe.html` | `{% acoes_rapidas produto "detalhe" %}` no bloco `acoes` do cabeçalho; a seção vazia `#produto-<id>-historico` é **substituída** por `{% historico_produto produto %}` (que renderiza a mesma raiz) |

`produtos/partials/resumo.html` é usado sem alteração. As views da 002 não mudam.

## 3. Resposta OOB de sucesso (`movimentacoes/partials/sucesso_dialogo.html`)

| `origem` | Fragmentos | Contexto |
|----------|------------|----------|
| `lista` | `<template>{% include "produtos/partials/linha.html" with produto=produto oob=True %}</template>` | `produto = Produto.objects.com_situacao().get(pk=…)` (situação de alerta atualizada) |
| `detalhe` | `{% include "produtos/partials/resumo.html" with oob=True %}` + `{% historico_produto produto oob=True %}` | idem |
| `alertas` | nenhum fragmento (corpo vazio) — relatório/painel da 004 se atualizam por `estoque-alterado` | — |

Enviada com `HX-Reswap: none`, para que só os OOB sejam aplicados e o diálogo seja fechado pelo
evento `fechar-dialogo`.

## 4. Eventos

| Evento | Emissor | Carga útil | Ouvinte | Efeito esperado |
|--------|---------|------------|---------|-----------------|
| `estoque-alterado` | toda movimentação bem-sucedida via HTMX (003) | `{produto_id, saldo_anterior, saldo_posterior}` | `#contador-alertas`, `#relatorio` e `#painel-kpis` (004), `hx-trigger="… estoque-alterado from:body"` | recarregam `/alertas/contador/`, o relatório e os KPIs em ≤ 1 s (SC-005) |
| `toast` | idem | `{nivel: "sucesso", texto: "<mensagem de confirmação>"}` | contêiner de toasts (001, `aria-live`) | exibe "Entrada registrada: #0001 … — saldo 10 → 15" |
| `fechar-dialogo` | sucesso no diálogo (003) | `{}` | `static/js/consus.js` (001) — contrato v1.1 | fecha o `<dialog>` e devolve o foco à ação que o abriu |
| `estoque-alterado` | cadastro de produto bem-sucedido via HTMX (view da 002) — contrato v1.1 | `{produto_id, saldo_anterior: 0, saldo_posterior}` | idem 004 | o novo produto entra na contagem de alertas, se nascer em alerta |

Sem HTMX (PRG), o recarregamento completo da página já exibe saldo, badge e mensagem
(`django.contrib.messages`, renderizado pela 001) atualizados.

## 5. Dependências assumidas

- **001**: `<dialog id="dialogo">` em `base.html`, aberto após o *swap* de conteúdo em
  `#dialogo`; contêiner de toasts que escuta `toast` e renderiza `messages`; HTMX configurado para
  trocar respostas 422; helpers `eh_fragmento`/`disparar_evento`/`disparar_toast`; componentes de
  botão, selo, tabela, campo, paginação e estado vazio; navegação com item "Movimentações" (vira
  link sozinho ao registrar `movimentacoes:lista`).
- **002**: `Produto` com `CheckConstraint(quantidade_atual >= 0)`, `Produto.codigo`,
  `ProdutoQuerySet.com_situacao()`, `QUANTIDADE_MAXIMA` (teto de saldo), `cadastrar_produto`,
  partials acima.
- **004**: ouvintes de `estoque-alterado`.
