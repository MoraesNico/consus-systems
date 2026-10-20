# Contrato de fragmentos, IDs e eventos HTMX — `produtos` (002)

Templates em `apps/produtos/templates/produtos/` (páginas, estendem `base.html` da 001) e
`apps/produtos/templates/produtos/partials/` (fragmentos). Componentes visuais (tabela, campo,
botão, badge, diálogo, estado vazio, toast) vêm de `templates/components/` (001); os fragmentos
abaixo os compõem sem estilos próprios fora dos tokens.

## Páginas

| Template | Rota | Conteúdo |
|----------|------|----------|
| `produtos/lista.html` | `produtos:lista` | título "Produtos", ação primária "Novo produto" (`data-atalho="n"`), `filtros.html`, `#contagem-produtos`, `resultados.html` |
| `produtos/novo.html` | `produtos:novo` | `form_produto.html` (contexto `pagina`) |
| `produtos/detalhe.html` | `produtos:detalhe` | `resumo.html`, ação "Editar", região `#produto-movimentacoes` (vazia nesta feature) |
| `produtos/editar.html` | `produtos:editar` | `form_edicao.html` |
| `produtos/nao_encontrado.html` | detalhe/editar (404) | "Produto não encontrado" + link para a lista |

## Fragmentos

| Partial | Elemento raiz / ID | Contexto | Usado por |
|---------|--------------------|----------|-----------|
| `partials/filtros.html` | `<form id="filtros-produtos" method="get" role="search">` | `q`, `situacao`, `oob` | lista; OOB no sucesso do diálogo |
| `partials/resultados.html` | `<div id="resultados">` | `page_obj`, `q`, `situacao`, `ordem`, `total_geral`, `destaque_id` | lista (completa e parcial); sucesso do diálogo |
| `partials/contagem.html` | `<p id="contagem-produtos" role="status">` ("1–25 de 60") | `page_obj`, `oob` | lista; OOB nas respostas parciais |
| `partials/linha.html` | `<tr id="produto-<id>">` | `produto`, `destaque` | resultados; **003** (OOB após movimentação) |
| `partials/situacao.html` | badge de situação | `produto` | linha, resumo; **004** |
| `partials/form_produto.html` | `<form id="form-produto" novalidate>` | `form`, `contexto` (`pagina`/`dialogo`) | novo.html, dialogo_novo.html |
| `partials/dialogo_novo.html` | conteúdo de `#dialogo` (título, form, "Cancelar") | `form` | GET/POST parcial de `produtos:novo` |
| `partials/resumo.html` | `<div id="produto-resumo">` | `produto` | detalhe; **003** (OOB após movimentação) |
| `partials/form_edicao.html` | `<form id="form-edicao" novalidate>` | `form`, `produto` | editar.html |

### Regras de marcação relevantes

- **Busca** (`filtros.html`): `<input type="search" name="q" hx-get="{% url 'produtos:lista' %}"
  hx-trigger="input changed delay:300ms, search" hx-target="#resultados" hx-swap="outerHTML"
  hx-include="#filtros-produtos, #ordem-atual" hx-sync="this:replace" hx-push-url="true"
  data-atalho="/">` com dica `<kbd>/</kbd>`; o `<select name="situacao">` (Todos / Em alerta /
  OK) dispara em `change` com os mesmos alvo/inclusão. Sem scripts, o botão "Buscar" envia o
  formulário GET.
- **Ordem corrente**: `resultados.html` contém
  `<input type="hidden" id="ordem-atual" name="ordem" form="filtros-produtos">`, para que busca e
  filtro preservem a ordenação (com e sem HTMX). Busca/filtro sempre voltam à página 1.
- **Cabeçalhos ordenáveis**: `<th aria-sort="ascending|descending|none">` com link
  `{% url 'produtos:lista' %}{% querystring ordem=<nova> pagina=None %}` + `hx-get` igual,
  `hx-target="#resultados"`, `hx-push-url="true"`.
- **Paginação**: `<nav aria-label="Paginação">` com links `{% querystring pagina=<n> %}`
  (mesmos atributos HTMX).
- **Linha**: ID (`produto.codigo`) e nome são links para o detalhe; números com `|intcomma`,
  alinhados à direita em fonte tabular; linha destacada recebe o estado de destaque do
  componente de tabela + selo "NOVO" (não só cor).
- **Situação** (`situacao.html`): em alerta → badge variante alerta com ícone SVG de aviso +
  texto "REPOSIÇÃO NECESSÁRIA"; ok → badge neutro "OK" (FR-020).
- **Formulários**: `novalidate`; erros por campo com `aria-invalid="true"` e
  `aria-describedby` apontando a mensagem; primeiro campo inválido com `autofocus`; botão
  "Salvar" com `hx-disabled-elt="this"` (evita envio duplo). Campos numéricos:
  `type="text" inputmode="numeric" pattern="[0-9]*"`, sem valor inicial no cadastro.
- **Diálogo**: link "Novo produto" e ação do estado vazio:
  `<a href="{% url 'produtos:novo' %}" hx-get="{% url 'produtos:novo' %}" hx-target="#dialogo"
  hx-swap="innerHTML">`; formulário do diálogo com `hx-post` e `hx-target="#dialogo"`; "Cancelar"
  é `<button formmethod="dialog" formnovalidate>`.
- **IDs em atributos**: `{{ produto.pk|unlocalize }}`; URLs sempre por `{% url %}`.

## Eventos (`HX-Trigger`)

| Evento | Payload | Emitido por | Escutado por |
|--------|---------|-------------|--------------|
| `toast` | `{"nivel": "sucesso", "texto": "Produto #0007 cadastrado"}` | `POST produtos:novo` parcial válido | layout da 001 (região `aria-live`) |
| `estoque-alterado` | `{}` | `POST produtos:novo` parcial válido (o produto pode nascer em alerta) | contador e painel da 004 (`hx-trigger="estoque-alterado from:body"`) |
| `dialogo-fechar` | `{}` | `POST produtos:novo` parcial válido | 001 (fecha o `<dialog>`) — nome proposto (research P5) |

Fluxos comuns/*boosted* não emitem eventos: o servidor re-renderiza o `<body>` (inclusive o
contador da 004) e as notificações vêm de `django.contrib.messages`.

## Pontos de integração

| Para | O que a 002 garante |
|------|---------------------|
| 001 | Usa `#dialogo`, `components/*`, configuração de troca do status 422, toasts de `messages`; consome o manipulador `data-atalho` de `static/js/consus.js` (ou o adiciona — ver tasks) |
| 003 | `#produto-movimentacoes` no detalhe; `partials/linha.html` e `partials/resumo.html` re-renderizáveis com `hx-swap-oob="true"` a partir de um `produto`; `cadastrar_produto` como ponto de extensão (FR-030) |
| 004 | `ProdutoQuerySet.em_alerta()/sem_alerta()/com_situacao()`, `Produto.em_alerta/situacao`, `partials/situacao.html`, filtro `?situacao=alerta`, evento `estoque-alterado` no cadastro parcial |
