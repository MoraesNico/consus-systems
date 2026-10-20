# Implementation Plan: Fundação do Consus e Design System

**Branch**: `001-fundacao-design-system` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-fundacao-design-system/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Criar o esqueleto executável do Consus: projeto Django 5.2 (`config/` + `apps/core`) configurado
só por variáveis de ambiente, empacotado em Docker (Gunicorn + WhiteNoise, PostgreSQL 17 via
Compose, migrações no entrypoint, `collectstatic` no build, healthcheck por `/saude/`), com a
casca HTMX (`base.html` com navegação auto-ativada por nome de rota, slot do badge de alertas,
região de toasts `aria-live`, `<dialog>` único, `consus.js` < 100 linhas), o design system
**High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise** implementado como tokens CSS
(`docs/design/design-system.md` é a fonte de verdade) + 16 componentes de template, o catálogo
vivo `/design/` (com demonstrações reais de diálogo/422/toasts), páginas de erro estilizadas e os
quality gates (Ruff, pytest-django com cobertura ≥ 90 %, verificação automática de contraste e de
"valores mágicos"). Decisões técnicas em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.2 LTS, django-htmx ≥ 1.23, HTMX 2.0.x (vendorizado),
dj-database-url ≥ 2.3, psycopg[binary] ≥ 3.2, Gunicorn ≥ 23, WhiteNoise ≥ 6.8; fontes IBM Plex
Sans/Mono (OFL) e ícones Lucide (ISC) vendorizados. Dev: pytest, pytest-django, pytest-cov, Ruff;
gerenciador uv (`pyproject.toml` + `uv.lock`).

**Storage**: PostgreSQL 17 (Compose, volume `dados_postgres`); SQLite em desenvolvimento/testes.
Nenhum modelo próprio nesta feature (só migrações de `contenttypes` e `sessions`).

**Testing**: pytest + pytest-django + pytest-cov (`fail_under = 90`); testes de configuração em
subprocesso; teste de integração Docker opt-in (`-m docker`); suíte também roda no PostgreSQL
via serviço `testes` (perfil do Compose).

**Target Platform**: contêiner Linux (python:3.13-slim-bookworm) servido a navegadores
evergreen (2 últimas versões de Chrome, Edge, Firefox, Safari).

**Project Type**: aplicação web renderizada no servidor (Django + HTMX, sem build de frontend).

**Performance Goals**: `/saude/` < 1 s (p95) e ≤ 3 s com banco fora; primeira visita ≤ 300 KB de
recursos (CSS + JS + fontes + sprite), com cache imutável (manifesto do WhiteNoise).

**Constraints**: sem CDN em execução; JS próprio < 100 linhas; todo valor visual em
`static/css/tokens.css`; contraste WCAG 2.1 AA verificado por teste; funciona sem JavaScript;
configuração só por ambiente; processo sem root.

**Scale/Scope**: uso local monousuário (professor/colegas); 3 rotas + 5 tratadores de erro;
1 layout; 16 templates de componentes; 18 seções de componentes + 9 de tokens no catálogo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra | Avaliação | Evidência no plano |
|-------------------|-----------|--------------------|
| **I. Integridade do Estoque** | ✅ Não se aplica diretamente (sem saldo nesta feature) e é **protegido**: admin não exposto, sem `django.contrib.admin`/`auth` (FR-044), eliminando a via de edição direta de saldo. | research R18; FR-044 |
| **II. Interface dirigida pelo servidor** | ✅ HTML renderizado no servidor; HTMX 2 vendorizado; `hx-boost`, `HX-Trigger` (`toast`, `fechar-dialogo`), 422 configurado; `consus.js` < 100 linhas (teste conta as linhas); tudo funciona sem JS (fallbacks de diálogo e toasts); views usam `request.htmx` via `eh_parcial`. | R6, R7, R8; contracts/layout-e-htmx.md |
| **III. Testes primeiro** | ✅ Cada FR-001…FR-044 tem tarefa de teste que o cita, escrita antes da implementação (tasks.md); testes de view cobrem variante normal e HTMX; cobertura ≥ 90 % (inclui `selectors.py`); suíte em SQLite e PostgreSQL. `core` não tem `models.py`/`services.py` (não há escrita de domínio). | R15; tasks.md |
| **IV. Design system** | ✅ `docs/design/design-system.md` como fonte de verdade; tokens únicos em `tokens.css`; teste reprova literais fora dele; grade de 12 colunas e base 4/8 px; bordas 1 px (2 px foco/destaque), raio 0–2 px, sombras sólidas; paleta tinta/papel + 1 acento + semânticas; tabelas 32/40 px com mono tabular à direita; contraste AA testado; alerta = ícone SVG + "REPOSIÇÃO NECESSÁRIA" + cor; `aria-live`; pt-BR com `dd/mm/aaaa HH:MM` e milhar ".". | R10, R11, R12, R13, R14 |
| **V. Simplicidade, containers, 12-factor** | ✅ `docker compose up --build` + cópia do `.env.example`; config só por ambiente; segredos fora do repositório; cada dependência justificada (R2 — `dj-database-url` é a única não citada na constituição, justificada); HTMX/fontes/ícones locais. | R2, R3, R4 |
| Restrições técnicas (Python 3.13, Django 5.2, PG 17/SQLite, Gunicorn+WhiteNoise, pytest/Ruff, domínio em pt, estrutura `config/` + `apps/`) | ✅ Todas atendidas. | Technical Context |
| Fluxo (SDD, branch `NNN-slug`, Conventional Commits pt, quality gates: `ruff check`, `ruff format --check`, `pytest`, `makemigrations --check`, build Docker) | ✅ Gates viram tarefas e testes (FR-040…FR-042, teste Docker). | quickstart.md §3 |

