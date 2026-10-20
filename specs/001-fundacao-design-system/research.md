# Research: Fundação do Consus e Design System

**Feature**: `001-fundacao-design-system` · **Data**: 2026-10-20 · **Spec**: [spec.md](spec.md)

Fase 0 do `/speckit-plan`. Cada decisão segue o formato *Decision / Rationale / Alternatives
considered*. A pesquisa visual (referências de design) está em
[`docs/design/referencias.md`](../../docs/design/referencias.md) e não é repetida aqui; este
arquivo cobre as decisões técnicas. Não restou nenhum `NEEDS CLARIFICATION` no Technical Context.

---

## R1. Estrutura do projeto

- **Decision**: projeto Django único com `config/` (settings, urls, wsgi, asgi) e `apps/core/`
  (app de rótulo `core`, `name="apps.core"`); templates globais em `templates/` (layout, páginas
  de erro e `components/`) e por app em `apps/core/templates/core/`; estáticos em `static/`. Esta
  feature cria somente `apps/__init__.py` e `apps/core/`; `produtos`, `movimentacoes` e `alertas`
  nascem nas features 002–004.
- **Rationale**: é exatamente a estrutura de `docs/arquitetura.md` e da constituição. Um único
  `settings.py` lido do ambiente atende ao 12-factor sem módulos `dev/prod`.
- **Alternatives considered**: settings divididos (`base/dev/prod`) — rejeitado: duplicação e
  divergência de comportamento entre ambientes, contra o fator III (config no ambiente);
  `src/` layout — rejeitado: diverge do contrato.

## R2. Dependências e gerenciador

- **Decision**: `pyproject.toml` + `uv.lock` (uv), `requires-python = ">=3.13,<3.14"`,
  `[tool.uv] package = false` (aplicação, não biblioteca). Dependências de execução:

  | Pacote | Faixa | Justificativa (Constituição V — YAGNI) |
  |--------|-------|----------------------------------------|
  | `django` | `>=5.2,<5.3` | framework exigido (LTS) |
  | `django-htmx` | `>=1.23` | `request.htmx` e `trigger_client_event` exigidos pelo princípio II |
  | `psycopg[binary]` | `>=3.2` | driver do PostgreSQL 17 |
  | `dj-database-url` | `>=2.3` | traduz `DATABASE_URL` (FR-004/FR-006) com escape, opções e SQLite em ~1 linha; reimplementar o parser não traz ganho |
  | `gunicorn` | `>=23` | servidor exigido |
  | `whitenoise` | `>=6.8` | estáticos exigidos (compressão + manifesto, sem Nginx) |

  Grupo `dev`: `pytest`, `pytest-django`, `pytest-cov`, `ruff`. **Nenhuma** outra dependência
  (sem `django-environ`, `beautifulsoup4`, `PyYAML`, Playwright).
- **Rationale**: uv é rápido, gera lock reprodutível multiplataforma e tem imagem oficial para
  copiar o binário no Dockerfile. Faixas com limite superior na série do Django evitam saltos de
  versão; o lock fixa o exato (FR-042).
- **Alternatives considered**: `pip-tools`/`requirements.txt` — rejeitado: dois arquivos, sem
  grupos; Poetry — rejeitado: mais lento e com build backend desnecessário; `django-environ` —
  rejeitado: só `DATABASE_URL` precisa de parsing não trivial.

## R3. Configuração por variáveis de ambiente

