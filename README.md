# Consus

> *Consus* — divindade romana guardiã dos grãos armazenados nos celeiros.

Sistema web de **Controle de Estoque Simples**, porém altamente funcional: cadastro de produtos
com ID automático, entradas e saídas com bloqueio de saldo negativo e alerta automático de
reposição. Feito em **Django 5.2 + HTMX 2**, com PostgreSQL no Docker.

Esse repositório deve conter o conteúdo dos códigos, como optei por HTMX não terá API no
momento então terá somente um repositório.

## Como executar

Pré-requisitos: [Docker](https://docs.docker.com/get-docker/) com o plugin Compose.

```bash
cp .env.example .env          # revise os valores se quiser
docker compose up --build     # app + PostgreSQL 17, migrações automáticas
```

Abra <http://localhost:8000>. Outras páginas úteis:

| Endereço | O que é |
|----------|---------|
| `/` | Painel |
| `/design/` | Catálogo vivo do design system |
| `/saude/` | Verificação de saúde (JSON) |

Validação completa passo a passo: [`specs/001-fundacao-design-system/quickstart.md`](specs/001-fundacao-design-system/quickstart.md).

### Sem Docker (desenvolvimento)

```bash
uv sync                                   # Python 3.13 + dependências
DJANGO_DEBUG=true uv run python manage.py migrate
DJANGO_DEBUG=true uv run python manage.py runserver
```

Sem `DATABASE_URL`, o Consus usa SQLite local.

## Qualidade

| Comando | Verifica |
|---------|----------|
| `uv run ruff check .` | lint |
| `uv run ruff format --check .` | formatação |
| `uv run pytest` | testes + cobertura (mínimo 90 %) em SQLite |
| `uv run python manage.py makemigrations --check --dry-run` | migrações em dia |
| `uv run python manage.py checar_contraste` | contraste WCAG AA dos tokens |
| `docker compose --profile testes run --rm testes` | suíte completa no PostgreSQL |
| `uv run pytest -m docker` | integração com Docker Compose (sobe e derruba um ambiente isolado) |

## Como o projeto foi especificado

Desenvolvimento orientado por especificação com o [GitHub Spec Kit](https://github.com/github/spec-kit):

- [`.specify/memory/constitution.md`](.specify/memory/constitution.md) — princípios do projeto;
- [`docs/arquitetura.md`](docs/arquitetura.md) — contrato compartilhado entre as features;
- [`docs/design/`](docs/design/) — design system (High-Density Neo-Brutalism Sóbrio / Swiss Grid
  Enterprise) e as referências estudadas (shadcn/ui, Tremor, Carbon, design-resources,
  Refactoring UI);
- [`specs/`](specs/) — uma pasta por atividade, cada uma com `spec.md`, `plan.md` e `tasks.md`.

Branches: cada feature nasce de `develop` (`NNN-slug`) e volta por merge `--no-ff`;
`main` recebe apenas releases vindas de `develop`.
