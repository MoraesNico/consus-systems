---

description: "Lista de tarefas da feature 004 — Alerta de Reposição"
---

# Tasks: Alerta de Reposição — varredura, relatório, contador automático e painel

**Input**: Design documents from `/specs/004-alerta-reposicao/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (consultas-e-regras,
http-alertas, http-painel, fragmentos-e-eventos, cli), quickstart.md

**Tests**: OBRIGATÓRIOS (constituição, princípio III — testes primeiro). Toda tarefa de teste cita
os FR/SC que cobre; cada teste deve citar o FR no nome ou docstring (ex.:
`test_fr002_quantidade_igual_ao_minimo_entra_em_alerta`) e falhar antes da implementação.

**Organization**: tarefas agrupadas por história de usuário (US1…US6 da spec), precedidas de
Setup e Fundação (a regra de alerta, que bloqueia todas as histórias).

**Pré-condição de execução**: features 001, 002 e 003 integradas em `develop` (ordem do contrato
001 → 002 → 003 → 004).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história a que a tarefa pertence (US1…US6)
- Caminhos conforme `docs/arquitetura.md` e [plan.md](plan.md#project-structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: criar o app `alertas` e ligá-lo ao projeto.

- [ ] T001 Criar o pacote do app com `apps/alertas/__init__.py`, `apps/alertas/apps.py` (`AlertasConfig`, `name="apps.alertas"`, `verbose_name="Alertas"`), `apps/alertas/urls.py` (`app_name = "alertas"`, `urlpatterns = []`), `apps/alertas/templatetags/__init__.py`, `apps/alertas/management/__init__.py`, `apps/alertas/management/commands/__init__.py` e `apps/alertas/tests/__init__.py` — sem `models.py`/`services.py`/`forms.py` (plan.md §Complexity Tracking)
- [ ] T002 Estender config/settings.py registrando `"apps.alertas"` em `INSTALLED_APPS` e definindo `ALERTAS_INTERVALO_SEGUNDOS` lido do ambiente (padrão 30, mínimo 5, valor inválido → 30); estender .env.example com `ALERTAS_INTERVALO_SEGUNDOS=30` comentado (research R15)
- [ ] T003 Estender config/urls.py com `path("alertas/", include("apps.alertas.urls"))`
- [ ] T004 [P] Criar fixtures em apps/alertas/tests/conftest.py: `criar_produto(nome, quantidade, minimo)` via `produtos.services.cadastrar_produto(nome=…, quantidade_inicial=…, estoque_minimo=…)`; `movimentar(produto, tipo, quantidade)` via `movimentacoes.services.registrar_movimentacao`; cabeçalhos `htmx` (`HTTP_HX_REQUEST="true"`) e `boosted` (`HTTP_HX_REQUEST` + `HTTP_HX_BOOSTED="true"`); fixture `agora` (aware, `America/Sao_Paulo`, 20/10/2026 14:32) que também fixa `timezone.now` usado por `apps.alertas.selectors` via `monkeypatch` (as views chamam `varrer()`/`resumo_painel()` sem `agora`) e aceita outro instante quando o teste precisar
- [ ] T005 [P] Conferir em `develop` os nomes de que a 004 depende (contrato `docs/arquitetura.md` v1.1) — 001: contêiner `#badge-alertas` em `templates/components/navegacao.html`, `#anuncio-alertas` e `#dialogo` em `templates/base.html`, helpers `apps.core.htmx` (`eh_fragmento`, `disparar_evento`, `disparar_toast`), `components/kpi.html`, `components/badge_estoque.html`, `components/barra_progresso.html` (com `sufixo`), `components/estado_vazio.html`, classe `.contador-alertas`, ícones `triangle-alert`/`octagon-x`/`circle-check`, classe `visualmente-oculto`, vocabulário de `toast.nivel` (`sucesso|info|alerta|erro`); 002: `produtos/partials/situacao.html` (já com SEM ESTOQUE), `ProdutoQuerySet.com_situacao()` anotando `alerta`, `Produto.em_alerta`/`codigo`, `QUANTIDADE_MAXIMA`, `cadastrar_produto`, `editar_produto`; 003: `Movimentacao.mensagem_confirmacao`, `origem=alertas` e `quantidade` em `movimentacoes:nova`, `partials/sucesso_dialogo.html`, comando `movimentar`, `auditar_saldos` — e registrar divergências em specs/004-alerta-reposicao/research.md

**Checkpoint**: `python manage.py check` sem erros com o app instalado.

---

## Phase 2: Foundational (Blocking Prerequisites) — a regra de alerta

**Purpose**: regra única (SQL + Python), ordenação por criticidade, varredura, serialização CSV e
selo de situação — usados por todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

### Testes da fundação (escrever primeiro e ver falhar)

