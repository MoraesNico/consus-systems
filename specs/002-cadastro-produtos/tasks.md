---

description: "Lista de tarefas para implementar a feature 002 — Cadastro de Produtos"
---

# Tasks: Cadastro de Produtos

**Input**: Design documents from `/specs/002-cadastro-produtos/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: OBRIGATÓRIOS — a constituição (princípio III) exige testes antes da implementação e ao
menos um teste por FR, citado no nome (`test_fr0NN_...`) ou na docstring. Em cada fase, as
tarefas de teste vêm primeiro e DEVEM falhar antes da implementação (Red → Green → Refactor).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- App Django em `apps/produtos/` (contrato `docs/arquitetura.md`): `models.py`, `services.py`,
  `selectors.py`, `forms.py`, `views.py`, `urls.py`, `templates/produtos/`,
  `templates/produtos/partials/`, `tests/`.
- Arquivos compartilhados da 001: `config/settings.py`, `config/urls.py`, `templates/base.html`,
  `static/js/consus.js`, `static/css/components.css` (alterações aditivas).
- Cabeçalhos HTMX nos testes: `client.get(url, headers={"HX-Request": "true", "HX-Target": "resultados"})`
  (parcial) e `headers={"HX-Request": "true", "HX-Boosted": "true"}` (*boosted*).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: criar a app `produtos` e ligá-la ao projeto da 001.

- [ ] T001 Criar o esqueleto da app em apps/produtos/ (`__init__.py`, `apps.py` com `ProdutosConfig(name="apps.produtos", verbose_name="Produtos")`, `migrations/__init__.py`, `tests/__init__.py` e as pastas `templates/produtos/partials/`)
- [ ] T002 Registrar `"apps.produtos"` e `"django.contrib.humanize"` em `INSTALLED_APPS` em config/settings.py (ou no módulo base equivalente definido pela 001)
- [ ] T003 Criar apps/produtos/urls.py com `app_name = "produtos"` e `urlpatterns = []`, e incluir `path("produtos/", include("apps.produtos.urls"))` em config/urls.py
- [ ] T004 [P] Criar apps/produtos/tests/conftest.py com a fixture `produto_factory(**kwargs)` (cria produtos via `apps.produtos.services.cadastrar_produto`, com nome único por padrão) e as fixtures `hx_parcial(alvo)` → `{"HX-Request": "true", "HX-Target": alvo}` e `hx_boosted` → `{"HX-Request": "true", "HX-Boosted": "true"}`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelo `Produto`, restrições de banco e regra de situação — base de todas as histórias.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Testes (escrever primeiro; devem falhar)

- [ ] T005 [P] Escrever os testes do modelo em apps/produtos/tests/test_models.py: `test_fr002_id_automatico_crescente_sem_informar` (dois `Produto.objects.create` consecutivos → `b.pk > a.pk`), `test_fr003_codigo_quatro_digitos_sem_truncar` (`#0001`, `#0042`, `#12345`), `test_str_codigo_e_nome` (`"#0001 — Caneta Azul"`), `test_fr006_sc006_constraint_quantidade_atual_nao_negativa` (`Produto.objects.filter(pk=...).update(quantidade_atual=-1)` dentro de `transaction.atomic()` → `IntegrityError`), `test_fr006_constraint_estoque_minimo_nao_negativo`, `test_fr004_constraint_nome_nao_vazio`, `test_fr005_sc006_unique_lower_nome_no_banco` (`"Caneta"` e `"CANETA"` → `IntegrityError`), `test_fr015_em_alerta_inclui_igualdade` (0/0 e 5/5 → `em_alerta` e `situacao == "alerta"`; 6/5 → `"ok"`), `test_fr015_queryset_em_alerta_sem_alerta_com_situacao` (filtros e anotação `alerta`)

### Implementação

- [ ] T006 Implementar em apps/produtos/models.py: `QUANTIDADE_MAXIMA = 2_147_483_647`; `ProdutoQuerySet` com `em_alerta()` (`quantidade_atual__lte=F("estoque_minimo")`), `sem_alerta()` (`quantidade_atual__gt=F("estoque_minimo")`) e `com_situacao()` (anota `alerta` com `ExpressionWrapper(Q(quantidade_atual__lte=F("estoque_minimo")), output_field=BooleanField())`); modelo `Produto` com `id = BigAutoField(primary_key=True)`, `nome = CharField(max_length=120)`, `quantidade_atual = PositiveIntegerField()`, `estoque_minimo = PositiveIntegerField()`, `criado_em = DateTimeField(auto_now_add=True)`, `atualizado_em = DateTimeField(auto_now=True)`, `objects = ProdutoQuerySet.as_manager()`, `Meta.ordering = ["-id"]` e `Meta.constraints` = `CheckConstraint(condition=Q(quantidade_atual__gte=0), name="produto_quantidade_atual_nao_negativa")`, `CheckConstraint(condition=Q(estoque_minimo__gte=0), name="produto_estoque_minimo_nao_negativo")`, `CheckConstraint(condition=~Q(nome=""), name="produto_nome_nao_vazio")`, `UniqueConstraint(Lower("nome"), name="produto_nome_unico_ci")`; propriedades `codigo` (`f"#{self.pk:04d}"`), `em_alerta`, `situacao` (`"alerta"`/`"ok"`), `__str__` e `get_absolute_url()` (`reverse("produtos:detalhe", args=[self.pk])`); **não** registrar no admin (research R16)
- [ ] T007 Gerar apps/produtos/migrations/0001_initial.py com `python manage.py makemigrations produtos`, conferir os nomes das quatro restrições e rodar `pytest apps/produtos/tests/test_models.py` até ficar verde

