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

### Parte 2 — Passo 3: Módulo Financeiro e Fluxo de Caixa (O Desafio)

| # | Requisito da atividade (Parte 2) | Feature |
|---|----------------------------------|---------|
| 1 | Cadastro de produtos ganha **Preço de Custo (Unitário)** e **Preço de Venda (Unitário)**, obrigatórios | 007 |
| 1 | Calcular automaticamente a **Margem de Lucro Bruta Prevista** por unidade: Margem = Preço de Venda − Preço de Custo | 007 |
| 2 | **Entrada de Mercadoria** registra uma **despesa** = Qtd Entrada × Preço de Custo | 008 |
| 2 | **Saída/Venda** registra uma **receita** = Qtd Saída × Preço de Venda | 008 |
| 2 | Histórico simples de transações com **Data/Hora, ID do Produto, Tipo (Entrada/Saída), Quantidade e Valor Total da Operação** | 008 |
| 3 | Painel financeiro: **Valor Total do Estoque** = Σ (Quantidade Atual × Preço de Custo) | 009 |
| 3 | **Faturamento Total** = soma de todas as receitas das saídas/vendas | 009 |
| 3 | **Lucro Bruto Realizado** = Receita Total − Custo dos Produtos Vendidos | 009 |
| 3 | **Alerta Financeiro**: indicador visual quando o saldo do caixa (Receitas − Despesas) estiver negativo no período | 009 |

### Pedidos do usuário junto com a Parte 2

| Pedido | Feature |
|--------|---------|
| "Uma parte de login interativa" | 006 |
| "O sistema está com poucas animações e transições" | 005 |
| "Dixe um pouco mais sobrea a paleta de cores" — lido como "deixe a paleta um pouco mais **sóbria**"; a 005 também documenta a paleta | 005 |
| "Uma forma de portar ou fazer funcionar apenas com Python, sem Docker — mas mantenha a infra Docker" | 010 |

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
| 005 | `005-movimento-e-paleta` | Paleta sóbria (tokens v2), sistema de movimento (tokens, `motion.css`, transições de página, diálogo, toasts, linhas, barras, carregamento), documentação da paleta |
| 006 | `006-autenticacao` | App `contas`: login interativo, sair, troca de senha, bloqueio por tentativas, todas as páginas protegidas, usuário registrado nas movimentações |
| 007 | `007-precos-margem` | Preço de custo e de venda no cadastro/edição, `DinheiroField`, margem prevista (R$ e %), prévia ao vivo, colunas na lista |
| 008 | `008-transacoes-financeiras` | App `financeiro`: `Transacao` imutável gerada por toda Entrada/Saída, histórico `/financeiro/transacoes/` com filtros e CSV, valor na prévia e no livro-razão |
| 009 | `009-painel-financeiro` | `/financeiro/`: valor do estoque, faturamento, lucro bruto realizado, saldo do caixa com alerta, períodos, gráficos; faixa financeira no Painel; `resumo_financeiro`; demo com preços e 30 dias de histórico |
| 010 | `010-execucao-local` | Rodar só com Python 3.11+ (venv + pip + SQLite) via `python iniciar.py`, `requirements*.txt` sincronizados com o `uv.lock`, README; Docker mantido |

Dependências: 001 → 002 → 003 → 004 (Parte 1, entregue na v1.0.0) e
005 → 006 → 007 → 008 → 009 → 010 (Parte 2, implementação sequencial; especificação em paralelo).

## Stack

Python 3.11+ (imagem Docker em 3.13) · Django 5.2 LTS · django-htmx · HTMX 2.x (vendorizado) · PostgreSQL 17
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
  contas/               # login, sair, troca de senha, bloqueio por tentativas (006)
  financeiro/           # Transacao, histórico, painel financeiro, resumo_financeiro (008, 009)
templates/
  base.html
  components/           # badges, kpi, campo, diálogo, estado vazio, toast… (botões e tabelas são classes CSS)
static/
  css/tokens.css        # ÚNICA fonte de cores/espaços/tipos/bordas/sombras
  css/base.css  css/components.css  css/motion.css  css/utilities.css
  js/consus.js          # utilitários progressivos (< 100 linhas)
  vendor/htmx.min.js
  fonts/                # IBM Plex Sans / IBM Plex Mono (woff2, self-hosted)
