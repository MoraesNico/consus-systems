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
  (`Movimentacao` do tipo `INICIAL`, gerada inclusive quando a quantidade é 0), na mesma
  transação. Antes da feature 003 existir, o serviço de cadastro apenas define
  `quantidade_atual`; com a 003, o produto nasce com 0 e o saldo vem do `INICIAL`.
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
| `/produtos/` | `produtos:lista` (`?q=`, `?situacao=alerta\|ok`, `?ordem=`, `?pagina=`; 25 por página) | 002 |
| `/produtos/novo/` | `produtos:novo` | 002 |
| `/produtos/<id>/` | `produtos:detalhe` | 002 (+ histórico na 003) |
| `/produtos/<id>/editar/` | `produtos:editar` | 002 |
| `/movimentacoes/` | `movimentacoes:lista` (`?produto=&tipo=&de=&ate=&pagina=`) | 003 |
| `/movimentacoes/nova/` | `movimentacoes:nova` (`?produto=<id>&tipo=ENTRADA\|SAIDA&quantidade=<n>&origem=pagina\|lista\|detalhe\|alertas`) | 003 |
| `/alertas/` | `alertas:relatorio` (relatório de reposição / varredura; `?formato=html\|csv`) | 004 |
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

## Decisões consolidadas (v1.1 — 2026-10-20)

Consolidação das propostas registradas nos `research.md` das features 002, 003 e 004.
Onde as propostas divergiam, vale a coluna **Decisão**; specs, planos e tarefas devem usar
exatamente estes nomes.

### Domínio e serviços

| Tema | Decisão |
|------|---------|
| Exibição do ID | `Produto.codigo` → `"#0001"` (`f"#{pk:04d}"`, não trunca ≥ 10000); `str(produto)` → `"#0001 — Nome"`. Em atributos HTML usar `|unlocalize` (evita `1.234`). |
| Nome | `normalizar_nome()`: apara extremidades e colapsa espaços internos; unicidade por `UniqueConstraint(Lower("nome"))`; acentos diferenciam ("Café" ≠ "Cafe"). |
| Limites | `produtos.models.QUANTIDADE_MAXIMA = 2_147_483_647` (teto de saldo, quantidade inicial e estoque mínimo). Quantidade por Entrada/Saída: 1 a 1.000.000. Campos aceitam só dígitos (`"1.000"`, `"2,5"`, `"+5"` são recusados). |
| Serviços de produto | `cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo) -> Produto`; `editar_produto(*, produto_id, nome, estoque_minimo) -> Produto` (salva com `update_fields`, nunca sobrescreve `quantidade_atual`). |
| Situação (regra única) | `ProdutoQuerySet.em_alerta()`, `sem_alerta()`, `com_situacao()` → anota `alerta` (bool, 002), `deficit` e `cobertura_percentual` (004, com `Cast(..., BigIntegerField())`). Propriedades do modelo: `em_alerta` (bool) e `situacao` (`"alerta"`/`"ok"`). Proibido criar propriedades `alerta`, `deficit` ou `cobertura_percentual` no modelo (colidem com as anotações). |
| Variações do selo | `produtos/partials/situacao.html` é o selo único do sistema: `OK`, `⚠ REPOSIÇÃO NECESSÁRIA` (quantidade ≤ mínimo) e `SEM ESTOQUE` (quantidade 0 — forma mais grave do mesmo alerta). |
| Exceções da 003 | `MovimentacaoError` (base) → `MovimentacaoInvalidaError`, `EstoqueInsuficienteError` (`disponivel`, `solicitado`), `SaldoMaximoExcedidoError`; `MovimentacaoImutavelError` no modelo. |
| Mensagens | `Movimentacao.mensagem_confirmacao` (003) enriquecida por `alertas.regras.confirmacao_com_alerta(mov)` (004) quando a situação piora ou melhora. |
| Dados de demonstração | `popular_demo` usa apenas `cadastrar_produto` e `registrar_movimentacao`; nunca grava `quantidade_atual` diretamente. |

### Interface e HTMX

| Tema | Decisão |
|------|---------|
| Fragmento × página | Helper `apps.core.htmx.eh_fragmento(request)` = `request.htmx and not request.htmx.boosted and not request.htmx.history_restore_request`. Views com variantes declaram `Vary: HX-Request, HX-Target`. |
| Validação | Erro de formulário responde **422** em todas as variantes (001 configura o HTMX para trocar 422). |
| Parâmetros de lista | `q`, `situacao`, `ordem` (prefixo `-` = decrescente, lista branca) e **`pagina`** em todas as listas (não `page`). |
| Partials de produto (002) | `produtos/partials/linha.html` → `<tr id="produto-<id>">`; `produtos/partials/resumo.html` → `<section id="produto-<id>-resumo">`; ambos aceitam `oob` no contexto para emitir `hx-swap-oob="true"`. Região do histórico no detalhe (003): `<section id="produto-<id>-historico">`. Alvo da lista: `#resultados`. |
| Evento `estoque-alterado` | Emitido após **qualquer** operação que altere saldo **ou situação**: cadastro, movimentação e edição do estoque mínimo. Carga opcional `{produto_id, saldo_anterior, saldo_posterior}`. |
| Evento `fechar-dialogo` | Via `HX-Trigger`; `static/js/consus.js` (001) fecha o `<dialog id="dialogo">`. |
| Evento `toast` | `{nivel, texto}` com `nivel ∈ {sucesso, info, alerta, erro}`. |
| Atalhos | `data-atalho="<tecla>"` tratado genericamente por `consus.js` (001); `/` foca a busca, `n` abre novo produto. |
| Pontos fixos do `base.html` (001) | `<dialog id="dialogo">`, região de toasts `#toasts` (`aria-live="polite"`), região visualmente oculta `#anuncio-alertas` (`role="status"`), item de menu "Alertas" com o slot `{% contador_alertas %}` (tag da 004; placeholder vazio antes dela). |
| Contador de alertas | `#contador-alertas` com `hx-get="/alertas/contador/?anterior=<n>"`, `hx-trigger="every 30s, estoque-alterado from:body"`; responde 204 quando nada mudou. |
| Diálogo de movimentação | `movimentacoes:nova` aceita `origem` (`pagina`, `lista`, `detalhe`, `alertas`) e `quantidade` opcional (pré-preenche a sugestão de reposição). |
| CSV | `alertas:relatorio?formato=csv` — separador `;`, UTF-8 com BOM, proteção contra injeção de fórmula. |

### Testes

- Marcador `postgres` registrado no `pyproject.toml` para testes que exigem PostgreSQL
  (concorrência, `Lower()` com acentos); pulados automaticamente no SQLite.
- A suíte completa roda no SQLite (rápida) e no PostgreSQL (CI/Docker).

## Design system (resumo — detalhes em `docs/design/`)

High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise. Tipografia IBM Plex Sans + IBM
Plex Mono (números tabulares). Paleta tinta-sobre-papel (neutros quentes), um acento e
cores semânticas; bordas 1px sólidas; raio 0–2px; sombras sólidas deslocadas sem desfoque;
grade de 12 colunas e base de 8px; tabelas densas (32–40px por linha). O alerta de reposição
é SEMPRE ícone ⚠ (SVG) + texto "REPOSIÇÃO NECESSÁRIA" + cor de alerta.
