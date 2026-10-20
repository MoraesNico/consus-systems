# Implementation Plan: Alerta de Reposição — varredura, relatório, contador automático e painel

**Branch**: `004-alerta-reposicao` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-alerta-reposicao/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Implementa o item 3 da atividade ("Sistema Automatizado de Alerta de Baixa"): a regra
`em_alerta ⇔ quantidade_atual ≤ estoque_minimo` (com a variação mais grave **SEM ESTOQUE** quando
a quantidade é 0) passa a ser a única fonte de verdade para seis superfícies — Relatório de
Reposição (`/alertas/`, varredura sob demanda + exportação CSV), contador automático no menu
(`/alertas/contador/`, polling HTMX de 30 s + evento `estoque-alterado`), selos de situação na
lista/detalhe de produtos, aviso no toast da movimentação que piora a situação, Painel (`/`) com
KPIs e o comando de terminal `varrer_estoque` (texto/csv/json, código de saída). Inclui o comando
`popular_demo` (dados de demonstração idempotentes).

Abordagem técnica: a regra é expressa **uma vez em SQL** (`ProdutoQuerySet.em_alerta()` e as
anotações de `com_situacao()` — `alerta` da 002, mais `deficit` e `cobertura_percentual` da 004 —
com aritmética em `bigint` para não estourar o `integer` do PostgreSQL) e **uma vez em Python puro** (`apps/alertas/regras.py`, usado onde não há
consulta — transição de situação do toast, exportação), e um teste de equivalência em grade
garante que as duas nunca divirjam. `alertas.selectors` monta o resultado de varredura (ordenado
por criticidade no banco) e o resumo do painel; `alertas.exportacao` serializa o mesmo resultado
para CSV/JSON/texto, de modo que web, CSV e terminal concordem por construção. Nada é persistido
(Clarificação 1): não há modelo, migração nem tabela nova. A interface é 100% renderizada no
servidor (fragmentos HTMX, `hx-swap-oob`, eventos), com 0 linhas novas de JavaScript próprio.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.2 LTS, django-htmx, HTMX 2.x vendorizado (todos já trazidos pela
feature 001). Da biblioteca padrão: `csv`, `json`, `dataclasses`, `enum`. **Nenhuma dependência nova.**

**Storage**: PostgreSQL 17 (Docker) / SQLite (dev e testes). **Sem tabelas, colunas, índices ou
migrações novas** — apenas consultas anotadas sobre `produtos_produto` e
`movimentacoes_movimentacao`.

**Testing**: pytest + pytest-django + pytest-cov; cliente de teste do Django com cabeçalhos
`HX-Request`/`HX-Boosted`; `django_assert_max_num_queries` para orçamento de consultas;
`call_command` + `CommandError.returncode` para os comandos; `freezegun` **não** é usado — as
funções aceitam `agora=` injetável.

**Target Platform**: servidor Linux em container (Gunicorn + WhiteNoise); navegadores atuais
(com e sem JavaScript); terminal UTF-8 (com fallback para terminais sem o símbolo ⚠).

**Project Type**: aplicação web Django monolítica renderizada no servidor + comandos de gerenciamento.

**Performance Goals**: relatório com 1.000 produtos em ≤ 2 s (≤ 3 consultas SQL); contador em
≤ 0,5 s (1 consulta `COUNT`); painel com ≤ 7 consultas; atualização pós-movimentação percebida
em ≤ 1 s (1 requisição GET por região ouvinte).

**Constraints**: somente leitura (exceto `popular_demo`, que escreve exclusivamente pelos serviços
das features 002/003); 0 linhas novas de JS; aritmética da regra imune a estouro de inteiro
32 bits; datas `dd/mm/aaaa HH:MM` em `America/Sao_Paulo`; mesmo resultado em PostgreSQL e SQLite.