docs/
specs/
Dockerfile  docker-compose.yml  .env.example  entrypoint.sh  pyproject.toml  uv.lock
iniciar.py  requirements.txt  requirements-dev.txt     # execução só com Python (010)
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
| `preco_custo` / `preco_venda` | `DinheiroField` (007) | preço unitário em R$; obrigatórios no cadastro e na edição (> R$ 0,00); ver "Decisões da Parte 2" |
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
| `registrado_por` | FK → usuário, `null=True`, `PROTECT` (006) | quem registrou; vazio em registros anteriores à 2.0 e no terminal sem `--usuario` |
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
| `/entrar/` | `contas:entrar` (GET/POST; `?next=`) — **pública** | 006 |
| `/sair/` | `contas:sair` (somente POST) | 006 |
| `/conta/senha/` | `contas:senha` (troca da própria senha) | 006 |
| `/produtos/previa-margem/` | `produtos:previa_margem` (GET `?preco_custo=&preco_venda=`; fragmento `<output id="previa-margem">`) | 007 |
| `/financeiro/` | `financeiro:painel` (`?periodo=tudo\|hoje\|7d\|30d\|mes\|personalizado&de=&ate=`) | 009 |
| `/financeiro/transacoes/` | `financeiro:transacoes` (`?produto=&tipo=ENTRADA\|SAIDA&de=&ate=&pagina=&formato=html\|csv`) | 008 |

`/saude/` continua **pública** (healthcheck do Docker). Todas as demais rotas exigem login (006).

## Convenções HTMX

- `hx-boost="true"` no `<body>` para navegação; `hx-push-url` em buscas e filtros.
- Busca com `hx-get` + `hx-trigger="input changed delay:300ms, search"`, alvo `#resultados`.
- Formulários: `hx-post`; sucesso → fragmento atualizado + `HX-Trigger`; erro de validação →
  formulário re-renderizado com status **422** (HTMX configurado para trocar 422).
- Eventos: `estoque-alterado` (após qualquer operação que altere saldo ou situação; o contador
  de alertas e o painel escutam com `hx-trigger="estoque-alterado from:body"`), `toast`
  (mensagem `{nivel, texto}`) e `fechar-dialogo`.
- `hx-swap-oob` para atualizar a linha e o resumo do produto na mesma resposta; o contador de
  alertas se atualiza sozinho ao ouvir `estoque-alterado`.
- Diálogos usam `<dialog>` nativo; conteúdo carregado por `hx-get` em `#dialogo`.
- CSRF via `hx-headers` no `<body>`.

## Decisões consolidadas (v1.1 — 2026-10-20)

Consolidação das propostas registradas nos `research.md` das features 001, 002, 003 e 004.
Onde as propostas divergiam, vale a coluna **Decisão**; specs, planos e tarefas devem usar
exatamente estes nomes.

### Domínio e serviços

| Tema | Decisão |
|------|---------|
| Exibição do ID | `Produto.codigo` → `"#0001"` (`f"#{pk:04d}"`, não trunca ≥ 10000); `str(produto)` → `"#0001 — Nome"`. Em atributos HTML usar `\|unlocalize` (evita `1.234`). |
| Nome | `normalizar_nome()`: apara extremidades e colapsa espaços internos; unicidade por `UniqueConstraint(Lower("nome"))`; acentos diferenciam ("Café" ≠ "Cafe"). |
| Limites | `produtos.models.QUANTIDADE_MAXIMA = 2_147_483_647` (teto de saldo, quantidade inicial e estoque mínimo). Quantidade por Entrada/Saída: 1 a 1.000.000. Campos aceitam só dígitos (`"1.000"`, `"2,5"`, `"+5"` são recusados). |
| Serviços de produto | `cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo) -> Produto`; `editar_produto(*, produto_id, nome, estoque_minimo) -> Produto` (salva com `update_fields`, nunca sobrescreve `quantidade_atual`). |
| Situação (regra única) | `ProdutoQuerySet.em_alerta()`, `sem_alerta()`, `com_situacao()` → anota `alerta` (bool, 002), `deficit` e `cobertura_percentual` (004, com `Cast(..., BigIntegerField())`). Propriedades do modelo: `em_alerta` (bool) e `situacao` (`"alerta"`/`"ok"`). Proibido criar propriedades `alerta`, `deficit` ou `cobertura_percentual` no modelo (colidem com as anotações). |
| Variações do selo | `produtos/partials/situacao.html` é o selo único do sistema: `OK`, `⚠ REPOSIÇÃO NECESSÁRIA` (quantidade ≤ mínimo) e `SEM ESTOQUE` (quantidade 0 — forma mais grave: selo composto que mantém o texto "REPOSIÇÃO NECESSÁRIA"). Visual definido em `docs/design/design-system.md`. |
| Exceções da 003 | `MovimentacaoError` (base) → `MovimentacaoInvalidaError`, `EstoqueInsuficienteError` (`disponivel`, `solicitado`), `SaldoMaximoExcedidoError`; `MovimentacaoImutavelError` no modelo. |
| Mensagens | `Movimentacao.mensagem_confirmacao` (003) enriquecida por `alertas.regras.confirmacao_com_alerta(mov)` (004) quando a situação piora ou melhora. |
| Dados de demonstração | `popular_demo` usa apenas `cadastrar_produto` e `registrar_movimentacao`; nunca grava `quantidade_atual` diretamente. |