**Checkpoint**: modelo e restrições prontos — histórias podem começar.

---

## Phase 3: User Story 1 - Cadastrar um novo produto (Priority: P1) 🎯 MVP

**Goal**: cadastrar produto (página própria e diálogo) com ID automático, validação junto ao campo, e vê-lo no topo da lista com destaque e notificação.

**Independent Test**: com a base vazia, cadastrar três produtos (página e diálogo) → `#0001`, `#0002`, `#0003` no topo com destaque e toast; entradas inválidas recusadas com mensagens pt-BR e nada gravado (quickstart M1–M5).

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Escrever os testes do serviço de cadastro em apps/produtos/tests/test_services.py: `test_fr001_cadastrar_produto_com_tres_campos`, `test_fr002_ids_consecutivos_via_servico`, `test_fr008_quantidade_atual_igual_inicial`, `test_fr004_nome_aparado_e_espacos_colapsados` (`"  Caneta   Azul "` → `"Caneta Azul"`), `test_fr004_nome_vazio_ou_so_espacos_recusado` (código `nome_obrigatorio`), `test_fr004_limite_120_apos_normalizacao` (120 aceito; 121 → `nome_longo`; 121 com espaço duplo interno aceito), `test_fr005_nome_duplicado_ignora_maiusculas` (mensagem `"Já existe um produto com este nome (#0001)."`), `test_fr005_acentos_significativos` (`"Café"` e `"Cafe"` coexistem), `test_fr005_acentuadas_maiusculas_duplicadas_postgres` (`skipif(connection.vendor != "postgresql")`: `"ÁGUA"` × `"água"`), `test_fr005_corrida_integrity_error_vira_validation_error` (desativar a pré-checagem com `monkeypatch` → `ValidationError` `nome_duplicado`), `test_fr006_faixa_e_tipo` (aceita 0 e 2_147_483_647; recusa -1, 2_147_483_648, 2.5 e `True`), `test_fr029_somente_argumentos_nomeados` (`TypeError` com posicionais), `test_fr029_atomico_nada_gravado_em_erro`, `test_fr030_poscondicoes_invariantes` (pós-condições 1–4 de contracts/servicos-e-consultas.md, que a extensão da 003 deve preservar)
- [ ] T009 [P] [US1] Escrever os testes de formulário em apps/produtos/tests/test_forms.py: `test_fr006_inteiro_estrito` (parametrizado: `"0"`, `"7"`, `" 12 "`, `"007"` aceitos; `"-5"`, `"2,5"`, `"2.5"`, `"2.0"`, `"1.000"`, `"1e3"`, `"+5"`, `"dez"`, `"٣"` → `"Informe um número inteiro igual ou maior que zero."`; `"2147483648"` → `"Informe um valor de no máximo 2.147.483.647."`), `test_fr006_campos_numericos_obrigatorios_sem_valor_inicial` (`"Informe a quantidade inicial."`, `"Informe o estoque mínimo."`; nenhum `initial`), `test_fr007_mensagens_nome_ptbr` (`"Informe o nome do produto."`, `"O nome deve ter no máximo 120 caracteres."`), `test_fr004_form_normaliza_nome`, `test_fr006_widget_numerico_texto` (`type="text"`, `inputmode="numeric"`, `pattern="[0-9]*"`)
- [ ] T010 [P] [US1] Escrever os testes de view do cadastro em apps/produtos/tests/test_views_cadastro.py: `test_fr009_get_novo_pagina_completa_comum_e_boosted` (200, `produtos/novo.html`, campos numéricos sem `value`), `test_fr009_get_novo_dialogo_parcial` (`HX-Target: dialogo` → 200, `produtos/partials/dialogo_novo.html`, sem `<html`, campo `nome` com `autofocus`), `test_fr009_salvar_indisponivel_durante_envio` (botão "Salvar" com `hx-disabled-elt`), `test_fr009_mesmas_mensagens_pagina_e_dialogo`, `test_fr010_fr011_post_valido_comum_e_boosted_302_com_destaque` (302 → `/produtos/`; ao seguir: linha `id="produto-<id>"` no topo com selo "NOVO" e mensagem `"Produto #0001 cadastrado"`; nova carga sem destaque), `test_fr007_post_invalido_comum_422_preserva_valores` (422, `aria-invalid="true"`, `aria-describedby`, valores preservados, `Produto.objects.count() == 0`), `test_fr010_post_valido_dialogo_cabecalhos` (200; `HX-Retarget: #resultados`; `HX-Reswap: outerHTML`; `HX-Push-Url: /produtos/`; `HX-Trigger` com `toast` `{"nivel": "sucesso", "texto": "Produto #0001 cadastrado"}` e `dialogo-fechar`; corpo com `id="resultados"` e a linha destacada), `test_fr031_post_valido_dialogo_emite_estoque_alterado`, `test_fr007_post_invalido_dialogo_422_com_autofocus` (fragmento do diálogo; primeiro campo inválido com `autofocus`), `test_fr005_post_duplicado_mensagem_com_codigo`, `test_fr006_post_quantidade_invalida_422`, `test_novo_metodos_nao_permitidos_405` (PUT/DELETE)
- [ ] T011 [P] [US1] Escrever os testes da lista básica em apps/produtos/tests/test_views_lista.py: `test_fr012_colunas_e_formatos` (cabeçalhos ID, Nome, Quantidade atual, Estoque mínimo, Situação; `#0001`; `1.500` com separador de milhar), `test_fr003_lista_exibe_codigo`, `test_fr020_situacao_alerta_icone_e_texto` (`REPOSIÇÃO NECESSÁRIA` + `<svg`; ok → `OK`), `test_fr016_ordem_padrao_id_decrescente` (mais recente no topo), `test_fr019_estado_vazio_sem_produtos` (`"Nenhum produto cadastrado"` + ação `"Cadastrar produto"` com `href` para `produtos:novo` e `hx-get` para `#dialogo`), `test_fr010_destaque_consumido_da_sessao` (chave `produtos_destaque` removida após a exibição)

