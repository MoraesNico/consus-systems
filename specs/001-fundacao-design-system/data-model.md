# Data Model: Fundação do Consus e Design System

**Feature**: `001-fundacao-design-system` · **Data**: 2026-10-20

Esta feature **não cria modelos Django nem tabelas de negócio**. As migrações aplicadas na subida
são as de `contenttypes` e `sessions` (apps padrão mantidos — ver research R18). Os modelos
`Produto` e `Movimentacao` pertencem às features 002 e 003 (`docs/arquitetura.md`).

O que esta feature define são **estruturas de configuração e de contrato** — dados que trafegam
entre servidor, templates e navegador ou que parametrizam o sistema. Elas são descritas abaixo
com campos, regras de validação e origem.

---

## 1. Variáveis de ambiente

Fonte: `os.environ` (lido em `config/settings.py` e pelo `docker-compose.yml`). Documentadas uma
a uma em `.env.example` (FR-004).

| Variável | Obrigatória | Padrão | Validação / efeito | Consumidor |
|----------|-------------|--------|--------------------|------------|
| `DJANGO_SECRET_KEY` | sim, se `DJANGO_DEBUG` falso | — (dev: chave fixa de desenvolvimento) | ausente com debug falso ⇒ `ImproperlyConfigured` na inicialização (FR-005) | settings |
| `DJANGO_DEBUG` | não | `false` | aceita `1/true/yes/on` (sem diferenciar maiúsculas) como verdadeiro | settings |
| `DJANGO_ALLOWED_HOSTS` | não | `localhost,127.0.0.1` | lista separada por vírgula | settings |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | não | `http://localhost:8000,http://127.0.0.1:8000` | lista; cada item com esquema | settings |
| `DATABASE_URL` | não | `sqlite:///<BASE_DIR>/db.sqlite3` | URL no formato `dj-database-url`; ausente ⇒ SQLite (FR-006) | settings |
| `DATABASE_CONNECT_TIMEOUT` | não | `2` | inteiro em segundos; aplicado só a PostgreSQL (`OPTIONS.connect_timeout`) | settings, `/saude/` |
| `DJANGO_LOG_LEVEL` | não | `INFO` | `DEBUG/INFO/WARNING/ERROR/CRITICAL` | settings (`LOGGING`) |
| `DJANGO_SECURE_COOKIES` | não | `false` | booleano ⇒ `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` (FR-043) | settings |
| `WEB_CONCURRENCY` | não | `3` | inteiro ≥ 1 (lido nativamente pelo Gunicorn) | gunicorn |
| `CONSUS_PORTA` | não | `8000` | porta publicada no host | compose |
| `POSTGRES_DB` | sim (compose) | `consus` (no exemplo) | nome do banco criado pelo serviço `db` | compose (`db`) |
| `POSTGRES_USER` | sim (compose) | `consus` (no exemplo) | usuário do banco | compose (`db`) |
| `POSTGRES_PASSWORD` | sim (compose) | `consus` (no exemplo, trocar fora do uso local) | senha do banco | compose (`db`) |

No `.env.example`, `DATABASE_URL=postgres://consus:consus@db:5432/consus` (aponta para o serviço
`db`) e `DJANGO_SECRET_KEY` traz um valor marcado como "troque-esta-chave" — não é segredo real.

---

## 2. Token de design

Fonte: `static/css/tokens.css` (bloco `:root`), especificação em
`docs/design/design-system.md` §2. Lido por `apps/core/design_tokens.py`.

| Campo | Tipo | Regra |
|-------|------|-------|
| `nome` | str | custom property: `--palette-*` (primitiva) ou `--color-* / --font-* / --text-* / --leading-* / --tracking-* / --space-* / --size-* / --icon-* / --border-* / --radius-* / --shadow-* / --focus-* / --grid-* / --page-margin / --bp-* / --table-* / --z-* / --duration-* / --ease-* / --opacity-* / --measure / --header-h / --container-max / --form-max / --dialog-w-* / --toast-w` |
| `valor` | str | literal CSS; pode referenciar outro token via `var(--…)` |
| `categoria` | enum | derivada do prefixo (cor, tipografia, espaço, tamanho, borda, sombra, foco, grid, tabela, camada, movimento, opacidade) |
| `valor_resolvido` | str | `var()` resolvido recursivamente (para cores: hex `#RRGGBB`) |

Regras: primitivas `--palette-*` só podem ser referenciadas dentro de `tokens.css`; durações
≤ 150 ms; nenhum token semântico de cor fica sem par documentado se for usado como texto.

## 3. Par de contraste

Fonte: `apps/core/design_tokens.py::PARES_CONTRASTE` (espelho de `design-system.md` §3).

| Campo | Tipo | Regra |
|-------|------|-------|
| `primeiro_plano` | nome de token `--color-*` | deve existir em `tokens.css` |
| `fundo` | nome de token `--color-*` | idem |
| `minimo` | float | `4.5` (texto normal), `3.0` (texto grande/não-texto) ou `0` (isento — documentação) |
| `uso` | str | descrição exibida no catálogo |
| `razao` | float (calculado) | WCAG 2.1: `(L1 + 0.05) / (L2 + 0.05)` com luminância relativa sRGB |