### Interface e HTMX

| Tema | Decisão |
|------|---------|
| Helpers HTMX (001) | `apps/core/htmx.py`: `eh_fragmento(request)`, `disparar_evento(response, nome, dados=None)` e `disparar_toast(response, nivel, texto)` (acumulam em um único `HX-Trigger`). Formulários usam o `FORM_RENDERER` do projeto. Botões e tabelas são classes CSS do design system, não templates. |
| Fragmento × página | Helper `apps.core.htmx.eh_fragmento(request)` = `request.htmx and not request.htmx.boosted and not request.htmx.history_restore_request`. Views com variantes declaram `Vary: HX-Request, HX-Target`. |
| Validação | Erro de formulário responde **422** em todas as variantes (001 configura o HTMX para trocar 422). |
| Parâmetros de lista | `q`, `situacao`, `ordem` (prefixo `-` = decrescente, lista branca) e **`pagina`** em todas as listas (não `page`). |
| Partials de produto (002) | `produtos/partials/linha.html` → `<tr id="produto-<id>">`; `produtos/partials/resumo.html` → `<section id="produto-<id>-resumo">`; ambos aceitam `oob` no contexto para emitir `hx-swap-oob="true"`. Região do histórico no detalhe (003): `<section id="produto-<id>-historico">`. Alvo da lista: `#resultados`. |
| Evento `estoque-alterado` | Emitido após **qualquer** operação que altere saldo **ou situação**: cadastro, movimentação e edição do estoque mínimo. Carga opcional `{produto_id, saldo_anterior, saldo_posterior}`. |
| Evento `fechar-dialogo` | Via `HX-Trigger`; `static/js/consus.js` (001) fecha o `<dialog id="dialogo">`. |
| Evento `toast` | `{nivel, texto}` com `nivel ∈ {sucesso, info, alerta, erro}`. |
| Atalhos | `data-atalho="<tecla>"` tratado genericamente por `consus.js` (001); `/` foca a busca, `n` abre novo produto. |
| Pontos fixos do `base.html` (001) | `<dialog id="dialogo">`, região de toasts `#toasts` (`aria-live="polite"`), região visualmente oculta `#anuncio-alertas` (`role="status"`), item de menu "Alertas" com o contêiner `<span id="badge-alertas">` onde a 004 renderiza `{% contador_alertas %}` (vazio antes dela). Itens de menu cujas rotas ainda não existem aparecem como "(em breve)" e viram link automaticamente quando a rota é registrada. |
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

## Decisões da Parte 2 (v1.2 — 2026-10-27)

Decisões transversais das features 005–010. Como na v1.1, specs, planos e tarefas devem usar
exatamente estes nomes; propostas de mudança vão para a seção "Propostas ao contrato" do
`research.md` da feature, nunca direto neste arquivo.

### Dinheiro (criado pela 007; usado por 008 e 009)