### Implementation for User Story 1

- [ ] T012 [US1] Implementar `normalizar_nome(valor)` (`" ".join(valor.split())`) e `cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo) -> Produto` em apps/produtos/services.py: nome "1–120 caracteres após normalização"; inteiros (`int`, não `bool`) "de 0 a `QUANTIDADE_MAXIMA`"; unicidade com `annotate(nome_ci=Lower("nome")).filter(nome_ci=Lower(Value(nome)))`; `transaction.atomic()`; `IntegrityError` de `produto_nome_unico_ci` → `ValidationError({"nome": ...}, code="nome_duplicado")` citando o código do existente; `quantidade_atual = quantidade_inicial`; mensagens e códigos de data-model.md; docstring com o ponto de extensão da 003 (FR-030)
- [ ] T013 [US1] Implementar em apps/produtos/forms.py: `NomeProdutoField` (normaliza com `normalizar_nome` e valida "máximo 120 caracteres" após normalizar), `InteiroNaoNegativoField` (aceita só `^[0-9]+$` após aparar; `MaxValueValidator(QUANTIDADE_MAXIMA)`; widget `TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"})`) e `ProdutoForm` (`nome`, `quantidade_inicial`, `estoque_minimo`, sem valores iniciais, mensagens de data-model.md)
- [ ] T014 [P] [US1] Implementar em apps/produtos/selectors.py: `POR_PAGINA = 25`, `ORDEM_PADRAO = "-id"` e `listar_produtos()` mínimo (`Produto.objects.com_situacao().order_by("-id")`)
- [ ] T015 [P] [US1] Criar apps/produtos/templates/produtos/partials/situacao.html com o componente de badge da 001: em alerta → variante de alerta com ícone SVG de aviso + texto "REPOSIÇÃO NECESSÁRIA"; ok → variante neutra "OK" (nunca só cor — FR-020)
- [ ] T016 [P] [US1] Criar apps/produtos/templates/produtos/partials/linha.html: `<tr id="produto-{{ produto.pk|unlocalize }}">`, `produto.codigo`, nome, quantidade e mínimo com `|intcomma` alinhados à direita em fonte tabular, `situacao.html`; quando `destaque`, estado de destaque do componente de tabela + selo "NOVO"
- [ ] T017 [US1] Criar apps/produtos/templates/produtos/partials/resultados.html: `<div id="resultados">` com tabela (caption visualmente oculto, cabeçalhos das 5 colunas, linhas via `linha.html` com `destaque=produto.pk == destaque_id`) e estado vazio "Nenhum produto cadastrado" com ação primária "Cadastrar produto" (`href="{% url 'produtos:novo' %}"`, `hx-get` com `hx-target="#dialogo"`)
- [ ] T018 [US1] Criar apps/produtos/templates/produtos/lista.html (estende `base.html`): título "Produtos", ação primária "Novo produto" (`<a href="{% url 'produtos:novo' %}" hx-get="{% url 'produtos:novo' %}" hx-target="#dialogo" hx-swap="innerHTML">`) e `{% include "produtos/partials/resultados.html" %}`
- [ ] T019 [P] [US1] Criar apps/produtos/templates/produtos/partials/form_produto.html: `<form id="form-produto" method="post" novalidate>` com CSRF, campos via componente de campo da 001, erros com `aria-invalid="true"` e `aria-describedby`, `autofocus` no primeiro campo inválido, botão "Salvar" com `hx-disabled-elt="this"`; variação por `contexto` (`pagina`: `action` comum; `dialogo`: `hx-post="{% url 'produtos:novo' %}"` e `hx-target="#dialogo"`)
- [ ] T020 [P] [US1] Criar apps/produtos/templates/produtos/partials/dialogo_novo.html: título "Novo produto", `form_produto.html` com `contexto="dialogo"` e `autofocus` no campo Nome ao abrir, e botão "Cancelar" `<button formmethod="dialog" formnovalidate>` (Esc e Cancelar fecham sem salvar; o `<dialog>` nativo devolve o foco ao controle que o abriu)
- [ ] T021 [P] [US1] Criar apps/produtos/templates/produtos/novo.html (estende `base.html`; título "Novo produto"; `form_produto.html` com `contexto="pagina"`; link "Voltar para a lista")
- [ ] T022 [US1] Implementar em apps/produtos/views.py o utilitário `_variante(request)` (parcial só com `request.htmx` e sem `boosted`/`history_restore_request`; alvo via `request.htmx.target`) e as views `lista` (página 1 de `listar_produtos()`, `destaque_id = request.session.pop("produtos_destaque", None)`) e `novo` (`require_http_methods(["GET", "POST"])`; GET → `novo.html` ou `dialogo_novo.html` com `HX-Target: dialogo`; POST → `cadastrar_produto`, erros do serviço anexados ao form; comum/boosted: `messages.success(f"Produto {p.codigo} cadastrado")` + `session["produtos_destaque"]` + `redirect("produtos:lista")`, inválido 422; diálogo: `resultados.html` na visão padrão com `HX-Retarget: #resultados`, `HX-Reswap: outerHTML`, `HX-Push-Url: /produtos/`, `HX-Trigger` `toast`/`estoque-alterado`/`dialogo-fechar` via `django_htmx.http`, inválido 422) conforme contracts/rotas-http.md
- [ ] T023 [US1] Registrar as rotas `path("", views.lista, name="lista")` e `path("novo/", views.novo, name="novo")` em apps/produtos/urls.py
- [ ] T024 [P] [US1] Garantir o item "Produtos" (`{% url 'produtos:lista' %}`, marcado como atual na seção) na navegação em templates/base.html
- [ ] T025 [P] [US1] Garantir os estados "linha destacada" e "selo NOVO" do componente de tabela em static/css/components.css usando apenas tokens de static/css/tokens.css (somente se a 001 ainda não os oferecer; coordenar com a 001)
- [ ] T026 [US1] Rodar `pytest apps/produtos` (Phase 2 + US1 verdes) e validar os cenários M1–M5 de specs/002-cadastro-produtos/quickstart.md

