---

description: "Lista de tarefas da feature 001 — Fundação do Consus e Design System"
---

# Tasks: Fundação do Consus e Design System

**Input**: Design documents from `/specs/001-fundacao-design-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (rotas-core, layout-e-htmx, componentes), quickstart.md · Fonte visual: `docs/design/design-system.md`

**Tests**: OBRIGATÓRIOS (Constituição III — testes primeiro). Toda tarefa de teste cita os FR que
cobre e DEVE falhar antes da implementação correspondente. Cada teste referencia o FR na
docstring (ex.: `"""FR-013: item indisponível sem link e com "(em breve)"."""`). Testes de view
cobrem as duas variantes: requisição comum e requisição HTMX.

**Organization**: tarefas agrupadas por história de usuário (US1–US5 do spec.md) para
implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história a que a tarefa pertence (US1…US5)
- Caminhos relativos à raiz do repositório, conforme `docs/arquitetura.md` e plan.md

## Path Conventions

Aplicação Django única: `config/`, `apps/core/`, `templates/`, `static/`, testes em
`apps/core/tests/`, arquivos de contêiner na raiz.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: inicialização do projeto, dependências e assets de terceiros

- [ ] T001 Criar o esqueleto de pacotes do plan.md: `manage.py` (padrão `DJANGO_SETTINGS_MODULE=config.settings`), `config/__init__.py` com `__version__ = "0.1.0"`, `apps/__init__.py`, `apps/core/__init__.py`, `apps/core/apps.py` (`CoreConfig(name="apps.core", label="core", verbose_name="Núcleo")`) e `apps/core/tests/__init__.py`
- [ ] T002 Criar `pyproject.toml` (uv): `name="consus"`, `version="0.1.0"`, `requires-python=">=3.13,<3.14"`; dependências `django>=5.2,<5.3`, `django-htmx>=1.23`, `dj-database-url>=2.3`, `psycopg[binary]>=3.2`, `gunicorn>=23`, `whitenoise>=6.8`; `[dependency-groups] dev = pytest>=8.3, pytest-django>=4.9, pytest-cov>=6, ruff`; `[tool.uv] package = false`; `[tool.ruff]` (`target-version="py313"`, `line-length=100`, `extend-exclude=["**/migrations/**"]`, `lint.select=["E","F","W","I","UP","B","DJ","SIM"]`); `[tool.pytest.ini_options]` (`DJANGO_SETTINGS_MODULE="config.settings"`, `testpaths=["apps"]`, `addopts='-m "not docker" --cov --cov-report=term-missing'`, `markers=["docker: integração com Docker Compose (opt-in)"]`); `[tool.coverage.run]` (`source=["apps","config"]`, `branch=true`, `omit=["*/tests/*","*/migrations/*"]`) e `[tool.coverage.report]` (`fail_under=90`, `show_missing=true`) — research R2/R15
- [ ] T003 Gerar `uv.lock` com `uv lock` a partir de `pyproject.toml` e validar `uv sync` em ambiente limpo (FR-042)
- [ ] T004 [P] Criar `.env.example` com uma linha de comentário + `NOME=valor` para cada variável de data-model §1: `DJANGO_SECRET_KEY=troque-esta-chave-antes-de-publicar`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`, `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000`, `DATABASE_URL=postgres://consus:consus@db:5432/consus`, `DATABASE_CONNECT_TIMEOUT=2`, `DJANGO_LOG_LEVEL=INFO`, `DJANGO_SECURE_COOKIES=false`, `WEB_CONCURRENCY=3`, `CONSUS_PORTA=8000`, `POSTGRES_DB=consus`, `POSTGRES_USER=consus`, `POSTGRES_PASSWORD=consus`
- [ ] T005 [P] Criar `.dockerignore` com `.git`, `.venv`, `**/__pycache__`, `*.sqlite3`, `.env`, `staticfiles/`, `specs/`, `docs/`, `.specify/`, `.claude/`, `htmlcov/`, `.coverage` (research R4)
- [ ] T006 [P] Vendorizar HTMX 2.0.x (versão estável mais recente da série 2.0) em `static/vendor/htmx.min.js` e criar `static/vendor/README.md` com tabela origem/versão/SHA-256/licença (HTMX 0BSD) — research R6
- [ ] T007 [P] Vendorizar as fontes do release oficial `IBM/plex` em `static/fonts/`: `IBMPlexSans-Regular-Latin1.woff2`, `IBMPlexSans-Medium-Latin1.woff2`, `IBMPlexSans-SemiBold-Latin1.woff2`, `IBMPlexMono-Regular-Latin1.woff2`, `IBMPlexMono-SemiBold-Latin1.woff2` + `static/fonts/OFL.txt`; registrar versão e SHA-256 em `static/vendor/README.md` — research R13
- [ ] T008 [P] Montar o sprite `static/vendor/lucide/sprite.svg` com um `<symbol id="<nome>" viewBox="0 0 24 24">` para cada ícone da tabela de `docs/design/design-system.md` §2.13 (`layout-dashboard`, `package`, `arrow-left-right`, `bell`, `triangle-alert`, `circle-check`, `info`, `octagon-x`, `circle-alert`, `arrow-down-to-line`, `arrow-up-from-line`, `arrow-up`, `arrow-down`, `arrow-right`, `plus`, `search`, `x`, `chevron-left`, `chevron-right`, `chevron-down`, `inbox`, `loader-circle`, `activity`) sem atributos de cor/traço (definidos no CSS) + `static/vendor/lucide/LICENSE` (ISC); registrar versão do Lucide em `static/vendor/README.md`
- [ ] T009 Criar `conftest.py` na raiz com fixture `autouse` que troca `settings.STORAGES["staticfiles"]` por `django.contrib.staticfiles.storage.StaticFilesStorage` durante a suíte (research R5)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: configuração por ambiente, roteamento, tokens e CSS base — bloqueiam todas as histórias

**⚠️ CRITICAL**: nenhuma história começa antes desta fase

### Tests (escrever primeiro, devem falhar)