| Tema | Decisão |
|------|---------|
| Representação | Valores monetários são `decimal.Decimal` com exatamente 2 casas. **`float` é proibido** em qualquer cálculo ou armazenamento de dinheiro. |
| Campo de modelo | `apps/core/dinheiro.py::DinheiroField` — subclasse de `BigIntegerField` que **grava centavos inteiros** e devolve `Decimal` em reais (`from_db_value` aceita `int` e o `Decimal` que o PostgreSQL devolve em agregações). Recusa valores com mais de 2 casas. Motivo: aritmética e `CheckConstraint` exatas no SQLite e no PostgreSQL (o SQLite guarda `DecimalField` como ponto flutuante). |
| Limites | `CENTAVO = Decimal("0.01")`; `PRECO_MAXIMO = Decimal("999999.99")` (R$ 999.999,99 por unidade). Com quantidade máxima de movimentação 1.000.000, o maior valor de uma operação cabe com folga em `bigint`. |
| Entrada de texto | `interpretar_valor(texto) -> Decimal` aceita `12,50`, `1.234,56`, `R$ 1.234,56`, `1234` e ponto decimal com 1–2 dígitos (`12.5`); recusa negativos, letras e mais de 2 casas. Formulários usam `CampoDinheiro` (`inputmode="decimal"`, `autocomplete="off"`, placeholder `0,00`). |
| Exibição | `formatar_moeda(valor, *, sinal=False)` → `R$ 1.234,56`; negativo `−R$ 1.234,56` (sinal U+2212, como em 003); `sinal=True` → `+R$ 12,00`. Filtro de template `moeda` em `apps/core/templatetags/consus.py` (já é builtin): `{{ v\|moeda }}`, `{{ v\|moeda:"sinal" }}`. Valores em fonte mono tabular, alinhados à direita. |
| Agregação | `Coalesce(Sum(..., output_field=DinheiroField()), 0)`; produtos `quantidade × preço` no banco são inteiros (centavos). |
| CSV | Dinheiro como `1234,56` (sem milhar, vírgula decimal, sem `R$`). |

### Produto com preços e margem (007)

| Tema | Decisão |
|------|---------|
| Campos | `preco_custo` e `preco_venda` (`DinheiroField`). Banco: `produto_preco_custo_nao_negativo`, `produto_preco_venda_nao_negativo` (`>= 0`) e `produto_precos_ate_maximo`. Serviços e formulários exigem **> R$ 0,00** e `<= PRECO_MAXIMO` nos dois campos. |
| Produtos anteriores à 2.0 | A migração grava `0` nos dois preços. `Produto.precos_pendentes` (bool) fica verdadeiro e o produto mostra o selo **PREÇO PENDENTE** (variante info, ícone + texto) até ser editado; a edição exige informar os dois preços. |
| Serviços | `cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo, preco_custo, preco_venda, usuario=None)` e `editar_produto(*, produto_id, nome, estoque_minimo, preco_custo, preco_venda)`. Mudar o preço **nunca** altera transações já registradas. |
| Margem prevista | Propriedades `margem_prevista` (`preco_venda − preco_custo`, pode ser negativa), `margem_percentual` (`Decimal` com 1 casa = margem ÷ venda × 100; `None` se venda = 0), `valor_em_estoque` (`quantidade_atual × preco_custo`) e `variante_margem` (`positiva`, `zero`, `negativa`, `pendente`). `ProdutoQuerySet.com_financeiro()` anota `margem` e `valor_estoque` (nomes proibidos como propriedade). |
| Venda abaixo do custo | Permitida (promoção, queima de estoque), com aviso não bloqueante "Preço de venda abaixo do custo: prejuízo de R$ X por unidade." e selo **MARGEM NEGATIVA** (ícone + texto + cor de perigo). |
| Interface | Formulário: Nome, Quantidade inicial, Estoque mínimo, Preço de custo (unitário), Preço de venda (unitário) e a prévia `produtos/partials/previa_margem.html` → `<output id="previa-margem" aria-live="polite">` atualizada por `hx-get` em `produtos:previa_margem` (`input changed delay:300ms`). Lista: colunas Custo, Venda e Margem (R$ e %) depois de Estoque mínimo; `ordem` aceita `margem`/`-margem`. Detalhe: seção "Preços e margem". Selo: `produtos/partials/selo_margem.html`. |