**Checkpoint**: MVP — cadastro completo, funcionando com e sem JavaScript.

---

## Phase 4: User Story 2 - Localizar produtos na lista (Priority: P2)

**Goal**: busca instantânea por ID (`12`, `#12`, `#0012`) ou nome, filtro por situação, ordenação por colunas, paginação de 25 e URL que reflete o estado.

**Independent Test**: com ~60 produtos variados, buscar por cada formato de ID e por nome, combinar filtro e ordenação, paginar e reabrir a URL em outra aba com o mesmo resultado; busca sem resultado mostra o estado próprio (quickstart M6–M9).

### Tests for User Story 2 ⚠️

- [ ] T027 [P] [US2] Escrever os testes de busca e seletores em apps/produtos/tests/test_selectors.py: `test_fr013_hash_busca_somente_id` (`#12`, `#0012`, `# 12` → só `#0012`, mesmo existindo "Bucha 12 mm"), `test_fr013_numero_puro_id_ou_nome` (`12` → `#0012` e "Bucha 12 mm"), `test_fr013_nome_parcial_sem_diferenciar_maiusculas` (`cAnEtA`), `test_fr013_caracteres_especiais_literais` (`%`, `_`, `'`, `#abc`), `test_fr013_numero_gigante_sem_erro` (25 dígitos com e sem `#`), `test_fr013_hash_zero_sem_resultado`, `test_fr013_termo_vazio_ou_espacos_sem_filtro`, `test_fr015_filtro_situacao` (`alerta`, `ok`, valor inválido = todos), `test_fr016_ordenacoes_validas_e_desempate` (cada chave asc/desc; `nome` sem diferenciar maiúsculas; `situacao` crescente = alerta primeiro; desempate `-id`), `test_fr016_ordem_invalida_usa_padrao`
- [ ] T028 [P] [US2] Escrever os testes de view da lista em apps/produtos/tests/test_views_lista.py: `test_fr014_parcial_hx_target_resultados` (só o fragmento `id="resultados"`, sem `<html`, com `id="contagem-produtos"` OOB), `test_fr014_boosted_e_restauracao_retornam_pagina_completa`, `test_fr014_busca_sem_js_formulario_get` (`<form method="get" role="search">` com botão "Buscar"), `test_fr014_indica_atualizacao_e_anuncia_contagem` (busca com `hx-indicator="#resultados"`; `#contagem-produtos` com `role="status"`), `test_fr018_hx_push_url_canonica` (sem parâmetros vazios/padrão), `test_fr018_vary_hx_request_hx_target`, `test_fr018_mesma_url_mesmo_resultado` (página completa e parcial com os mesmos parâmetros listam as mesmas linhas), `test_fr017_paginacao_25_e_indicador` (60 produtos: 25 linhas, "1–25 de 60"; `pagina=3` → 10; `pagina=999` → última; `pagina=abc` → 1; links preservam `q`/`situacao`/`ordem`), `test_fr016_cabecalhos_aria_sort_e_links`, `test_fr015_select_situacao_opcoes` (Todos / Em alerta / OK), `test_fr019_nenhum_produto_encontrado_cita_termo_e_limpar_busca`, `test_sc003_lista_consultas_limitadas` (`django_assert_max_num_queries(4)` com 60 produtos)
- [ ] T029 [P] [US2] Escrever em apps/produtos/tests/test_views_cadastro.py o teste `test_fr010_sucesso_no_dialogo_reseta_filtros` (resposta parcial contém `id="filtros-produtos"` com `hx-swap-oob="true"` e campos vazios, e a contagem OOB)

