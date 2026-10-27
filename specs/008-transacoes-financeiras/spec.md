# Feature 008 — Registro de transações financeiras

**Origem**: Passo 3, item 2 · **Contrato**: `docs/arquitetura.md` v1.2, "Usuário nas movimentações e transações financeiras" e "Períodos".

## História
Como gestor, quero que toda entrada de estoque gere uma despesa e toda saída gere uma receita,
com um histórico consultável, para acompanhar o dinheiro que entra e sai.

## Requisitos
- **FR-001** O saldo inicial > 0 gera uma transação ENTRADA (despesa = quantidade × custo).
- **FR-002** Cada Entrada gera uma despesa = quantidade × preço de custo vigente.
- **FR-003** Cada Saída gera uma receita = quantidade × preço de venda vigente. O custo fica congelado (CPV), e mudar preços depois não altera a transação.
- **FR-004** O saldo inicial 0 não gera transação.
- **FR-005** Movimentação e transação são gravadas na mesma transação de banco: uma recusa não grava nenhuma das duas.
- **FR-006** `Transacao` é imutável: `save`, `delete`, `update` e o delete em massa são recusados.
- **FR-007** `totais()` devolve receitas, despesas, saldo, CPV, lucro bruto, unidades vendidas e o número de transações.
- **FR-008** `momento` só é aceito em ordem cronológica e nunca no futuro.
- **FR-009** `/financeiro/transacoes/` mostra Data/hora, ID do produto, Tipo, Quantidade, Preço unitário, Valor total e Registrado por. Tem filtros por produto, tipo e datas, 25 itens por página e exportação CSV.
- **FR-010** O livro-razão `/movimentacoes/` ganha a coluna Valor (+receita / −despesa; "—" sem transação).
- **FR-011** Há estados vazios distintos para "sem transações" e "filtro sem resultado".

Períodos: `apps/core/periodos.py` (tudo, hoje, 7d, 30d, mes, personalizado).