- [ ] T010 [P] Escrever `apps/core/tests/test_configuracao.py` (settings em **subprocesso** com `env` controlado — research R15): FR-004 (lê `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_LOG_LEVEL`, `DATABASE_CONNECT_TIMEOUT` do ambiente); FR-005 (`DEBUG` padrão falso; `DJANGO_DEBUG=false` sem `DJANGO_SECRET_KEY` ⇒ processo termina com código ≠ 0 e mensagem contendo "DJANGO_SECRET_KEY"); FR-006 (sem `DATABASE_URL` ⇒ engine `sqlite3`; com `postgres://…` ⇒ engine `postgresql` e `OPTIONS["connect_timeout"] == 2`); FR-009 (`LOGGING` com handler `StreamHandler` em `sys.stdout` e nível igual a `DJANGO_LOG_LEVEL`); FR-020 (`LANGUAGE_CODE == "pt-br"`, `TIME_ZONE == "America/Sao_Paulo"`, `USE_THOUSAND_SEPARATOR`; template `{{ 1240 }}` → `1.240`; `{{ dt|date:"SHORT_DATETIME_FORMAT" }}` → `20/10/2026 14:30`); FR-043 (resposta de `GET /nao-existe/` com `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`; `DJANGO_SECURE_COOKIES=true` ⇒ `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` verdadeiros); FR-044 (`django.contrib.admin` e `django.contrib.auth` fora de `INSTALLED_APPS`; `GET /admin/` → 404)
- [ ] T011 [P] Escrever `apps/core/tests/test_tokens.py`: FR-023 (`static/css/tokens.css` define todos os tokens semânticos de design-system §2 — lista explícita no teste; `base.css`, `components.css`, `utilities.css` sem `#hex`, `rgb(`, `hsl(`, nomes de cor nem medidas `px/rem/em` ≠ 0 fora de prelúdios `@media` comentados com o token; nenhum `--palette-` fora de `tokens.css`; `:root` com `color-scheme: light`); FR-024 (todo par de `apps.core.design_tokens.PARES_CONTRASTE` com `minimo > 0` atinge o mínimo; a lista contém os 31 pares de design-system §3); FR-025 (`base.css` tem regra `:focus-visible` com `outline` usando `--focus-width`, `--focus-color` e `--focus-offset`; nenhum `outline: none`/`outline: 0` nos CSS; `tokens.css` contém `@media (forced-colors: active)` redefinindo `--color-border` e `--focus-color`); FR-026 (`base.css` declara 5 `@font-face` com `font-display: swap`; `.num` usa `var(--font-mono)` e `tabular-nums`); FR-030 (todos os `--duration-*` ≤ 150 ms; bloco `prefers-reduced-motion: reduce` zera as durações; nenhum `transition: all` e propriedades em `transition`/`transition-property` restritas a `background-color`, `color`, `border-color`, `box-shadow`, `transform` e `opacity`)
- [ ] T012 [P] Escrever `apps/core/tests/test_assets.py`: FR-008 (existem `static/vendor/htmx.min.js` (série 2.x), os 5 `woff2`, `OFL.txt`, `sprite.svg` e `LICENSE`; nenhum `http://`, `https://` ou `//` de protocolo relativo em `src`/`href`/`url()` de `templates/**`, `apps/**/templates/**`, `static/css/**`, `static/js/**`); FR-026 (arquivos de fonte presentes e não vazios); FR-029 (o sprite contém um `<symbol>` para cada ícone de design-system §2.13)

### Implementation

- [ ] T013 Implementar `config/settings.py` (research R3/R5/R14/R18/R19): auxiliares `_bool`/`_lista`; `DEBUG` padrão falso; `ImproperlyConfigured` se `DEBUG` falso e sem `DJANGO_SECRET_KEY`; `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` do ambiente; `INSTALLED_APPS = [contenttypes, sessions, messages, staticfiles, django_htmx, apps.core]`; `MIDDLEWARE` (Security, WhiteNoise, Session, Common, Csrf, Messages, XFrameOptions, `django_htmx.middleware.HtmxMiddleware`); `TEMPLATES` (`DIRS=[BASE_DIR/"templates"]`, `APP_DIRS`, context processors `request`, `messages`, `apps.core.context_processors.consus`); `DATABASES` via `dj_database_url.config(default=sqlite, conn_max_age=60, conn_health_checks=True)` + `OPTIONS["connect_timeout"]` para PostgreSQL; pt-BR (`LANGUAGE_CODE`, `TIME_ZONE`, `USE_TZ`, `USE_THOUSAND_SEPARATOR`, `FORMAT_MODULE_PATH=["config.formatos"]`); `STATIC_URL`, `STATIC_ROOT=BASE_DIR/"staticfiles"`, `STATICFILES_DIRS=[BASE_DIR/"static"]`, `STORAGES` com `CompressedManifestStaticFilesStorage`; `MESSAGE_TAGS` (`DEBUG/INFO→info`, `SUCCESS→sucesso`, `WARNING→alerta`, `ERROR→erro`); `X_FRAME_OPTIONS="DENY"`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY="same-origin"`, cookies seguros por `DJANGO_SECURE_COOKIES`; `LOGGING` para stdout; `DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"`
- [ ] T014 [P] Criar `config/formatos/__init__.py`, `config/formatos/pt_BR/__init__.py` e `config/formatos/pt_BR/formats.py` com `DATE_FORMAT = SHORT_DATE_FORMAT = "d/m/Y"`, `DATETIME_FORMAT = SHORT_DATETIME_FORMAT = "d/m/Y H:i"`, `THOUSAND_SEPARATOR = "."`, `DECIMAL_SEPARATOR = ","`, `NUMBER_GROUPING = 3` (research R14)
- [ ] T015 Implementar `config/urls.py` (`path("", include("apps.core.urls"))`, sem admin), `apps/core/urls.py` (`app_name = "core"`, lista vazia a ser preenchida pelas histórias), `config/wsgi.py` e `config/asgi.py`
- [ ] T016 Implementar `apps/core/context_processors.py` com `consus(request)` retornando `{"versao": config.__version__}` (estendido em T031)
- [ ] T017 [P] Implementar `static/css/tokens.css` com **todos** os tokens de `docs/design/design-system.md` §2 (primitivas `--palette-*`; semânticas `--color-*` com os hex da tabela §2.1.2; `--font-*`, `--font-weight-*`, `--text-*`/`--leading-*`, `--tracking-*`, `--measure`; `--space-0…13`; `--size-*`, `--icon-*`, `--header-h`, `--container-max`, `--form-max`, `--dialog-w-*`, `--toast-w`; `--border-width*`, `--radius-*`; `--shadow-offset-*`, `--shadow-*`; `--focus-*`; `--grid-*`, `--page-margin`, `--bp-*`; `--table-*`; `--z-*`; `--duration-*`, `--ease-*`; `--opacity-busy`), `:root { color-scheme: light }`, media queries de `--grid-columns` (4 → 8 → 12), `--grid-gutter` e `--page-margin` em 42rem e 66rem (comentadas com o token), bloco `@media (prefers-reduced-motion: reduce)` zerando durações e bloco `@media (forced-colors: active)` (`--color-border: CanvasText`, `--focus-color: Highlight`) — FR-023/025/030
- [ ] T018 Implementar `apps/core/design_tokens.py` (depende de T017): `carregar_tokens(caminho) -> dict[str, str]` (custom properties do `:root` principal), `resolver(nome, tokens)` (resolve `var()` encadeado), `luminancia(hex)`, `razao_contraste(a, b)` (WCAG 2.1), dataclass `ParContraste(primeiro_plano, fundo, minimo, uso)`, `PARES_CONTRASTE` com os 31 pares de design-system §3 e `avaliar_pares() -> list[dict]` com `razao` e `aprovado` (research R11, data-model §2–§3)
- [ ] T019 Implementar `static/css/base.css`: `@layer base, components, utilities;`; 5 `@font-face` (`font-display: swap`, `unicode-range` Latin-1); reset mínimo; `html/body` (`--font-sans`, `--text-sm`/`--leading-sm`, `--color-ink` sobre `--color-paper`); estilos tipográficos compostos de §2.2 para `h1–h3`, `.rotulo`, `.ajuda`; links; foco global `:focus-visible` com `outline: var(--focus-width) solid var(--focus-color); outline-offset: var(--focus-offset)`; controles de formulário base (`:focus` em campos); `.num` (mono, `tabular-nums`, à direita) — só tokens
- [ ] T020 [P] Implementar `static/css/utilities.css` em `@layer utilities`: `.visualmente-oculto`, `.num`, `.mono`, `.grade` (`repeat(var(--grid-columns), minmax(0, 1fr))` com `--grid-gutter`; abaixo de 42rem todo filho ocupa a linha inteira com `grid-column: 1 / -1`), `.col-md-{1..8}` (≥ 42rem), `.col-lg-{1..12}` (≥ 66rem) — sem classes de span sem prefixo, para nunca exceder as 4 colunas do celular, `.pilha`, `.cluster`, `.texto-atenuado`, `.texto-sutil` — breakpoints literais comentados com `--bp-md`/`--bp-lg`
- [ ] T021 Rodar `uv run pytest apps/core/tests/test_configuracao.py apps/core/tests/test_tokens.py apps/core/tests/test_assets.py` até ficar verde