### Implementation for User Story 2

- [ ] T030 [US2] Implementar `ProdutoQuerySet.buscar(q)` em apps/produtos/models.py conforme a tabela de verdade de contracts/servicos-e-consultas.md: termo normalizado; `^#\s*([0-9]+)$` → só `pk`; `^[0-9]+$` → `Q(pk=n) | Q(nome__icontains=termo)`; demais → `nome__icontains`; números acima de `9_223_372_036_854_775_807` nunca filtram por ID
- [ ] T031 [US2] Completar apps/produtos/selectors.py: `ORDENS_VALIDAS`, `SITUACOES_VALIDAS`, `normalizar_ordem()`, `normalizar_situacao()` e `listar_produtos(*, q="", situacao="", ordem="")` (`com_situacao().buscar(q)`, `em_alerta()`/`sem_alerta()`, mapeamento de ordenação de research R7 com desempate `-id`)
- [ ] T032 [P] [US2] Criar apps/produtos/templates/produtos/partials/filtros.html: `<form id="filtros-produtos" method="get" action="{% url 'produtos:lista' %}" role="search">` com `<input type="search" name="q">` (`hx-get`, `hx-trigger="input changed delay:300ms, search"`, `hx-target="#resultados"`, `hx-swap="outerHTML"`, `hx-include="#filtros-produtos, #ordem-atual"`, `hx-sync="this:replace"`, `hx-push-url="true"`, `hx-indicator="#resultados"`), `<select name="situacao">` (Todos / Em alerta / OK, dispara em `change`), botão "Buscar" para uso sem JS e suporte a `oob`
- [ ] T033 [P] [US2] Criar apps/produtos/templates/produtos/partials/contagem.html: `<p id="contagem-produtos" role="status">` com "1–25 de 60" (ou "0 produtos") e suporte a `hx-swap-oob="true"`
- [ ] T034 [US2] Estender apps/produtos/templates/produtos/partials/resultados.html: cabeçalhos ordenáveis `<th aria-sort="ascending|descending|none">` com link `{% url 'produtos:lista' %}{% querystring ordem=... pagina=None %}` + `hx-get`/`hx-target="#resultados"`/`hx-push-url="true"`; `<input type="hidden" id="ordem-atual" name="ordem" form="filtros-produtos">`; `<nav aria-label="Paginação">` com `{% querystring pagina=n %}`; estado "Nenhum produto encontrado" citando `q` + ação "Limpar busca" (`/produtos/`)
- [ ] T035 [US2] Incluir `filtros.html` e `contagem.html` em apps/produtos/templates/produtos/lista.html, acima de `resultados.html`
- [ ] T036 [US2] Estender a view `lista` em apps/produtos/views.py: ler `q`, `situacao`, `ordem`, `pagina`; `Paginator(qs, POR_PAGINA).get_page(pagina)`; `total_geral` só quando há filtro e a página está vazia; variante parcial (`HX-Target: resultados`) → `resultados.html` + `contagem.html` OOB + `HX-Push-Url` com a URL canônica; `@vary_on_headers("HX-Request", "HX-Target")`
- [ ] T037 [US2] Na resposta de sucesso do diálogo da view `novo` em apps/produtos/views.py, acrescentar `filtros.html` (campos limpos) e `contagem.html` com `hx-swap-oob="true"`
- [ ] T038 [US2] Rodar `pytest apps/produtos` e validar M6–M9 e a seção 5 (carga de 10 mil produtos, SC-003) de specs/002-cadastro-produtos/quickstart.md

**Checkpoint**: US1 e US2 funcionam de forma independente.

---

## Phase 5: User Story 3 - Consultar os dados de um produto (Priority: P3)

**Goal**: página de detalhe com dados completos e região reservada às movimentações (003); 404 próprio para produto inexistente.

**Independent Test**: abrir o detalhe pela lista e por URL direta; conferir dados e datas; abrir `/produtos/999999/` → "Produto não encontrado" (quickstart M10).

### Tests for User Story 3 ⚠️