**Scale/Scope**: até 10.000 produtos (referência da 002); relatório não paginado (cenário típico
≤ 1.000 itens em alerta); 2 rotas, 2 comandos, 6 superfícies de exibição.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação (pré-pesquisa) | Avaliação (pós-design) |
|-----------|--------------------------|------------------------|
| **I. Integridade do Estoque** (NÃO-NEGOCIÁVEL) | ✅ A feature é de leitura: nenhuma view, comando ou template altera `quantidade_atual`. O único escritor, `popular_demo`, usa `produtos.services.cadastrar_produto` e `movimentacoes.services.registrar_movimentacao` (FR-034/FR-037); nunca faz `update()` de saldo nem de `criado_em`. | ✅ Confirmado em [data-model.md](data-model.md) (invariantes I-1…I-4) e [contracts/cli.md](contracts/cli.md); teste de `popular_demo` verifica que `saldo == soma das movimentações` e a cadeia `saldo_anterior → saldo_posterior`. |
| **II. Interface Dirigida pelo Servidor** | ✅ Relatório, contador e painel são fragmentos HTML; atualização por `hx-trigger="every 30s, estoque-alterado from:body"`, `hx-swap-oob` (contador e anúncio) e `HX-Trigger` (toast da 003). Sem SPA. | ✅ 0 linhas novas de JS; todas as rotas respondem página completa sem HTMX (aprimoramento progressivo — FR-013), fragmento com `HX-Request` e página completa com `HX-Boosted`; `Vary: HX-Request` ([contracts/http-alertas.md](contracts/http-alertas.md)). |
| **III. Testes Primeiro** (NÃO-NEGOCIÁVEL) | ✅ Cada FR-001…FR-037 tem tarefa de teste que o cita, escrita antes da implementação (tasks.md). Regra nos `selectors`/`regras`/queryset antes das views. | ✅ Testes de limite em grade (equivalência SQL × Python), variantes comum/HTMX/boosted em todas as views, cobertura ≥ 90% em `selectors.py`, `regras.py`, `exportacao.py` e `apps/produtos/models.py`. |
| **IV. Design System** | ✅ Selo sempre ícone SVG + texto + cor (FR-021); números em mono tabular à direita; estados vazios projetados; `aria-live` para o contador (FR-017). | ✅ Novos componentes `components/barra_cobertura.html` e `components/bar_list.html` usam apenas tokens de `static/css/tokens.css`; nenhum valor mágico (a largura da barra é dado, via custom property `--valor`); tabela densa 40 px; sem emoji como ícone na web (⚠ só no terminal, como texto). |
| **V. Simplicidade, Containers e 12-Factor** | ✅ Nenhuma dependência nova; intervalo de polling configurável por variável de ambiente `ALERTAS_INTERVALO_SEGUNDOS` (padrão 30). | ✅ Sem persistência nova (Clarificação 1, YAGNI); `docker compose up --build` inalterado; comandos rodam via `docker compose exec web python manage.py …`. |

**Resultado**: nenhuma violação; nenhum item na tabela de Complexity Tracking exige justificativa
constitucional. Os desvios do *padrão de app* do contrato (não da constituição) estão listados
abaixo.

## Project Structure

### Documentation (this feature)

```text
specs/004-alerta-reposicao/
├── plan.md              # Este arquivo (/speckit-plan)
├── research.md          # Fase 0 — decisões e propostas de ajuste ao contrato
├── data-model.md        # Fase 1 — anotações, objetos derivados, transições, dados de demonstração
├── quickstart.md        # Fase 1 — guia de validação
├── contracts/           # Fase 1
│   ├── consultas-e-regras.md   # ProdutoQuerySet, alertas.selectors, alertas.regras, alertas.exportacao
│   ├── http-alertas.md         # GET /alertas/ (html | fragmento | csv) e GET /alertas/contador/
│   ├── http-painel.md          # GET / (core:painel)
│   ├── fragmentos-e-eventos.md # selo, contador, anúncio, barra, BarList, toast, eventos, integrações
│   └── cli.md                  # varrer_estoque e popular_demo
├── checklists/
│   ├── requirements.md  # qualidade da spec (/speckit-specify, /speckit-clarify)
│   └── *.md             # checklists de domínio (/speckit-checklist)
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/alertas/                                   # NOVO (feature 004)
├── __init__.py
├── apps.py                                     # AlertasConfig(name="apps.alertas")
├── regras.py                                   # Situacao, classificar, deficit, cobertura_percentual,
│                                               # sugestao_reposicao, transicao, aviso_movimentacao,
│                                               # confirmacao_com_alerta (sem consultas)
├── selectors.py                                # produtos_por_criticidade, varrer, total_em_alerta,
│                                               # resumo_painel + dataclasses ResultadoVarredura, ResumoPainel
├── exportacao.py                               # COLUNAS, para_csv, para_json, para_texto
├── views.py                                    # relatorio, contador
├── urls.py                                     # app_name="alertas": "" e "contador/"
├── demo.py                                     # PRODUTOS_DEMO + popular()
├── templatetags/
│   ├── __init__.py
│   └── alertas_tags.py                         # {% contador_alertas %}, filtro limitar_100
├── management/commands/
│   ├── __init__.py
│   ├── varrer_estoque.py
│   └── popular_demo.py
├── templates/alertas/
│   ├── relatorio.html                          # página completa (estende base.html)
│   └── partials/
│       ├── relatorio.html                      # região #relatorio (resumo + tabela | estado vazio)
│       ├── linha_reposicao.html
│       ├── contador.html                       # #contador-alertas (polling e OOB)
│       └── anuncio.html                        # OOB para #anuncio-alertas (aria-live)
└── tests/
    ├── __init__.py
    ├── conftest.py                             # fábrica criar_produto(nome, quantidade, minimo)
    ├── test_regras.py
    ├── test_equivalencia_regra.py
    ├── test_selectors_varredura.py
    ├── test_selectors_painel.py
    ├── test_exportacao.py
    ├── test_views_relatorio.py
    ├── test_views_contador.py
    ├── test_templatetags.py
    ├── test_selo_produtos.py
    ├── test_aviso_movimentacao.py
    ├── test_comando_varrer_estoque.py
    ├── test_comando_popular_demo.py
    └── test_desempenho.py

apps/produtos/models.py                         # ALTERA (002): com_situacao() + deficit, cobertura_percentual (bigint)
apps/produtos/tests/test_queryset_situacao.py   # NOVO: limites da regra e anotações
apps/produtos/templates/produtos/partials/situacao.html  # ALTERA (002): ramo SEM ESTOQUE (selo único)
apps/movimentacoes/views.py                     # ALTERA (003): toast/messages via alertas.regras.confirmacao_com_alerta
apps/movimentacoes/forms.py                     # ALTERA (003): origem aceita "alertas"
apps/movimentacoes/templates/movimentacoes/partials/sucesso_dialogo.html  # ALTERA (003): origem=alertas sem OOB
apps/movimentacoes/management/commands/movimentar.py  # ALTERA (003): imprime o aviso de reposição
apps/core/views.py                              # ALTERA (001): painel usa alertas.selectors.resumo_painel
apps/core/templates/core/painel.html            # ALTERA (001): KPIs, listas, região #painel-conteudo
apps/core/templates/core/partials/painel_conteudo.html   # NOVO
apps/core/tests/test_painel_kpis.py             # NOVO
templates/base.html                             # ALTERA (001): {% contador_alertas %} no menu + #anuncio-alertas
templates/components/barra_cobertura.html       # NOVO componente (estilo ProgressBar/CategoryBar do Tremor)
templates/components/bar_list.html              # NOVO componente (estilo BarList do Tremor)
static/css/components.css                       # ALTERA (001): .selo-situacao, .contador-alertas,
                                                # .barra-cobertura, .bar-list (somente tokens)
config/settings.py                              # ALTERA (001): INSTALLED_APPS += "apps.alertas";
                                                # ALERTAS_INTERVALO_SEGUNDOS (env, padrão 30, mínimo 5)
config/urls.py                                  # ALTERA (001): path("alertas/", include("apps.alertas.urls"))
.env.example                                    # ALTERA (001): ALERTAS_INTERVALO_SEGUNDOS=30
```

