---

description: "Lista de tarefas da feature 003 — Controle de Movimentação (Entradas e Saídas)"
---

# Tasks: Controle de Movimentação — Entradas e Saídas

**Input**: Design documents from `/specs/003-movimentacao-estoque/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: OBRIGATÓRIOS — a constituição (princípio III, NÃO-NEGOCIÁVEL) exige testes antes da
implementação, ao menos um teste por FR citando o identificador no nome ou docstring, cobertura
≥ 90% em `services.py`, `models.py` e `selectors.py` e views testadas nas variantes comum e HTMX.

**Organization**: tarefas agrupadas por história de usuário (US1…US5 da spec), cada uma testável
de forma independente após a fundação e a US1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário da tarefa (US1…US5)
- Caminhos conforme `docs/arquitetura.md` e [plan.md](plan.md#project-structure)

## Path Conventions

- App da feature: `apps/movimentacoes/` (templates em `apps/movimentacoes/templates/movimentacoes/`,
  fragmentos HTMX em `.../partials/`, testes em `apps/movimentacoes/tests/`)
- Pontos de integração de outras features: `config/`, `pyproject.toml`, `templates/base.html`,
  `apps/produtos/services.py`, `apps/produtos/templates/produtos/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: esqueleto do app, registro e infraestrutura de testes