- [ ] T039 [P] [US3] Escrever os testes do detalhe em apps/produtos/tests/test_views_detalhe.py: `test_fr021_detalhe_exibe_dados_e_datas` (código, nome, quantidade com milhar, mínimo, situação, `criado_em`/`atualizado_em` em `dd/mm/aaaa HH:MM`), `test_fr021_detalhe_comum_e_boosted_200` (`produtos/detalhe.html`), `test_fr022_regiao_movimentacoes_vazia_sem_controles` (`id="produto-movimentacoes"` presente, sem `<button`, `<form` ou `<a` dentro), `test_fr023_produto_inexistente_404_com_link_para_lista` (`produtos/nao_encontrado.html`), `test_fr023_id_acima_do_bigint_404`, `test_fr026_post_e_delete_no_detalhe_405_produto_permanece`
- [ ] T040 [P] [US3] Escrever em apps/produtos/tests/test_selectors.py os testes `test_fr023_obter_produto_inexistente_does_not_exist` e `test_fr023_obter_produto_id_gigante_does_not_exist`
- [ ] T041 [P] [US3] Escrever em apps/produtos/tests/test_views_lista.py o teste `test_fr012_id_e_nome_levam_ao_detalhe` (links para `produto.get_absolute_url()`)

### Implementation for User Story 3

- [ ] T042 [US3] Implementar `obter_produto(produto_id)` em apps/produtos/selectors.py (`Produto.DoesNotExist` também para IDs acima de `9_223_372_036_854_775_807`, sem consultar o banco)
- [ ] T043 [P] [US3] Criar apps/produtos/templates/produtos/partials/resumo.html: `<div id="produto-resumo">` com código, nome, quantidade atual e mínimo (`|intcomma`, fonte tabular), `situacao.html` e datas `|date:"d/m/Y H:i"` — re-renderizável pela 003 com `hx-swap-oob`
- [ ] T044 [P] [US3] Criar apps/produtos/templates/produtos/nao_encontrado.html (estende `base.html`; "Produto não encontrado" e link "Voltar para a lista")
- [ ] T045 [US3] Criar apps/produtos/templates/produtos/detalhe.html (estende `base.html`): título com `produto.codigo` e nome, `resumo.html` e `<section id="produto-movimentacoes" aria-label="Movimentações">` vazia, com comentário de template indicando o ponto de inclusão da 003
- [ ] T046 [US3] Implementar a view `detalhe` em apps/produtos/views.py (`require_GET` → 405 para outros métodos; `obter_produto`; `DoesNotExist` → `nao_encontrado.html` com status 404) e registrar `path("<int:produto_id>/", views.detalhe, name="detalhe")` em apps/produtos/urls.py
- [ ] T047 [US3] Transformar código e nome em links para `produto.get_absolute_url` em apps/produtos/templates/produtos/partials/linha.html
- [ ] T048 [US3] Rodar `pytest apps/produtos` e validar M10 de specs/002-cadastro-produtos/quickstart.md

**Checkpoint**: detalhe pronto e região de integração disponível para a 003.

---

## Phase 6: User Story 4 - Corrigir nome e estoque mínimo (Priority: P4)

**Goal**: editar nome e estoque mínimo com as regras do cadastro, sem jamais alterar a quantidade; nenhuma exclusão.

**Independent Test**: editar nome e mínimo e conferir na lista e no detalhe; nome de outro produto é recusado; envio adulterado com quantidade não a altera; nenhuma ação de excluir em lugar algum (quickstart M11–M12).

### Tests for User Story 4 ⚠️

- [ ] T049 [P] [US4] Escrever os testes do serviço de edição em apps/produtos/tests/test_services.py: `test_fr024_editar_nome_e_estoque_minimo`, `test_fr024_unicidade_desconsidera_o_proprio` (mudar só maiúsculas/minúsculas aceito), `test_fr024_nome_de_outro_produto_recusado`, `test_fr024_mesmas_validacoes_do_cadastro` (nome vazio/longo, mínimo negativo/acima do limite), `test_fr025_editar_nunca_grava_quantidade_atual` (`CaptureQueriesContext`: o `UPDATE` não contém `quantidade_atual`), `test_fr027_atualizado_em_avanca`, `test_fr023_editar_produto_inexistente`
- [ ] T050 [P] [US4] Escrever em apps/produtos/tests/test_forms.py o teste `test_fr025_form_edicao_so_nome_e_estoque_minimo` (`list(ProdutoEdicaoForm().fields) == ["nome", "estoque_minimo"]`)
- [ ] T051 [P] [US4] Escrever os testes de view da edição em apps/produtos/tests/test_views_edicao.py: `test_fr024_get_editar_preenchido_comum_e_boosted` (200; valores atuais; quantidade atual somente leitura com a nota "Muda apenas por movimentação"; nenhum `<input name="quantidade_atual"`), `test_fr027_post_valido_302_detalhe_com_mensagem` (comum e boosted; ao seguir: `"Produto #0001 atualizado"`), `test_fr027_situacao_recalculada_apos_mudar_minimo`, `test_fr031_edicao_boosted_rerenderiza_pagina_completa` (resposta final com o layout inteiro), `test_fr025_post_adulterado_quantidade_ignorada`, `test_fr024_post_invalido_422` (duplicado, vazio, negativo), `test_fr023_editar_inexistente_404`, `test_fr026_nenhuma_acao_de_excluir` (HTML de lista, detalhe e edição sem "Excluir"/`method="delete"`)