**Checkpoint**: configuração, tokens e CSS base prontos — histórias podem começar

---

## Phase 3: User Story 1 - Subir o sistema com um comando e navegar pela casca (Priority: P1) 🎯 MVP

**Goal**: `docker compose up --build` entrega o Painel com marca, navegação (itens "em breve"), slot do badge, região de toasts e `<dialog>` funcionando.

**Independent Test**: clone limpo → `cp .env.example .env` → `docker compose up --build` → `http://localhost:8000/` mostra o Painel com casca completa (quickstart §1, M1–M2, M8–M13).

### Tests for User Story 1 ⚠️ (escrever primeiro, devem falhar)

- [ ] T022 [P] [US1] Criar fixtures em `apps/core/tests/conftest.py` (`cliente_htmx` com `HX-Request: true`; `cliente_boost` com `HX-Request` + `HX-Boosted`; `urls_com_secoes` que define `settings.ROOT_URLCONF = "apps.core.tests.urls_teste"`) e `apps/core/tests/urls_teste.py` (inclui as rotas reais + namespaces fictícios `produtos` (`lista` `/produtos/`, `novo` `/produtos/novo/`, `detalhe` `/produtos/<int:pk>/`), `movimentacoes` (`lista`), `alertas` (`relatorio`, `contador`) com views triviais que estendem `base.html`; e views de teste `/teste/mensagem/<nivel>/` (adiciona mensagem e redireciona), `/teste/erro-500/`, `/teste/erro-400/` (`SuspiciousOperation`), `/teste/erro-403/` (`PermissionDenied`))
- [ ] T023 [P] [US1] Escrever `apps/core/tests/test_layout.py` (variantes normal e HTMX/boost): FR-011 (primeiro elemento focável do `<body>` é `a.pular-conteudo[href="#conteudo"]`; marca "Consus" com link para `core:painel`; `<main id="conteudo">`; rodapé com `versao` e links para `/design/` e `/saude/`); FR-015 (`#toasts` com `role="status"`, `aria-live="polite"` e `hx-preserve`; `<template id="modelo-toast">`; após `/teste/mensagem/<nivel>/` a página mostra `[data-mensagens]` com aviso do nível mapeado por `MESSAGE_TAGS`); FR-016 (`#toasts` com `data-duracao-ms="5000"` e `data-maximo="3"`; `consus.js` lê esses atributos e aplica `role="alert"` a `alerta`/`erro`); FR-017 (`<dialog id="dialogo" aria-labelledby="dialogo-titulo">`; `consus.js` trata `showModal`, `close`, `fechar-dialogo` e `[data-toasts]`); FR-018 (`<body hx-boost="true">`; `hx-headers` com `X-CSRFToken` válido; `<meta name="htmx-config">` em JSON com `204→swap false`, `422→swap true`, `[45]..→swap false/error true`, `historyCacheSize 0`; `<script src=".../vendor/htmx.min.js">`; `consus.js` trata `htmx:responseError` e `htmx:sendError`); FR-019 (`<title>Painel — Consus</title>`); FR-020 (`<html lang="pt-BR">`); FR-021 (`<meta name="viewport">`; CSS da navegação com `overflow-x: auto` < 42rem; `.tabela-contenedor` com `overflow-x: auto`); FR-023 (`<meta name="color-scheme" content="light">`); Constituição II (`static/js/consus.js` com < 100 linhas)
- [ ] T024 [P] [US1] Escrever `apps/core/tests/test_navegacao.py`: FR-012 (4 itens na ordem Painel, Produtos, Movimentações, Alertas; em `/` só Painel tem `aria-current="page"`; com `urls_com_secoes`, `GET /produtos/12/` marca Produtos e não Painel; em `/design/` nenhum item fica ativo); FR-013 (urlconf real: Produtos, Movimentações e Alertas sem `href`, com `aria-disabled="true"` e "(em breve)"; com `urls_com_secoes`: viram links para `/produtos/`, `/movimentacoes/`, `/alertas/`); FR-014 (urlconf real: `#badge-alertas` vazio e sem atributos `hx-*`; com `urls_com_secoes`: `hx-get="/alertas/contador/"`, `hx-trigger="load, estoque-alterado from:body, every 60s"`, `hx-swap="innerHTML"`)
- [ ] T025 [P] [US1] Escrever `apps/core/tests/test_htmx.py`: FR-018 (`eh_parcial` falso para requisição comum e boost, verdadeiro para HTMX não boost); FR-015 (`disparar_toast(resp, "Salvo.")` grava `HX-Trigger` `{"toast": {"nivel": "sucesso", "texto": "Salvo."}}`; `nivel` fora de `sucesso|info|alerta|erro` ⇒ `ValueError`; texto vazio ou com mais de 200 caracteres ⇒ `ValueError`); FR-017 (`fechar_dialogo` acrescenta `fechar-dialogo` e se mescla com `toast` e com um `estoque-alterado` preexistente no mesmo cabeçalho)
- [ ] T026 [P] [US1] Escrever `apps/core/tests/test_painel.py` (normal, boost e HTMX parcial — todas recebem a página completa): FR-022 (`GET /` 200 com `<h1>` "Painel", `section#painel-kpis`, estado vazio "Os indicadores aparecem aqui" e ação "Cadastrar produto" desabilitada com "(em breve)"; com `urls_com_secoes` a ação vira link para `/produtos/novo/`; `POST /` → 405)
- [ ] T027 [P] [US1] Escrever `apps/core/tests/test_infra_arquivos.py` (verificação textual, sem Docker): FR-001 (`docker-compose.yml` com serviços `db` e `app`; `app` com `build.target: producao`, `env_file: .env` e porta `${CONSUS_PORTA:-8000}:8000`); FR-002 (`Dockerfile` executa `collectstatic --noinput` no estágio `producao`; `entrypoint.sh` executa `migrate --noinput`, usa `set -eu`, encerra com código ≠ 0 após esgotar 15 tentativas e só então chama `exec "$@"` em caso de sucesso); FR-003 (`app.depends_on.db.condition: service_healthy`; `db.healthcheck` com `pg_isready`); FR-004 (`.env.example` contém cada variável de data-model §1, cada uma precedida de comentário, e `DJANGO_SECRET_KEY` com valor de exemplo "troque-…"); FR-007 (volume nomeado `dados_postgres` montado em `/var/lib/postgresql/data`); FR-010 (estágio `producao` termina com `USER` não-root)
- [ ] T028 [P] [US1] Escrever `apps/core/tests/test_infra_docker.py` marcado `@pytest.mark.docker` (pula se `docker` indisponível): sobe `docker compose -p consus-teste up -d --build --wait` com `.env` gerado de `.env.example` e `CONSUS_PORTA` numa porta livre escolhida pelo teste; FR-001 (`GET /` 200 em até 120 s); FR-002 (logs do `app` contêm a execução do `migrate`); FR-003 (subida concluída mesmo com o `db` iniciando junto); FR-010 (`docker compose exec app id -u` ≠ `0`); FR-007 (após `restart`, `migrate` informa "No migrations to apply" e o volume persiste); `down -v` no teardown

