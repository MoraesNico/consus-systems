# Consus — Contrato de Arquitetura

Documento de referência compartilhado por todas as features em `specs/`. Ele fixa nomes,
fronteiras e decisões transversais para que cada especificação seja escrita de forma
independente sem divergir das demais. Alterações aqui exigem atualizar as specs afetadas.

## Origem: a atividade proposta (SENAI-SP)

> Desenvolver um sistema focado em **Controle de Estoque Simples**, porém altamente
> funcional e eficaz.

| # | Requisito da atividade | Feature |
|---|------------------------|---------|
| 1 | Registrar produto informando **Nome**, **Quantidade Inicial** e **Estoque Mínimo de Segurança** | 002 |
| 1 | Cada produto ganha um **ID numérico automático** para facilitar a busca | 002 |
| 2 | Função para atualizar o saldo do estoque | 003 |
| 2 | Registrar **Entrada** (soma ao estoque atual) | 003 |
| 2 | Registrar **Saída/Venda** (subtrai do estoque atual) | 003 |
| 2 | *Regra de validação*: o estoque de um produto **não pode ficar negativo** | 003 |
| 3 | Opção de **relatório** ou **varredura automática** | 004 |
| 3 | Cruzar **Quantidade Atual** com **Estoque Mínimo de Segurança** | 004 |
| 3 | Se quantidade **≤ mínimo**, exibir alerta visual destacado (ex.: ⚠ **REPOSIÇÃO NECESSÁRIA**) | 004 |

A atividade original descreve um app de console; o Consus entrega a mesma regra de negócio
como aplicação web (Django + HTMX) **e** mantém paridade de terminal por comandos de
gerenciamento (`varrer_estoque`).

## Features (Spec Kit)

| Feature | Branch | Escopo |
|---------|--------|--------|
| 001 | `001-fundacao-design-system` | Projeto Django, Docker/Compose, design system (tokens + componentes), layout base com navegação, página de referência `/design/`, verificação de saúde `/saude/`, painel inicial (placeholder) |
| 002 | `002-cadastro-produtos` | Modelo `Produto`, cadastro, listagem com busca por ID/nome, detalhe, edição de nome e estoque mínimo |
| 003 | `003-movimentacao-estoque` | Modelo `Movimentacao`, entradas, saídas/vendas, bloqueio de saldo negativo, histórico (livro-razão) |
| 004 | `004-alerta-reposicao` | Varredura/relatório de reposição, badge automático, painel com KPIs, comando `varrer_estoque`, dados de demonstração |

Dependências: 001 → 002 → 003 → 004 (implementação sequencial; especificação em paralelo).

## Stack

Python 3.13 · Django 5.2 LTS · django-htmx · HTMX 2.x (vendorizado) · PostgreSQL 17
(Docker) / SQLite (dev e testes) · Gunicorn · WhiteNoise · pytest-django · Ruff ·
dependências declaradas em `pyproject.toml` e travadas com `uv.lock`.

## Estrutura de diretórios

```text
config/                 # settings, urls, wsgi/asgi
apps/
  core/                 # layout, componentes, painel, /design/, /saude/
  produtos/             # Produto
  movimentacoes/        # Movimentacao
  alertas/              # varredura, relatório, contador, comando varrer_estoque
templates/
  base.html
  components/           # botões, badges, kpi, tabela, campo, diálogo, estado vazio, toast
static/
  css/tokens.css        # ÚNICA fonte de cores/espaços/tipos/bordas/sombras
  css/base.css  css/components.css  css/utilities.css
  js/consus.js          # utilitários progressivos (< 100 linhas)
  vendor/htmx.min.js
  fonts/                # IBM Plex Sans / IBM Plex Mono (woff2, self-hosted)
docs/
specs/
Dockerfile  docker-compose.yml  .env.example  entrypoint.sh  pyproject.toml
```

Cada app tem `models.py`, `services.py` (escrita), `selectors.py` (leitura), `forms.py`,
`views.py`, `urls.py`, `templates/<app>/` (página completa) e
`templates/<app>/partials/` (fragmentos HTMX), `tests/`.

## Modelo de dados

### `produtos.Produto`

| Campo | Tipo | Regras |
|-------|------|--------|
| `id` | BigAutoField | ID numérico automático; exibido como `#0001` (4 dígitos, zero à esquerda) |
| `nome` | CharField(120) | obrigatório, aparado, único sem diferenciar maiúsculas/minúsculas |
| `quantidade_atual` | PositiveIntegerField | `CheckConstraint(quantidade_atual >= 0)`; só muda via `Movimentacao` |
| `estoque_minimo` | PositiveIntegerField | estoque mínimo de segurança, `>= 0` |
| `criado_em` / `atualizado_em` | DateTimeField | automáticos |