- [ ] T006 [P] Testes da regra pura em apps/alertas/tests/test_regras.py: `classificar` — 10/10 → `REPOSICAO_NECESSARIA`, 11/10 → `OK`, 0/0 e 0/8 → `SEM_ESTOQUE`, 9/10 → `REPOSICAO_NECESSARIA` (FR-002, FR-003); `deficit` e `cobertura_percentual` com a tabela-verdade de data-model.md §3, incluindo 999/1.000 → 99, 3/0 → `None`, 0/0 → 0 (FR-004); `sugestao_reposicao` — 4/10 → 16, 10/10 → 10, 0/0 → 1, 11/10 → `None`, 2.147.483.647/2.147.483.647 → 0 (FR-005); propriedade "atual + sugestão ⇒ `OK`" para todo mínimo < 1.073.741.824 numa grade de valores (FR-005, SC-008); `Situacao.rotulo` ("OK", "REPOSIÇÃO NECESSÁRIA", "SEM ESTOQUE"), `.gravidade` (0, 1, 2) e `.variante` ("ok", "reposicao", "sem_estoque" — vocabulário de `badge_estoque`/`barra_progresso` da 001) (FR-003, FR-024)
- [ ] T007 [P] Testes do queryset em apps/produtos/tests/test_queryset_situacao.py: `em_alerta()` inclui quantidade = mínimo e 0/0 e exclui mínimo + 1 (FR-002); `com_situacao()` anota `alerta`, `deficit` e `cobertura_percentual` sem filtrar nem reordenar (FR-001, FR-004); quantidade e mínimo 2.147.483.647 e quantidade 30.000.000 com mínimo 1 não levantam `integer out of range` (research R2 — roda também no PostgreSQL); a situação muda após `registrar_movimentacao` e após `editar_produto` alterar o mínimo, sem nenhum campo de situação persistido (FR-001); `Produto` não define atributos `alerta`, `deficit` nem `cobertura_percentual` (proibidos pelo contrato v1.1 por colidirem com as anotações)
- [ ] T008 [P] Teste de equivalência em apps/alertas/tests/test_equivalencia_regra.py: para a grade quantidade 0…6 × mínimo 0…6 mais os extremos de T007, as anotações (`alerta`, `deficit`, `cobertura_percentual`, `gravidade`, `sugestao_reposicao`) de `selectors.produtos_por_criticidade(incluir_ok=True)` são iguais às funções de `regras.py` produto a produto (FR-001…FR-005, invariante I-2)
- [ ] T009 [P] Testes da varredura em apps/alertas/tests/test_selectors_varredura.py: ordem `gravidade DESC, deficit DESC, cobertura_percentual ASC NULLS LAST, id ASC` com empates resolvidos pelo menor ID e duas varreduras idênticas (FR-006); `varrer(agora=…)` devolve só itens em alerta como `Produto` com `situacao_estoque`, `executada_em == agora`, `total_analisado`, `total_em_alerta`, `total_sem_estoque` coerentes com os itens e com `em_alerta().count()` (FR-008, I-4); `incluir_ok=True` põe os OK no fim por cobertura (FR-030); `sem_produtos`/`sem_alertas` (FR-010); nada gravado — contagens de `Produto`/`Movimentacao` inalteradas (FR-008, FR-037); `total_em_alerta()` inclui SEM ESTOQUE (FR-003); orçamentos `django_assert_max_num_queries(2)` para `varrer` e `(1)` para `total_em_alerta`
- [ ] T010 [P] Testes do CSV em apps/alertas/tests/test_exportacao.py: cabeçalho exatamente `ID;Produto;Quantidade atual;Estoque mínimo;Déficit;Cobertura (%);Sugestão de reposição;Situação`, separador `;`, fim de linha `\r\n`, BOM `﻿` só com `bom=True`, ID `#0001`, inteiros sem separador de milhar (`1500`), cobertura e sugestão vazias quando `None`, situação pelo rótulo, nome com `;`, aspas e acentos íntegro em uma célula (FR-032); nomes iniciados por `=`, `+`, `-`, `@`, TAB ou CR recebem `'` inicial (FR-033); resultado sem alertas → só o cabeçalho; `nome_arquivo_csv` → `reposicao-20261020-1432.csv` no fuso local (FR-032)
- [ ] T011 [P] Testes do selo em apps/alertas/tests/test_selo_produtos.py renderizando `produtos/partials/situacao.html` (da 002, sem alterá-lo): quantidade 0 (com mínimo 0 e com mínimo 5) → selo composto com **ambos** "REPOSIÇÃO NECESSÁRIA" e "SEM ESTOQUE", ícones SVG `aria-hidden="true"` (constituição IV); 0 < q ≤ m → "REPOSIÇÃO NECESSÁRIA" com ícone; q > m → "OK" sem cor de alerta (FR-003, FR-018, FR-020, FR-021); a classe/variante emitida coincide com `regras.classificar(...).variante`; funciona com `Produto` anotado e não anotado sem consultas extras (`django_assert_num_queries(0)`)

### Implementação da fundação

- [ ] T012 [P] Implementar apps/alertas/regras.py: `FATOR_ESTOQUE_ALVO = 2`; uso de `QUANTIDADE_MAXIMA` de `apps.produtos.models`; `Situacao` (`StrEnum` com `rotulo`, `gravidade`, `variante` ∈ `ok|reposicao|sem_estoque`); `classificar` (`SEM_ESTOQUE` se `q == 0`; `REPOSICAO_NECESSARIA` se `0 < q ≤ m`; `OK` se `q > m`), `deficit` (`max(m − q, 0)`), `cobertura_percentual` (`0` se `q == 0`; `None` se `m == 0`; senão `q * 100 // m`) e `sugestao_reposicao` (`None` se OK; senão `min(max(2*m − q, 1), QUANTIDADE_MAXIMA − q)`) — contracts/consultas-e-regras.md §2
- [ ] T013 [P] Estender `ProdutoQuerySet.com_situacao()` em apps/produtos/models.py mantendo a anotação `alerta` e `em_alerta()` da 002 e acrescentando, com `q = Cast("quantidade_atual", BigIntegerField())` e `m = Cast("estoque_minimo", BigIntegerField())`: `deficit = Greatest(m − q, 0)` e `cobertura_percentual = Case(When(quantidade_atual=0, then 0), When(estoque_minimo=0, then NULL), default=(q * 100) / m)` (data-model.md §2); não criar propriedades `deficit`/`cobertura_percentual` no modelo
- [ ] T014 Implementar em apps/alertas/selectors.py `produtos_por_criticidade(*, incluir_ok=False)` (anota `gravidade` = 2 se `q = 0`, 1 se `alerta`, senão 0; `sugestao_reposicao` = `Least(Greatest(2·m − q, 1), QUANTIDADE_MAXIMA − q)` se `alerta`, senão `NULL`; ordena por `gravidade DESC, deficit DESC, cobertura_percentual ASC NULLS LAST, id ASC`), `ResultadoVarredura` (dataclass imutável com `executada_em`, `total_analisado`, `total_em_alerta`, `total_sem_estoque`, `itens`, propriedades `sem_produtos`/`sem_alertas`), `varrer(*, incluir_ok=False, agora=None)` (2 consultas; atribui `situacao_estoque = regras.classificar(...)` a cada item) e `total_em_alerta()` (depende de T012, T013)
- [ ] T015 Implementar em apps/alertas/exportacao.py `COLUNAS`, `para_csv(resultado, *, bom)` (`csv.writer` com `delimiter=";"`, `lineterminator="\r\n"`, proteção de fórmula) e `nome_arquivo_csv(resultado)` (`reposicao-AAAAMMDD-HHMM.csv` em hora local) — contracts/consultas-e-regras.md §4 (depende de T014)
- [ ] T016 [P] Conferir (sem editar) que apps/produtos/templates/produtos/partials/situacao.html da 002 já decide `sem_estoque` (quantidade 0) → `reposicao` (`em_alerta`) → `ok` e delega a `components/badge_estoque.html` (contrato v1.1, contracts/fragmentos-e-eventos.md §1); divergência é corrigida na 002 — a 004 não cria CSS de selo

