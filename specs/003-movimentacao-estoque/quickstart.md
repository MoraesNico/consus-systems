# Quickstart: validar a feature 003 — Movimentação de estoque

**Feature**: `003-movimentacao-estoque` | **Plan**: [plan.md](plan.md)

Guia de validação ponta a ponta. Detalhes de comportamento: [contratos](contracts/) e
[modelo de dados](data-model.md).

## Pré-requisitos

- Features 001 (fundação, layout, componentes, Docker) e 002 (produtos) implementadas e
  integradas em `develop`.
- `cp .env.example .env` (uma vez).

## 1. Subir e migrar

```bash
docker compose up --build -d
docker compose exec app python manage.py migrate          # aplica movimentacoes 0001 e 0002
docker compose exec app python manage.py makemigrations --check --dry-run   # sem pendências
```

Esperado: `0002_saldo_inicial_retroativo` cria um "Saldo inicial" para cada produto que já existia
sem histórico.

## 2. Testes automatizados

```bash
# Suíte rápida (SQLite local) — testes "postgres" são pulados
pytest apps/movimentacoes -q

# Suíte completa no PostgreSQL do Compose (serviço `testes` da 001), incluindo concorrência (SC-003)
docker compose --profile testes run --rm testes pytest apps/movimentacoes -q
docker compose --profile testes run --rm testes pytest -m postgres -q

# Cobertura mínima de 90% nos módulos de regra (constituição, princípio III)
docker compose --profile testes run --rm testes pytest apps/movimentacoes \
  --cov=apps.movimentacoes.services --cov=apps.movimentacoes.models \
  --cov=apps.movimentacoes.selectors --cov-report=term-missing --cov-fail-under=90

# Quality gates
ruff check . && ruff format --check .
```

Esperado: tudo verde; `test_concorrencia.py` executa (não é pulado) no serviço `testes`.

## 3. Auditoria do livro-razão (SC-004)

```bash
docker compose exec app python manage.py shell -c \
  "from apps.movimentacoes.selectors import auditar_saldos; print(auditar_saldos())"
```

Esperado: `[]` (todo saldo é igual à soma das movimentações e a sequência é contínua).

## 4. Cenários manuais (navegador, http://localhost:8000)

Prepare um produto: cadastre "Parafuso" com Quantidade Inicial 10 e Estoque Mínimo 3.

| # | Passos | Resultado esperado | Requisitos |
|---|--------|--------------------|------------|
| 1 | Detalhe do produto → Histórico | 1 linha "Saldo inicial", `+10`, `0 → 10` | FR-027, US4 |
| 2 | Lista de produtos → "+ Entrada" na linha do Parafuso | diálogo com produto e tipo Entrada, saldo atual 10, foco na quantidade | FR-013, FR-032 |
| 3 | Digitar 5 | prévia "Saldo após: 15" | FR-014 |
| 4 | Confirmar | diálogo fecha; linha mostra 15 sem recarregar; toast "Entrada registrada: #0001 Parafuso — saldo 10 → 15"; badge de alertas reage | FR-015…FR-017, SC-005 |
| 5 | "− Saída" → 20 → ver prévia → Confirmar | prévia avisa "Saldo insuficiente: disponível 15, solicitado 20"; ao confirmar, diálogo permanece com a mesma mensagem; saldo continua 15 | FR-004, FR-018 |
| 6 | "− Saída" → 15 → Confirmar | saldo 0; produto passa a "REPOSIÇÃO NECESSÁRIA" (004) | FR-004 (zerar permitido) |
| 7 | "− Saída" → 0, `-1`, `+5`, `2,5`, `1.000`, `abc` | recusas com mensagem no campo; nada gravado | FR-005 |
| 8 | Menu → Nova movimentação → escolher produto, Entrada 7, obs "NF 123" → Confirmar | página volta pronta para o próximo registro (mesmo produto/tipo, campos vazios, saldo 7) + toast | FR-012, esclarecimento Q2 |
| 9 | Repetir o passo 8 com JavaScript desativado | mesmo resultado por envio tradicional (mensagem exibida após o redirect); erros com página re-renderizada | FR-019, SC-008 |
| 10 | Movimentações → filtrar produto Parafuso + tipo Saída/Venda + período de hoje; ir à página 2 (se houver) | só as saídas do Parafuso; URL contém os filtros e `pagina=2`; recarregar mantém o resultado | FR-022, FR-023, FR-024 |
| 11 | Filtrar com data final anterior à inicial | aviso e período ignorado | FR-026 |
| 12 | Procurar editar/excluir uma movimentação | não há ação disponível | FR-021, SC-006 |
| 13 | Detalhe de um produto com mais de 10 movimentações | 10 mais recentes + "Ver histórico completo" → Movimentações filtrada | FR-025 |

## 5. Terminal (US5)

```bash
docker compose exec app python manage.py movimentar 1 entrada 5 --obs "NF 4521"; echo "código $?"
docker compose exec app python manage.py movimentar 1 saida 9999; echo "código $?"
```

Esperado: "Entrada registrada: #0001 Parafuso — saldo X → X+5" e código 0; depois
"CommandError: Saldo insuficiente: disponível …, solicitado 9.999" e código 1.

## 6. Concorrência manual (opcional)

Abra o diálogo "− Saída" do mesmo produto (saldo 10) em duas abas, digite 6 nas duas e confirme
quase ao mesmo tempo: uma é aceita (saldo 4), a outra é recusada com
"Saldo insuficiente: disponível 4, solicitado 6".