### Usuário nas movimentações e transações financeiras (006, 008)

| Tema | Decisão |
|------|---------|
| Assinatura | `registrar_movimentacao(*, produto_id, tipo, quantidade, observacao="", usuario=None, momento=None)`. `usuario` (006) grava `registrado_por`. `momento` (009) existe só para dados de demonstração/importação: precisa ser ≤ agora e ≥ `criado_em` da última movimentação do produto (senão `MovimentacaoInvalidaError`), mantendo o livro-razão em ordem. |
| Transação na mesma transação de banco | Depois de criar a `Movimentacao`, ainda dentro do `transaction.atomic()` e com o produto bloqueado, `registrar_movimentacao` chama `apps.financeiro.services.registrar_transacao(movimentacao=mov, produto=produto)` (importação tardia, como produtos → movimentacoes). Se a transação financeira falhar, a movimentação é desfeita. |
| Mapeamento | `ENTRADA` → transação `ENTRADA` (**despesa** = quantidade × preço de custo). `SAIDA` → transação `SAIDA` (**receita** = quantidade × preço de venda; custo congelado para o CPV). `INICIAL` com quantidade > 0 → transação `ENTRADA` (a quantidade inicial é mercadoria adquirida: despesa = quantidade inicial × custo). `INICIAL` com 0 → nenhuma transação. |
| Histórico | Transações começam na instalação da 2.0: a migração **não** cria transações para movimentações antigas, e o livro-razão mostra "—" no valor dessas linhas. |
| Toasts | Os textos de confirmação da 003/004 **não mudam**. O valor aparece na prévia do diálogo de movimentação ("Despesa prevista: R$ X" / "Receita prevista: R$ X") e numa coluna "Valor" do livro-razão `/movimentacoes/`. |

`financeiro.Transacao` (imutável, mesmo padrão da `Movimentacao`):

| Campo | Tipo | Regras |
|-------|------|--------|
| `id` | BigAutoField | |
| `movimentacao` | OneToOne → Movimentacao, `PROTECT`, `related_name="transacao"` | uma transação por Entrada/Saída |
| `produto` | FK → Produto, `PROTECT`, `related_name="transacoes"` | o "ID do Produto" do histórico |
| `tipo` | CharField choices `TipoTransacao`: `ENTRADA` ("Entrada"), `SAIDA` ("Saída/Venda") | o "Tipo (Entrada/Saída)" da atividade |
| `quantidade` | PositiveIntegerField | `> 0` |
| `preco_unitario` | DinheiroField | custo (ENTRADA) ou venda (SAIDA) vigente no momento, congelado |
| `valor_total` | DinheiroField | `quantidade × preco_unitario`: despesa (ENTRADA) ou receita (SAIDA) |
| `custo_unitario` | DinheiroField | custo vigente congelado; na ENTRADA é igual a `preco_unitario` |
| `custo_total` | DinheiroField | `quantidade × custo_unitario` (o CPV da venda) |
| `criado_em` | DateTimeField | igual ao `criado_em` da movimentação, indexado |

- Restrições: `transacao_tipo_valido`, `transacao_quantidade_positiva`,
  `transacao_valor_total_consistente`, `transacao_custo_total_consistente`,
  `transacao_entrada_custo_igual_preco`, `transacao_valores_nao_negativos`.
- `TransacaoImutavelError`; `save()` de registro existente, `delete()`, `QuerySet.update()` e
  `QuerySet.delete()` levantam o erro.
- Propriedades: `natureza` ("Despesa"/"Receita"), `eh_receita`, `valor_assinado` (+receita,
  −despesa), `lucro_bruto` (SAIDA: `valor_total − custo_total`; ENTRADA: `None`).
- `TransacaoQuerySet`: `receitas()`, `despesas()`, `do_produto(id)`, `do_tipo(tipo)`,
  `no_periodo(de, ate)` (mesma semântica de `Movimentacao.no_periodo`), `recentes()` e
  `totais() -> Totais` (dataclass: `receitas`, `despesas`, `saldo`, `custo_vendido`,
  `lucro_bruto`, `quantidade_vendida`, `quantidade_transacoes`).
