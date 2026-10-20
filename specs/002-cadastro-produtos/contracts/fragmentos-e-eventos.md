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
| `produtos/detalhe.html` | `produtos:detalhe` | `resumo.html`, ação "Editar", região `<section id="produto-<id>-historico">` (vazia nesta feature; a 003 a substitui por `{% historico_produto produto %}`) |
| `produtos/editar.html` | `produtos:editar` | `form_edicao.html` |
| `produtos/nao_encontrado.html` | detalhe/editar (404) | "Produto não encontrado" + link para a lista |

## Fragmentos

| Partial | Elemento raiz / ID | Contexto | Usado por |
|---------|--------------------|----------|-----------|
| `partials/filtros.html` | `<form id="filtros-produtos" method="get" role="search">` | `q`, `situacao`, `oob` | lista; OOB no sucesso do diálogo |
| `partials/resultados.html` | `<div id="resultados">` | `page_obj`, `q`, `situacao`, `ordem`, `total_geral`, `destaque_id` | lista (completa e parcial); sucesso do diálogo; **003** acrescenta o cabeçalho "Ações" |
| `partials/contagem.html` | `<p id="contagem-produtos" role="status">` ("1–25 de 60") | `page_obj`, `oob` | lista; OOB nas respostas parciais |
| `partials/linha.html` | `<tr id="produto-<id>">` | `produto`, `destaque`, `oob` | resultados; **003** (OOB após movimentação; acrescenta a célula de ações) |
| `partials/situacao.html` | selo único de situação (inclui `components/badge_estoque.html`) | `produto` | linha, resumo; **004** (relatório e painel) |
| `partials/form_produto.html` | `<form id="form-produto" novalidate>` | `form`, `contexto` (`pagina`/`dialogo`) | novo.html, dialogo_novo.html |
| `partials/dialogo_novo.html` | conteúdo de `#dialogo` (título, form, "Cancelar") | `form` | GET/POST parcial de `produtos:novo` |
| `partials/resumo.html` | `<section id="produto-<id>-resumo">` | `produto`, `oob` | detalhe; **003** (OOB após movimentação) |
| `partials/form_edicao.html` | `<form id="form-edicao" novalidate>` | `form`, `produto` | editar.html |

### Regras de marcação relevantes

- **Busca** (`filtros.html`): `<input type="search" name="q" hx-get="{% url 'produtos:lista' %}"
  hx-trigger="input changed delay:300ms, search" hx-target="#resultados" hx-swap="outerHTML"
  hx-include="#filtros-produtos, #ordem-atual" hx-sync="this:replace" hx-push-url="true"
  hx-indicator="#resultados" data-atalho="/">` com dica `<kbd>/</kbd>` (o HTMX marca
  `#resultados` com a classe de requisição em andamento, estilizada pela 001); o `<select name="situacao">` (Todos / Em alerta /
  OK) dispara em `change` com os mesmos alvo/inclusão. Sem scripts, o botão "Buscar" envia o
  formulário GET.
- **Ordem corrente**: `resultados.html` contém
  `<input type="hidden" id="ordem-atual" name="ordem" form="filtros-produtos">`, para que busca e
  filtro preservem a ordenação (com e sem HTMX). Busca/filtro sempre voltam à página 1.
- **Cabeçalhos ordenáveis**: `<th aria-sort="ascending|descending|none">` com link
  `{% url 'produtos:lista' %}{% querystring ordem=<nova> pagina=None %}` + `hx-get` igual,
  `hx-target="#resultados"`, `hx-push-url="true"`.
- **Paginação**: componente `components/paginacao.html` da 001 (`pagina=page_obj`,
  `rotulo_itens="produtos"`, `alvo="#resultados"`) → `<nav aria-label="Paginação">` com links
  `{% querystring pagina=<n> %}`, `hx-get`, `hx-target="#resultados"`, `hx-swap="outerHTML"` e
  `hx-push-url="true"`.
- **Linha**: raiz `<tr id="produto-{{ produto.pk|unlocalize }}"{% if oob %} hx-swap-oob="true"{% endif %}>`
  com `.tabela__linha--alerta` / `.tabela__linha--sem-estoque` conforme a situação (design-system
  §4.3); ID (`produto.codigo`) e nome são links para o detalhe; números com `|intcomma`,
  alinhados à direita em fonte tabular; linha destacada recebe o estado de destaque do
  componente de tabela + selo "NOVO" (não só cor).
