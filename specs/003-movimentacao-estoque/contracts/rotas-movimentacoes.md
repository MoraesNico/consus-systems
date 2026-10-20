# Contrato HTTP: rotas de movimentação

**App**: `apps/movimentacoes` (`app_name = "movimentacoes"`), incluído em `config/urls.py` como
`path("movimentacoes/", include("apps.movimentacoes.urls"))`.

Convenções gerais (de `docs/arquitetura.md`):

- "Requisição HTMX" = `request.htmx and not request.htmx.boosted`. Requisições *boosted*
  (`hx-boost` no `<body>`) recebem a página completa, como uma requisição comum.
- Erro de validação → status **422** (a 001 configura o HTMX para trocar 422).
- CSRF enviado por `hx-headers` no `<body>` (001) e pelo `{% csrf_token %}` do formulário.
- Eventos via cabeçalho `HX-Trigger` (JSON), emitidos com `django_htmx.http.trigger_client_event`.
- Sem rota, método ou view de edição/exclusão de movimentação (FR-021): `PUT`, `PATCH` e
  `DELETE` → 405.

---

## 1. `GET /movimentacoes/` — `movimentacoes:lista`

Página **Movimentações** (livro-razão). FR-022, FR-023, FR-024, FR-026; SC-007.

### Parâmetros (querystring, todos opcionais)

| Nome | Formato | Efeito | Inválido |
|------|---------|--------|----------|
| `produto` | ID inteiro | só movimentações do produto | aviso "Produto não encontrado." e filtro ignorado |
| `tipo` | `INICIAL` \| `ENTRADA` \| `SAIDA` | só esse tipo | aviso e filtro ignorado |
| `de` | `aaaa-mm-dd` ou `dd/mm/aaaa` | `criado_em >= 00:00 de` (fuso local) | aviso "Data inicial inválida." e período ignorado |
| `ate` | `aaaa-mm-dd` ou `dd/mm/aaaa` | `criado_em < 00:00 do dia seguinte` | aviso "Data final inválida." e período ignorado |
| `de` > `ate` | — | — | aviso "A data final deve ser igual ou posterior à inicial." e período ignorado |
| `page` | inteiro ≥ 1 | página (25 por página) | não numérico → 1; acima do total → última |

### Respostas

| Requisição | Status | Template | Conteúdo |
|------------|--------|----------|----------|
| comum / *boosted* | 200 | `movimentacoes/lista.html` (extends `base.html`) | título, ação "Nova movimentação", `partials/filtros.html`, `<div id="resultados">` com `partials/tabela_movimentacoes.html` |
| HTMX com `HX-Target: resultados` | 200 | `movimentacoes/partials/tabela_movimentacoes.html` | só o conteúdo de `#resultados` |

`partials/tabela_movimentacoes.html`:

- avisos de filtro no topo (`role="alert"`), quando houver;
- contagem "N movimentações" e "Página X de Y";
- tabela densa com colunas **Data/hora** (`dd/mm/aaaa HH:MM`), **Produto** (`#0001 Nome`, link
  para `produtos:detalhe`), **Tipo** (selo com texto), **Quantidade** (`+5` / `−3`, mono tabular,
  alinhada à direita), **Saldo** (`10 → 15`, mono tabular, à direita), **Observação**; cada linha
  vem de `partials/linha_movimentacao.html`; **nenhuma** coluna de ações;
- paginação com links `href` (funciona sem HTMX) + `hx-get`, `hx-target="#resultados"`,
  `hx-push-url="true"`, preservando os filtros;
- estado vazio: "Nenhuma movimentação encontrada." + "Limpar filtros" (link para
  `/movimentacoes/`) quando há filtros, ou "Registre a primeira movimentação" (link para
  `movimentacoes:nova`) quando não há nenhuma.

`partials/filtros.html`: `<form id="filtros" method="get" action="{% url 'movimentacoes:lista' %}"
hx-get="{% url 'movimentacoes:lista' %}" hx-target="#resultados" hx-push-url="true"
hx-trigger="change, submit">` com `produto` (select "#0001 — Nome", opção "Todos os produtos"),
`tipo` (Todos, Saldo inicial, Entrada, Saída/Venda), `de`, `ate` (`type="date"`), botão
"Filtrar" (necessário sem HTMX) e link "Limpar".

---

## 2. `GET /movimentacoes/nova/` — `movimentacoes:nova`

Formulário de movimentação. FR-012, FR-013, FR-014, FR-019.

### Parâmetros (querystring, opcionais)

| Nome | Formato | Efeito | Inválido |
|------|---------|--------|----------|
| `produto` | ID inteiro | pré-seleciona o produto e mostra seu saldo | ignorado (formulário sem produto) |
| `tipo` | `ENTRADA` \| `SAIDA` | pré-seleciona o tipo | ignorado (inclui `INICIAL`) |
| `origem` | `lista` \| `detalhe` | só no `hx-get` do diálogo: preenche o campo oculto `origem` | tratado como `lista` |
| `quantidade` | texto | só na prévia | prévia mostra apenas o saldo atual |

### Respostas

