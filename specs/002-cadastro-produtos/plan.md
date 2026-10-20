# Implementation Plan: Cadastro de Produtos

**Branch**: `002-cadastro-produtos` | **Date**: 2026-10-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-cadastro-produtos/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Implementar o item 1 da atividade: o modelo `produtos.Produto` (ID `BigAutoField` exibido como
`#0001`, nome normalizado e único sem diferenciar maiúsculas/minúsculas, `quantidade_atual` e
`estoque_minimo` inteiros ≥ 0 com `CheckConstraint`), o serviço
`produtos.services.cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo) -> Produto`
(nesta feature apenas define `quantidade_atual`; ponto de extensão da 003), a lista densa com
busca por ID (`12`/`#12`/`#0012`) ou nome, filtro por situação, ordenação, paginação de 25 e URL
canônica, o detalhe com região reservada à 003 e a edição de nome e estoque mínimo que nunca
grava a quantidade. A interface é HTML renderizado no servidor com HTMX 2: cada rota atende a
navegação comum (e *boosted*) com página completa + `302`, e requisições parciais (`HX-Target`
`resultados`/`dialogo`) com fragmentos, status 422 em erros e `HX-Trigger` (`toast`,
`estoque-alterado`, `dialogo-fechar`). Decisões detalhadas em [research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.2 LTS, django-htmx, HTMX 2.x (vendorizado pela 001),
`django.contrib.humanize` (embutido no Django). **Nenhuma dependência nova.**

**Storage**: PostgreSQL 17 (Docker) em produção; SQLite para desenvolvimento e testes rápidos
(a suíte passa nos dois — testes de maiúsculas/minúsculas acentuadas só no PostgreSQL, R3).
Tabela `produtos_produto`, migração `0001_initial`.

**Testing**: pytest + pytest-django + pytest-cov (`django_assert_max_num_queries`), Ruff (lint +
format); cobertura ≥ 90% em `models.py`, `services.py` e `selectors.py`.

**Target Platform**: contêiner Linux (Gunicorn + WhiteNoise); navegadores atuais, com e sem
JavaScript.

**Project Type**: aplicação web Django monolítica com HTML sobre o fio (HTMX), apps em `apps/`.

**Performance Goals**: lista, busca, filtro, ordenação e paginação respondem em até 1 s com
10.000 produtos (SC-003); no máximo 4 consultas SQL por requisição de lista.

**Constraints**: aprimoramento progressivo obrigatório (tudo funciona sem JS); JS próprio do
projeto < 100 linhas (esta feature acrescenta ~12, atalhos); erros de validação com status 422;
WCAG 2.1 AA; interface em pt-BR; quantidade nunca editável diretamente.

**Scale/Scope**: até 10 mil produtos; 1 modelo, 1 migração, 4 rotas, 5 páginas, 9 fragmentos,
3 eventos HTMX, 31 requisitos funcionais, 5 histórias de usuário.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano cumpre | Pré-pesquisa | Pós-design |
|-----------|---------------------|:------------:|:----------:|
| **I. Integridade do Estoque** | Saldo nunca negativo em 3 camadas: `InteiroNaoNegativoField` (formulário), `cadastrar_produto`/`editar_produto` em `transaction.atomic()` com `select_for_update()` na edição (serviço) e `CheckConstraint` `produto_quantidade_atual_nao_negativa` (banco). `quantidade_atual` só é definida no cadastro; a edição usa `update_fields` sem ela; não há formulário, admin (R16) nem rota de exclusão (405) que a altere. Quantidade Inicial vira `Movimentacao INICIAL` quando a 003 existir (FR-030, ponto de extensão documentado). Inteiros estritos (R2). | ✅ | ✅ |
| **II. Interface Dirigida pelo Servidor** | Django Templates + HTMX 2; fragmentos em `templates/produtos/partials/`; `hx-swap-oob` (filtros, contagem; linha/resumo para a 003); `HX-Trigger` para `toast`/`estoque-alterado`/`dialogo-fechar`. Toda ação funciona sem HTMX (GET/POST + `302`). Views escolhem página/fragmento por `request.htmx` (django-htmx), tratando *boosted* e restauração de histórico como navegação comum (R8). JS próprio: ~12 linhas de atalhos. | ✅ | ✅ |
| **III. Testes Primeiro** | `tasks.md` coloca testes antes da implementação em cada fase; cada FR-001…FR-031 citado em nome/docstring de teste; serviços e consultas testados antes das views; testes de view cobrem variantes comum, *boosted* e parcial (200/302/422/404/405); meta de cobertura ≥ 90% em models/services/selectors; suíte em SQLite e PostgreSQL. | ✅ | ✅ |
| **IV. Design System** | Somente componentes e tokens da 001 (tabela densa, campo, botão, badge, diálogo, estado vazio, toast); números em fonte tabular alinhados à direita com separador "."; situação em alerta = ícone SVG + "REPOSIÇÃO NECESSÁRIA" + cor; estados vazios projetados; `aria-sort`, `aria-invalid`/`aria-describedby`, `role="status"`, foco visível; ação primária "Novo produto", secundárias discretas, nenhuma ação destrutiva. Estados novos (linha destacada, `<kbd>`) entram em `components.css` usando apenas tokens. | ✅ | ✅ |
| **V. Simplicidade, Containers, 12-Factor** | Nenhuma dependência nova (humanize é do Django); sem factory_boy, sem `pg_trgm`, sem índices extras (YAGNI, R15); nenhuma configuração nova de ambiente; migração aplicada pelo fluxo `docker compose up` da 001. | ✅ | ✅ |
| **Restrições técnicas** | Domínio em português (`Produto`, `quantidade_atual`, `estoque_minimo`, `cadastrar_produto`); estrutura `apps/produtos/` com `models/services/selectors/forms/views/urls/templates/tests` conforme o contrato. | ✅ | ✅ |
| **Fluxo de desenvolvimento** | spec → plan → tasks antes de código; `/speckit-analyze` executado; quality gates (`ruff check`, `ruff format --check`, `pytest`, `makemigrations --check`, build Docker) na fase final de `tasks.md`. | ✅ | ✅ |

**Resultado**: nenhum desvio; nada a justificar em *Complexity Tracking*. Reavaliação após a
Fase 1 (data-model, contratos, quickstart): mantida, pois o design não introduziu dependências,
caminhos de escrita de saldo nem JS além dos atalhos.

## Project Structure

### Documentation (this feature)

```text
specs/002-cadastro-produtos/
├── spec.md              # Especificação (/speckit-specify + /speckit-clarify)
├── plan.md              # Este arquivo (/speckit-plan)
├── research.md          # Fase 0: decisões R1–R16 + propostas de ajuste ao contrato
├── data-model.md        # Fase 1: Produto, restrições, QuerySet, mensagens
├── quickstart.md        # Fase 1: validação (comandos, cenários manuais, carga)
├── contracts/
│   ├── rotas-http.md            # rotas, variantes comum/boosted/parcial, status, cabeçalhos
│   ├── servicos-e-consultas.md  # API Python: services, selectors, ProdutoQuerySet
│   └── fragmentos-e-eventos.md  # templates, IDs, atributos HTMX, eventos, integração 001/003/004
├── checklists/
│   ├── requirements.md  # qualidade da spec (/speckit-specify)
│   ├── ux.md            # checklist de domínio: UX e acessibilidade (/speckit-checklist)
│   └── integridade.md   # checklist de domínio: integridade de dados (/speckit-checklist)
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/produtos/
├── __init__.py
├── apps.py                  # ProdutosConfig(name="apps.produtos", verbose_name="Produtos")
├── models.py                # QUANTIDADE_MAXIMA, ProdutoQuerySet, Produto
├── services.py              # normalizar_nome, cadastrar_produto, editar_produto
├── selectors.py             # listar_produtos, obter_produto, normalizar_ordem, normalizar_situacao
├── forms.py                 # NomeProdutoField, InteiroNaoNegativoField, ProdutoForm, ProdutoEdicaoForm
├── views.py                 # lista, novo, detalhe, editar
├── urls.py                  # app_name = "produtos"
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── templates/produtos/
│   ├── lista.html
│   ├── novo.html
│   ├── detalhe.html
│   ├── editar.html
│   ├── nao_encontrado.html
│   └── partials/
│       ├── filtros.html
│       ├── resultados.html
│       ├── contagem.html
│       ├── linha.html
│       ├── situacao.html
│       ├── form_produto.html
│       ├── dialogo_novo.html
│       ├── resumo.html
│       └── form_edicao.html
└── tests/
    ├── __init__.py
    ├── conftest.py          # fixture produto_factory (via cadastrar_produto), cabeçalhos HTMX
    ├── test_models.py
    ├── test_services.py
    ├── test_selectors.py
    ├── test_forms.py
    ├── test_views_cadastro.py
    ├── test_views_lista.py
    ├── test_views_detalhe.py
    ├── test_views_edicao.py
    └── test_atalhos.py

# Arquivos compartilhados (da 001) tocados de forma pontual
config/settings.py           # INSTALLED_APPS += "apps.produtos", "django.contrib.humanize"
config/urls.py               # path("produtos/", include("apps.produtos.urls"))
templates/base.html          # item "Produtos" na navegação (se ainda ausente)
static/js/consus.js          # manipulador genérico data-atalho (se a 001 não o fornecer)
static/css/components.css    # estado "linha destacada" e <kbd> (se ausentes), só com tokens
```

**Structure Decision**: estrutura de app Django definida em `docs/arquitetura.md` (`apps/<app>/`
com `models.py`, `services.py`, `selectors.py`, `forms.py`, `views.py`, `urls.py`,
`templates/<app>/`, `templates/<app>/partials/` e `tests/`). Se a 001 organizar as configurações
em pacote (ex.: `config/settings/base.py`), a alteração de `INSTALLED_APPS` vai para o módulo
base equivalente. Alterações em arquivos compartilhados são aditivas e coordenadas pelas
propostas P5/P6 de [research.md](./research.md#propostas-de-ajuste-ao-contrato).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação a justificar.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