- Histórico `/financeiro/transacoes/`: colunas Data/hora · Produto (`#0001` + nome) · Tipo ·
  Quantidade · Preço unitário · Valor total (receita `+R$`, despesa `−R$`, com selo de natureza) ·
  Registrado por; filtros `produto`, `tipo`, `de`, `ate`; 25 por página; `?formato=csv`
  (`transacoes-AAAAMMDD-HHMM.csv`). Os auxiliares de CSV da 004 passam para
  `apps/core/csv.py` (`proteger_celula`, `montar_csv(cabecalho, linhas, *, bom)`) sem mudar um
  byte da saída da 004.

### Períodos (008 cria; 009 usa)

`apps/core/periodos.py`: `Periodo(chave, rotulo, de, ate)` (dataclass imutável) e
`resolver_periodo(chave, de=None, ate=None, *, hoje=None) -> Periodo`. Chaves e rótulos:
`tudo` "Todo o período" (padrão; `de = ate = None`), `hoje` "Hoje", `7d` "Últimos 7 dias"
(hoje e os 6 anteriores), `30d` "Últimos 30 dias", `mes` "Este mês" (dia 1 até hoje) e
`personalizado` "Personalizado" (exige `de ≤ ate`; datas inválidas viram erro de formulário).
Datas inclusivas no fuso `America/Sao_Paulo`. Chave desconhecida → `tudo`.

### Painel financeiro (009)

| Tema | Decisão |
|------|---------|
| Leitura | `apps/financeiro/selectors.py::resumo_financeiro(periodo, *, agora=None) -> ResumoFinanceiro` com `valor_estoque` (foto do momento, ignora o período), `produtos_preco_pendente`, `receitas`, `despesas`, `saldo_caixa`, `custo_vendido`, `lucro_bruto`, `margem_realizada_percentual` (`None` sem receitas), `caixa_negativo` (`saldo_caixa < 0`), `serie_fluxo` (por dia se o intervalo tem até 62 dias, senão por mês), `top_faturamento`, `top_lucro`, `maiores_valores_estoque` (5 cada) e `ultimas_transacoes` (5). Orçamento: ≤ 8 consultas. |
| KPIs | Valor total do estoque · Faturamento · Lucro bruto realizado (com margem realizada %) · Saldo do caixa (receitas − despesas, com as despesas como linha secundária). |
| Alerta financeiro | `caixa_negativo` ⇒ KPI "Saldo do caixa" na variante de perigo e aviso **⚠ CAIXA NEGATIVO** ("As despesas superam as receitas em R$ X no período.") — sempre ícone + texto + cor; saldo zero é neutro. Parcial `financeiro/partials/selo_caixa.html`. |
| Período | Padrão `tudo` (o Faturamento Total da atividade é "a soma de todas as receitas"); atalhos Todo o período · Este mês · Últimos 30 dias · Últimos 7 dias · Hoje · Personalizado, por `hx-get` com `hx-push-url`, alvo `#painel-financeiro`, que também escuta `estoque-alterado from:body`. |
| Painel `/` | Ganha a faixa `section#painel-financeiro-resumo` (Valor em estoque, Faturamento total, Saldo do caixa + alerta) com link para `/financeiro/`. |
| Terminal | `python manage.py resumo_financeiro [--periodo CHAVE] [--de AAAA-MM-DD --ate AAAA-MM-DD] [--formato texto\|json] [--falhar-se-negativo]`; códigos de saída 0, 1 (caixa negativo com a opção) e 2 (erro de banco ou argumento). |
| Demonstração | `popular_demo` passa a cadastrar preços nos 12 produtos e a espalhar as movimentações pelos últimos 30 dias (via `momento`, em ordem cronológica), preservando os invariantes da 004 (12 produtos, 4 em alerta, 1 sem estoque, 16 movimentações, Σ saldos 474, mesma ordem de criticidade). Resultado esperado: "Todo o período" com **caixa negativo** (compra do estoque inicial) e "Últimos 7 dias" com saldo positivo, para que os dois estados apareçam. |

### Autenticação (006)

