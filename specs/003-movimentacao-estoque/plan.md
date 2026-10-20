# Implementation Plan: Controle de Movimentação — Entradas e Saídas

**Branch**: `003-movimentacao-estoque` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-movimentacao-estoque/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Implementar o item 2 da atividade: a função única de atualização de saldo
(`movimentacoes.services.registrar_movimentacao`) que registra **Entrada** (soma) e
**Saída/Venda** (subtrai) como movimentações imutáveis de um livro-razão, impedindo saldo negativo
em três camadas (validação do formulário, serviço transacional com `select_for_update()` e
restrições no banco). A interface é dirigida pelo servidor (Django Templates + HTMX 2): página
`/movimentacoes/nova/` (funciona sem JavaScript, padrão PRG), diálogo HTMX aberto pelas ações
rápidas "+ Entrada" / "− Saída" da lista e do detalhe do produto, prévia de saldo renderizada no
servidor, atualização imediata via `hx-swap-oob`, eventos `HX-Trigger` (`estoque-alterado`,
`toast`, `fechar-dialogo`) e erros com status 422. O histórico (`/movimentacoes/`) tem filtros por
produto, tipo e período, paginação de 25 e um recorte das 10 últimas no detalhe do produto. O
cadastro de produto (feature 002) passa a gerar a movimentação `INICIAL` na mesma transação, e uma
migração de dados cria o `INICIAL` retroativo para produtos pré-existentes. Paridade de terminal
pelo comando `python manage.py movimentar`.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.2 LTS, django-htmx (detecção `request.htmx`, utilitários
`trigger_client_event` / `reswap`), HTMX 2.x vendorizado em `static/vendor/htmx.min.js`
(feature 001). **Nenhuma dependência nova.**

**Storage**: PostgreSQL 17 (Docker Compose) em execução e no teste de concorrência; SQLite no
desenvolvimento local e na suíte rápida. Nova tabela `movimentacoes_movimentacao`; usa a tabela
`produtos_produto` (feature 002) com bloqueio de linha.

**Testing**: pytest + pytest-django + pytest-cov; testes de concorrência marcados
`@pytest.mark.postgres` (pulados automaticamente fora do PostgreSQL); cliente de teste do Django
com cabeçalhos `HX-Request` / `HX-Target` para as variantes HTMX.

**Target Platform**: contêiner Linux (Gunicorn + WhiteNoise) servindo navegadores modernos
(Chromium, Firefox, Safari atuais), com aprimoramento progressivo.

**Project Type**: aplicação web monolítica Django renderizada no servidor (apps em `apps/`).

**Performance Goals**: registro de movimentação < 300 ms p95 em ambiente local; primeira página
do histórico < 1 s com 100.000 movimentações (SC-007); atualização visível em ≤ 1 s após
confirmar (SC-005).

**Constraints**: saldo nunca negativo sob concorrência (FR-004, FR-008, SC-003); livro-razão
*append-only*; nenhum JavaScript novo (o orçamento de < 100 linhas é da feature 001); todo fluxo
funciona sem HTMX; erros de validação com status 422; datas `dd/mm/aaaa HH:MM` no fuso
`America/Sao_Paulo`; números com separador de milhar `.`.