### Implementation for User Story 4

- [ ] T052 [US4] Implementar `editar_produto(*, produto_id, nome, estoque_minimo) -> Produto` em apps/produtos/services.py: `transaction.atomic()`, `Produto.objects.select_for_update().get(pk=produto_id)`, normalização e validações do cadastro (unicidade excluindo o próprio `pk`), `save(update_fields=["nome", "estoque_minimo", "atualizado_em"])`
- [ ] T053 [P] [US4] Implementar `ProdutoEdicaoForm` (apenas `nome` com `NomeProdutoField` e `estoque_minimo` com `InteiroNaoNegativoField`) em apps/produtos/forms.py
- [ ] T054 [P] [US4] Criar apps/produtos/templates/produtos/partials/form_edicao.html: `<form id="form-edicao" method="post" novalidate>` com `nome` e `estoque_minimo` preenchidos, quantidade atual exibida somente leitura (texto, não campo) com a nota "Muda apenas por movimentação", erros acessíveis e `autofocus` no primeiro inválido
- [ ] T055 [US4] Criar apps/produtos/templates/produtos/editar.html (estende `base.html`; título "Editar #0001"; `form_edicao.html`; link "Cancelar" para o detalhe)
- [ ] T056 [US4] Implementar a view `editar` em apps/produtos/views.py (`require_http_methods(["GET", "POST"])`; 404 com `nao_encontrado.html`; POST → `editar_produto`; sucesso → `messages.success(f"Produto {p.codigo} atualizado")` + `redirect(p)`; inválido → 422) e registrar `path("<int:produto_id>/editar/", views.editar, name="editar")` em apps/produtos/urls.py
- [ ] T057 [US4] Adicionar a ação secundária "Editar" (`{% url 'produtos:editar' produto.pk %}`) em apps/produtos/templates/produtos/detalhe.html
- [ ] T058 [US4] Rodar `pytest apps/produtos` e validar M11–M12 de specs/002-cadastro-produtos/quickstart.md

**Checkpoint**: edição segura; quantidade continua intocável.

---

## Phase 7: User Story 5 - Acesso rápido pelo teclado (Priority: P5)

**Goal**: `/` foca a busca e `n` abre o cadastro na lista, como aprimoramento progressivo.

**Independent Test**: na lista, `/` foca a busca e `n` abre o diálogo; dentro de campos nada é acionado; sem scripts a lista segue utilizável (quickstart M13).

### Tests for User Story 5 ⚠️