**Checkpoint**: T006–T011 verdes; `pytest apps/alertas apps/produtos/tests/test_queryset_situacao.py` passa em SQLite e PostgreSQL.

---

## Phase 3: User Story 1 - Relatório de reposição sob demanda (Priority: P1) 🎯 MVP

**Goal**: página `/alertas/` que executa a varredura ao abrir e em "Executar varredura", lista só
os produtos em alerta por criticidade, com selo, déficit, cobertura, sugestão e "+ Entrada".

**Independent Test**: com A (5/10), B (10/10), C (11/10), D (0/0) e E (0/8), abrir `/alertas/` e
conferir a ordem E, D, A, B, a ausência de C, os valores e os selos; repetir sem JavaScript.

### Tests for User Story 1 ⚠️

> Escrever primeiro e garantir que falham.

- [ ] T017 [P] [US1] Testes da página completa em apps/alertas/tests/test_views_relatorio.py: GET `/alertas/` sem HTMX → 200 com `alertas/relatorio.html`, título "Relatório de reposição", formulário `method="get"` com `action="/alertas/"` e botão "Executar varredura" (funciona sem scripts — FR-007, FR-013); resumo "Varredura em 20/10/2026 14:32 · 5 produtos analisados · 4 em alerta (2 sem estoque)" com `agora` fixo (FR-008, FR-036); requisição *boosted* e restauração de histórico → página completa (research R8); `POST` → 405; `Cache-Control` com `no-store` e `Vary` com `HX-Request` e `HX-Target`; nenhuma escrita no banco (FR-037)
- [ ] T018 [US1] Testes de conteúdo e ordem em apps/alertas/tests/test_views_relatorio.py (cenários 1–3 da História 1): A e B com "REPOSIÇÃO NECESSÁRIA", C ausente (FR-002, FR-009); D e E com "SEM ESTOQUE" antes dos demais e E antes de D (FR-003, FR-006, SC-002); colunas na ordem ID (`#0001`), Produto, Situação, Atual, Mínimo, Déficit, Cobertura, Sugestão, Ações (FR-009); A mostra déficit 5, cobertura "50%" e sugestão "+15" (FR-004, FR-005); quantidades ≥ 1.000 com separador "." (FR-036); linhas com `id="reposicao-<id>"`
- [ ] T019 [US1] Testes de estados vazios e ação rápida em apps/alertas/tests/test_views_relatorio.py: sem produtos → "Nenhum produto cadastrado" com link para `produtos:novo`; com produtos e nenhum em alerta → "Nenhum produto precisa de reposição" e "N produtos analisados" (FR-010); cada linha tem "+ Entrada" com `href="/movimentacoes/nova/?produto=<id>&tipo=ENTRADA&quantidade=<sugestão>"` (sugestão 2.000.000 → `quantidade=1000000`; sugestão 0 → sem `quantidade`; produto com pk 1234 → `produto=1234`, nunca `1.234`), `hx-get` com `origem=alertas`, `hx-target="#dialogo"` e `aria-label="Registrar entrada de #0003 …"` (FR-011, FR-021)
- [ ] T020 [US1] Testes da variante HTMX em apps/alertas/tests/test_views_relatorio.py: GET com `HX-Request` (não *boosted*) → 200 só com `alertas/partials/relatorio.html` (`<section id="relatorio">` com `hx-get="/alertas/"`, `hx-trigger="estoque-alterado from:body"`, `hx-swap="outerHTML"`) (FR-012) e OOB `<div id="anuncio-alertas" hx-swap-oob="innerHTML">` "Varredura concluída: 4 produtos em alerta (2 sem estoque) de 5 analisados." (FR-008); o botão tem `hx-get`, `hx-target="#relatorio"` e `hx-disabled-elt` (FR-007); duas requisições com `agora` diferentes mostram horários diferentes (FR-007, FR-008); `django_assert_max_num_queries(3)` (SC-005)
- [ ] T021 [P] [US1] Testes de integração com a 003 em apps/alertas/tests/test_integracao_movimentacoes.py: GET HTMX `/movimentacoes/nova/?produto=<id>&tipo=ENTRADA&quantidade=<sugestão>&origem=alertas` abre o diálogo com produto e tipo Entrada pré-selecionados e a quantidade pré-preenchida; POST HTMX com `origem=alertas` → 200, `HX-Reswap: none`, corpo sem `produto-<id>` e `HX-Trigger` com `estoque-alterado`, `toast` e `fechar-dialogo` (FR-011); depois de registrar como entrada a sugestão de A, o fragmento do relatório não lista mais A (FR-012, SC-008)
- [ ] T022 [P] [US1] Testes da cobertura em apps/alertas/tests/test_templatetags.py: a coluna Cobertura de `alertas/partials/linha_reposicao.html` com `cobertura_percentual=None` → "—" sem barra; 40 → `components/barra_progresso.html` (001) com `role="meter"`, `aria-valuenow="40"`, `aria-valuemax="100"` e texto "40%"; 150 → barra cheia e texto "150%"; tom igual a `situacao_estoque.variante` (FR-004, FR-009, FR-024); nenhum template novo em `templates/components/` (constituição IV)

### Implementation for User Story 1