| Requisição | Status | Template | Conteúdo |
|------------|--------|----------|----------|
| comum / *boosted* | 200 | `movimentacoes/nova.html` (extends `base.html`) | título "Nova movimentação" + `partials/form_movimentacao.html` em modo página (select de produto) |
| HTMX com `HX-Target: dialogo` | 200 | `movimentacoes/partials/dialogo_movimentacao.html` | título `<h2 id="dialogo-titulo">Registrar entrada — #0001 Parafuso</h2>` + formulário em modo diálogo (produto fixo: texto + `<input type="hidden">`); sem produto válido, cai para o modo página dentro do diálogo |
| HTMX com `HX-Target: previa-saldo` | 200 | `movimentacoes/partials/previa_saldo.html` | ver "Prévia" abaixo |

### Formulário (`partials/form_movimentacao.html`)

```text
<form id="form-movimentacao" method="post" action="/movimentacoes/nova/"
      hx-post="/movimentacoes/nova/" hx-target="this" hx-swap="outerHTML"
      hx-disabled-elt="find button[type=submit]">
  csrf · origem (hidden: pagina|lista|detalhe)
  produto     select "#0001 — Nome" (página)  |  hidden + texto (diálogo)
  tipo        rádio: Entrada | Saída/Venda (fieldset com legenda "Tipo")
  quantidade  type=number inputmode=numeric min=1 max=1000000 step=1 required autofocus
  observacao  type=text maxlength=200, dica "Ex.: nº da nota, cliente"
  <output id="previa-saldo" aria-live="polite" hx-get="/movimentacoes/nova/"
          hx-include="closest form" hx-target="this"
          hx-trigger="input changed delay:300ms from:closest form, change from:closest form">
  [Confirmar]  [Cancelar]   (diálogo: formmethod="dialog"; página: link para produtos:lista)
  resumo de erros com role="alert"; cada erro ligado ao campo por aria-describedby
</form>
```

### Prévia (`partials/previa_saldo.html`, sempre 200)

| Situação | Texto |
|----------|-------|
| sem produto | "Selecione um produto para ver o saldo." |
| produto, quantidade vazia/inválida | "Saldo atual: 10" |
| Entrada válida | "Saldo atual: 10 · Saldo após: 15" |
| Saída ≤ saldo | "Saldo atual: 10 · Saldo após: 7" |
| Saída > saldo | aviso (ícone + texto) "Saldo insuficiente: disponível 10, solicitado 12" |
| Entrada acima do teto | aviso "Saldo máximo excedido: atual X, entrada Y, máximo 2.147.483.647" |

---

## 3. `POST /movimentacoes/nova/` — `movimentacoes:nova`

FR-001…FR-008, FR-012, FR-015…FR-020.

### Campos

`produto` (ID), `tipo` (`ENTRADA`|`SAIDA`), `quantidade`, `observacao` (opcional), `origem`
(`pagina` padrão | `lista` | `detalhe`), `csrfmiddlewaretoken`.

### Respostas

| Requisição | Resultado | Status | Corpo | Cabeçalhos / efeitos |
|------------|-----------|--------|-------|----------------------|
| comum | sucesso | 302 → `/movimentacoes/nova/?produto=<id>&tipo=<tipo>` | — | `messages.success(<mensagem de confirmação>)` (exibida pela 001 como toast) |
| comum | erro | 422 | `movimentacoes/nova.html` com erros e valores preservados | — |
| HTMX, `origem=pagina` | sucesso | 200 | `partials/form_movimentacao.html` limpo: mesmo produto e tipo, quantidade/observação vazias, saldo atualizado | `HX-Trigger`: `estoque-alterado`, `toast` |
| HTMX, `origem=lista` | sucesso | 200 | `partials/sucesso_dialogo.html` com `<template><tr id="produto-<id>" hx-swap-oob="true">…</tr></template>` | `HX-Reswap: none`; `HX-Trigger`: `estoque-alterado`, `toast`, `fechar-dialogo` |
| HTMX, `origem=detalhe` | sucesso | 200 | `partials/sucesso_dialogo.html` com `#produto-<id>-resumo` e `#produto-<id>-historico` (`hx-swap-oob="true"`) | `HX-Reswap: none`; `HX-Trigger`: `estoque-alterado`, `toast`, `fechar-dialogo` |
| HTMX (qualquer origem) | erro | 422 | `partials/form_movimentacao.html` com erros, valores preservados e saldo atual relido | sem `HX-Trigger` (nada mudou) |

**Erros e campos**: saldo insuficiente, quantidade inválida e saldo máximo → campo `quantidade`;
produto inexistente → `produto`; tipo inválido (inclusive `INICIAL`) → `tipo`; observação longa →
`observacao`. A mensagem de saldo insuficiente é exatamente
"Saldo insuficiente: disponível X, solicitado Y".

**Exemplo de `HX-Trigger` (sucesso no diálogo)**:

```json
{
  "estoque-alterado": {"produto_id": 1, "saldo_anterior": 10, "saldo_posterior": 7},
  "toast": {"nivel": "sucesso", "texto": "Saída registrada: #0001 Parafuso — saldo 10 → 7"},
  "fechar-dialogo": {}
}
```

**Garantia de não gravação**: em toda linha "erro" acima, nenhuma `Movimentacao` é criada e
`quantidade_atual` não muda (verificado nos testes de view).