- [ ] T001 Criar o pacote do app em apps/movimentacoes/ com `__init__.py`, `apps.py` (`MovimentacoesConfig(name="apps.movimentacoes", label="movimentacoes", verbose_name="Movimentações")`), `migrations/__init__.py`, `tests/__init__.py`, `templatetags/__init__.py`, `management/__init__.py` e `management/commands/__init__.py`
- [ ] T002 Registrar `"apps.movimentacoes"` em `INSTALLED_APPS` (depois de `"apps.produtos"`) em config/settings.py — ou no módulo base, se a 001 tiver dividido o settings em pacote
- [ ] T003 Criar apps/movimentacoes/urls.py (`app_name = "movimentacoes"`; `path("", views.lista_movimentacoes, name="lista")`, `path("nova/", views.nova_movimentacao, name="nova")`) e apps/movimentacoes/views.py com as duas funções como *stubs* que levantam `NotImplementedError`
- [ ] T004 Incluir `path("movimentacoes/", include("apps.movimentacoes.urls"))` em config/urls.py (se a 001 ainda não o tiver)
- [ ] T005 [P] Registrar o marcador `"postgres: testes que exigem PostgreSQL (concorrência e desempenho)"` em `[tool.pytest.ini_options] markers` de pyproject.toml
- [ ] T006 [P] Criar fixtures em apps/movimentacoes/tests/conftest.py: fábrica `produto_com_saldo(nome="Parafuso", saldo=10, minimo=3)` que usa `produtos.services.cadastrar_produto(nome=…, quantidade_inicial=…, estoque_minimo=…)` (nunca grava `quantidade_atual` direto), `htmx_headers` (`{"HX-Request": "true"}`) e `htmx_alvo(alvo)` (acrescenta `"HX-Target": alvo`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelo `Movimentacao` com as restrições de banco e a imutabilidade — base de todas as histórias

**⚠️ CRITICAL**: nenhuma história começa antes desta fase terminar

- [ ] T007 Escrever (falhando) testes do modelo em apps/movimentacoes/tests/test_models.py: `TipoMovimentacao` com valores/rótulos `INICIAL`="Saldo inicial", `ENTRADA`="Entrada", `SAIDA`="Saída/Venda"; gravação direta violando `mov_tipo_valido`, `mov_quantidade_positiva_exceto_inicial` (quantidade 0 em ENTRADA), `mov_saldo_posterior_consistente` (posterior ≠ anterior ± quantidade), `mov_inicial_parte_de_zero`, `mov_inicial_unica_por_produto` e `saldo_posterior` negativo levanta `IntegrityError` (FR-009, FR-010); ordenação padrão `-criado_em, -id`; propriedades `sinal` (`"+"`/`"−"` U+2212), `quantidade_assinada`, `variante_selo` e `mensagem_confirmacao` ("Saída registrada: #0001 Parafuso — saldo 10 → 7") (FR-016, FR-033)
- [ ] T008 Escrever (falhando) testes de imutabilidade em apps/movimentacoes/tests/test_models.py: `save()` de registro existente, `delete()`, `Movimentacao.objects.update()` e `.delete()` levantam `MovimentacaoImutavelError`; apagar produto com movimentação levanta `ProtectedError` (FR-021, SC-006)
- [ ] T009 Implementar apps/movimentacoes/models.py: constantes `QUANTIDADE_MAXIMA = 1_000_000`, `SALDO_MAXIMO = 2_147_483_647`, `OBSERVACAO_MAX = 200`, `HISTORICO_DETALHE = 10`, `ITENS_POR_PAGINA = 25`; `TipoMovimentacao(models.TextChoices)`; `MovimentacaoImutavelError`; `MovimentacaoQuerySet` (`do_produto`, `do_tipo`, `no_periodo(de, ate)` com intervalo `[início(de), início(ate + 1 dia))` no fuso atual, `recentes`, `update`/`delete` bloqueados); `Movimentacao` com `produto = ForeignKey("produtos.Produto", on_delete=PROTECT, related_name="movimentacoes")`, `tipo = CharField(max_length=7, choices=TipoMovimentacao.choices)`, `quantidade`/`saldo_anterior`/`saldo_posterior = PositiveIntegerField()`, `observacao = CharField(max_length=200, blank=True, default="")`, `criado_em = DateTimeField(default=timezone.now, db_index=True, editable=False)`; `Meta` com `ordering = ["-criado_em", "-id"]`, as restrições `CheckConstraint(condition=…)` e `UniqueConstraint(fields=["produto"], condition=Q(tipo="INICIAL"))` do data-model.md e o índice `mov_produto_criado_idx` (`produto`, `-criado_em`); guardas `save`/`delete` e propriedades de apresentação
- [ ] T010 Gerar apps/movimentacoes/migrations/0001_initial.py com `python manage.py makemigrations movimentacoes` (dependendo da última migração de `produtos`) e conferir as restrições `mov_*` com `python manage.py sqlmigrate movimentacoes 0001`

**Checkpoint**: modelo e migração prontos; T007/T008 verdes

---

## Phase 3: User Story 1 - Registrar Entrada e Saída sem jamais negativar o saldo (Priority: P1) 🎯 MVP

**Goal**: serviço único de escrita + página `/movimentacoes/nova/` (comum e HTMX) com as três camadas da regra de saldo não negativo

**Independent Test**: produto com saldo 10 → Entrada 5 (15) → Saída 15 (0) → Saída 1 recusada com "Saldo insuficiente: disponível 0, solicitado 1", sem gravação; o mesmo fluxo com e sem HTMX

### Tests for User Story 1 ⚠️

> Escrever primeiro e confirmar que FALHAM antes da implementação

- [ ] T011 [P] [US1] Testes do serviço em apps/movimentacoes/tests/test_services.py: Entrada soma (FR-002); Saída subtrai (FR-003); Saída igual ao saldo zera (FR-004); Saída maior que o saldo levanta `EstoqueInsuficienteError` com `str` "Saldo insuficiente: disponível 3, solicitado 5", atributos `disponivel`/`solicitado`, saldo inalterado e nenhuma movimentação gravada (FR-004, SC-002); quantidade 0, negativa, 1.000.001, `bool` e não inteira levanta `MovimentacaoInvalidaError` (FR-005); Entrada acima de `SALDO_MAXIMO` levanta `SaldoMaximoExcedidoError` "Saldo máximo excedido: atual X, entrada Y, máximo 2.147.483.647" (FR-005); observação aparada e > 200 caracteres recusada (FR-006); tipo inválido e produto inexistente ("Produto #0099 não encontrado.") recusados (FR-007); snapshots `saldo_anterior`/`saldo_posterior` e `criado_em` corretos (FR-010); mensagens com separador de milhar ("disponível 1.200, solicitado 1.500") (FR-033)
- [ ] T012 [US1] Testes de atomicidade e via única em apps/movimentacoes/tests/test_services.py: falha simulada (monkeypatch) na criação da `Movimentacao` desfaz a alteração de saldo (FR-011); o serviço decide com o saldo relido sob bloqueio e não com o saldo carregado antes por outra instância (saldo desatualizado) (FR-008); POST com `quantidade_atual` em `produtos:editar` não altera o saldo e `Movimentacao` não está registrada no admin (FR-001)
- [ ] T013 [P] [US1] Testes de concorrência em apps/movimentacoes/tests/test_concorrencia.py com `pytestmark = [pytest.mark.postgres, pytest.mark.django_db(transaction=True), pytest.mark.skipif(connection.vendor != "postgresql", reason="requer PostgreSQL")]`, *threads* sincronizadas por `threading.Barrier` e `connection.close()` ao fim de cada *thread*: saldo 10 + 20 saídas simultâneas de 1 → exatamente 10 aceitas, 10 `EstoqueInsuficienteError`, saldo final 0 e 10 saídas gravadas, parametrizado em 20 rodadas (FR-008, SC-003); saldo 10 + duas saídas de 6 → uma aceita e outra "Saldo insuficiente: disponível 4, solicitado 6"; espera comprovada (a *thread* B conclui só após o *commit* da A e registra `saldo_anterior` = `saldo_posterior` da A); Entrada e Saída simultâneas mantêm a continuidade dos saldos (FR-008)
- [ ] T014 [P] [US1] Testes do formulário em apps/movimentacoes/tests/test_forms.py: `QuantidadeField` recusa "2,5", "2.5", "1.000", "abc", "" e "  " com "Informe um número inteiro, sem casas decimais nem separadores." e aceita " 7 " (FR-005); limites 0 → "Informe uma quantidade maior que zero." e 1.000.001 → "Informe no máximo 1.000.000." (FR-005); `tipo` aceita só `ENTRADA`/`SAIDA` e recusa `INICIAL` (FR-007); produto inexistente → "Selecione um produto válido." (FR-007); observação aparada e > 200 recusada com "Use no máximo 200 caracteres." (FR-006); `clean()` recusa Saída acima do saldo com a mensagem do serviço (FR-004, FR-009 camada 1) e Entrada acima do teto (FR-005)
- [ ] T015 [P] [US1] Testes da variante comum em apps/movimentacoes/tests/test_views_nova.py: GET 200 com `movimentacoes/nova.html`, produto e tipo pré-selecionados por `?produto=&tipo=` e saldo atual exibido; pré-seleção inválida (produto inexistente, `tipo=INICIAL`) ignorada (FR-012, FR-014); POST válido → 302 para `/movimentacoes/nova/?produto=<id>&tipo=<tipo>` e mensagem "Entrada registrada: #0001 Parafuso — saldo 10 → 15" na página seguinte, pronta para novo registro (FR-012, FR-016, FR-019); POST de Saída acima do saldo → 422 com a página completa, "Saldo insuficiente: disponível X, solicitado Y", valores preservados e nada gravado (FR-004, FR-018, FR-019); `PUT`/`DELETE` → 405
- [ ] T016 [US1] Testes da variante HTMX em apps/movimentacoes/tests/test_views_nova.py: POST com `HX-Request` e `origem=pagina` → 200 apenas com `partials/form_movimentacao.html` limpo (mesmo produto/tipo, quantidade vazia, saldo atualizado) e `HX-Trigger` com `estoque-alterado` (`{produto_id, saldo_anterior, saldo_posterior}`) e `toast` (`{nivel: "sucesso", texto: …}`) (FR-012, FR-016, FR-017); erro → 422 com o partial, sem `HX-Trigger` e sem gravação (FR-018); requisição *boosted* recebe a página completa; o formulário tem `hx-disabled-elt="find button[type=submit]"` (FR-020) e resumo de erros com `role="alert"` (FR-032)

### Implementation for User Story 1

- [ ] T017 [US1] Implementar apps/movimentacoes/services.py: `formatar_numero`; exceções `MovimentacaoError`, `MovimentacaoInvalidaError`, `EstoqueInsuficienteError(disponivel, solicitado)` ("Saldo insuficiente: disponível X, solicitado Y") e `SaldoMaximoExcedidoError(atual, entrada)`; `registrar_movimentacao(*, produto_id, tipo, quantidade, observacao="") -> Movimentacao` para `ENTRADA`/`SAIDA` com `transaction.atomic()`, `Produto.objects.select_for_update().get(pk=produto_id)` (sem `nowait`), quantidade `1..QUANTIDADE_MAXIMA`, observação aparada `<= 200`, teto `SALDO_MAXIMO`, `produto.save(update_fields=["quantidade_atual", "atualizado_em"])` e criação da `Movimentacao` (contracts/servico-movimentacao.md)
- [ ] T018 [US1] Implementar apps/movimentacoes/forms.py: `QuantidadeField` (aceita só `^[+-]?\d+$` após aparar; mínimo 1; máximo 1.000.000; mensagens pt-BR do T014; widget `type="number" inputmode="numeric" min="1" max="1000000" step="1"`) e `MovimentacaoForm` (`produto` = `ModelChoiceField` ordenado por nome com rótulo "#0001 — Nome"; `tipo` = `RadioSelect` ENTRADA/SAIDA; `quantidade`; `observacao` = `CharField(max_length=200, required=False, strip=True)`; `origem` oculto `pagina|lista|detalhe`, padrão `pagina`; `clean()` com checagem de saldo e teto)
- [ ] T019 [US1] Criar apps/movimentacoes/templates/movimentacoes/nova.html (extends `base.html`, título "Nova movimentação") e apps/movimentacoes/templates/movimentacoes/partials/form_movimentacao.html (`<form id="form-movimentacao" method="post" action hx-post hx-target="this" hx-swap="outerHTML" hx-disabled-elt="find button[type=submit]">`, saldo atual do produto, campos com erros ligados por `aria-describedby`, resumo `role="alert"`, botões Confirmar/Cancelar) usando os componentes de campo e botão da 001
- [ ] T020 [US1] Implementar `nova_movimentacao` em apps/movimentacoes/views.py: `require_http_methods(["GET", "POST"])`; parcial só se `request.htmx and not request.htmx.boosted`; GET com pré-seleção por `produto`/`tipo`; POST chama `registrar_movimentacao` e converte `MovimentacaoError` em `form.add_error` (status 422); sucesso comum → `messages.success(mov.mensagem_confirmacao)` + redirect para `/movimentacoes/nova/?produto=<id>&tipo=<tipo>`; sucesso HTMX `origem=pagina` → formulário limpo + `trigger_client_event` `estoque-alterado` e `toast` (contracts/rotas-movimentacoes.md §2–3)

**Checkpoint**: US1 funcional e testável sozinha (MVP do item 2 da atividade)

---

## Phase 4: User Story 2 - Ações rápidas a partir do produto com atualização imediata (Priority: P2)

**Goal**: "+ Entrada" / "− Saída" na lista e no detalhe de produtos, diálogo HTMX com prévia, atualização OOB e eventos

**Independent Test**: na lista de produtos, "− Saída" no produto de saldo 10 → digitar 3 → prévia "Saldo após: 7" → Confirmar → linha mostra 7 sem recarregar, toast "10 → 7", `estoque-alterado` disparado

### Tests for User Story 2 ⚠️

- [ ] T021 [P] [US2] Testes em apps/movimentacoes/tests/test_integracao_produtos.py: `{% acoes_rapidas produto "lista" %}` renderiza "+ Entrada" e "− Saída" (U+2212) com `href="/movimentacoes/nova/?produto=<id>&tipo=…"`, `hx-get` com `origem=lista`, `hx-target="#dialogo"` e `aria-label="Registrar entrada de #0001 Parafuso"` (FR-013, FR-032); `produtos:lista` e `produtos:detalhe` exibem as ações para cada produto, inclusive com saldo 0 (FR-013)
- [ ] T022 [P] [US2] Testes do diálogo e da prévia em apps/movimentacoes/tests/test_views_nova.py: GET HTMX com `HX-Target: dialogo` → 200 com `partials/dialogo_movimentacao.html`, título "Registrar entrada — #0001 Parafuso", produto oculto, tipo marcado, saldo atual, `autofocus` na quantidade e `origem` preenchido (FR-013, FR-014, FR-032); GET HTMX com `HX-Target: previa-saldo` → "Saldo atual: 10 · Saldo após: 15" (Entrada 5), "Saldo insuficiente: disponível 10, solicitado 12" (Saída 12), "Selecione um produto para ver o saldo." (sem produto) e aviso de saldo máximo (FR-014)
- [ ] T023 [US2] Testes de sucesso/erro no diálogo em apps/movimentacoes/tests/test_views_nova.py: POST HTMX `origem=lista` → 200, `HX-Reswap: none`, corpo com `<template>` + `<tr id="produto-<id>" hx-swap-oob="true">` mostrando o novo saldo e `HX-Trigger` com `estoque-alterado`, `toast` e `fechar-dialogo` (FR-015, FR-016, FR-017); `origem=detalhe` → OOB de `#produto-<id>-resumo` com o novo saldo (FR-015); Saída acima do saldo → 422 com o formulário do diálogo, mensagem, valores preservados, sem OOB, sem `HX-Trigger` e sem gravação (FR-018)

### Implementation for User Story 2

- [ ] T024 [P] [US2] Criar apps/movimentacoes/templatetags/movimentacoes_tags.py com a inclusion tag `acoes_rapidas(produto, origem)` e o template apps/movimentacoes/templates/movimentacoes/partials/acoes_rapidas.html (contracts/integracao-produtos.md §1)
- [ ] T025 [P] [US2] Criar apps/movimentacoes/templates/movimentacoes/partials/dialogo_movimentacao.html (título `id="dialogo-titulo"`, formulário em modo diálogo com produto fixo e Cancelar `formmethod="dialog"`) e apps/movimentacoes/templates/movimentacoes/partials/previa_saldo.html (`<output id="previa-saldo" aria-live="polite" hx-get hx-include="closest form" hx-target="this" hx-trigger="input changed delay:300ms from:closest form, change from:closest form">`), incluindo a prévia em apps/movimentacoes/templates/movimentacoes/partials/form_movimentacao.html
- [ ] T026 [P] [US2] Criar apps/movimentacoes/templates/movimentacoes/partials/sucesso_dialogo.html com os fragmentos OOB por `origem`: `lista` → `<template>{% include "produtos/partials/linha_produto.html" with oob=True %}</template>`; `detalhe` → `{% include "produtos/partials/resumo_produto.html" with oob=True %}`
- [ ] T027 [US2] Estender `nova_movimentacao` em apps/movimentacoes/views.py: GET `HX-Target: dialogo` → diálogo (sem produto válido, modo página dentro do diálogo); GET `HX-Target: previa-saldo` → prévia calculada com as mesmas mensagens do serviço; POST HTMX `origem=lista|detalhe` → `sucesso_dialogo.html` com o produto relido por `Produto.objects.com_situacao().get(pk=…)`, `reswap(response, "none")` e `trigger_client_event` `estoque-alterado`, `toast` e `fechar-dialogo`
- [ ] T028 [US2] Ajustar apps/produtos/templates/produtos/partials/linha_produto.html: raiz `<tr id="produto-{{ produto.id }}"{% if oob %} hx-swap-oob="true"{% endif %}>` e `{% load movimentacoes_tags %}{% acoes_rapidas produto "lista" %}` na célula de ações
- [ ] T029 [US2] Criar/ajustar apps/produtos/templates/produtos/partials/resumo_produto.html (raiz `<section id="produto-{{ produto.id }}-resumo"{% if oob %} hx-swap-oob="true"{% endif %}>` com saldo, mínimo e situação) e apps/produtos/templates/produtos/detalhe.html (inclui o resumo e `{% acoes_rapidas produto "detalhe" %}` no cabeçalho)

**Checkpoint**: US1 + US2 funcionando; ações rápidas atualizam a tela sem recarregar

---

## Phase 5: User Story 3 - Consultar o histórico imutável (livro-razão) (Priority: P2)

**Goal**: página `/movimentacoes/` com filtros, paginação e estados vazios; histórico das 10 últimas no detalhe do produto; nenhuma edição/exclusão

**Independent Test**: com movimentações de dois produtos em dias diferentes, filtrar produto #0001 + Saída + período e conferir linhas, sinais e saldos; não há ação de editar/excluir

### Tests for User Story 3 ⚠️

> Contagens devem filtrar por tipo ou ser relativas: após a US4 todo produto também tem um `INICIAL`.

- [ ] T030 [P] [US3] Testes dos seletores em apps/movimentacoes/tests/test_selectors.py: `listar_movimentacoes` ordena por `-criado_em, -id` e filtra por produto, tipo e `de`/`ate` inclusivos no fuso `America/Sao_Paulo` (bordas 00:00 e 23:59), isoladamente e combinados (FR-022, FR-023); `historico_do_produto` devolve só as 10 mais recentes do produto (FR-025)
- [ ] T031 [P] [US3] Testes de `FiltroMovimentacoesForm` em apps/movimentacoes/tests/test_forms.py: aceita `aaaa-mm-dd` e `dd/mm/aaaa`; data malformada, `de > ate` ("A data final deve ser igual ou posterior à inicial."), produto inexistente e tipo inválido geram aviso e não filtram, mantendo os demais filtros válidos (FR-023, FR-026)
- [ ] T032 [P] [US3] Testes da página em apps/movimentacoes/tests/test_views_lista.py: comum → 200 `movimentacoes/lista.html` com data/hora `dd/mm/aaaa HH:MM`, produto `#0001 Parafuso` com link para o detalhe, selo com texto do tipo, quantidade `+5`/`−3`, saldo `10 → 15` e observação (FR-022, FR-033); HTMX com `HX-Target: resultados` → só `partials/tabela_movimentacoes.html` (FR-023); 25 por página com filtros preservados nos links, `page` inválido → 1 e acima do total → última (FR-024); estados vazios "Limpar filtros" / "Registre a primeira movimentação" (FR-026); nenhuma ação de editar/excluir e `POST`/`PUT`/`DELETE` → 405 (FR-021, SC-006); números "1.234" (FR-033)
- [ ] T033 [US3] Testes em apps/movimentacoes/tests/test_integracao_produtos.py: `produtos:detalhe` exibe `#produto-<id>-historico` com as 10 mais recentes, sem coluna produto, e o link "Ver histórico completo" para `/movimentacoes/?produto=<id>` (FR-025); sucesso no diálogo com `origem=detalhe` inclui o OOB de `#produto-<id>-historico` com a nova movimentação no topo (FR-015)

### Implementation for User Story 3

- [ ] T034 [US3] Implementar apps/movimentacoes/selectors.py: `listar_movimentacoes(*, produto_id=None, tipo=None, de=None, ate=None)` (via `MovimentacaoQuerySet`, `select_related("produto")`, `-criado_em, -id`) e `historico_do_produto(produto_id, *, limite=HISTORICO_DETALHE)`
- [ ] T035 [US3] Implementar `FiltroMovimentacoesForm` em apps/movimentacoes/forms.py: `produto` opcional ("Todos os produtos"), `tipo` ("Todos" + 3 tipos), `de`/`ate` com `input_formats=["%Y-%m-%d", "%d/%m/%Y"]`, validação `de <= ate` e método que devolve só os filtros válidos e a lista de avisos
- [ ] T036 [P] [US3] Criar apps/movimentacoes/templates/movimentacoes/lista.html, apps/movimentacoes/templates/movimentacoes/partials/filtros.html (`hx-get`, `hx-target="#resultados"`, `hx-push-url="true"`, `hx-trigger="change, submit"`, botão Filtrar e link Limpar), apps/movimentacoes/templates/movimentacoes/partials/tabela_movimentacoes.html (avisos `role="alert"`, contagem, tabela densa sem ações, paginação com `href` + `hx-get`, estados vazios) e apps/movimentacoes/templates/movimentacoes/partials/linha_movimentacao.html (`|date:"d/m/Y H:i"`, `#0001 Nome`, selo do tipo via componente da 001, `+`/`−` e saldos em mono tabular à direita)
- [ ] T037 [US3] Implementar `lista_movimentacoes` em apps/movimentacoes/views.py: `require_GET`; `Paginator(qs, ITENS_POR_PAGINA).get_page(request.GET.get("page"))`; querystring dos filtros preservada; parcial quando `HX-Target: resultados` (contracts/rotas-movimentacoes.md §1)
- [ ] T038 [US3] Adicionar a inclusion tag `historico_produto(produto, oob=False)` em apps/movimentacoes/templatetags/movimentacoes_tags.py e o template apps/movimentacoes/templates/movimentacoes/partials/historico_produto.html (`<section id="produto-<id>-historico">`, linhas de `linha_movimentacao.html` sem coluna produto, link "Ver histórico completo", estado vazio)
- [ ] T039 [US3] Incluir `{% historico_produto produto %}` em apps/produtos/templates/produtos/detalhe.html e `{% historico_produto produto oob=True %}` no ramo `detalhe` de apps/movimentacoes/templates/movimentacoes/partials/sucesso_dialogo.html

**Checkpoint**: livro-razão consultável; detalhe do produto com histórico

---

## Phase 6: User Story 4 - Saldo inicial registrado como primeira movimentação (Priority: P2)

**Goal**: `cadastrar_produto` gera `INICIAL` na mesma transação; carga retroativa; invariante saldo = Σ movimentações auditável

**Independent Test**: cadastrar "Parafuso" com Quantidade Inicial 10 → histórico com exatamente um "Saldo inicial" 0 → 10; `auditar_saldos() == []`

### Tests for User Story 4 ⚠️

- [ ] T040 [P] [US4] Testes em apps/movimentacoes/tests/test_saldo_inicial.py: `cadastrar_produto` com Quantidade Inicial 10 cria exatamente uma movimentação `INICIAL` 0 → 10 e saldo 10 (FR-027); com 0 cria `INICIAL` 0 → 0 (FR-027); falha forçada no registro do `INICIAL` não deixa produto nem movimentação gravados (FR-027); `registrar_movimentacao(tipo=INICIAL)` em produto com histórico ou saldo > 0 levanta `MovimentacaoInvalidaError` "Saldo inicial já registrado para #0001." (FR-028); "Saldo inicial" nunca aparece nas opções de tipo do formulário (FR-007, FR-028)
- [ ] T041 [P] [US4] Teste da migração em apps/movimentacoes/tests/test_migracao_saldo_inicial.py (`django_db(transaction=True)`, `MigrationExecutor`): com produtos criados no estado `0001_initial` (modelos históricos), migrar para `0002_saldo_inicial_retroativo` cria `INICIAL` com `quantidade = quantidade_atual` (inclusive 0), `saldo_anterior = 0` e `criado_em = produto.criado_em`, sem alterar saldos, e não toca produtos que já têm histórico (FR-030)
- [ ] T042 [P] [US4] Testes do invariante em apps/movimentacoes/tests/test_invariante.py: após sequência pseudoaleatória (semente fixa) de cadastros, Entradas, Saídas e recusas, `auditar_saldos() == []`, saldo = Σ(INICIAL + ENTRADA) − Σ(SAIDA), continuidade anterior/posterior em ordem de registro e `INICIAL` único e primeiro (FR-028, FR-029, SC-004); `auditar_saldos()` aponta divergência fabricada com `Produto.objects.filter(pk=…).update(quantidade_atual=…)` com motivo `"soma"`

### Implementation for User Story 4

- [ ] T043 [US4] Estender `registrar_movimentacao` em apps/movimentacoes/services.py para `tipo=INICIAL`: quantidade `0..SALDO_MAXIMO`, aceito só se o produto não tiver movimentações e estiver com saldo 0
- [ ] T044 [US4] Estender `cadastrar_produto` em apps/produtos/services.py: criar o `Produto` com `quantidade_atual=0` e, no mesmo `transaction.atomic()`, chamar `registrar_movimentacao(produto_id=produto.pk, tipo=TipoMovimentacao.INICIAL, quantidade=quantidade_inicial)`; `produto.refresh_from_db()` antes de retornar
- [ ] T045 [US4] Criar apps/movimentacoes/migrations/0002_saldo_inicial_retroativo.py: `RunPython` com `apps.get_model`, criando para cada produto sem movimentações `INICIAL(quantidade=quantidade_atual, saldo_anterior=0, saldo_posterior=quantidade_atual, criado_em=produto.criado_em)`; `reverse_code=migrations.RunPython.noop`
- [ ] T046 [US4] Implementar `DivergenciaSaldo` (`NamedTuple`: `produto_id`, `saldo_atual`, `saldo_calculado`, `motivo` em `"soma" | "continuidade" | "inicial"`) e `auditar_saldos()` em apps/movimentacoes/selectors.py

**Checkpoint**: todo saldo explicado pelo histórico desde o cadastro

---

## Phase 7: User Story 5 - Movimentar pelo terminal (Priority: P3)

**Goal**: paridade de console com `python manage.py movimentar`

**Independent Test**: `movimentar 1 saida 3 --obs "Venda balcão"` → "Saída registrada: #0001 … — saldo 10 → 7"; `movimentar 1 saida 50` → `CommandError` com código 1 e nada gravado

### Tests for User Story 5 ⚠️

- [ ] T047 [P] [US5] Testes em apps/movimentacoes/tests/test_comando_movimentar.py com `call_command`: `movimentar 1 entrada 5` imprime "Entrada registrada: #0001 Parafuso — saldo 10 → 15" (FR-031); aceita `#0001`, `SAIDA` e `saída`; saldo insuficiente → `CommandError` "Saldo insuficiente: disponível 7, solicitado 50" sem gravação (FR-031, FR-004); produto inexistente, tipo `inicial`/inválido, quantidade "2,5"/"0" e `--obs` com mais de 200 caracteres → `CommandError` sem gravação (FR-031, FR-005, FR-006)

### Implementation for User Story 5

- [ ] T048 [US5] Implementar apps/movimentacoes/management/commands/movimentar.py: argumentos `produto` (`12`, `#12`, `#0012`), `tipo` (`entrada|saida`, sem diferenciar maiúsculas/acentos), `quantidade` (mesma validação do `QuantidadeField`) e `--obs`; `MovimentacaoError` → `CommandError`; sucesso → `self.stdout.write(self.style.SUCCESS(mov.mensagem_confirmacao))` (contracts/comando-movimentar.md)

**Checkpoint**: todas as histórias funcionais

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T049 [P] Adicionar à navegação de templates/base.html o item "Movimentações" (`movimentacoes:lista`) e o atalho "Nova movimentação" (`movimentacoes:nova`), se a 001 ainda não os tiver
- [ ] T050 [P] Teste de desempenho em apps/movimentacoes/tests/test_desempenho.py (`@pytest.mark.postgres`, pulado fora do PostgreSQL): com 100.000 movimentações consistentes criadas por `bulk_create`, a primeira página de `/movimentacoes/` (sem filtro e filtrada por produto) responde em < 1 s e com no máximo 5 consultas (`django_assert_max_num_queries`) (SC-007)
- [ ] T051 Revisar os templates de apps/movimentacoes/templates/movimentacoes/ contra o design system: só tokens/componentes da 001 (nenhuma cor/espaço literal), números em mono tabular à direita, selo sempre com texto, foco visível, contraste AA, `aria-live`/`role="alert"` nas mensagens (constituição IV, FR-032, FR-033)
- [ ] T052 Verificar a rastreabilidade FR → teste: `grep -rhoE "FR-0[0-9]{2}" apps/movimentacoes/tests | sort -u` deve listar FR-001 a FR-033 (constituição III)
- [ ] T053 Rodar os quality gates: `ruff check .`, `ruff format --check .`, `python manage.py makemigrations --check --dry-run`, `pytest` (SQLite) e `docker compose exec web pytest` (PostgreSQL, incluindo `-m postgres`) com `--cov=apps.movimentacoes.services --cov=apps.movimentacoes.models --cov=apps.movimentacoes.selectors --cov-fail-under=90`
- [ ] T054 Executar os cenários de specs/003-movimentacao-estoque/quickstart.md (manuais, terminal e `auditar_saldos()`), registrando as medições de SC-001 e SC-005

---

## Cobertura FR → tarefas de teste

| FR | Testes | FR | Testes | FR | Testes |
|----|--------|----|--------|----|--------|
| FR-001 | T012 | FR-012 | T015, T016 | FR-023 | T030, T031, T032 |
| FR-002 | T011 | FR-013 | T021, T022 | FR-024 | T032 |
| FR-003 | T011 | FR-014 | T015, T022 | FR-025 | T030, T033 |
| FR-004 | T011, T014, T015, T047 | FR-015 | T023, T033 | FR-026 | T031, T032 |
| FR-005 | T011, T014, T047 | FR-016 | T007, T015, T016, T023 | FR-027 | T040 |
| FR-006 | T011, T014, T047 | FR-017 | T016, T023 | FR-028 | T040, T042 |
| FR-007 | T011, T014, T040 | FR-018 | T015, T016, T023 | FR-029 | T042 |
| FR-008 | T012, T013 | FR-019 | T015 | FR-030 | T041 |
| FR-009 | T007, T014 | FR-020 | T016 | FR-031 | T047 |
| FR-010 | T007, T011 | FR-021 | T008, T032 | FR-032 | T016, T021, T022 |
| FR-011 | T012 | FR-022 | T030, T032 | FR-033 | T007, T011, T032 |

Critérios de sucesso: SC-002 (T011), SC-003 (T013), SC-004 (T042), SC-006 (T008, T032),
SC-007 (T050), SC-008 (T015 + quickstart), SC-001/SC-005 (T054, medição manual).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: requer as features 001 e 002 implementadas em `develop`
- **Foundational (Phase 2)**: depende do Setup — BLOQUEIA todas as histórias
- **US1 (Phase 3)**: depende da Fase 2; é o MVP e fornece o serviço usado por todas as demais
- **US2, US3, US4, US5 (Fases 4–7)**: dependem da US1; podem seguir em paralelo entre si
- **Polish (Phase 8)**: depois das histórias desejadas

### User Story Dependencies

- **US1 (P1)**: só da Fase 2
- **US2 (P2)**: do serviço, do formulário e da view da US1 (`form_movimentacao.html`, `nova_movimentacao`)
- **US3 (P2)**: do serviço da US1 (dados de teste); T039 integra com `sucesso_dialogo.html` da US2 — se a US2 ainda não existir, fica só a inclusão no detalhe
- **US4 (P2)**: do serviço da US1 (estende-o com `INICIAL`); afeta as fixtures (todo produto passa a ter `INICIAL`)
- **US5 (P3)**: do serviço da US1 e do `QuantidadeField` (T018)

### Within Each User Story

- Testes primeiro, falhando (Red) → modelo/serviço/seletor → formulário → templates → view (Green) → refatorar
- Tarefas no mesmo arquivo são sequenciais (sem `[P]`)

### Parallel Opportunities

- Setup: T005 e T006
- US1: T011, T013, T014 e T015 em paralelo (arquivos distintos); T012 após T011, T016 após T015
- US2: T021 e T022; depois T024, T025 e T026
- US3: T030, T031 e T032; depois T036 em paralelo com T034/T035
- US4: T040, T041 e T042
- Após a US1, as histórias US2…US5 podem ser feitas por pessoas diferentes

---

## Parallel Example: User Story 1

```bash
# Testes da US1 (arquivos diferentes), escritos juntos e falhando:
Task: "T011 Testes do serviço em apps/movimentacoes/tests/test_services.py"
Task: "T013 Testes de concorrência em apps/movimentacoes/tests/test_concorrencia.py"
Task: "T014 Testes do formulário em apps/movimentacoes/tests/test_forms.py"
Task: "T015 Testes da variante comum em apps/movimentacoes/tests/test_views_nova.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Fase 1 (Setup) → Fase 2 (modelo e restrições)
2. Fase 3 (US1): serviço + página com as três camadas
3. **PARAR e VALIDAR**: US1 sozinha (inclusive `pytest -m postgres` no Compose)
4. Demonstrar: entrada, saída, zerar, recusa — item 2 da atividade atendido

### Incremental Delivery

1. Setup + Fundação → base pronta
2. US1 → MVP (item 2 da atividade)
3. US2 → ações rápidas e atualização imediata
4. US3 → livro-razão consultável
5. US4 → saldo inicial e auditoria completa
6. US5 → paridade de terminal
7. Polish → gates de qualidade e quickstart

---

## Notes

- [P] = arquivos diferentes, sem dependências
- [Story] mapeia a tarefa à história para rastreabilidade
- Todo teste cita o FR no nome ou docstring (ex.: `test_fr004_saida_maior_que_saldo_bloqueia`)
- Fixtures criam produtos só por `cadastrar_produto` (nunca gravando `quantidade_atual`)
- Commit após cada tarefa ou grupo lógico (Conventional Commits em português)