- [ ] T023 [P] [US1] Criar apps/alertas/templatetags/alertas_tags.py (biblioteca `register = template.Library()`, preenchida por T036 e T044) — a cobertura do relatório usa `components/barra_progresso.html` da 001 diretamente em T026 (`valor`, `maximo=100`, `sufixo="%"`, `tom`), sem componente nem CSS novos (contracts/fragmentos-e-eventos.md §3)
- [ ] T024 [P] [US1] Teste em apps/alertas/tests/test_views_relatorio.py: com a rota registrada, o item "Alertas" da navegação da 001 vira link para `/alertas/` e fica ativo em `/alertas/`; `base.html` contém `#anuncio-alertas` (`role="status"`, `aria-live="polite"`) — **sem editar** templates/base.html (ambos entregues pela 001)
- [ ] T025 [P] [US1] Conferir (sem editar) que a 003 já aceita `origem=alertas` (campo oculto em apps/movimentacoes/forms.py e ramo sem OOB em apps/movimentacoes/templates/movimentacoes/partials/sucesso_dialogo.html) e o parâmetro `quantidade` em `movimentacoes:nova` (contrato v1.1); divergência é corrigida na 003 — coberto pelos testes T021
- [ ] T026 [US1] Criar apps/alertas/templates/alertas/partials/relatorio.html (`<section id="relatorio" …>`, resumo, estados vazios, tabela densa com `<caption>` visualmente oculta e `<th scope="col">`), apps/alertas/templates/alertas/partials/linha_reposicao.html (`<tr id="reposicao-{{ produto.pk|unlocalize }}">`, selo via `{% include "produtos/partials/situacao.html" %}`, números `|intcomma` em `.num`, cobertura via `components/barra_progresso.html`, "+ Entrada" com `origem=alertas` e `quantidade`) e apps/alertas/templates/alertas/partials/anuncio.html (`hx-swap-oob="innerHTML"`) — contracts/http-alertas.md (depende de T023)
- [ ] T027 [US1] Criar apps/alertas/templates/alertas/relatorio.html estendendo `base.html` com título, formulário GET "Executar varredura" (`hx-get="/alertas/"`, `hx-target="#relatorio"`, `hx-swap="outerHTML"`, `hx-disabled-elt="find button"`) e `{% include "alertas/partials/relatorio.html" %}` (depende de T026)
- [ ] T028 [US1] Implementar a view `relatorio` em apps/alertas/views.py (`require_GET`, `never_cache`, `vary_on_headers("HX-Request", "HX-Target")`; `resultado = selectors.varrer()`; fragmento + OOB do anúncio só se `apps.core.htmx.eh_fragmento(request)`, senão página completa) e a rota `path("", views.relatorio, name="relatorio")` em apps/alertas/urls.py (depende de T014, T027)

**Checkpoint**: História 1 funcional e testável sozinha (MVP do item 3 da atividade).

---

## Phase 4: User Story 2 - Alerta automático em toda a interface (Priority: P2)

**Goal**: contador no menu com polling + evento, anúncio acessível só na mudança, selo SEM ESTOQUE
nas telas da 002 e aviso de reposição na confirmação da movimentação.

**Independent Test**: em qualquer página, registrar uma saída que leve um produto ao mínimo e ver
contador, selo e toast mudarem; alterar o estoque pelo terminal e ver o contador mudar sozinho.

### Tests for User Story 2 ⚠️

- [ ] T029 [P] [US2] Testes do contador em apps/alertas/tests/test_views_contador.py: GET sem `anterior` → 200 com `<span id="contador-alertas">`, `hx-get="/alertas/contador/?anterior=N"`, `hx-trigger="every 30s, estoque-alterado from:body"` e `hx-swap="outerHTML"`, com ícone + número + texto acessível "produto(s) em alerta de reposição" (FR-014, FR-016, FR-021); `override_settings(ALERTAS_INTERVALO_SEGUNDOS=10)` → `every 10s`; total 0 → elemento sem conteúdo e com atributo `hidden` (FR-016); conta igual ao mínimo e SEM ESTOQUE, não conta mínimo + 1 (FR-002, FR-003); `anterior` igual ao total → 204 sem corpo; diferente → 200 + OOB `#anuncio-alertas` "Alertas de reposição: 4 produtos (antes 3)." (FR-017); `anterior` vazio, negativo ou não numérico → 200 sem anúncio; a mesma resposta com e sem `HX-Request` (constituição III — duas variantes); `POST` → 405; `django_assert_num_queries(1)` (SC-005)
- [ ] T030 [P] [US2] Testes da tag do contador em apps/alertas/tests/test_templatetags.py: `#contador-alertas` aparece **dentro** de `#badge-alertas` no menu de `produtos:lista` e de `core:painel` renderizados sem HTMX com o total do momento do carregamento (FR-014) e com o intervalo de `ALERTAS_INTERVALO_SEGUNDOS`; `#badge-alertas` continua sem atributos `hx-*`; com urlconf sem `alertas:contador` a tag não renderiza nada (os testes da 001 com `urls_somente_core` continuam válidos)
- [ ] T031 [P] [US2] Testes de transição em apps/alertas/tests/test_transicoes.py: `transicao` para todos os pares da tabela de data-model.md §3 (OK→REPOSIÇÃO, OK→SEM ESTOQUE, REPOSIÇÃO→SEM ESTOQUE = `PIOROU`; →OK = `SAIU_DO_ALERTA`; SEM ESTOQUE→REPOSIÇÃO e inalterada = `NENHUMA`) (FR-019); `aviso_movimentacao` com os textos exatos "REPOSIÇÃO NECESSÁRIA: #0003 Parafuso M6 ficou com 10 un. (mínimo 10).", "REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: #0003 Parafuso M6 zerou (mínimo 5).", "#0003 Parafuso M6 saiu do alerta de reposição." e `None` para `INICIAL`; `confirmacao_com_alerta` = `mensagem_confirmacao` da 003 + ". " + aviso, nível `alerta` só quando piora; com nome de 120 caracteres e saldos de 10 dígitos, `len(texto) <= 200`, com "…" no nome e `#ID` preservado, e `disparar_toast` não levanta `ValueError` (FR-019)
- [ ] T032 [P] [US2] Testes de integração do aviso em apps/alertas/tests/test_integracao_movimentacoes.py: POST HTMX de Saída 11 → 10 (mínimo 10) → `HX-Trigger.toast == {"nivel": "alerta", "texto": "Saída registrada: … — saldo 11 → 10. REPOSIÇÃO NECESSÁRIA: …"}` e `estoque-alterado` presente; Saída 3 → 0 (mínimo 5) → "REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: … zerou"; Entrada que tira do alerta → nível `sucesso` + "saiu do alerta de reposição"; Entrada 2 → 5 (mínimo 10) → texto da 003 intacto (FR-019, cenários 1–4 da História 2); fluxo sem HTMX → mensagem do framework `messages` com nível `WARNING` e o mesmo texto; comando `movimentar` imprime o aviso (FR-019)
- [ ] T033 [P] [US2] Testes nas telas da 002 em apps/alertas/tests/test_selo_produtos.py: `produtos:lista` e `produtos:detalhe` mostram "SEM ESTOQUE" (0/5), "REPOSIÇÃO NECESSÁRIA" (5/5) e "OK" (6/5) com o mesmo texto/ícone/variante do relatório (FR-018, FR-020); após saída que zera um produto pela lista, a linha re-renderizada pela 003 mostra "SEM ESTOQUE" (FR-018)
- [ ] T034 [P] [US2] Teste em apps/alertas/tests/test_views_relatorio.py: o fragmento HTMX do relatório inclui `#contador-alertas` com `hx-swap-oob="true"` e o mesmo total da varredura exibida (FR-015)