- [ ] T059 [P] [US5] Escrever os testes de marcação em apps/produtos/tests/test_atalhos.py: `test_fr028_busca_tem_data_atalho_barra_e_dica` (`data-atalho="/"` e `<kbd>/</kbd>` junto à busca), `test_fr028_novo_produto_tem_data_atalho_n_e_href_funcional` (`data-atalho="n"`, `<kbd>n</kbd>`, `href` para `/produtos/novo/`), `test_fr028_script_progressivo_carregado` (a página referencia `js/consus.js`), `test_fr028_js_proprio_abaixo_de_100_linhas` (soma das linhas de static/js/*.js fora de `vendor/` < 100 — princípio II)

### Implementation for User Story 5

- [ ] T060 [P] [US5] Garantir em static/js/consus.js o manipulador genérico de `data-atalho` (~12 linhas; somente se a 001 não o fornecer): `keydown` no documento; ignora com Ctrl/Meta/Alt, com alvo editável (`input`, `textarea`, `select`, `[contenteditable]`) ou com `<dialog open>`; localiza `[data-atalho="<tecla>"]`; campo → `focus()`, demais → `click()`; `preventDefault()`
- [ ] T061 [US5] Adicionar `data-atalho="/"` e a dica `<kbd>/</kbd>` ao campo de busca em apps/produtos/templates/produtos/partials/filtros.html
- [ ] T062 [US5] Adicionar `data-atalho="n"` e a dica `<kbd>n</kbd>` à ação "Novo produto" em apps/produtos/templates/produtos/lista.html
- [ ] T063 [US5] Rodar `pytest apps/produtos` e validar M13 de specs/002-cadastro-produtos/quickstart.md

**Checkpoint**: todas as histórias funcionando de forma independente.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: portões de qualidade da constituição e validação final.

- [ ] T064 [P] Revisar acessibilidade dos templates em apps/produtos/templates/produtos/ contra specs/002-cadastro-produtos/checklists/ux.md (rótulos, foco visível, `aria-*`, contraste só via tokens, região `aria-live` das notificações) e corrigir desvios
- [ ] T065 [P] Verificar a rastreabilidade FR → teste com o laço de specs/002-cadastro-produtos/quickstart.md (seção 2): nenhum FR-001…FR-031 sem teste em apps/produtos/tests/
- [ ] T066 Medir cobertura com `pytest apps/produtos --cov=apps/produtos --cov-report=term-missing` e completar testes até ≥ 90% em apps/produtos/models.py, apps/produtos/services.py e apps/produtos/selectors.py
- [ ] T067 Rodar a suíte no PostgreSQL via docker-compose.yml (`docker compose exec web pytest apps/produtos`), incluindo os testes marcados como somente PostgreSQL
- [ ] T068 Rodar os portões de qualidade: `ruff check .`, `ruff format --check .`, `python manage.py makemigrations --check --dry-run` e `docker compose build` (Dockerfile)
- [ ] T069 Executar a validação completa de specs/002-cadastro-produtos/quickstart.md (M1–M14, seções 3, 5 e 6), incluindo uso somente por teclado e com JavaScript desativado (SC-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: depende da feature 001 implementada (projeto, layout, componentes).
- **Foundational (Phase 2)**: depende do Setup — BLOQUEIA todas as histórias.
- **US1 (Phase 3)**: depende da Phase 2. É o MVP.
- **US2 (Phase 4)** e **US3 (Phase 5)**: dependem da US1 (estendem `lista.html`, `resultados.html`
  e `linha.html`), mas **não** uma da outra — podem seguir em paralelo.
- **US4 (Phase 6)**: depende da US3 (redireciona para o detalhe e adiciona "Editar" em
  `detalhe.html`).
- **US5 (Phase 7)**: depende da US2 (campo de busca em `filtros.html`).
- **Polish (Phase 8)**: depende das histórias desejadas concluídas.

### User Story Dependencies

- **US1 (P1)**: após a Phase 2 — sem dependência de outras histórias.
- **US2 (P2)**: após US1 — testável sozinha (busca/filtro/ordem/paginação sobre a lista).
- **US3 (P3)**: após US1 — testável sozinha (detalhe por URL direta; link da lista em T047).
- **US4 (P4)**: após US3 — testável sozinha (edição por URL direta).
- **US5 (P5)**: após US2 — testável sozinha (atalhos sobre a lista).

### Within Each User Story

- Testes escritos e FALHANDO antes da implementação.
- Modelo/QuerySet → serviços/seletores → formulários → templates → views → rotas.
- Checkpoint (pytest + cenários do quickstart) antes de passar à próxima prioridade.

### Parallel Opportunities

- Setup: T004 em paralelo com T002/T003.
- US1: T008–T011 (quatro arquivos de teste) juntos; depois T014, T015, T016, T019, T020, T021,
  T024 e T025 em paralelo com T012/T013.
- US2: T027–T029 juntos; T032 e T033 juntos.
- US3: T039–T041 juntos; T043 e T044 juntos.
- US4: T049–T051 juntos; T053 e T054 juntos.
- Após a US1, US2 e US3 podem ser desenvolvidas em paralelo por pessoas diferentes.

---

## Parallel Example: User Story 1

```bash
# Testes da US1 juntos (arquivos diferentes):
Task: "T008 Testes do serviço de cadastro em apps/produtos/tests/test_services.py"
Task: "T009 Testes de formulário em apps/produtos/tests/test_forms.py"
Task: "T010 Testes de view do cadastro em apps/produtos/tests/test_views_cadastro.py"
Task: "T011 Testes da lista básica em apps/produtos/tests/test_views_lista.py"

# Templates da US1 juntos:
Task: "T015 partials/situacao.html"
Task: "T016 partials/linha.html"
Task: "T019 partials/form_produto.html"
Task: "T020 partials/dialogo_novo.html"
Task: "T021 novo.html"
```

## Parallel Example: User Story 2

```bash
Task: "T027 Testes de busca e seletores em apps/produtos/tests/test_selectors.py"
Task: "T028 Testes de view da lista em apps/produtos/tests/test_views_lista.py"
Task: "T029 Teste de reset dos filtros em apps/produtos/tests/test_views_cadastro.py"
Task: "T032 partials/filtros.html"
Task: "T033 partials/contagem.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup → 2. Phase 2: Foundational (modelo + restrições) → 3. Phase 3: US1.
4. **PARAR e VALIDAR**: `pytest apps/produtos` + quickstart M1–M5 (com e sem JavaScript).
5. Demonstrar: o item 1 da atividade (cadastro com ID automático) já está atendido.

### Incremental Delivery

1. Setup + Foundational → base pronta.
2. US1 → MVP (cadastro).
3. US2 → busca por ID/nome ("facilitar a busca", item 1 da atividade).
4. US3 → detalhe (âncora para a 003 começar).
5. US4 → edição segura.
6. US5 → atalhos.
7. Polish → portões da constituição e merge `--no-ff` em `develop`.

### Parallel Team Strategy

1. Equipe conclui Setup + Foundational + US1 juntos.
2. Em seguida: pessoa A → US2 (+ US5); pessoa B → US3 (+ US4).
3. Polish em conjunto.

---

## Notes

- `[P]` = arquivos diferentes, sem dependência de tarefa incompleta.
- `[USn]` mapeia a tarefa para a história da spec (rastreabilidade).
- Cada teste cita o FR no nome (`test_fr0NN_...`) ou na docstring (princípio III).
- Os testes da 002 verificam só a pós-condição observável de `cadastrar_produto`, para seguirem
  válidos quando a 003 a estender (FR-030).
- Nunca alterar `quantidade_atual` fora de `cadastrar_produto` (e, depois, da 003) — princípio I.
- Commit por tarefa ou grupo lógico (Conventional Commits em português).