### Implementation for User Story 1

- [ ] T029 [P] [US1] Implementar `apps/core/htmx.py`: `NIVEIS_TOAST = ("sucesso", "info", "alerta", "erro")`; `eh_parcial(request) -> bool` (`bool(request.htmx) and not request.htmx.boosted`); `disparar_toast(response, texto, nivel="sucesso")` (valida nível e texto de 1 a 200 caracteres; usa `django_htmx.http.trigger_client_event(response, "toast", {"nivel": nivel, "texto": texto})`); `fechar_dialogo(response)` (`trigger_client_event(response, "fechar-dialogo", {})`) — contracts/layout-e-htmx §4
- [ ] T030 [P] [US1] Implementar `apps/core/navegacao.py`: dataclass `ItemNavegacao(rotulo, rota, icone, secao)`; `ITENS_NAVEGACAO` = Painel (`core:painel`, `layout-dashboard`, rota exata), Produtos (`produtos:lista`, `package`, namespace `produtos`), Movimentações (`movimentacoes:lista`, `arrow-left-right`, namespace `movimentacoes`), Alertas (`alertas:relatorio`, `bell`, namespace `alertas`); `url_se_existir(nome) -> str | None` (captura `NoReverseMatch`); `resolver_itens(request) -> list[dict]` com `url`, `disponivel`, `ativo` (data-model §4)
- [ ] T031 [US1] Estender `apps/core/context_processors.py::consus` com `itens_navegacao` (de `resolver_itens`) e `badge_alertas_url` (`url_se_existir("alertas:contador")`) — depende de T030
- [ ] T032 [P] [US1] Implementar `apps/core/templatetags/__init__.py`, `apps/core/templatetags/consus.py` (inclusion tag `icone(nome, tamanho="sm", rotulo="")`) e `templates/components/icone.html` (`<svg class="icone icone--{{ tamanho }}">` + `<use href="{% static 'vendor/lucide/sprite.svg' %}#{{ nome }}">`; `aria-hidden="true" focusable="false"` sem rótulo; `role="img"` + `<title>` com rótulo) — contracts/componentes §2
- [ ] T033 [P] [US1] Implementar `templates/components/navegacao.html` conforme design-system §4.16 e contracts/layout-e-htmx §5 (`<nav aria-label="Principal">`, `aria-current="page"` no ativo, item indisponível como `<span aria-disabled="true">` com "(em breve)", slot `<span id="badge-alertas" class="navegacao__badge">` com atributos HTMX só quando `badge_alertas_url`)
- [ ] T034 [P] [US1] Implementar `templates/components/toast.html` (`.toast.toast--{{ nivel }}`, ícone do nível, texto, botão fechar `aria-label="Fechar notificação"`) e `templates/components/aviso.html` (`nivel`, `titulo` opcional, `texto`; ícone; `role="alert"` para `erro`) — design-system §4.12/§4.13
- [ ] T035 [P] [US1] Implementar `templates/components/estado_vazio.html` (`icone`, `titulo`, `descricao`, `acao_rotulo`, `acao_url` — `None` ⇒ botão secundário desabilitado com "(em breve)" —, `acao_secundaria`, `compacto`), alinhado à esquerda — design-system §4.14
- [ ] T036 [US1] Implementar `templates/base.html` conforme contracts/layout-e-htmx §1–§2: `lang="pt-BR"`, metas `viewport`/`color-scheme`/`htmx-config`, `<title>{% block titulo %}{% endblock %} — Consus</title>`, preload da Plex Sans Regular, CSS na ordem tokens → base → components → utilities, `htmx.min.js` e `consus.js` com `defer`, `<body hx-boost="true" hx-headers=…>`, link de pular, cabeçalho com marca + `{% include "components/navegacao.html" %}`, `<main id="conteudo" tabindex="-1">` com `[data-mensagens]` (mensagens como `aviso`), cabeçalho de página com blocos `sobretitulo`/`titulo`/`descricao`/`acoes`, bloco `conteudo`, rodapé, `#toasts` (`role="status"`, `aria-live="polite"`, `hx-preserve`, `data-duracao-ms="5000"`, `data-maximo="3"`), `<template id="modelo-toast">` e `<dialog id="dialogo" class="dialogo" aria-labelledby="dialogo-titulo">`
- [ ] T037 [US1] Acrescentar a `static/css/base.css` a casca da aplicação (design-system §4.16, §4.17, §5.1): `.pular-conteudo`, `.cabecalho-app` (sticky, `--header-h`, filete `--border-width-strong`), marca, `.navegacao` (estados D/H/F/ativo/indisponível, rolagem horizontal < 42rem), `.navegacao__badge`, contêiner do `<main>` (`--container-max`, `--page-margin`), `.cabecalho-pagina`, `.rodape-app`, região `.toasts` (fixa, `--z-toast`, largura total < 42rem) — só tokens
- [ ] T038 [US1] Implementar em `static/css/components.css` (`@layer components`) os blocos `.botao` (variantes, tamanhos, só-ícone e estados D/H/F/A/X/C de design-system §4.1), `.toast` (§4.12), `.aviso` (§4.13), `.estado-vazio` (§4.14) e `.icone` (traço 2 px, `stroke-linecap: square`, `stroke-linejoin: miter`, `--icon-sm`/`--icon-md`) — só tokens
- [ ] T039 [US1] Implementar `static/js/consus.js` (< 100 linhas, contracts/layout-e-htmx §8): toasts a partir do evento `toast` e de `[data-mensagens]` (no `DOMContentLoaded` e `htmx:load`), duração/máximo lidos de `data-duracao-ms`/`data-maximo`, pausa em hover/foco, `role="alert"` para `alerta`/`erro`, texto via `textContent`; abrir `#dialogo` com `showModal()` após `htmx:afterSwap`, guardar acionador em `htmx:beforeRequest`, devolver foco e limpar no `close`, fechar no evento `fechar-dialogo`, toasts em `dialog[open] [data-toasts]` quando houver; toasts de erro em `htmx:responseError` ("Não foi possível concluir a ação (erro N).") e `htmx:sendError` ("Sem conexão com o servidor.")
- [ ] T040 [US1] Implementar a view `painel` em `apps/core/views.py` (`@require_safe`; contexto `url_cadastro_produto = url_se_existir("produtos:novo")`), o template `apps/core/templates/core/painel.html` (estende `base.html`; título "Painel", descrição "Visão geral do estoque."; `section#painel-kpis` com `components/estado_vazio.html` "Os indicadores aparecem aqui") e a rota `""` → `core:painel` em `apps/core/urls.py` — contracts/rotas-core
- [ ] T041 [P] [US1] Implementar `entrypoint.sh` (POSIX `sh`, `set -eu`, executável): até 15 tentativas de `python manage.py migrate --noinput` com 2 s de intervalo, registrando cada falha; após a última falha, `exit 1`; em caso de sucesso, `exec "$@"` — FR-002/FR-003
- [ ] T042 [US1] Implementar `Dockerfile` com estágios `base` (`python:3.13-slim-bookworm`, binário do uv copiado de `ghcr.io/astral-sh/uv:<tag exata>`, `UV_PROJECT_ENVIRONMENT=/opt/venv`, `ENV PATH=/opt/venv/bin:$PATH`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `uv sync --frozen --no-dev --no-install-project`) e `producao` (código, `DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput`, usuário `consus` UID 1000, `USER consus`, `EXPOSE 8000`, `ENTRYPOINT ["./entrypoint.sh"]`, `CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]`) — research R4
- [ ] T043 [US1] Implementar `docker-compose.yml`: serviço `db` (`postgres:17-alpine`, `env_file: .env`, volume `dados_postgres:/var/lib/postgresql/data`, healthcheck `pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB`), serviço `app` (`build: {context: ., target: producao}`, `env_file: .env`, `ports: ["${CONSUS_PORTA:-8000}:8000"]`, `depends_on: {db: {condition: service_healthy}}`, `restart: unless-stopped`) e `volumes: {dados_postgres: {}}`
- [ ] T044 [US1] Atualizar `README.md` com a seção "Como executar" (pré-requisitos, `cp .env.example .env`, `docker compose up --build`, endereço, `/design/`, `/saude/`) apontando para `specs/001-fundacao-design-system/quickstart.md`
- [ ] T045 [US1] Rodar `uv run pytest apps/core/tests/test_layout.py apps/core/tests/test_navegacao.py apps/core/tests/test_htmx.py apps/core/tests/test_painel.py apps/core/tests/test_infra_arquivos.py` e `uv run pytest -m docker` até ficarem verdes; conferir quickstart §1 e cenários M1, M2, M8–M13