### Implementation for User Story 2

- [ ] T035 [P] [US2] Acrescentar `Transicao`, `Aviso` (dataclass imutável `nivel`, `texto`), `transicao(saldo_anterior, saldo_posterior, minimo)`, `aviso_movimentacao(movimentacao)` e `confirmacao_com_alerta(movimentacao)` em apps/alertas/regras.py (contracts/consultas-e-regras.md §2; data-model.md §3)
- [ ] T036 [P] [US2] Criar apps/alertas/templates/alertas/partials/contador.html (contracts/http-alertas.md: `id="contador-alertas"`, `class="contador-alertas"` — estilo da 001 —, `hx-get` com `anterior`, `hx-trigger` com o intervalo, `hx-swap="outerHTML"`, `hx-swap-oob` opcional, ícone `triangle-alert` `aria-hidden`, texto visualmente oculto) e a *inclusion tag* `contador_alertas` em apps/alertas/templatetags/alertas_tags.py (não renderiza nada se `alertas:contador` não resolver)
- [ ] T037 [US2] Implementar a view `contador` em apps/alertas/views.py (`require_GET`, `never_cache`; `anterior` válido e igual → `HttpResponse(status=204)`; diferente → fragmento + `alertas/partials/anuncio.html`; ausente/inválido → só o fragmento) e a rota `path("contador/", views.contador, name="contador")` em apps/alertas/urls.py (depende de T036)
- [ ] T038 [US2] Estender templates/components/navegacao.html (001) inserindo `{% load alertas_tags %}{% contador_alertas %}` **dentro** do contêiner `<span id="badge-alertas" class="navegacao__badge">` do item "Alertas", sem acrescentar atributos ao contêiner (mecanismo único do contrato v1.1; depende de T036)
- [ ] T039 [US2] Incluir no fragmento do relatório o OOB do contador (`alertas/partials/contador.html` com `oob=True` e o total da varredura) em apps/alertas/templates/alertas/partials/relatorio.html e no contexto da view em apps/alertas/views.py (depende de T028, T036, T037)
- [ ] T040 [US2] Estender a view `nova_movimentacao` em apps/movimentacoes/views.py com `confirmacao_com_alerta(mov)` (HTMX: `disparar_toast(response, aviso.nivel, aviso.texto)`; sem HTMX: `messages.add_message` com `WARNING` quando `nivel == "alerta"`, senão `SUCCESS`) e no comando apps/movimentacoes/management/commands/movimentar.py (aviso em `style.WARNING`) — contracts/fragmentos-e-eventos.md §6 (depende de T035)

**Checkpoint**: Histórias 1 e 2 funcionam de forma independente; o item 3 da atividade está
coberto nas duas formas ("relatório" e "varredura automática").

---

## Phase 5: User Story 3 - Painel de controle (Priority: P3)

**Goal**: `/` com 4 KPIs, "Reposição necessária" (top 5), cobertura (BarList, 8) e últimas 5
movimentações, atualizando com `estoque-alterado`.

**Independent Test**: com o cenário 1 da História 3, abrir `/` e conferir KPIs e listas; registrar
uma movimentação por um "+ Entrada" do painel e ver tudo mudar sem recarregar.

### Tests for User Story 3 ⚠️

- [ ] T041 [P] [US3] Testes de `resumo_painel` em apps/alertas/tests/test_selectors_painel.py: 12 produtos, 1.250 unidades, 4 em alerta (1 sem estoque) e 7 entradas/saídas → KPIs exatos (FR-022); com `agora` = agora + 24 h 1 min o indicador de movimentações é 0 e `INICIAL` nunca conta (FR-022, Assumptions); `criticos` = 5 primeiros da ordem de criticidade (FR-023, FR-006); `cobertura` = 8 menores percentuais, exclui mínimo 0 com saldo > 0, empate pelo menor ID (FR-024); `ultimas_movimentacoes` = 5 mais recentes com produto carregado (FR-025); base vazia → zeros e listas vazias; `django_assert_max_num_queries(5)`
- [ ] T042 [P] [US3] Testes da view em apps/core/tests/test_painel_kpis.py: GET `/` sem HTMX → `core/painel.html` com "PRODUTOS CADASTRADOS 12", "UNIDADES EM ESTOQUE 1.250", "4 · 1 sem estoque", "7" e as três listas (FR-022…FR-025, FR-036); com 7 alertas → 5 itens + "Ver relatório completo (7)" e "+ Entrada" com `origem=alertas` (FR-023); estados vazios — sem alertas "Nenhum produto precisa de reposição.", sem produtos com link para `produtos:novo`, "Nenhuma movimentação registrada.", "Sem produtos com estoque mínimo definido." (FR-023, FR-024, FR-025); HTMX não *boosted* → só `core/partials/painel_kpis.html` com raiz `<section id="painel-kpis">` e `hx-trigger="estoque-alterado from:body"` (FR-026); *boosted* → página completa; `Vary` com `HX-Request` e `HX-Target`; datas `dd/mm/aaaa HH:MM` (FR-036); `django_assert_max_num_queries(7)`

### Implementation for User Story 3