- A **Quantidade Inicial** informada no cadastro vira o primeiro registro do histórico
  (`Movimentacao` do tipo `INICIAL`), na mesma transação. Antes da feature 003 existir,
  o serviço de cadastro apenas define `quantidade_atual`.
- `ProdutoQuerySet` concentra consultas: `buscar(q)` (por ID — aceita `12`, `#12`,
  `#0012` — ou parte do nome), `em_alerta()` e `com_situacao()` (anotações para a 004).
- Situação derivada (não persistida): `em_alerta = quantidade_atual <= estoque_minimo`.
- Edição permitida: `nome` e `estoque_minimo`. **Não** há edição direta de quantidade
  nem exclusão de produto (preserva o histórico) — fora de escopo.

### `movimentacoes.Movimentacao` (imutável)

| Campo | Tipo | Regras |
|-------|------|--------|
| `id` | BigAutoField | |
| `produto` | FK → Produto, `on_delete=PROTECT`, `related_name="movimentacoes"` | |
| `tipo` | CharField choices | `INICIAL` ("Saldo inicial"), `ENTRADA` ("Entrada"), `SAIDA` ("Saída/Venda") |
| `quantidade` | PositiveIntegerField | `> 0` (exceto `INICIAL`, que aceita `>= 0`) |
| `saldo_anterior` / `saldo_posterior` | PositiveIntegerField | snapshot para auditoria |
| `observacao` | CharField(200) | opcional (ex.: nº da nota, cliente) |
| `criado_em` | DateTimeField | automático, indexado |

Serviço único de escrita:
`movimentacoes.services.registrar_movimentacao(*, produto_id, tipo, quantidade, observacao="") -> Movimentacao`
— executa em `transaction.atomic()` com `select_for_update()` no produto, recalcula o saldo
e lança `EstoqueInsuficienteError` (mensagem: "Saldo insuficiente: disponível X, solicitado Y")
quando a saída deixaria o saldo negativo.

## Rotas (namespaced)

| Rota | Nome | Feature |
|------|------|---------|
| `/` | `core:painel` | 001 (placeholder) → 004 (KPIs) |
| `/design/` | `core:design` | 001 |
| `/saude/` | `core:saude` | 001 |
| `/produtos/` | `produtos:lista` (busca `?q=`, filtro `?situacao=alerta\|ok`, paginação 25) | 002 |
| `/produtos/novo/` | `produtos:novo` | 002 |
| `/produtos/<id>/` | `produtos:detalhe` | 002 (+ histórico na 003) |
| `/produtos/<id>/editar/` | `produtos:editar` | 002 |
| `/movimentacoes/` | `movimentacoes:lista` (filtros produto/tipo/período) | 003 |
| `/movimentacoes/nova/` | `movimentacoes:nova` (`?produto=<id>&tipo=ENTRADA\|SAIDA`) | 003 |
| `/alertas/` | `alertas:relatorio` (relatório de reposição / varredura) | 004 |
| `/alertas/contador/` | `alertas:contador` (fragmento do badge, polling HTMX) | 004 |

## Convenções HTMX

- `hx-boost="true"` no `<body>` para navegação; `hx-push-url` em buscas e filtros.
- Busca com `hx-get` + `hx-trigger="input changed delay:300ms, search"`, alvo `#resultados`.
- Formulários: `hx-post`; sucesso → fragmento atualizado + `HX-Trigger`; erro de validação →
  formulário re-renderizado com status **422** (HTMX configurado para trocar 422).
- Eventos: `estoque-alterado` (após qualquer movimentação; badge e painel escutam com
  `hx-trigger="estoque-alterado from:body"`), `toast` (mensagem `{nivel, texto}`).
- `hx-swap-oob` para atualizar a linha do produto e o badge de alertas na mesma resposta.
- Diálogos usam `<dialog>` nativo; conteúdo carregado por `hx-get` em `#dialogo`.
- CSRF via `hx-headers` no `<body>`.

## Design system (resumo — detalhes em `docs/design/`)

High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise. Tipografia IBM Plex Sans + IBM
Plex Mono (números tabulares). Paleta tinta-sobre-papel (neutros quentes), um acento e
cores semânticas; bordas 1px sólidas; raio 0–2px; sombras sólidas deslocadas sem desfoque;
grade de 12 colunas e base de 8px; tabelas densas (32–40px por linha). O alerta de reposição
é SEMPRE ícone ⚠ (SVG) + texto "REPOSIÇÃO NECESSÁRIA" + cor de alerta.