**Checkpoint**: MVP — o sistema sobe com um comando e a casca funciona sozinha

---

## Phase 4: User Story 2 - Consultar o catálogo vivo do design system (Priority: P2)

**Goal**: `/design/` mostra todos os tokens (com contraste calculado) e os 18 componentes em todos os estados, com demonstrações reais de diálogo (422/sucesso) e toasts.

**Independent Test**: abrir `/design/`, conferir sumário/âncoras/estados/trechos, abrir o diálogo de exemplo, enviar vazio e preenchido, disparar os 4 toasts (quickstart M3–M6).

### Tests for User Story 2 ⚠️

- [ ] T046 [P] [US2] Escrever `apps/core/tests/test_componentes.py` (render de cada template com parâmetros de contracts/componentes §2): FR-027 (os 16 templates de `templates/components/` renderizam sem erro; `components.css` define `.botao--primario`, `--secundario`, `--fantasma`, `--perigo`, `.tabela`, `.tabela--compacta`, `.badge` e variantes, `.cartao--interativo`; `campo.html` via `FORM_RENDERER` gera `<label for>`, `aria-describedby` com ids de ajuda/erro, `aria-invalid="true"` com erro e "(opcional)" quando `required=False`; `paginacao.html` mostra "1–25 de 132 produtos", `aria-label="Paginação"`, preserva `q` na query string e não renderiza com uma página; `delta.html` usa "−" e texto acessível; `kpi.html` com `valor=None` mostra "—"; `lista_barras.html` aplica mínimo de 2 %; `barra_categorias.html` tem barra `aria-hidden` e legenda com percentuais; `rastreador.html` tem `role="img"` com `aria-label` = resumo; `barra_progresso.html` tem `role="meter"` e `aria-valuenow/min/max`); FR-028 (`badge_estoque` `ok` → "OK" + `circle-check`; `reposicao` → "REPOSIÇÃO NECESSÁRIA" + `triangle-alert` + classe de alerta; `sem_estoque` → contém **ambos** "REPOSIÇÃO NECESSÁRIA" e "SEM ESTOQUE"; nome acessível "Situação: …"; nenhum caractere "⚠" no HTML; texto presente independentemente do ícone; situação desconhecida → vazio); FR-029 (`{% icone %}` sem rótulo → `aria-hidden="true"`; com rótulo → `role="img"` + `<title>`; nenhum emoji em `templates/**` e `apps/**/templates/**`)
- [ ] T047 [P] [US2] Escrever `apps/core/tests/test_design.py` (normal, boost e HTMX): FR-031 (`GET /design/` 200; sumário com links para as 9 âncoras de tokens e as 18 de componentes de data-model §7; tabela de contraste com as mesmas razões de `design_tokens.avaliar_pares()`; cada seção de componente com `<pre><code>`); FR-032 (`GET ?exemplo=dialogo` HTMX → fragmento com `id="dialogo-titulo"`, `autofocus` e `[data-toasts]`; sem HTMX → página completa; `POST exemplo=toast&nivel=<n>` HTMX → 204 + `HX-Trigger` com o nível, sem HTMX → 302 para `/design/#toast` + mensagem; `POST exemplo=formulario` inválido HTMX → **422** com `aria-invalid`, válido HTMX → 200 + `HX-Trigger` com `fechar-dialogo` e `toast` de sucesso; sem HTMX inválido → 422 página, válido → 302; `exemplo`/`nivel` inválidos → 400); FR-033 (com `DEBUG=False` continua 200; `<meta name="robots" content="noindex, nofollow">`; `/design/` não está em `itens_navegacao`; dados de exemplo rotulados "Exemplo")
- [ ] T048 [P] [US2] Escrever `apps/core/tests/test_comando_contraste.py`: FR-024 (`call_command("checar_contraste")` imprime uma linha por par com a razão e termina sem erro; com `PARES_CONTRASTE` substituído por um par reprovado o comando termina com código 1)

### Implementation for User Story 2