- [ ] T043 [P] [US3] Implementar `ResumoPainel` (dataclass imutável: `total_produtos`, `total_unidades`, `total_em_alerta`, `total_sem_estoque`, `movimentacoes_24h`, `criticos`, `cobertura`, `ultimas_movimentacoes`) e `resumo_painel(*, agora=None)` em apps/alertas/selectors.py — KPIs numa agregação (`Count`, `Coalesce(Sum("quantidade_atual"), 0)`, `Count(filter=…)`), `tipo__in=[ENTRADA, SAIDA]` com `criado_em >= agora − 24 h`, críticos `[:5]`, cobertura não nula `order_by("cobertura_percentual", "id")[:8]`, últimas `select_related("produto").order_by("-criado_em", "-id")[:5]`; itens de `criticos` e `cobertura` recebem `situacao_estoque` (data-model.md §4)
- [ ] T044 [P] [US3] Criar a *inclusion tag* `lista_cobertura(produtos)` em apps/alertas/templatetags/alertas_tags.py e o template apps/alertas/templates/alertas/partials/lista_cobertura.html (`<ul class="pilha">`; por item: link `produto.codigo` + nome para `get_absolute_url()` e `components/barra_progresso.html` da 001 com `valor=cobertura_percentual`, `maximo=100`, `sufixo="%"`, `tom=situacao_estoque.variante`; sem itens: "Sem produtos com estoque mínimo definido.") — sem componente nem CSS novos (contracts/fragmentos-e-eventos.md §3)
- [ ] T045 [US3] Criar apps/core/templates/core/partials/painel_kpis.html (raiz `<section id="painel-kpis">`, nome previsto pela 001) e estender apps/core/templates/core/painel.html para incluí-lo no lugar do estado vazio provisório, conforme contracts/http-painel.md (KPIs com `components/kpi.html`, grade 12 colunas, selo via `produtos/partials/situacao.html`, cobertura via `{% lista_cobertura resumo.cobertura %}`, tabela das últimas movimentações); atualizar apps/core/tests/test_painel.py (001) — manter `<h1>` "Painel", `#painel-kpis` e 405, trocar o estado vazio provisório pelo estado vazio "Cadastre o primeiro produto" (depende de T043, T044)
- [ ] T046 [US3] Estender a view `painel` em apps/core/views.py para usar `alertas.selectors.resumo_painel()` e devolver fragmento só se `apps.core.htmx.eh_fragmento(request)` (`never_cache`, `vary_on_headers("HX-Request", "HX-Target")`) (depende de T045)

**Checkpoint**: painel substitui o placeholder da 001 e reage a movimentações.

---

## Phase 6: User Story 4 - Varredura pelo terminal (Priority: P3)

**Goal**: `python manage.py varrer_estoque` com formatos texto/csv/json, `--todos` e
`--falhar-se-alerta`, com os mesmos dados do relatório web.

**Independent Test**: com 5 produtos (2 em alerta, 1 sem estoque), rodar o comando nos 3 formatos
e com/sem a opção de falha, conferindo conteúdo, ordem e código de saída.

### Tests for User Story 4 ⚠️

- [ ] T047 [P] [US4] Testes de texto e JSON em apps/alertas/tests/test_exportacao.py: `para_texto` — "CONSUS — VARREDURA DE ESTOQUE", "Executada em 20/10/2026 14:32", "Produtos analisados: 5", "Em alerta: 2 (1 sem estoque)", uma linha por item iniciada por "⚠ REPOSIÇÃO NECESSÁRIA" (com "· SEM ESTOQUE" quando zerado), números com separador ".", nome com mais de 40 caracteres encurtado com "…", `simbolo="(!)"`, mensagens "Nenhum produto precisa de reposição." e "Nenhum produto cadastrado." (FR-027, Edge Cases); `para_json` — chaves e tipos de contracts/cli.md, `ensure_ascii=False`, `null` em cobertura/sugestão quando não se aplica, `executada_em` ISO 8601 com deslocamento (FR-028)
- [ ] T048 [P] [US4] Testes do comando em apps/alertas/tests/test_comando_varrer_estoque.py (`call_command` com `StringIO`): saída texto do cenário 1 da História 4 na mesma ordem e com os mesmos totais de `varrer()` (FR-027, SC-006); `--formato csv` igual a `para_csv(..., bom=False)` (FR-028, FR-032); `--formato json` parseável e com os mesmos itens/totais do relatório web (FR-028, SC-006); `--todos` acrescenta os OK no fim marcados "OK" (FR-030); `--falhar-se-alerta` com alerta → `CommandError` com `returncode == 1`, relatório completo no stdout e "Há 2 produto(s) em alerta de reposição." (FR-029); sem alerta e base vazia → sucesso mesmo com a opção (FR-029, Edge Cases); `run_from_argv([... "--formato", "pdf"])` → `SystemExit(2)` (FR-029); `DatabaseError` simulado → `returncode == 2` sem relatório parcial (FR-029); stdout cp1252 → marcador "(!)" mantendo "REPOSIÇÃO NECESSÁRIA" (Edge Cases); `--no-color` sem sequências ANSI; contagens e saldos inalterados após qualquer execução (FR-031)

### Implementation for User Story 4

- [ ] T049 [US4] Implementar `para_texto(resultado, *, simbolo="⚠")` (lista de `(linha, eh_alerta)`) e `para_json(resultado)` em apps/alertas/exportacao.py conforme contracts/cli.md
- [ ] T050 [US4] Implementar apps/alertas/management/commands/varrer_estoque.py: argumentos `--formato {texto,csv,json}` (padrão `texto`), `--todos`, `--falhar-se-alerta`; escolha do marcador pela codificação do stdout; linhas em alerta com `self.style.WARNING`; `DatabaseError` → `CommandError(..., returncode=2)`; com alerta e `--falhar-se-alerta` → `CommandError("Há N produto(s) em alerta de reposição.", returncode=1)` após imprimir (depende de T049)

**Checkpoint**: paridade de terminal com a proposta original de app de console.

---

## Phase 7: User Story 5 - Exportar o relatório em CSV (Priority: P4)

**Goal**: "Exportar CSV" no relatório, com o mesmo conteúdo da tela.

**Independent Test**: com 3 produtos em alerta, baixar o CSV e conferir cabeçalho, linhas, ordem,
BOM e nome do arquivo; abrir numa planilha em pt-BR.

### Tests for User Story 5 ⚠️

- [ ] T051 [P] [US5] Testes em apps/alertas/tests/test_views_exportacao.py: GET `/alertas/?formato=csv` → 200, `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="reposicao-20261020-1432.csv"` e corpo igual a `para_csv(varrer(agora), bom=True)` com as mesmas linhas e ordem da tela (FR-032, SC-006); sem alertas → só o cabeçalho; com `HX-Request` continua CSV; `?formato=pdf` → 400 "Formato não suportado. Use html ou csv."; produto `=1+1` exportado como `'=1+1` (FR-033); a página tem o link "Exportar CSV" com `href="/alertas/?formato=csv"`, `hx-boost="false"` e `download` (research R9)

### Implementation for User Story 5

- [ ] T052 [US5] Tratar o parâmetro `formato` (`html` padrão, `csv`, outro → `HttpResponseBadRequest`) na view `relatorio` em apps/alertas/views.py, devolvendo `HttpResponse(para_csv(resultado, bom=True), content_type="text/csv; charset=utf-8")` com `Content-Disposition` de `nome_arquivo_csv` (contracts/http-alertas.md)
- [ ] T053 [US5] Acrescentar o link secundário "Exportar CSV" (`hx-boost="false"`, `download`) ao lado de "Executar varredura" em apps/alertas/templates/alertas/relatorio.html