**Resultado do gate (pré-pesquisa)**: aprovado, sem violações.

**Re-check pós-design (Fase 1)**: aprovado. O design acrescentou dois pontos que reforçam a
constituição: (a) `apps/core/design_tokens.py` torna a regra "tokens primeiro" e o contraste AA
verificáveis no CI; (b) o renderizador de formulários padrão garante rótulo/erro acessíveis em
todas as features. Nenhum item entrou em *Complexity Tracking*.

## Project Structure

### Documentation (this feature)

```text
specs/001-fundacao-design-system/
├── plan.md              # Este arquivo
├── research.md          # Fase 0 — decisões R1–R19 + propostas de ajuste ao contrato
├── data-model.md        # Fase 1 — estruturas de configuração e contrato (sem tabelas)
├── quickstart.md        # Fase 1 — validação ponta a ponta
├── contracts/
│   ├── rotas-core.md    # HTTP: /, /design/, /saude/, tratadores de erro
│   ├── layout-e-htmx.md # base.html, ids, htmx-config, eventos, utilitários, navegação, diálogo
│   └── componentes.md   # API dos componentes (classes, templates, template tags)
├── checklists/
│   ├── requirements.md  # qualidade da spec (/speckit-specify)
│   ├── ux.md            # checklist de domínio: UX/acessibilidade/design system (/speckit-checklist)
│   └── operacao.md      # checklist de domínio: contêineres/configuração/qualidade (/speckit-checklist)
└── tasks.md             # Fase 2 (/speckit-tasks)

docs/design/
├── referencias.md       # pesquisa de referências (shadcn, Tremor, Carbon, curadoria, RUI)
└── design-system.md     # FONTE DE VERDADE VISUAL (tokens, contraste, componentes)
```

### Source Code (repository root)