- [ ] T049 [US2] Implementar `apps/core/formularios.py` (`RenderizadorConsus(TemplatesSetting)` com `form_template_name = "components/formulario.html"` e `field_template_name = "components/campo.html"`) e configurar `FORM_RENDERER = "apps.core.formularios.RenderizadorConsus"` em `config/settings.py` (research R12)
- [ ] T050 [P] [US2] Implementar `templates/components/formulario.html` (erros não ligados a campo como `aviso` de erro; campos via `as_field_group`) e `templates/components/campo.html` (rótulo, "(opcional)", controle com `aria-describedby`/`aria-invalid`, ajuda, erro com ícone `circle-alert`) — design-system §4.2
- [ ] T051 [P] [US2] Implementar `templates/components/badge_estoque.html` (`situacao` = `"ok"` | `"reposicao"` | `"sem_estoque"`; badge composto para `sem_estoque`) e `templates/components/delta.html` (`valor`, `sentido` = `positivo` | `negativo` | `neutro`, `sufixo`) — design-system §4.4
- [ ] T052 [P] [US2] Implementar `templates/components/kpi.html` (`rotulo`, `valor`, `meta`, `delta`, `delta_sentido`, `icone`, `href`, `destaque` = `alerta` | `perigo`) — design-system §4.6
- [ ] T053 [P] [US2] Implementar `templates/components/lista_barras.html` (`titulo`, `rotulo_valor`, `itens` [{`rotulo`, `valor`, `href`}], largura `--valor` com mínimo de 2 % para valor > 0, estado vazio compacto) — design-system §4.7
- [ ] T054 [P] [US2] Implementar `templates/components/barra_categorias.html` (`titulo`, `segmentos` [{`rotulo`, `valor`, `tom`}], `total`, `unidade`; barra `aria-hidden`; legenda com valor e percentual) — design-system §4.8
- [ ] T055 [P] [US2] Implementar `templates/components/rastreador.html` (`titulo`, `blocos` [{`tom`, `rotulo`}], `resumo` obrigatório; `role="img"`; `title` por bloco) — design-system §4.9
- [ ] T056 [P] [US2] Implementar `templates/components/barra_progresso.html` (`rotulo`, `valor`, `maximo` > 0, `tom`; `role="meter"`; acima do máximo ⇒ barra cheia) — design-system §4.10
- [ ] T057 [P] [US2] Implementar `templates/components/dialogo.html` (blocos `titulo`, `descricao`, `corpo`, `rodape`; `tamanho` `sm`|`md`; `<h2 id="dialogo-titulo">`; fechar via `<form method="dialog">` quando HTMX e link "Voltar" em página; região `[data-toasts]` com `aria-live="polite"`) — design-system §4.11
- [ ] T058 [P] [US2] Implementar `templates/components/paginacao.html` (`pagina`, `rotulo_itens`, `alvo` opcional ⇒ `hx-get`/`hx-target`/`hx-push-url="true"`; `{% querystring page=n %}`; não renderiza com uma página) — design-system §4.15
- [ ] T059 [US2] Completar `static/css/components.css` com `.campo` (§4.2, incluindo erro com `box-shadow` inset), `.tabela-contenedor`/`.tabela` (§4.3, `thead` sticky, `.num`, linhas em alerta/sem estoque, densidades), `.badge` + composto + delta (§4.4), `.cartao` (§4.5), `.kpi` (§4.6), `.lista-barras` (§4.7), `.barra-categorias` (§4.8), `.rastreador` (§4.9), `.barra-progresso` (§4.10), `.dialogo` + `::backdrop` (§4.11), `.paginacao` (§4.15) — só tokens semânticos
- [ ] T060 [P] [US2] Implementar `apps/core/forms.py::FormularioExemplo` com `nome = CharField(max_length=120)` (obrigatório, aparado, ajuda "Dado fictício — nada é salvo.") e `quantidade = IntegerField(min_value=1)` (mensagem "Informe um número inteiro maior que zero.") — data-model §8
- [ ] T061 [US2] Implementar a view `design` em `apps/core/views.py` e a rota `design/` → `core:design` em `apps/core/urls.py`, conforme contracts/rotas-core: GET (catálogo; `?exemplo=dialogo` com `eh_parcial` → fragmento ou página), POST `exemplo=toast` (204 + `disparar_toast` ou 302 + mensagem) e `exemplo=formulario` (422 com fragmento/página; sucesso com `fechar_dialogo` + `disparar_toast` ou 302), 400 para valores inválidos; contexto com `tokens`, `pares_contraste` (`avaliar_pares()`), `COMPONENTES_CATALOGO` (18 âncoras de data-model §7) e dados fictícios rotulados "Exemplo"
- [ ] T062 [US2] Implementar `apps/core/templates/core/design.html` (bloco `head_extra` com `noindex, nofollow`; sumário; seções de tokens `cores`, `contraste`, `tipografia`, `espacamento`, `tamanhos`, `bordas`, `sombras`, `camadas`, `movimento`; 18 seções de componentes com todos os estados aplicáveis de design-system §4 e `<pre><code>` com o trecho de uso; botões de demonstração de diálogo e dos 4 toasts com `hx-get`/`hx-post` e fallback `href`/`form`)
- [ ] T063 [US2] Implementar `apps/core/templates/core/partials/design_dialogo.html` (estende `components/dialogo.html`; formulário `hx-post` com `hx-target="#dialogo"`, `autofocus` no primeiro campo) e `apps/core/templates/core/design_dialogo_pagina.html` (estende `base.html`; mesmo formulário em `.cartao` com `--form-max`)
- [ ] T064 [P] [US2] Implementar o comando `apps/core/management/__init__.py`, `apps/core/management/commands/__init__.py` e `apps/core/management/commands/checar_contraste.py` (tabela com primeiro plano, fundo, razão, mínimo e resultado a partir de `avaliar_pares()`; `sys.exit(1)` se algum par reprovar)
- [ ] T065 [US2] Rodar `uv run pytest apps/core/tests/test_componentes.py apps/core/tests/test_design.py apps/core/tests/test_comando_contraste.py` até ficar verde e conferir quickstart M3–M6

**Checkpoint**: catálogo completo; features 002–004 podem copiar os componentes

---

## Phase 5: User Story 3 - Verificar a saúde do sistema (Priority: P2)

**Goal**: `/saude/` responde 200/503 em JSON e o Compose usa a rota como healthcheck.

**Independent Test**: `curl -i /saude/` com banco no ar (200) e parado (503 em ≤ 3 s) — quickstart M14.

### Tests for User Story 3 ⚠️