**Scale/Scope**: ~1.000 produtos, ~100.000 movimentações, poucos operadores simultâneos;
2 páginas novas, 1 diálogo, 2 fragmentos embutidos nas páginas da 002, 1 comando de terminal.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação (pré-pesquisa) | Pós-design |
|-----------|--------------------------|------------|
| **I. Integridade do Estoque** | Três camadas: `MovimentacaoForm.clean()` (camada 1), `registrar_movimentacao` com `transaction.atomic()` + `select_for_update()` (camada 2), `CheckConstraint(quantidade_atual >= 0)` do `Produto` + restrições do `Movimentacao` (camada 3). Saldo só muda pelo serviço; `cadastrar_produto` passa a criar com 0 e registrar `INICIAL`. Livro-razão imutável com saldo anterior/posterior. Quantidade inteira > 0 (exceto `INICIAL`). | ✅ PASS — ver [data-model.md](data-model.md) (restrições `mov_*`, guardas de imutabilidade) e [contracts/servico-movimentacao.md](contracts/servico-movimentacao.md). |
| **II. Interface Dirigida pelo Servidor** | Templates Django + partials; `hx-swap-oob` para linha/resumo/histórico; `HX-Trigger` para `estoque-alterado`, `toast`, `fechar-dialogo`; prévia de saldo renderizada no servidor (sem JS novo); todo POST funciona sem HTMX (PRG); views escolhem template por `request.htmx`. | ✅ PASS — ver [contracts/rotas-movimentacoes.md](contracts/rotas-movimentacoes.md). |
| **III. Testes Primeiro (NÃO-NEGOCIÁVEL)** | Cada FR tem teste que o cita no nome/docstring; testes de serviço/seletor/modelo antes das views; cobertura ≥ 90% em `services.py`, `models.py`, `selectors.py`; views testadas nas variantes comum e HTMX; teste de concorrência em PostgreSQL. | ✅ PASS — mapeamento FR → teste em `tasks.md`; comandos em [quickstart.md](quickstart.md). |
| **IV. Design System** | Usa tokens e componentes da 001 (diálogo, toast, selo, tabela densa, campo, estado vazio); quantidades em mono tabular alinhadas à direita; tipo como selo com texto; sinal `+`/`−` (U+2212) + texto, nunca só cor; mensagens com `aria-live`/`role="alert"`; foco visível; datas e números em pt-BR. Nenhum valor mágico de CSS nesta feature. | ✅ PASS |
| **V. Simplicidade, Containers, 12-Factor** | Sem dependências novas; migrações versionadas; teste de concorrência roda no PostgreSQL do Compose; nenhuma configuração nova além do registro do app/rotas e do marcador `postgres`. | ✅ PASS |
| **Restrições Técnicas** | App `apps/movimentacoes` com `models.py`, `services.py`, `selectors.py`, `forms.py`, `views.py`, `urls.py`, `templates/movimentacoes/{,partials/}`, `tests/`; domínio em português. | ✅ PASS |
| **Fluxo de Desenvolvimento** | spec → plan → tasks; `/speckit-analyze` antes de implementar; quality gates (`ruff`, `pytest`, `makemigrations --check`, build Docker) listados no quickstart. | ✅ PASS |

**Resultado**: nenhuma violação; *Complexity Tracking* vazio.

## Project Structure

### Documentation (this feature)

```text
specs/003-movimentacao-estoque/
├── plan.md              # Este arquivo
├── research.md          # Fase 0 — decisões e propostas de ajuste ao contrato
├── data-model.md        # Fase 1 — Movimentacao, restrições, invariantes, migrações
├── quickstart.md        # Fase 1 — como validar a feature
├── contracts/
│   ├── servico-movimentacao.md   # registrar_movimentacao, exceções, seletores, cadastrar_produto
│   ├── rotas-movimentacoes.md    # /movimentacoes/ e /movimentacoes/nova/ (comum × HTMX)
│   ├── integracao-produtos.md    # fragmentos nas páginas da 002, OOB, eventos para a 004
│   └── comando-movimentar.md     # python manage.py movimentar
├── checklists/
│   ├── requirements.md
│   ├── integridade.md
│   └── ux.md
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/movimentacoes/                         # NOVO (feature 003)
├── __init__.py
├── apps.py                                 # MovimentacoesConfig(name="apps.movimentacoes", label="movimentacoes")
├── models.py                               # TipoMovimentacao, constantes, MovimentacaoQuerySet, Movimentacao, MovimentacaoImutavelError
├── services.py                             # registrar_movimentacao + MovimentacaoError, MovimentacaoInvalidaError,
│                                           #   EstoqueInsuficienteError, SaldoMaximoExcedidoError
├── selectors.py                            # listar_movimentacoes, historico_do_produto, auditar_saldos
├── forms.py                                # QuantidadeField, MovimentacaoForm, FiltroMovimentacoesForm
├── views.py                                # lista_movimentacoes (movimentacoes:lista), nova_movimentacao (movimentacoes:nova)
├── urls.py                                 # app_name="movimentacoes"
├── templatetags/
│   ├── __init__.py
│   └── movimentacoes_tags.py               # {% acoes_rapidas produto origem %}, {% historico_produto produto %}
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── movimentar.py                   # python manage.py movimentar <id> entrada|saida <qtd> [--obs]
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py                     # tabela, índices e restrições mov_*
│   └── 0002_saldo_inicial_retroativo.py    # RunPython: INICIAL para produtos sem histórico
├── templates/movimentacoes/
│   ├── lista.html                          # página Movimentações (extends base.html)
│   ├── nova.html                           # página Nova movimentação (extends base.html)
│   └── partials/
│       ├── filtros.html                    # <form id="filtros"> produto/tipo/de/ate
│       ├── tabela_movimentacoes.html       # conteúdo de #resultados: avisos, tabela, paginação, vazio
│       ├── linha_movimentacao.html         # <tr> reutilizada na lista e no histórico do produto
│       ├── form_movimentacao.html          # <form id="form-movimentacao"> (página e diálogo)
│       ├── previa_saldo.html               # <output id="previa-saldo"> saldo atual → prévia
│       ├── dialogo_movimentacao.html       # conteúdo carregado em #dialogo
│       ├── sucesso_dialogo.html            # fragmentos OOB após sucesso no diálogo
│       ├── acoes_rapidas.html              # "+ Entrada" / "− Saída" (inclusion tag)
│       └── historico_produto.html          # <section id="produto-<id>-historico"> (inclusion tag)
└── tests/
    ├── __init__.py
    ├── conftest.py                         # fixtures: produto_com_saldo, htmx_headers
    ├── test_models.py
    ├── test_services.py
    ├── test_concorrencia.py                # @pytest.mark.postgres
    ├── test_invariante.py
    ├── test_selectors.py
    ├── test_forms.py
    ├── test_views_nova.py
    ├── test_views_lista.py
    ├── test_integracao_produtos.py
    ├── test_saldo_inicial.py
    ├── test_migracao_saldo_inicial.py
    ├── test_desempenho.py                  # @pytest.mark.postgres (SC-007)
    └── test_comando_movimentar.py

# Arquivos de outras features tocados na implementação (003 é implementada depois de 001 e 002)
config/settings.py                          # INSTALLED_APPS += "apps.movimentacoes" (se ainda ausente)
config/urls.py                              # path("movimentacoes/", include("apps.movimentacoes.urls"))
pyproject.toml                              # [tool.pytest.ini_options] markers += "postgres: ..."
templates/base.html                         # item "Movimentações" na navegação (se ainda ausente)
apps/produtos/services.py                   # cadastrar_produto → cria com 0 + registrar_movimentacao(INICIAL)
apps/produtos/templates/produtos/partials/linha_produto.html    # inclui {% acoes_rapidas produto "lista" %}
apps/produtos/templates/produtos/partials/resumo_produto.html   # bloco #produto-<id>-resumo (alvo OOB)
apps/produtos/templates/produtos/detalhe.html                   # ações rápidas + {% historico_produto produto %}
```