**Checkpoint**: exportação concorda com a tela e com o terminal.

---

## Phase 8: User Story 6 - Dados de demonstração (Priority: P4)

**Goal**: `python manage.py popular_demo` idempotente, com os 12 produtos de data-model.md §6.

**Independent Test**: rodar em base vazia, conferir a composição e a varredura; rodar de novo e
conferir que nada mudou.

### Tests for User Story 6 ⚠️

- [ ] T054 [P] [US6] Testes em apps/alertas/tests/test_comando_popular_demo.py: base vazia → 12 produtos com as situações finais de data-model.md §6 (4 em alerta, exatamente 1 sem estoque, "Fita adesiva transparente 48 mm" no mínimo, "Grampeador de mesa 26/6" em mínimo + 1, "Etiqueta adesiva 100x50 (rolo)" com mínimo 0), 16 entradas/saídas e 12 saldos iniciais, saída "12 produto(s) criado(s), 0 já existia(m)" e "Movimentações registradas: 16." (FR-034); `movimentacoes.selectors.auditar_saldos() == []` (todo saldo vem do livro-razão — FR-034, FR-037); segunda execução → "0 produto(s) criado(s), 12 já existia(m)", nenhuma movimentação nova (FR-035, SC-009); produto do usuário "CANETA ESFEROGRÁFICA AZUL" pré-existente não é alterado e conta como existente (FR-035); falha simulada em `registrar_movimentacao` no 3º produto reverte só esse produto e termina com `returncode == 2`, e uma nova execução completa o que faltou (research R14); após a demo, `varrer()` lista Cola branca 90 g → Parafuso sextavado M6 x 20 → Luva de nitrilo (caixa c/ 100) → Fita adesiva transparente 48 mm (SC-009)

### Implementation for User Story 6

- [ ] T055 [US6] Criar apps/alertas/demo.py com `MovimentoDemo`/`ProdutoDemo` (dataclasses imutáveis), `PRODUTOS_DEMO` exatamente como a tabela de data-model.md §6 e `popular() -> tuple[int, int, int]` (criados, existentes, movimentações) — existência por `Produto.objects.filter(nome__iexact=…)`; cada produto novo em `transaction.atomic()` com `cadastrar_produto` + `registrar_movimentacao` na ordem do roteiro
- [ ] T056 [US6] Implementar apps/alertas/management/commands/popular_demo.py chamando `demo.popular()` e imprimindo o resumo de contracts/cli.md; erro de banco ou de movimentação → `CommandError(..., returncode=2)` (depende de T055)

**Checkpoint**: apresentação reproduzível com um comando.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: critérios de sucesso transversais, qualidade e documentação.