- [ ] T066 [P] [US3] Escrever `apps/core/tests/test_saude.py` (requisição comum e com `HX-Request` devolvem o mesmo JSON): FR-034 (`GET` 200 com `Content-Type: application/json` e chaves exatamente `status`, `banco`, `versao`; `HEAD` sem corpo; `POST`/`PUT`/`DELETE` → 405 com `Allow` contendo `GET, HEAD`; `Cache-Control` com `no-store`; sem `Set-Cookie`; funciona com `Client(enforce_csrf_checks=True)`); FR-035 (banco ok → 200 `{"status": "ok", "banco": "ok", "versao": "0.1.0"}`; `connections.create_connection` monkeypatchado para levantar `OperationalError("senha=segredo host=db")` → 503 `{"status": "erro", "banco": "indisponivel", "versao": "0.1.0"}` sem o texto da exceção; a conexão criada é sempre fechada)
- [ ] T067 [P] [US3] Acrescentar a `apps/core/tests/test_infra_arquivos.py`: FR-036 (`app.healthcheck` em `docker-compose.yml` consulta `http://127.0.0.1:8000/saude/` com timeout; `db.healthcheck` presente e `app` depende de `db` saudável)
- [ ] T068 [P] [US3] Acrescentar a `apps/core/tests/test_infra_docker.py`: FR-036 (após `up --wait`, `docker compose ps` mostra `app` como `healthy`); FR-035 e SC-005 (com o banco no ar, 20 chamadas a `GET /saude/` com p95 < 1 s; `docker compose stop db` ⇒ responde 503 em ≤ 3 s; `start db` ⇒ volta a 200)

### Implementation for User Story 3

- [ ] T069 [US3] Implementar `apps/core/selectors.py::estado_saude() -> dict` (conexão nova via `connections.create_connection("default")`, `SELECT 1`, `close()` em `finally`; `DatabaseError` ⇒ `banco="indisponivel"`; retorna `{"status", "banco", "versao"}` de data-model §6) — research R17
- [ ] T070 [US3] Implementar a view `saude` em `apps/core/views.py` (`@require_safe`, `@never_cache`, `JsonResponse(estado, status=200|503)`) e a rota `saude/` → `core:saude` em `apps/core/urls.py`
- [ ] T071 [US3] Acrescentar ao serviço `app` de `docker-compose.yml` o `healthcheck` (`python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/saude/', timeout=3)"`, `interval: 10s`, `timeout: 5s`, `retries: 6`, `start_period: 20s`)
- [ ] T072 [US3] Rodar `uv run pytest apps/core/tests/test_saude.py apps/core/tests/test_infra_arquivos.py` e `uv run pytest -m docker`; conferir quickstart M14

**Checkpoint**: saúde operacional e integrada ao Compose

---

## Phase 6: User Story 4 - Ver páginas de erro no mesmo estilo (Priority: P3)

**Goal**: 400/403/404/500 estilizadas, a 500 sem dependência de banco; erros de requisições parciais viram toast.

**Independent Test**: `GET /nao-existe/` (404 estilizada) e erro forçado com `DEBUG` falso (500 estilizada) — quickstart M7/M15.

### Tests for User Story 4 ⚠️

- [ ] T073 [P] [US4] Escrever `apps/core/tests/test_erros.py`: FR-037 (`GET /nao-existe/` → 404 usando `404.html`, com navegação, "404", o caminho solicitado escapado em mono e link para `/`; com `HX-Request` o status continua 404); FR-038 (com `urls_com_secoes` e `raise_request_exception=False`, `/teste/erro-500/` → 500 com "500", sem traceback; `render_to_string("500.html")` sem `request` funciona e executa 0 consultas ao banco); FR-039 (`/teste/erro-403/` → 403 com `403.html` e navegação; `POST /design/` com `Client(enforce_csrf_checks=True)` sem token → 403 com `403_csrf.html` orientando "Recarregue a página"; `/teste/erro-400/` → 400 com `400.html`; todas com ação "Voltar ao Painel"); FR-018 (o `consus.js` registra `htmx:responseError` com a mensagem de erro e o status)

### Implementation for User Story 4

- [ ] T074 [US4] Implementar `templates/erro_base.html` (autônomo: `<head>` com os 4 CSS via `{% static %}`, cabeçalho só com a marca, bloco de erro alinhado à esquerda nas colunas 1–8, sem context processors nem consultas) e `templates/500.html`, `templates/400.html`, `templates/403_csrf.html` estendendo-o (código no estilo código-erro, título, descrição sem jargão, "Voltar ao Painel") — design-system §5.5, research R16
- [ ] T075 [P] [US4] Implementar `templates/404.html` e `templates/403.html` estendendo `base.html` (código, título, descrição, `request.path` em mono na 404, ação primária "Voltar ao Painel")
- [ ] T076 [US4] Acrescentar `.pagina-erro` (código-erro, espaçamento `--space-10` no topo, coluna 1–8) a `static/css/components.css` — só tokens
- [ ] T077 [US4] Rodar `uv run pytest apps/core/tests/test_erros.py` até ficar verde e conferir quickstart M7

**Checkpoint**: todas as falhas têm página no visual do Consus

---

## Phase 7: User Story 5 - Executar os quality gates do projeto (Priority: P3)

**Goal**: lint, formatação, testes (SQLite e PostgreSQL), cobertura, migrações e lock verificáveis por comandos únicos.

**Independent Test**: comandos do quickstart §3 terminam com sucesso em clone limpo.

### Tests for User Story 5 ⚠️

- [ ] T078 [P] [US5] Escrever `apps/core/tests/test_qualidade.py`: FR-040 (`ruff check .` e `ruff format --check .` em subprocesso terminam com código 0; pula se `ruff` ausente); FR-041 (`pyproject.toml` lido com `tomllib` tem `fail_under >= 90` e `source` com `apps` e `config`; `docker-compose.yml` tem serviço `testes` com `profiles: ["testes"]`, `target: testes` e `DATABASE_URL` apontando para `db`); FR-042 (`uv.lock` existe e `uv lock --check` termina com 0 — pula se `uv` ausente; `call_command("makemigrations", "--check", "--dry-run")` não encerra com erro)
- [ ] T079 [P] [US5] Acrescentar a `apps/core/tests/test_infra_docker.py`: FR-041 (`docker compose --profile testes run --rm testes` termina com código 0 contra o PostgreSQL)

### Implementation for User Story 5