**Structure Decision**: aplicação Django única, conforme `docs/arquitetura.md` — a feature cria o
app `apps/movimentacoes/` com o conjunto padrão de módulos do contrato e estende pontos bem
delimitados das features 001 (registro do app, rota, navegação, marcador de teste) e 002
(serviço de cadastro e templates da lista/detalhe). A integração com as páginas de produto é
feita por *inclusion tags* (`movimentacoes_tags`), sem alterar as views da 002. Se a 001 tiver
dividido o settings em pacote (ex.: `config/settings/base.py`), a tarefa de registro do app
aplica-se ao módulo base equivalente. Os nomes de partials/IDs da 002 usados como alvo OOB estão
propostos em [research.md](research.md#propostas-de-ajuste-ao-contrato).

## Phase 0 — Research

Consolidado em [research.md](research.md): 16 decisões (bloqueio pessimista, comportamento sob
concorrência, três camadas, imutabilidade, saldo inicial e migração retroativa, validação da
quantidade, despacho de variantes na mesma rota, prévia no servidor, OOB + eventos, PRG sem HTMX,
histórico/filtros/paginação, integração por inclusion tags, teste de concorrência, comando de
terminal, formatação pt-BR, zero dependências novas) e 10 propostas de ajuste ao contrato. Nenhum
`NEEDS CLARIFICATION` restante.

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) — entidade `Movimentacao`, `TipoMovimentacao`, constantes,
  restrições `mov_*`, índices, invariantes, imutabilidade, migrações 0001/0002, extensão do
  `Produto`.
- [contracts/servico-movimentacao.md](contracts/servico-movimentacao.md) — API Python de escrita e
  leitura (serviço, exceções e mensagens, seletores, extensão de `cadastrar_produto`).
- [contracts/rotas-movimentacoes.md](contracts/rotas-movimentacoes.md) — matriz de requisição ×
  resposta das rotas `movimentacoes:lista` e `movimentacoes:nova`.
- [contracts/integracao-produtos.md](contracts/integracao-produtos.md) — fragmentos embutidos na
  lista/detalhe de produtos, alvos OOB e eventos consumidos pela 004.
- [contracts/comando-movimentar.md](contracts/comando-movimentar.md) — comando de terminal.
- [quickstart.md](quickstart.md) — validação ponta a ponta.

**Re-avaliação da Constitution Check pós-design**: todos os princípios continuam ✅ (tabela acima,
coluna "Pós-design"). O design não introduziu dependência, JavaScript ou caminho de escrita de
saldo fora do serviço.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação a justificar.