| Tema | Decisão |
|------|---------|
| Apps e middleware | `django.contrib.auth` e `apps.contas` em `INSTALLED_APPS`; `AuthenticationMiddleware` logo após `SessionMiddleware`; `apps.contas.middleware.LoginObrigatorioMiddleware` (subclasse do `LoginRequiredMiddleware` do Django 5.1+) depois do `HtmxMiddleware`. Requisição HTMX anônima → resposta com `HX-Redirect` para o login (com `next`); requisição comum → 302. |
| Rotas públicas | Somente `contas:entrar` e `core:saude` (decorador `login_not_required`). Páginas de erro funcionam sem login. |
| Configuração | `LOGIN_URL = "contas:entrar"`, `LOGIN_REDIRECT_URL = "core:painel"`, `LOGOUT_REDIRECT_URL = "contas:entrar"`, `SESSION_COOKIE_AGE = 1209600` (14 dias, usado por "Manter conectado"); sem essa opção a sessão expira ao fechar o navegador. Validadores de senha padrão do Django. |
| Formulário | Campos `usuario` (`autocomplete="username"`), `senha` (`autocomplete="current-password"`) e `lembrar` ("Manter conectado por 14 dias"). Erro genérico **"Usuário ou senha incorretos."** (422, nunca diz qual campo errou; usuário inativo recebe a mesma mensagem). Sucesso: HTMX → `HX-Redirect` (recarga completa, para o novo token CSRF); sem HTMX → 302. `next` validado com `url_has_allowed_host_and_scheme`. Mensagem "Olá, <nome>! Sessão iniciada." vira toast. |
| Interatividade | Mostrar/ocultar senha (botão com `aria-pressed`), aviso de Caps Lock (`aria-live`), botão com estado "Entrando…", cartão que treme no erro e entra animado, foco devolvido ao campo de senha (limpo) após erro. Sem JavaScript tudo funciona por POST comum. |
| Bloqueio | `contas.TentativaAcesso(usuario, ip, criado_em)` registra só falhas. 5 falhas em 15 min para o mesmo usuário (sem diferenciar maiúsculas) **ou** 20 do mesmo IP bloqueiam novas tentativas até a falha mais antiga expirar: resposta **429** com o formulário e "Muitas tentativas. Tente novamente em N min." O `htmx-config` passa a trocar 429. Login bem-sucedido apaga as falhas daquele usuário. |
| Casca | `base.html` ganha os blocos `cabecalho_app` e `rodape_app` (a tela de login usa layout próprio sem navegação). Autenticado, o cabeçalho mostra o menu do usuário (inicial + nome + "Trocar senha" + botão **Sair**, um `<form method="post">` com `hx-boost="false"`). |
| Usuários | Sem cadastro público. `python manage.py garantir_usuario [--usuario X --senha Y]` (ou `CONSUS_USUARIO`/`CONSUS_SENHA`) cria o usuário se não existir e nunca troca a senha de um existente; o `entrypoint.sh` o executa quando as duas variáveis existem. `createsuperuser` também funciona. `.env.example`: `CONSUS_USUARIO=admin`, `CONSUS_SENHA=troque-esta-senha`. |
| Modo demonstração | Com `CONSUS_POPULAR_DEMO=1` (setting `CONSUS_DEMO`), a tela de login mostra "Ambiente de demonstração: usuário admin; a senha é a de CONSUS_SENHA no .env." — nunca imprime a senha. |
| Testes | O `conftest.py` da raiz oferece `usuario` e torna o `client` autenticado por padrão (`force_login`); `cliente_anonimo` cobre os cenários sem login. |

### Movimento e paleta (005) — nomes usados pelas demais features