- **Resumo**: raiz `<section id="produto-{{ produto.pk|unlocalize }}-resumo"{% if oob %} hx-swap-oob="true"{% endif %}>`
  (contrato v1.1) — a 003 o re-renderiza fora de banda sem alterar este template.
- **Situação** (`situacao.html`, selo único do sistema — contrato v1.1): inclui
  `components/badge_estoque.html` (001) com `situacao="sem_estoque"` se
  `produto.quantidade_atual == 0`, `"reposicao"` se `produto.em_alerta`, senão `"ok"` →
  respectivamente o selo composto "⚠ REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE", "⚠ REPOSIÇÃO
  NECESSÁRIA" (ícone SVG `triangle-alert` + texto + cor de alerta) e "OK" discreto (FR-020).
  Funciona com produto anotado ou não, sem consulta extra; a 004 o reutiliza sem alterá-lo.
- **Formulários**: `novalidate`; erros por campo com `aria-invalid="true"` e
  `aria-describedby` apontando a mensagem; primeiro campo inválido com `autofocus`; botão
  "Salvar" com `hx-disabled-elt="this"` (evita envio duplo). Campos numéricos:
  `type="text" inputmode="numeric" pattern="[0-9]*"`, sem valor inicial no cadastro.
- **Diálogo**: ao abrir, o campo Nome tem `autofocus`; ao fechar, o `<dialog>` nativo devolve
  o foco ao controle que o abriu. Link "Novo produto" e ação do estado vazio:
  `<a href="{% url 'produtos:novo' %}" hx-get="{% url 'produtos:novo' %}" hx-target="#dialogo"
  hx-swap="innerHTML">`; formulário do diálogo com `hx-post` e `hx-target="#dialogo"`; "Cancelar"
  é `<button formmethod="dialog" formnovalidate>`.
- **IDs em atributos**: `{{ produto.pk|unlocalize }}`; URLs sempre por `{% url %}`.

## Eventos (`HX-Trigger`)

| Evento | Payload | Emitido por | Escutado por |
|--------|---------|-------------|--------------|
| `toast` | `{"nivel": "sucesso", "texto": "Produto #0007 cadastrado"}` | `POST produtos:novo` parcial válido (`disparar_toast(resp, "sucesso", …)`) | layout da 001 (região `aria-live`) |
| `estoque-alterado` | `{"produto_id": 7, "saldo_anterior": 0, "saldo_posterior": <quantidade inicial>}` | `POST produtos:novo` parcial válido (o produto pode nascer em alerta); qualquer resposta parcial de edição bem-sucedida (contrato v1.1) | `#contador-alertas`, `#relatorio` e `#painel-kpis` da 004 (`hx-trigger="… estoque-alterado from:body"`) |
| `fechar-dialogo` | `{}` | `POST produtos:novo` parcial válido (`disparar_evento(resp, "fechar-dialogo")`) | `consus.js` da 001 (fecha o `<dialog>`) |

Fluxos comuns/*boosted* não emitem eventos: o servidor re-renderiza o `<body>` (inclusive o
contador da 004) e as notificações vêm de `django.contrib.messages`. A edição (página própria)
só tem variantes comum/*boosted* nesta feature; se ganhar variante parcial, ela DEVE emitir
`estoque-alterado` (FR-031).

## Pontos de integração

| Para | O que a 002 garante |
|------|---------------------|
| 001 | Usa `#dialogo`, `components/*` (inclusive `badge_estoque.html` e `paginacao.html`), helpers `apps.core.htmx`, configuração de troca do status 422, toasts de `messages`; consome o manipulador `data-atalho` de `static/js/consus.js` (fornecido pela 001, FR-045) |
| 003 | `<section id="produto-<id>-historico">` reservada no detalhe; `partials/linha.html` (`#produto-<id>`) e `partials/resumo.html` (`#produto-<id>-resumo`) re-renderizáveis com `oob=True` a partir de um `produto`; `cadastrar_produto` como ponto de extensão (FR-030) |
| 004 | `ProdutoQuerySet.em_alerta()/sem_alerta()/com_situacao()` (anotação `alerta`; a 004 acrescenta `deficit` e `cobertura_percentual`), `Produto.em_alerta/situacao`, selo único `partials/situacao.html` (já com SEM ESTOQUE), filtro `?situacao=alerta`, evento `estoque-alterado` no cadastro parcial |