**Structure Decision**: aplicação Django única do contrato (`config/` + `apps/`). Todo o código
novo vive em `apps/alertas/`; as alterações fora dele são **pontos de integração** previstos pelo
contrato (queryset da 002 "anotações para a 004", painel da 001 "placeholder → 004 (KPIs)",
toast/evento da 003, menu do `base.html`). Os nomes usados (`produtos/partials/situacao.html`,
`Produto.em_alerta`/`codigo`, anotação `alerta`, `QUANTIDADE_MAXIMA`, `Movimentacao.mensagem_confirmacao`,
`origem`, `sucesso_dialogo.html`, `movimentar`) vêm dos contratos já publicados pela 002 e pela
003; o selo é **um único parcial**, o da 002, estendido com SEM ESTOQUE
([contracts/fragmentos-e-eventos.md](contracts/fragmentos-e-eventos.md)).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Não há violações da constituição. Registro, por transparência, os desvios conscientes do padrão
de app descrito em `docs/arquitetura.md` ("cada app tem `models.py`, `services.py`, `forms.py`…"):

| Desvio | Por que é necessário | Alternativa mais simples rejeitada porque |
|--------|----------------------|-------------------------------------------|
| `apps/alertas` **sem** `models.py`, `services.py` e `forms.py` | A feature não persiste nada (Clarificação 1) e não escreve dados; não há formulário de entrada | Criar arquivos vazios só para seguir o padrão adicionaria ruído sem comportamento |
| Módulos extras `regras.py` e `exportacao.py` | `regras.py` é a regra em Python puro (toast, exportação, testes de equivalência) sem dependência de ORM; `exportacao.py` garante que web, CSV e terminal usem o mesmo serializador (SC-006) | Duplicar a formatação na view e no comando permitiria divergência entre CSV web e terminal |
| Regra expressa duas vezes (SQL e Python) | SQL é necessário para filtrar/ordenar/contar no banco (contador em 1 consulta, ordenação por criticidade); Python é necessário para transições a partir de `saldo_anterior/saldo_posterior` sem nova consulta | Só Python obrigaria carregar todos os produtos para contar alertas; só SQL obrigaria consulta extra por movimentação. O risco de divergência é eliminado por `test_equivalencia_regra.py` |
| `popular_demo` em `apps/alertas` (não em `core`) | O conjunto de dados existe para demonstrar alertas (limites, sem estoque) e é mantido junto da regra que exercita | Em `core` misturaria dados de exemplo com layout/componentes da fundação e espalharia o código da 004 por mais um app |