- **Decision**: `config/settings.py` lê `os.environ` com pequenos auxiliares (`_bool`, `_lista`).
  `DEBUG` padrão `false`. Se `DEBUG` é falso e `DJANGO_SECRET_KEY` não existe →
  `ImproperlyConfigured("Defina DJANGO_SECRET_KEY …")` (FR-005); com `DEBUG` verdadeiro usa uma
  chave de desenvolvimento explícita. `DATABASES["default"] = dj_database_url.config(default=
  f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=60, conn_health_checks=True)`; para
  PostgreSQL acrescenta `OPTIONS["connect_timeout"] = DATABASE_CONNECT_TIMEOUT` (padrão 2 s).
  Lista completa de variáveis em [data-model.md](data-model.md#variáveis-de-ambiente).
- **Rationale**: 12-factor; falha cedo e explícita em produção; SQLite sem configuração para
  desenvolvimento e testes (FR-006); `connect_timeout` sustenta o limite de 2 s de `/saude/`.
- **Alternatives considered**: arquivo `.env` lido pela aplicação (`python-dotenv`) — rejeitado:
  o Compose já injeta `env_file`; localmente o desenvolvedor exporta variáveis ou usa os padrões.

## R4. Contêineres (Dockerfile, Compose, entrypoint)

- **Decision**:
  - `Dockerfile` multi-estágio sobre `python:3.13-slim-bookworm`, com o binário do uv copiado da
    imagem oficial `ghcr.io/astral-sh/uv` (tag exata fixada na implementação). Estágio `base`:
    `uv sync --frozen --no-dev --no-install-project` em `/opt/venv`. Estágio `testes`: `base` +
    grupo dev + código (usado pelo serviço de testes). Estágio `producao`: `base` + código +
    `collectstatic --noinput` **no build** (com chave temporária só de build) + usuário
    `consus` (UID 1000, sem privilégios, FR-010) + `ENTRYPOINT ["./entrypoint.sh"]` +
    `CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]`.
  - `entrypoint.sh` (POSIX sh, `set -eu`): tenta `python manage.py migrate --noinput` até 15 vezes
    com 2 s de intervalo (cobre banco ainda subindo, FR-003) e termina com `exec "$@"`.
  - `docker-compose.yml`: serviço `db` (`postgres:17-alpine`, volume nomeado `dados_postgres`
    (FR-007), `healthcheck: pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB`); serviço `app`
    (`build: target: producao`, `env_file: .env`, `ports: "${CONSUS_PORTA:-8000}:8000"`,
    `depends_on: db: condition: service_healthy`, `healthcheck` com
    `python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/saude/', timeout=3)"`
    (FR-036); serviço `testes` no perfil `testes` (`target: testes`, mesma `DATABASE_URL`,
    `command: pytest`) para FR-041 no PostgreSQL.
  - `.dockerignore`: `.git`, `.venv`, `**/__pycache__`, `*.sqlite3`, `.env`, `staticfiles/`,
    `specs/`, `docs/`, `.specify/`, `.claude/`.
- **Rationale**: separa build (estáticos imutáveis), release (migrate no entrypoint) e run
  (gunicorn) — fatores V e IX; imagem sem ferramentas de build nem dependências de teste;
  `healthcheck` em Python evita instalar `curl` na imagem slim; `depends_on: service_healthy` +
  retry no entrypoint satisfazem FR-003 mesmo em reinícios do banco.
- **Alternatives considered**: `collectstatic` no entrypoint — rejeitado: escreve em disco a
  cada partida, atrasa a subida e exige diretório gravável; ambos atendem "automático", mas no
  build o artefato é reprodutível. Script `wait-for-it`/`netcat` — rejeitado: dependência extra;
  o retry do `migrate` já testa o banco de verdade. `postgres:17` (Debian) — aceitável, mas a
  variante alpine é ~4× menor.

## R5. Servidor e arquivos estáticos

- **Decision**: Gunicorn com workers síncronos (`WEB_CONCURRENCY`, padrão 3, lido nativamente
  pelo Gunicorn); WhiteNoise como middleware logo após `SecurityMiddleware`;
  `STORAGES["staticfiles"]` = `whitenoise.storage.CompressedManifestStaticFilesStorage` (nomes
  com hash ⇒ cache longo, SC-010). Nos testes, um `conftest.py` na raiz troca o storage por
  `django.contrib.staticfiles.storage.StaticFilesStorage` (o manifesto não existe na suíte).
- **Rationale**: exigência da constituição; manifesto garante que fontes, CSS e sprite fiquem em
  cache imutável no navegador.
- **Alternatives considered**: Nginx na frente — rejeitado (YAGNI para uso local); Uvicorn/ASGI —
  sem benefício (nenhum recurso assíncrono).

## R6. HTMX e aprimoramento progressivo

- **Decision**: HTMX **2.0.x** (versão exata e SHA-256 registrados em `static/vendor/README.md`)
  em `static/vendor/htmx.min.js`; `django_htmx.middleware.HtmxMiddleware`. No `<body>`:
  `hx-boost="true"` e `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`. Configuração por
  `<meta name="htmx-config">`: `responseHandling` = `204 → sem troca`; `2xx/3xx → troca`;
  `422 → troca`; `4xx/5xx → sem troca, erro`; `includeIndicatorStyles: false`;
  `historyCacheSize: 0` (evita restaurar páginas com saldo desatualizado). Regra de renderização
  para as views de todas as features: `apps.core.htmx.eh_parcial(request)` =
  `request.htmx and not request.htmx.boosted` → template parcial; senão → página completa
  (navegação "boostada" recebe a página inteira e o HTMX troca o `<body>`, atualizando o item
  ativo da navegação e o `<title>`).
- **Rationale**: a navegação boostada continua sendo HTML completo (funciona sem JS — FR-018);
  a configuração 422 é a convenção do contrato; desligar o cache de histórico evita mostrar saldo
  velho ao voltar. `includeIndicatorStyles: false` porque os indicadores são estilizados pelo
  design system (sem `<style>` injetado).
- **Alternatives considered**: `hx-target="#conteudo"` + `hx-select` no boost — rejeitado: o
  item ativo da navegação e o badge ficariam desatualizados; extensões HTMX (`response-targets`)
  — rejeitado: `responseHandling` nativo do HTMX 2 resolve.

## R7. Toasts (notificações temporárias)

- **Decision**: duas origens, uma aparência.
  1. **Respostas parciais**: evento `toast` no cabeçalho `HX-Trigger` com
     `{"nivel": "sucesso"|"info"|"alerta"|"erro", "texto": "…"}`, emitido por
     `apps.core.htmx.disparar_toast(response, texto, nivel="sucesso")`, que usa
     `django_htmx.http.trigger_client_event` (mescla com outros eventos, ex.: `estoque-alterado`).
  2. **Página inteira** (POST sem HTMX → redirect): framework de mensagens do Django com
     `MESSAGE_TAGS = {DEBUG: "info", INFO: "info", SUCCESS: "sucesso", WARNING: "alerta",
     ERROR: "erro"}`; o `base.html` renderiza as mensagens como `aviso` inline dentro de
     `<div data-mensagens>`; com JS, `consus.js` converte cada uma em toast e remove o bloco.
  - Região `<div id="toasts" class="toasts" role="status" aria-live="polite" hx-preserve
    data-duracao-ms="5000" data-maximo="3">`; toasts de `alerta`/`erro` recebem `role="alert"`.
    Modelo de toast em `<template id="modelo-toast">` (renderizado de `components/toast.html`).
  - Duração e máximo vêm de atributos do HTML (testáveis no servidor), não de constantes no JS.
- **Rationale**: o contrato fixa o evento `toast {nivel, texto}`; níveis em português mantêm o
  domínio em pt-BR e casam com as classes CSS; `hx-preserve` mantém toasts na navegação boostada
  (FR-016); sem JS as mensagens continuam visíveis (FR-015).
- **Alternatives considered**: toasts via `hx-swap-oob` (HTML) — rejeitado como padrão: cada view
  teria de renderizar markup de toast; o evento é mais simples e já está no contrato. Níveis em
  inglês (`success`, `error`) — rejeitado: inconsistência com o restante do domínio.

## R8. Diálogo modal

- **Decision**: `<dialog id="dialogo" class="dialogo" aria-labelledby="dialogo-titulo">` único no
  `base.html`. Gatilhos usam `hx-get="<url>" hx-target="#dialogo"` (contrato) e `href="<url>"`
  (fallback sem JS). Fragmentos **estendem** `components/dialogo.html` (blocos `titulo`,
  `descricao`, `corpo`, `rodape`), que inclui o botão fechar (`<form method="dialog">`) e a região
  interna `[data-toasts]`. `consus.js`: guarda o elemento acionador no `htmx:beforeRequest`, chama
  `showModal()` no `htmx:afterSwap` do `#dialogo`, devolve o foco no evento `close`, fecha no
  evento `fechar-dialogo` (emitido por `apps.core.htmx.fechar_dialogo(response)`), e direciona
  toasts para a região interna enquanto o diálogo está aberto. Foco inicial: atributo
  `autofocus` no primeiro campo (o algoritmo nativo de `showModal()` o respeita). Clique no
  `::backdrop` não fecha.
- **Rationale**: `<dialog>` nativo dá *top layer*, `Esc`, inércia do fundo e foco preso sem
  biblioteca; a região interna resolve a sobreposição da *top layer* sobre a região global.
- **Alternatives considered**: diálogo não modal (`show()`) — rejeitado: sem inércia nem foco
  preso; região de toasts como `popover` — rejeitado: conteúdo fora do diálogo modal fica inerte
  e oculto de tecnologias assistivas.

## R9. Navegação e itens indisponíveis (Clarificação Q1)

- **Decision**: registro estático em `apps/core/navegacao.py` (`ItemNavegacao(rotulo, rota,
  icone, secao)`), na ordem Painel (`core:painel`, ativo só na rota exata), Produtos
  (`produtos:lista`, ativo no namespace `produtos`), Movimentações (`movimentacoes:lista`,
  namespace `movimentacoes`), Alertas (`alertas:relatorio`, namespace `alertas`). Um context
  processor (`apps.core.context_processors.consus`) resolve cada item com `reverse()`; em
  `NoReverseMatch` o item sai como `disponivel=False` (renderizado sem `href`, com
  `aria-disabled="true"` e "(em breve)"). O mesmo resolve o **slot do badge**: se
  `alertas:contador` existir, o `<span id="badge-alertas">` recebe `hx-get`,
  `hx-trigger="load, estoque-alterado from:body, every 60s"` e `hx-swap="innerHTML"`. Função
  utilitária `url_se_existir(nome)` serve a ações como o botão do estado vazio do Painel.
- **Rationale**: as features 002–004 só precisam registrar suas rotas com os nomes do contrato;
  a navegação e o badge se ligam sozinhos, sem editar templates do core (reduz conflitos de merge).
- **Alternatives considered**: links fixos que caem no 404 — rejeitado na clarificação (experiência
  ruim na demo); esconder itens — rejeitado (layout muda a cada merge, e o avaliador não vê o
  mapa do sistema).

## R10. Design tokens e CSS

- **Decision**: CSS puro em quatro arquivos: `tokens.css` (único lugar com valores),
  `base.css`, `components.css`, `utilities.css`, carregados nessa ordem no `<head>`; `base.css`
  declara `@layer base, components, utilities;` para controlar especificidade sem `!important`.
  Nomes de tokens conforme `docs/design/design-system.md` §2 (`--color-*`, `--space-*`…);
  primitivas `--palette-*` só dentro de `tokens.css`. Classes em português com BEM. `color-scheme:
  light` em `:root` + `<meta name="color-scheme" content="light">` (Clarificação Q5).
- **Rationale**: constituição IV (tokens primeiro) e II (sem build Node). Cascade layers são
  suportadas por todos os navegadores-alvo.
- **Alternatives considered**: Sass/PostCSS — rejeitado (etapa de build); Tailwind — rejeitado
  (build + aparência genérica); um único CSS — rejeitado (o contrato lista os quatro arquivos).

## R11. Verificação automática de tokens e contraste

- **Decision**: módulo `apps/core/design_tokens.py` com: leitura das custom properties de
  `tokens.css` (expressão regular sobre o bloco `:root`), resolução de `var()` encadeado,
  luminância relativa e razão de contraste WCAG 2.1, e a lista `PARES_CONTRASTE` (espelho da
  tabela §3 do design system). Usado por: (1) testes (`test_tokens.py`): todos os pares ≥ mínimo;
  nenhum literal de cor/medida fora de `tokens.css`; nenhum `--palette-*` fora de `tokens.css`;
  durações ≤ 150 ms; bloco `prefers-reduced-motion`; (2) comando
  `python manage.py checar_contraste` (imprime a tabela e sai com código 1 se algum par falhar);
  (3) a view `/design/`, que exibe as razões calculadas na hora.
- **Rationale**: uma única fonte de cálculo para teste, CLI e catálogo; impossível o catálogo
  mostrar um número diferente do testado.
- **Alternatives considered**: ferramenta externa (pa11y/axe) — rejeitado: exige Node/navegador;
  parser CSS completo (tinycss2) — rejeitado: dependência para um formato que controlamos.

## R12. Componentes de template e formulários

- **Decision**: componentes compostos como templates em `templates/components/` usados por
  `{% include … with … %}` (ou `{% extends %}` no caso do diálogo); componentes simples (botão,
  tabela, badge genérico, cartão) como **API de classes** documentada no catálogo. Ícones por
  `{% icone "nome" %}` (inclusion tag em `apps/core/templatetags/consus.py`). Formulários: um
  renderizador próprio (`apps.core.formularios.RenderizadorConsus`, subclasse de
  `TemplatesSetting`) com `form_template_name = "components/formulario.html"` e
  `field_template_name = "components/campo.html"`, configurado em `FORM_RENDERER`; assim
  `{{ form }}` e `{{ form.campo.as_field_group }}` nas features 002/003 já saem com rótulo,
  ajuda, erro, `aria-describedby` e `aria-invalid`. Paginação usa a tag nativa
  `{% querystring %}` (Django 5.1+) para preservar filtros.
- **Rationale**: zero dependências (sem django-cotton/slippers); o renderizador garante
  acessibilidade de formulário por padrão em todas as features.
- **Alternatives considered**: django-cotton/django-components — rejeitado (dependência nova,
  YAGNI); widgets com `attrs={"class": …}` em cada form — rejeitado (repetição e esquecimento).

## R13. Fontes e ícones vendorizados

- **Decision**: IBM Plex Sans 400/500/600 e IBM Plex Mono 400/600 em `woff2` subset Latin-1
  (release oficial `IBM/plex`, licença SIL OFL 1.1, arquivo `OFL.txt` junto) em `static/fonts/`;
  `@font-face` com `font-display: swap` e `unicode-range` Latin-1; `<link rel="preload">` só para
  Plex Sans Regular. Ícones: subset de ~25 ícones Lucide (ISC) num sprite
  `static/vendor/lucide/sprite.svg` com `LICENSE`; `{% icone %}` gera
  `<svg><use href="{% static 'vendor/lucide/sprite.svg' %}#nome"></use></svg>`.
- **Rationale**: Constituição V (sem CDN); escolhas justificadas pela curadoria em
  `docs/design/referencias.md` §4; sprite único = 1 requisição em cache.
- **Alternatives considered**: fontes variáveis completas — rejeitado (maior que 5 arquivos
  subset); SVG inline repetido no HTML — rejeitado (peso por página); fonte de ícones —
  rejeitado (acessibilidade).

## R14. Localização

- **Decision**: `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`, `USE_TZ = True`,
  `USE_I18N = True`, `USE_THOUSAND_SEPARATOR = True`, `FORMAT_MODULE_PATH = ["config.formatos"]`
  com `config/formatos/pt_BR/formats.py` definindo `DATETIME_FORMAT = SHORT_DATETIME_FORMAT =
  "d/m/Y H:i"`, `DATE_FORMAT = SHORT_DATE_FORMAT = "d/m/Y"`, `THOUSAND_SEPARATOR = "."`,
  `DECIMAL_SEPARATOR = ","`, `NUMBER_GROUPING = 3`.
- **Rationale**: o formato longo padrão do Django em pt-BR ("20 de outubro de 2026 às 14:30") não
  é o exigido pela constituição (`dd/mm/aaaa HH:MM`).
- **Alternatives considered**: filtro customizado em cada template — rejeitado (fácil esquecer).

## R15. Estratégia de testes

- **Decision**: pytest + pytest-django + pytest-cov; testes em `apps/core/tests/`; `conftest.py`
  na raiz (storage de estáticos simples) e em `apps/core/tests/` (cliente HTMX, urlconf de teste
  com rotas fictícias `produtos:*`, `movimentacoes:*`, `alertas:*` para provar FR-012/013/014,
  e views que levantam exceções para 400/403/500). Cada teste cita o FR na docstring ("FR-013:
  …"). Configurações que dependem de ambiente (FR-004/005/006/009/043) são testadas em
  **subprocesso** (`sys.executable -c "import django; django.setup()"`) com `env` controlado.
  Infraestrutura: verificações de arquivo (Dockerfile, compose, entrypoint, `.env.example`) na
  suíte padrão + teste de integração marcado `@pytest.mark.docker` (sobe o Compose, consulta
  `/saude/`, verifica UID ≠ 0, para o banco e espera 503), excluído por padrão
  (`addopts = -m "not docker"`) e executado com `pytest -m docker`. Cobertura com
  `fail_under = 90` sobre `apps/` e `config/`. Comportamento de JavaScript (toasts, diálogo) é
  verificado no servidor pelo **contrato de marcação** (atributos, ids, cabeçalhos) e
  manualmente pelos cenários do `quickstart.md`.
- **Rationale**: Constituição III (FR citado em teste, duas variantes de request); subprocesso é
  a única forma confiável de testar leitura de settings; o teste Docker é lento e depende do
  motor de contêineres, por isso é opt-in.
- **Alternatives considered**: Playwright para JS — rejeitado (dependência pesada + navegadores;
  `consus.js` tem < 100 linhas e contrato verificável no servidor); `override_settings` para
  FR-005 — rejeitado (não reexecuta o módulo de settings).

## R16. Páginas de erro

- **Decision**: `templates/404.html` e `templates/403.html` estendem `base.html` (o Django as
  renderiza com `request`, então a navegação funciona); `templates/500.html`, `400.html` e
  `403_csrf.html` estendem `templates/erro_base.html`, autônomo (marca estática, sem navegação,
  sem context processors, sem consulta ao banco), pois o Django os renderiza sem `request`.
  Todas usam os mesmos CSS (`{% static %}` funciona sem contexto). Requisições parciais com erro
  4xx/5xx não trocam conteúdo (configuração R6) e `consus.js` mostra toast de erro no evento
  `htmx:responseError`; `htmx:sendError` mostra "Sem conexão com o servidor.".
- **Rationale**: a 500 precisa funcionar com o banco fora do ar (FR-038).
- **Alternatives considered**: handlers customizados para tudo — rejeitado: mais código e risco de
  a 500 depender de context processors que, na feature 004, consultam o banco (contador).

## R17. Verificação de saúde

- **Decision**: `apps/core/selectors.py::estado_saude()` abre uma **conexão nova**
  (`connections.create_connection("default")`), executa `SELECT 1` e fecha; qualquer
  `DatabaseError` → banco `indisponivel`. O limite de 2 s vem de `connect_timeout` (PostgreSQL);
  para SQLite a checagem é instantânea. View `core:saude` com `@require_safe` (GET/HEAD; demais
  → 405), `@never_cache`, `@csrf_exempt` não é necessário (só leitura), `JsonResponse` com
  `{"status", "banco", "versao"}` e status 200/503. Versão em `config/__init__.py`
  (`__version__ = "0.1.0"`), também exibida no rodapé.
- **Rationale**: conexão nova evita reaproveitar uma conexão persistente "zumbi" que mascararia
  a queda do banco; sem detalhes de exceção no JSON (FR-034).
- **Alternatives considered**: `connection.ensure_connection()` na conexão padrão — rejeitado
  pelo motivo acima; checar migrações pendentes na saúde — rejeitado (custo e escopo).

## R18. Segurança

- **Decision**: `SecurityMiddleware` + `XFrameOptionsMiddleware` com `X_FRAME_OPTIONS = "DENY"`,
  `SECURE_CONTENT_TYPE_NOSNIFF = True`, `SECURE_REFERRER_POLICY = "same-origin"`;
  `SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = DJANGO_SECURE_COOKIES` (padrão falso, uso local
  em HTTP); `CSRF_TRUSTED_ORIGINS` do ambiente. Sem `django.contrib.admin` nem
  `django.contrib.auth` em `INSTALLED_APPS` (Clarificação Q4); apps padrão mantidos:
  `contenttypes`, `sessions`, `messages`, `staticfiles`. Política de CSP fica fora desta versão.
- **Rationale**: FR-043/FR-044; remover o admin elimina a única via de edição direta de saldo
  fora das movimentações (Constituição I).
- **Alternatives considered**: admin somente leitura — rejeitado (exige auth, usuário, senha:
  escopo e risco sem requisito); CSP estrita — adiada (exige revisar `hx-headers`/`htmx-config`
  e não é requisito).

## R19. Logs

- **Decision**: `LOGGING` com um `StreamHandler` para `sys.stdout`, formato
  `"%(asctime)s %(levelname)s %(name)s %(message)s"`, nível `DJANGO_LOG_LEVEL` (padrão `INFO`);
  Gunicorn com `--access-logfile -`.
- **Rationale**: fator XI (logs como fluxo de eventos); `docker compose logs` mostra tudo.
- **Alternatives considered**: JSON estruturado — rejeitado (YAGNI para uso local).

---

## Propostas de ajuste ao contrato

Itens que esta feature define e que as features 002–004 consomem. **`docs/arquitetura.md` não
foi editado**; proponho incorporá-los ao contrato (seção "Convenções HTMX"):

1. **Níveis do evento `toast`**: `nivel ∈ {"sucesso", "info", "alerta", "erro"}` (em português);
   emissão por `apps.core.htmx.disparar_toast(response, texto, nivel="sucesso")`; mensagens do
   Django mapeadas por `MESSAGE_TAGS` para os mesmos níveis.
2. **Novo evento `fechar-dialogo`** (sem payload), emitido por
   `apps.core.htmx.fechar_dialogo(response)` após uma ação concluída dentro de `#dialogo`.
3. **Regra parcial × completa**: `apps.core.htmx.eh_parcial(request)` (= `request.htmx and not
   request.htmx.boosted`); navegação boostada recebe página completa.
4. **Slot do badge de alertas**: `<span id="badge-alertas">` no item Alertas é ligado
   automaticamente quando `alertas:contador` existe (`hx-trigger="load, estoque-alterado
   from:body, every 60s"`, `hx-swap="innerHTML"`); o fragmento de `alertas:contador` devolve
   **apenas o conteúdo interno** (badge ou vazio). Atualizações por OOB DEVEM usar
   `hx-swap-oob="innerHTML:#badge-alertas"` para não apagar os atributos do slot.
5. **Situação `sem_estoque`**: `quantidade_atual == 0` é um caso particular de `em_alerta`;
   sugerimos que `ProdutoQuerySet.com_situacao()` anote `situacao ∈ {"ok", "reposicao",
   "sem_estoque"}`, que é o parâmetro do componente `components/badge_estoque.html`; o badge de
   `sem_estoque` mantém o texto "REPOSIÇÃO NECESSÁRIA" (constituição IV).
6. **Sem autenticação e sem admin** (Clarificação Q4): nenhuma feature registra modelos no
   admin; `django.contrib.admin`/`auth` não fazem parte de `INSTALLED_APPS`.
7. **Formulários**: `FORM_RENDERER` do core renderiza campos com o componente `campo`; as
   features devem usar `{{ form }}`/`as_field_group` em vez de HTML manual de campos.
8. **Navegação automática**: os nomes de rota `produtos:lista`, `movimentacoes:lista`,
   `alertas:relatorio` e `alertas:contador` do contrato passam a ser também o "interruptor" que
   ativa os itens de navegação e o badge — não devem ser renomeados.
9. **Correção de referência**: o repositório do Carbon é `carbon-design-system/carbon`
   (o link `IBM/carbon` citado na constituição não existe publicamente). Não altera requisitos.