- [ ] T057 [P] Teste de concordância entre superfícies em apps/alertas/tests/test_concordancia.py: para os 5 casos de limite (abaixo, igual, mínimo + 1, 0 com mínimo 5, 0 com mínimo 0), relatório HTML, contador, lista de produtos da 002, `varrer_estoque --formato json` e CSV apresentam a mesma situação e os mesmos totais (SC-001, SC-006, FR-020)
- [ ] T058 [P] Teste de acessibilidade estrutural em apps/alertas/tests/test_acessibilidade.py: todo selo/contador de alerta tem ícone com `aria-hidden="true"` **e** texto (nenhuma variante de alerta sem texto — SC-007, FR-021); relatório com `<caption>` e `<th scope="col">`; `base.html` com `#anuncio-alertas` `role="status"` `aria-live="polite"`; ações com `aria-label` (FR-017, FR-021)
- [ ] T059 [P] Teste de volume em apps/alertas/tests/test_desempenho.py: 1.000 produtos criados por `bulk_create` de `Produto` + `Movimentacao(INICIAL)` coerentes (somente *setup* de teste — research R16) → relatório ≤ 3 consultas, contador 1, painel ≤ 7 e `varrer()` com 1.000 itens sem erro (SC-005)
- [ ] T060 [P] Documentar a feature em README.md: relatório `/alertas/`, contador automático e `ALERTAS_INTERVALO_SEGUNDOS`, `varrer_estoque` (formatos, `--todos`, `--falhar-se-alerta`, códigos 0/1/2, exemplo de cron) e `popular_demo`
- [ ] T061 Garantir cobertura ≥ 90% em apps/alertas/selectors.py, apps/alertas/regras.py, apps/alertas/exportacao.py e apps/produtos/models.py com `pytest --cov=apps.alertas --cov=apps.produtos.models --cov-fail-under=90` (constituição III)
- [ ] T062 Rodar os quality gates: `ruff check .`, `ruff format --check .`, `python manage.py makemigrations --check --dry-run` (nenhuma migração na 004), `pytest` em SQLite e em PostgreSQL e `docker compose up --build` — corrigir o que falhar
- [ ] T063 Executar a validação manual de specs/004-alerta-reposicao/quickstart.md (seções 1–7), incluindo teclado, leitor de tela e scripts desativados, e registrar o resultado na descrição do PR
- [ ] T064 [P] Teste ponta a ponta da atividade (SENAI-SP, itens 1–3) em apps/alertas/tests/test_fluxo_atividade.py, só por HTTP e pelos comandos, nas variantes comum e HTMX: (item 1) `POST /produtos/novo/` "Caneta Azul", quantidade inicial 10, mínimo 5 → `#0001` com quantidade 10, encontrado por `?q=1`, `?q=%231` e `?q=%230001`; (item 2) Entrada de 5 → saldo 15; Saída de 10 → saldo 5; Saída de 6 → 422 com "Saldo insuficiente: disponível 5, solicitado 6", saldo 5 e nenhuma movimentação nova; (item 3) com 5 ≤ 5 a lista e o detalhe mostram "REPOSIÇÃO NECESSÁRIA", `/alertas/` lista o produto, `/alertas/contador/` mostra 1 e `varrer_estoque` imprime a linha "⚠ REPOSIÇÃO NECESSÁRIA"; Saída de 5 → selo composto "REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE"; "+ Entrada" do relatório (`origem=alertas`, `quantidade` = sugestão 10) → produto sai do relatório, contador 0; ao fim `auditar_saldos() == []` (rastreabilidade: docs/rastreabilidade.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: requer 001–003 em `develop`; sem outras dependências.
- **Foundational (Phase 2)**: depende do Setup — BLOQUEIA todas as histórias.
- **US1 (P1)**: depende só da Fundação. MVP.
- **US2 (P2)**: depende da Fundação; T039 integra com a view de US1 (T028) — sem US1, pule T034/T039 e a história continua testável (contador, selos, toast).
- **US3 (P3)**: depende da Fundação; usa o "+ Entrada" com `origem=alertas` de US1 (T025) para o fluxo completo.
- **US4 (P3)**: depende da Fundação (usa `para_csv` de T015).
- **US5 (P4)**: depende da Fundação (T015) e da página de US1 (T027/T028).
- **US6 (P4)**: depende só do Setup e dos serviços da 002/003; os testes de ordem usam `varrer()` (T014).
- **Polish (Phase 9)**: depois das histórias desejadas.

### Dentro de cada história

- Testes antes da implementação, falhando (Red → Green → Refactor).
- regras/queryset → selectors → exportação → templates → views → integrações.
- Arquivos compartilhados (`apps/alertas/views.py`, `apps/alertas/templatetags/alertas_tags.py`,
  `templates/components/navegacao.html`, `test_views_relatorio.py`) recebem tarefas em sequência,
  nunca em paralelo. Arquivos de outras features são sempre **estendidos** (nunca recriados) e
  `static/css/components.css`/`templates/base.html` não são alterados pela 004.

### Mapa FR/SC → tarefas de teste

| Requisito | Testes | Requisito | Testes |
|-----------|--------|-----------|--------|
| FR-001 | T007, T008 | FR-020 | T011, T033, T057 |
| FR-002 | T006, T007, T018, T029 | FR-021 | T011, T019, T029, T058 |
| FR-003 | T006, T009, T011, T018, T029 | FR-022 | T041, T042 |
| FR-004 | T006, T007, T008, T018, T022 | FR-023 | T041, T042 |
| FR-005 | T006, T008, T018 | FR-024 | T022, T041, T042 |
| FR-006 | T009, T018, T041 | FR-025 | T041, T042 |
| FR-007 | T017, T020 | FR-026 | T042 |
| FR-008 | T009, T017, T020 | FR-027 | T047, T048 |
| FR-009 | T018, T022 | FR-028 | T047, T048 |
| FR-010 | T009, T019 | FR-029 | T048 |
| FR-011 | T019, T021 | FR-030 | T009, T048 |
| FR-012 | T020, T021 | FR-031 | T048 |
| FR-013 | T017 | FR-032 | T010, T048, T051 |
| FR-014 | T029, T030 | FR-033 | T010, T051 |
| FR-015 | T034 | FR-034 | T054 |
| FR-016 | T029 | FR-035 | T054 |
| FR-017 | T029, T058 | FR-036 | T017, T018, T042 |
| FR-018 | T011, T033 | FR-037 | T009, T017, T054 |
| FR-019 | T031, T032 | Atividade (itens 1–3, ponta a ponta) | T064 |

Critérios de sucesso: SC-001 (T057), SC-002 (T018), SC-003 (T020, T029, T042 — gatilhos
`estoque-alterado`), SC-004 (T029 — `every 30s`), SC-005 (T020, T029, T059), SC-006 (T048, T051,
T057), SC-007 (T058), SC-008 (T006, T021), SC-009 (T054).

### Parallel Opportunities

- Setup: T004 e T005.
- Fundação: testes T006–T011 juntos; depois T012, T013 e T016 juntos; T014 → T015.
- US1: T017, T021 e T022 juntos (T018–T020 seguem T017 no mesmo arquivo); implementação T023, T024 e T025 juntas.
- US2: testes T029–T034 juntos (arquivos distintos); T035 e T036 juntos; depois T037, T038 e T039 em sequência (mesmos arquivos) e T040.
- US3: T041 e T042 juntos; T043 e T044 juntos.
- US4: T047 e T048 juntos.
- Polish: T057–T060 e T064 juntos.
- Após a Fundação, US3, US4 e US6 podem ser feitas em paralelo por pessoas diferentes.

---

## Parallel Example: User Story 1

```bash
# Testes de US1 (arquivos diferentes):
Task: "T017 Testes da página completa em apps/alertas/tests/test_views_relatorio.py"
Task: "T021 Testes de integração com a 003 em apps/alertas/tests/test_integracao_movimentacoes.py"
Task: "T022 Testes do componente de cobertura em apps/alertas/tests/test_templatetags.py"

# Implementação independente de US1:
Task: "T023 alertas_tags.py + cobertura via components/barra_progresso.html (001)"
Task: "T024 Teste do item de menu e da região viva da 001"
Task: "T025 Conferir origem=alertas e quantidade na 003"
```

## Parallel Example: Foundational

```bash
Task: "T006 Testes da regra pura em apps/alertas/tests/test_regras.py"
Task: "T007 Testes do queryset em apps/produtos/tests/test_queryset_situacao.py"
Task: "T008 Teste de equivalência em apps/alertas/tests/test_equivalencia_regra.py"
Task: "T009 Testes da varredura em apps/alertas/tests/test_selectors_varredura.py"
Task: "T010 Testes do CSV em apps/alertas/tests/test_exportacao.py"
Task: "T011 Testes do selo em apps/alertas/tests/test_selo_produtos.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (Setup) → Phase 2 (Fundação: regra, varredura, selo).
2. Phase 3 (US1): relatório com varredura sob demanda — já atende o item 3 da atividade.
3. **PARAR e VALIDAR**: quickstart §3 + testes de US1.

### Incremental Delivery

1. Setup + Fundação → regra testada nos limites em SQLite e PostgreSQL.
2. US1 → relatório (MVP, demonstrável ao professor).
3. US2 → varredura automática (contador, selos, aviso no toast).
4. US3 → painel com KPIs.
5. US4 → paridade de terminal (`varrer_estoque`).
6. US5 → CSV; US6 → `popular_demo` para a apresentação.
7. Polish → concordância, acessibilidade, volume, cobertura, quality gates, merge `--no-ff` em `develop`.

---

## Notes

- [P] = arquivos diferentes, sem dependência de tarefa incompleta.
- Nenhuma tarefa cria migração; `makemigrations --check` deve continuar limpo.
- Nenhuma tarefa altera saldo fora de `registrar_movimentacao` (constituição I); o `bulk_create`
  de T059 é apenas *setup* de teste de volume.
- Commits em Conventional Commits em português, um assunto por commit (ex.:
  `test(004): limites da regra de alerta`, `feat(004): relatório de reposição`).