Validação: `razao >= minimo` para todo par com `minimo > 0` (FR-024, SC-002).

## 4. Item de navegação

Fonte: `apps/core/navegacao.py::ITENS_NAVEGACAO` (estático) → resolvido por requisição no
context processor `apps.core.context_processors.consus`.

| Campo | Tipo | Regra |
|-------|------|-------|
| `rotulo` | str | "Painel", "Produtos", "Movimentações", "Alertas" (ordem fixa, FR-012) |
| `rota` | str | nome de URL: `core:painel`, `produtos:lista`, `movimentacoes:lista`, `alertas:relatorio` |
| `icone` | str | nome no sprite Lucide (`layout-dashboard`, `package`, `arrow-left-right`, `bell`) |
| `secao` | str | regra de ativo: Painel = rota exata `core:painel`; demais = namespace (`produtos`, `movimentacoes`, `alertas`) |
| `url` *(resolvido)* | str \| None | `reverse(rota)`; `None` em `NoReverseMatch` |
| `disponivel` *(resolvido)* | bool | `url is not None` (FR-013) |
| `ativo` *(resolvido)* | bool | conforme `secao` × `request.resolver_match` (FR-012) |
| `badge_url` *(resolvido, só Alertas)* | str \| None | `reverse("alertas:contador")` ou `None` (FR-014) |

Estados: `indisponível` → `disponível` (transição automática quando a feature registra a rota);
`disponível` × `ativo`/`inativo` por requisição.

## 5. Notificação (toast)

Fontes: cabeçalho `HX-Trigger` (evento `toast`) ou framework de mensagens do Django.

| Campo | Tipo | Regra |
|-------|------|-------|
| `nivel` | enum | `sucesso` \| `info` \| `alerta` \| `erro` (inválido ⇒ tratado como `info` no cliente; no servidor, `disparar_toast` levanta `ValueError`) |
| `texto` | str | 1–200 caracteres (fora disso, `disparar_toast` levanta `ValueError`), frase curta com ponto final, exibido como texto puro (`textContent` no cliente; escapado no servidor) |

Mapeamento de mensagens do Django (`MESSAGE_TAGS`): `DEBUG→info`, `INFO→info`,
`SUCCESS→sucesso`, `WARNING→alerta`, `ERROR→erro`.

Comportamento derivado (FR-016): `sucesso`/`info` → duração `data-duracao-ms` (5000) com pausa em
hover/foco; `alerta`/`erro` → persistente, `role="alert"`; no máximo `data-maximo` (3) visíveis.

## 6. Estado de saúde

Fonte: `apps/core/selectors.py::estado_saude()` → `core:saude`.

| Campo | Tipo | Valores |
|-------|------|---------|
| `status` | enum | `ok` \| `erro` |
| `banco` | enum | `ok` \| `indisponivel` |
| `versao` | str | `config.__version__` (ex.: `0.1.0`) |

Regras (FR-035): `banco == "ok"` ⇔ `SELECT 1` em conexão nova concluiu em até
`DATABASE_CONNECT_TIMEOUT` s; `status == "ok"` ⇔ `banco == "ok"`; HTTP 200 se `status == "ok"`,
senão 503. Nunca inclui mensagem de exceção, host, usuário ou senha.

## 7. Componente do catálogo

Fonte: `apps/core/views.py` (lista `COMPONENTES_CATALOGO`) → `core/design.html`.

| Campo | Tipo | Regra |
|-------|------|-------|
| `ancora` | slug | id HTML estável da seção |
| `nome` | str | nome exibido no sumário |
| `secao_ds` | str | referência ao `design-system.md` (ex.: "§4.1") |
| `estados` | lista | estados demonstrados (D, H, F, A, X, E, C conforme aplicável) |
| `trecho` | str | exemplo de uso do template/classe, exibido em `<pre><code>` escapado |

Âncoras obrigatórias (SC-004 — 18 componentes): `botao`, `campo`, `tabela`, `badge`, `cartao`,
`kpi`, `lista-barras`, `barra-categorias`, `rastreador`, `barra-progresso`, `dialogo`, `toast`,
`aviso`, `estado-vazio`, `paginacao`, `navegacao`, `cabecalho-pagina`, `icone`. Âncoras de tokens:
`cores`, `contraste`, `tipografia`, `espacamento`, `tamanhos`, `bordas`, `sombras`, `camadas`,
`movimento`.

## 8. Formulário de exemplo (catálogo)

Fonte: `apps/core/forms.py::FormularioExemplo` (não persiste nada; só demonstra o padrão
422 / sucesso usado por 002 e 003).

| Campo | Tipo | Validação |
|-------|------|-----------|
| `nome` | `CharField(max_length=120)` | obrigatório, aparado; ajuda "Dado fictício — nada é salvo." |
| `quantidade` | `IntegerField(min_value=1)` | obrigatório, inteiro ≥ 1 (mensagem: "Informe um número inteiro maior que zero.") |
