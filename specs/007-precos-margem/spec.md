# Feature 007 — Preços de custo/venda e margem

**Origem**: Passo 3 (Módulo Financeiro), item 1 · **Contrato**: `docs/arquitetura.md` v1.2, "Dinheiro" e "Produto com preços e margem".

## História
Como responsável pelo estoque, quero informar o preço de custo e o de venda de cada produto e
ver a margem calculada na hora, para saber quanto ganho por unidade.

## Requisitos
- **FR-001** O cadastro grava `preco_custo` e `preco_venda` (`Decimal`, 2 casas, centavos no banco) e calcula a margem = venda − custo (R$ e %).
- **FR-002** Os dois preços são obrigatórios, > R$ 0,00 e ≤ R$ 999.999,99. Com mais de 2 casas, o valor é recusado.
- **FR-003** Venda abaixo do custo é permitida e aparece com o selo **MARGEM NEGATIVA** e um aviso de prejuízo por unidade.
- **FR-004** A edição exige os dois preços. Mudar o preço não altera transações passadas.
- **FR-005** Produtos anteriores à 2.0 ficam com os preços em 0 e o selo **PREÇO PENDENTE**.
- **FR-006** `com_financeiro()` anota `margem` e `valor_estoque` para listas e painéis.
- **FR-007** A lista ganha as colunas Custo, Venda e Margem, e ordena por margem.
- **FR-008** O formulário mostra uma prévia viva da margem (`produtos:previa_margem`, HTMX 300 ms).
- **FR-009** Os campos aceitam o formato brasileiro (`1.234,56`, `R$ 12,50`, `12.5`).
- **FR-010** Um preço ausente ou inválido gera uma mensagem no campo (422).

## Critérios de aceite
O cadastro com custo 10,00 e venda 15,00 mostra a margem R$ 5,00 (33,3%). Valor em estoque = quantidade × custo.