```text
pyproject.toml                # uv: dependências, grupo dev, Ruff, pytest, coverage
uv.lock
manage.py
conftest.py                   # storage de estáticos simples na suíte
Dockerfile                    # estágios base / testes / producao
docker-compose.yml            # db (postgres:17-alpine) + app + testes (perfil)
.dockerignore
.env.example
entrypoint.sh                 # migrate com retry + exec "$@"

config/
├── __init__.py               # __version__ = "0.1.0"
├── settings.py               # 12-factor (R3), segurança (R18), logs (R19), pt-BR (R14)
├── urls.py                   # include("apps.core.urls") ; features 002–004 acrescentam includes
├── wsgi.py
├── asgi.py
└── formatos/
    ├── __init__.py
    └── pt_BR/
        ├── __init__.py
        └── formats.py        # d/m/Y H:i, milhar "."

apps/
├── __init__.py
└── core/
    ├── __init__.py
    ├── apps.py               # CoreConfig(name="apps.core", label="core")
    ├── urls.py               # app_name="core": painel, design, saude
    ├── views.py              # painel, design (GET/POST demos), saude
    ├── selectors.py          # estado_saude()
    ├── navegacao.py          # ItemNavegacao, ITENS_NAVEGACAO, resolver_itens(), url_se_existir()
    ├── context_processors.py # consus(): itens_navegacao, badge_alertas_url, versao
    ├── htmx.py               # eh_parcial, disparar_toast, fechar_dialogo
    ├── formularios.py        # RenderizadorConsus (FORM_RENDERER)
    ├── forms.py              # FormularioExemplo (demo do catálogo)
    ├── design_tokens.py      # leitura de tokens.css, WCAG, PARES_CONTRASTE
    ├── management/
    │   ├── __init__.py
    │   └── commands/
    │       ├── __init__.py
    │       └── checar_contraste.py
    ├── templatetags/
    │   ├── __init__.py
    │   └── consus.py         # {% icone %}
    ├── templates/core/
    │   ├── painel.html
    │   ├── design.html
    │   ├── design_dialogo_pagina.html
    │   └── partials/
    │       └── design_dialogo.html
    └── tests/
        ├── __init__.py
        ├── conftest.py               # cliente HTMX, urlconf de teste
        ├── urls_teste.py             # rotas fictícias produtos/movimentacoes/alertas + views que falham
        ├── test_configuracao.py      # FR-004/005/006/009/020/043/044
        ├── test_infra_arquivos.py    # FR-001/002/003/007/010/036/042
        ├── test_infra_docker.py      # @docker: FR-001/002/003/007/010/035/036/041
        ├── test_layout.py            # FR-011/015/016/017/018/019/020/021/023(tema)
        ├── test_navegacao.py         # FR-012/013/014
        ├── test_htmx.py              # FR-015/017/018 (utilitários)
        ├── test_painel.py            # FR-022
        ├── test_tokens.py            # FR-023/024/025/026/030
        ├── test_componentes.py       # FR-027/028/029
        ├── test_assets.py            # FR-008/026/029
        ├── test_design.py            # FR-031/032/033
        ├── test_saude.py             # FR-034/035
        ├── test_erros.py             # FR-037/038/039
        ├── test_comando_contraste.py # FR-024
        └── test_qualidade.py         # FR-040/041/042

templates/
├── base.html
├── erro_base.html            # autônomo (500, 400, 403_csrf)
├── 400.html  403.html  403_csrf.html  404.html  500.html
└── components/
    ├── icone.html  formulario.html  campo.html
    ├── badge_estoque.html  delta.html  kpi.html
    ├── lista_barras.html  barra_categorias.html  rastreador.html  barra_progresso.html
    ├── dialogo.html  toast.html  aviso.html  estado_vazio.html
    └── paginacao.html  navegacao.html

static/
├── css/
│   ├── tokens.css            # ÚNICA fonte de valores visuais
│   ├── base.css
│   ├── components.css
│   └── utilities.css
├── js/
│   └── consus.js             # < 100 linhas
├── vendor/
│   ├── README.md             # versões, origens, SHA-256, licenças
│   ├── htmx.min.js           # HTMX 2.0.x
│   └── lucide/
│       ├── sprite.svg
│       └── LICENSE
└── fonts/
    ├── IBMPlexSans-Regular-Latin1.woff2
    ├── IBMPlexSans-Medium-Latin1.woff2
    ├── IBMPlexSans-SemiBold-Latin1.woff2
    ├── IBMPlexMono-Regular-Latin1.woff2
    ├── IBMPlexMono-SemiBold-Latin1.woff2
    └── OFL.txt
```

**Structure Decision**: aplicação web Django única, exatamente na estrutura de
`docs/arquitetura.md` (`config/`, `apps/core`, `templates/base.html`, `templates/components/`,
`static/css/{tokens,base,components,utilities}.css`, `static/js/consus.js`,
`static/vendor/htmx.min.js`, `static/fonts/`, `Dockerfile`, `docker-compose.yml`, `.env.example`,
`entrypoint.sh`, `pyproject.toml`). Acréscimos que o contrato não lista, todos internos a
diretórios do contrato: `config/formatos/` (formatos pt-BR), `static/vendor/lucide/` (ícones
vendorizados), `templates/erro_base.html` e templates de erro, `conftest.py` na raiz. Os apps
`produtos`, `movimentacoes` e `alertas` **não** são criados aqui.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação. (Registro de decisões que poderiam parecer complexidade, todas justificadas em
research.md: estágio `testes` no Dockerfile para rodar a suíte no PostgreSQL — R4; renderizador
de formulários próprio — R12; módulo de verificação de tokens — R11.)