| Tema | Decisão |
|------|---------|
| Tokens de movimento | `--duration-instant` 0 ms, `--duration-fast` 90 ms, `--duration-moderate` 160 ms, `--duration-slow` 240 ms, `--duration-deliberate` 400 ms; curvas `--ease-standard`, `--ease-entrance`, `--ease-exit`, `--ease-press`; distâncias `--motion-distance-sm` e `--motion-distance-md`. Em `prefers-reduced-motion: reduce` todas as durações e distâncias viram 0. |
| `static/css/motion.css` | Carregado depois de `components.css` e antes de `utilities.css`. Keyframes `consus-surgir`, `consus-sair`, `consus-tremer`, `consus-pulsar`, `consus-destacar`, `consus-crescer-x`, `consus-crescer-y`, `consus-girar` e `consus-carregando`. Classes `.animar-surgir` (escalonamento por `style="--ordem: N"`), `.animar-tremer` e `.animar-destacar`. |
| Comportamentos automáticos | Conteúdo novo do HTMX (`.htmx-added`) em linhas e seções recebe `consus-destacar`; barras de progresso e de gráfico crescem ao entrar; botões têm "pressionar" neo-brutalista (deslocamento + sombra); `<dialog>` abre e fecha animado (`@starting-style`); toasts entram e saem (`.toast--saindo`); barra global de carregamento `#barra-carregamento` (`hx-indicator` no `<body>`, aparece após 150 ms); transições de página por `globalViewTransitions: true` no `htmx-config`, com `view-transition-name` no cabeçalho e no indicador do item ativo do menu. |
| Limites | Anima-se apenas `transform`, `opacity`, `background-color` e `box-shadow`; nada passa de 400 ms, exceto o laço da barra de carregamento e o esmaecer do destaque de linha (1,2 s). Nenhuma animação bloqueia clique ou digitação. |
| Paleta v2 "sóbria" | Os nomes semânticos não mudam (`--color-accent`, `--color-warning*`, `--color-danger*`…), só as primitivas: acento azul-tinta dessaturado, semânticas terrosas (ocre, tijolo, musgo) e selos de alerta com fundo suave + borda forte + tinta escura em vez de amarelo saturado. Novos tokens: `--color-receita`, `--color-receita-subtle`, `--color-despesa`, `--color-despesa-subtle` e `--color-serie-1` … `--color-serie-5` (gráficos). Todos os pares continuam WCAG AA (teste de contraste). |
| Documentação | `docs/design/design-system.md` vai para a v2.0.0 (§2.1 paleta com o porquê de cada cor; §2.11 movimento completo); `/design/` ganha a seção "Movimento"; o README ganha "Paleta de cores". |
| Ícones | 005 acrescenta ao sprite (Lucide 1.60.0, mesmo processo e registro de hash em `static/vendor/README.md`): `eye`, `eye-off`, `log-in`, `log-out`, `user-round`, `lock-keyhole`, `key-round`, `wallet`, `banknote`, `trending-up`, `trending-down`, `receipt`, `calendar`, `percent`, `chart-column`, `circle-dollar-sign`. |
| JavaScript | Total de JavaScript próprio < 200 linhas (constituição 1.1.0). |
| Navegação | Painel · Produtos · Movimentações · **Financeiro** (`financeiro:painel`, ícone `wallet`, seção `financeiro`) · Alertas. |

### Execução local só com Python (010)

| Tema | Decisão |
|------|---------|
| Versões | `requires-python = ">=3.11"`; Ruff com `target-version = "py311"`; nada de sintaxe ou biblioteca exclusiva de 3.12+. A imagem Docker continua em 3.13. |
| Dependências | `requirements.txt` = `uv export --no-dev --no-hashes --format requirements-txt`; `requirements-dev.txt` = `-r requirements.txt` + grupo dev. Um teste confere que as versões batem com o `uv.lock`. |
| `iniciar.py` | Só biblioteca padrão; Windows, macOS e Linux. Confere Python ≥ 3.11 e Django instalado (mensagem clara se faltar), usa `DJANGO_DEBUG=true` e SQLite (`db.sqlite3`) quando não houver `DATABASE_URL`, roda `migrate`, `popular_demo` na primeira execução (`--sem-demo` pula), `garantir_usuario` (usuário `admin`, senha de `CONSUS_SENHA` ou `consus`, exibida no terminal) e `runserver` em `127.0.0.1:8000` (`--porta`, `--host`). |
| README | Seções "Rodar só com Python" (PowerShell e bash), "Levar para outra máquina" e "Usar PostgreSQL sem Docker" (`DATABASE_URL`). Docker continua sendo o caminho principal e não muda. |

### Versão e testes

- A Parte 2 sai como **2.0.0**: o login passa a ser obrigatório em todas as páginas.
- A suíte completa MUST passar no SQLite e no PostgreSQL e, a partir da 010, em Python 3.11 e
  3.13. Cada FR é citado no nome ou na docstring de ao menos um teste (constituição III).