- [ ] T080 [US5] Acrescentar ao `Dockerfile` o estágio `testes` (a partir de `base`: `uv sync --frozen --no-install-project` com o grupo dev, código copiado, `CMD ["pytest"]`)
- [ ] T081 [US5] Acrescentar a `docker-compose.yml` o serviço `testes` (`profiles: ["testes"]`, `build: {context: ., target: testes}`, `env_file: .env`, `environment: {DJANGO_DEBUG: "false"}`, `depends_on: {db: {condition: service_healthy}}`, `command: ["pytest"]`)
- [ ] T082 [US5] Acrescentar ao `README.md` a seção "Qualidade" com os comandos de quickstart §3 (`uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, `uv run python manage.py makemigrations --check --dry-run`, `uv run python manage.py checar_contraste`, `docker compose --profile testes run --rm testes`, `uv run pytest -m docker`)
- [ ] T083 [US5] Executar todos os gates da Constituição (`ruff check`, `ruff format --check`, `pytest` em SQLite e via serviço `testes` no PostgreSQL, `makemigrations --check`, `docker compose build`) e corrigir violações até ficarem verdes

**Checkpoint**: gates verdes — feature pronta para merge em `develop`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: critérios de sucesso transversais e coerência documentação × implementação

- [ ] T084 [P] Acrescentar a `apps/core/tests/test_assets.py` o orçamento de SC-010 (soma de `static/css/*.css`, `static/js/consus.js`, `static/vendor/htmx.min.js`, `static/vendor/lucide/sprite.svg` e das 5 fontes ≤ 300 KB) e a verificação de que `config/settings.py` usa armazenamento com manifesto (nomes com hash para cache longo)
- [ ] T085 [P] Conferir `docs/design/design-system.md` × `static/css/tokens.css` × `/design/`: qualquer divergência encontrada na implementação vira ajuste no documento com incremento de versão (constituição IV) e atualização de `PARES_CONTRASTE`
- [ ] T086 [P] Atualizar `static/vendor/README.md` com as versões e hashes finais de HTMX, Plex e Lucide
- [ ] T087 Executar o quickstart completo (§1–§3, cenários M1–M14) e registrar o resultado na descrição do PR
- [ ] T088 Revisar cobertura (`uv run pytest --cov-report=html`) garantindo ≥ 90 % e 100 % em `apps/core/selectors.py`, `apps/core/htmx.py`, `apps/core/navegacao.py` e `apps/core/design_tokens.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup — BLOQUEIA todas as histórias
- **US1 (Phase 3)**: depende da Foundational — entrega `base.html`, componentes da casca e Docker
- **US2 (Phase 4)**: depende da Foundational e de `base.html`/`icone`/`estado_vazio`/`toast`/`aviso` da US1 (T032–T036)
- **US3 (Phase 5)**: depende da Foundational; T071 depende de T043 (compose da US1)
- **US4 (Phase 6)**: depende da Foundational e de `base.html` (T036); o teste de CSRF usa `/design/` (T061)
- **US5 (Phase 7)**: depende do Setup/Foundational; T080/T081 dependem de T042/T043
- **Polish (Phase 8)**: depois de todas as histórias desejadas

### User Story Dependencies

- **US1 (P1)**: independente após a Foundational — MVP
- **US2 (P2)**: usa a casca da US1; testável isoladamente pelo catálogo
- **US3 (P2)**: view e seletor independentes; só o healthcheck do Compose toca arquivo da US1
- **US4 (P3)**: usa `base.html` da US1
- **US5 (P3)**: estende Dockerfile/Compose da US1; testes de qualidade independentes

### Within Each User Story

- Testes escritos e FALHANDO antes da implementação (Constituição III)
- Utilitários (`htmx.py`, `navegacao.py`, `selectors.py`) antes das views
- Componentes antes das páginas que os usam
- Arquivos compartilhados (`base.css`, `components.css`, `views.py`, `urls.py`, `docker-compose.yml`, `Dockerfile`) editados sequencialmente

### Parallel Opportunities

- Setup: T004–T008 em paralelo
- Foundational: T010–T012 (testes) em paralelo; T014, T017, T020 em paralelo
- US1: T022–T028 (testes) em paralelo; T029, T030, T032–T035, T041 em paralelo
- US2: T046–T048 em paralelo; T050–T058, T060, T064 em paralelo (um arquivo cada)
- US3 e US4 podem ser feitas em paralelo depois da US1 (arquivos distintos, exceto `views.py`/`urls.py` — coordenar)

---

## Parallel Example: User Story 2

```bash
# Testes da US2 juntos:
Task: "Escrever apps/core/tests/test_componentes.py (FR-027, FR-028, FR-029)"
Task: "Escrever apps/core/tests/test_design.py (FR-031, FR-032, FR-033)"
Task: "Escrever apps/core/tests/test_comando_contraste.py (FR-024)"

# Templates de componentes juntos (um arquivo cada):
Task: "templates/components/badge_estoque.html + delta.html"
Task: "templates/components/kpi.html"
Task: "templates/components/lista_barras.html"
Task: "templates/components/barra_categorias.html"
Task: "templates/components/rastreador.html"
Task: "templates/components/barra_progresso.html"
Task: "templates/components/dialogo.html"
Task: "templates/components/paginacao.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (Setup) → Phase 2 (Foundational)
2. Phase 3 (US1): o sistema sobe com `docker compose up --build` e mostra o Painel
3. **STOP and VALIDATE**: quickstart §1 + M1–M2 — já é demonstrável ao professor

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 → casca + Docker (MVP)
3. US2 → catálogo (desbloqueia a construção visual de 002–004)
4. US3 → saúde + healthcheck
5. US4 → páginas de erro
6. US5 → gates no PostgreSQL e documentação de qualidade
7. Polish → orçamento de peso, coerência do design system, quickstart completo

### Rastreabilidade FR/SC → testes

| Requisito | Tarefa(s) de teste |
|----|--------------------|
| FR-001 | T027, T028 |
| FR-002 | T027, T028 |
| FR-003 | T027, T028 |
| FR-004 | T010, T027 |
| FR-005 | T010 |
| FR-006 | T010 |
| FR-007 | T027, T028 |
| FR-008 | T012 |
| FR-009 | T010 |
| FR-010 | T027, T028 |
| FR-011 | T023 |
| FR-012 | T024 |
| FR-013 | T024 |
| FR-014 | T024 |
| FR-015 | T023, T025 |
| FR-016 | T023 |
| FR-017 | T023, T025 |
| FR-018 | T023, T025, T073 |
| FR-019 | T023 |
| FR-020 | T010, T023 |
| FR-021 | T023 |
| FR-022 | T026 |
| FR-023 | T011, T023 |
| FR-024 | T011, T048 |
| FR-025 | T011 |
| FR-026 | T011, T012 |
| FR-027 | T046 |
| FR-028 | T046 |
| FR-029 | T012, T046 |
| FR-030 | T011 |
| FR-031 | T047 |
| FR-032 | T047 |
| FR-033 | T047 |
| FR-034 | T066 |
| FR-035 | T066, T068 |
| FR-036 | T067, T068 |
| FR-037 | T073 |
| FR-038 | T073 |
| FR-039 | T073 |
| FR-040 | T078 |
| FR-041 | T078, T079 |
| FR-042 | T078 |
| FR-043 | T010 |
| FR-044 | T010 |
| SC-002 / SC-003 | T011 |
| SC-004 | T047 |
| SC-005 | T068 |
| SC-007 | T012 |
| SC-009 | T078, T079, T083 |
| SC-010 | T084 |
| SC-001, SC-006, SC-008 | T087 (quickstart manual: §1, M2, M10) |

---

## Notes

- [P] = arquivos diferentes, sem dependência pendente
- [USx] mapeia a tarefa à história para rastreabilidade
- Testes primeiro e falhando; commits por tarefa ou grupo lógico (Conventional Commits em pt-BR)
- Nenhum valor visual fora de `static/css/tokens.css`; dúvidas visuais se resolvem em `docs/design/design-system.md`
- Pare em qualquer checkpoint para validar a história de forma independente
