# Contrato: serviço de movimentação, exceções e seletores

**Módulos**: `apps/movimentacoes/services.py`, `apps/movimentacoes/selectors.py`,
`apps/produtos/services.py` (extensão) | **Requisitos**: FR-001…FR-011, FR-021, FR-027…FR-030

## Escrita — `registrar_movimentacao`

```python
def registrar_movimentacao(
    *, produto_id: int, tipo: str, quantidade: int, observacao: str = ""
) -> Movimentacao
```

Único ponto do sistema que altera `Produto.quantidade_atual` (FR-001). Assinatura fixada por
`docs/arquitetura.md`.

### Pré-condições (validadas pelo próprio serviço, independentemente do formulário)

| Entrada | Regra | Falha |
|---------|-------|-------|
| `tipo` | um de `TipoMovimentacao` (`"INICIAL"`, `"ENTRADA"`, `"SAIDA"`) | `MovimentacaoInvalidaError("Tipo de movimentação inválido.")` |
| `quantidade` | `int` (não `bool`); `ENTRADA`/`SAIDA`: `1..1_000_000`; `INICIAL`: `0..2_147_483_647` | `MovimentacaoInvalidaError("Informe uma quantidade maior que zero." / "Informe no máximo 1.000.000.")` |
| `observacao` | `str`, aparada, `len <= 200` | `MovimentacaoInvalidaError("Use no máximo 200 caracteres.")` |
| `produto_id` | produto existente | `MovimentacaoInvalidaError("Produto #0099 não encontrado.")` |
| `INICIAL` | produto sem nenhuma movimentação e com saldo 0 | `MovimentacaoInvalidaError("Saldo inicial já registrado para #0001.")` |

### Execução

1. `with transaction.atomic():`
2. `produto = Produto.objects.select_for_update().get(pk=produto_id)` — bloqueia a linha; uma
   segunda chamada concorrente para o mesmo produto **aguarda** (sem `nowait`).
3. `saldo_anterior = produto.quantidade_atual`
4. `SAIDA` e `quantidade > saldo_anterior` → `EstoqueInsuficienteError(disponivel=saldo_anterior,
   solicitado=quantidade)`.
5. `ENTRADA`/`INICIAL` e `saldo_anterior + quantidade > SALDO_MAXIMO` →
   `SaldoMaximoExcedidoError(atual=saldo_anterior, entrada=quantidade)`.
6. `produto.quantidade_atual = saldo_posterior`;
   `produto.save(update_fields=["quantidade_atual", "atualizado_em"])`.
7. `Movimentacao.objects.create(produto=produto, tipo=…, quantidade=…, saldo_anterior=…,
   saldo_posterior=…, observacao=…)`.
8. Retorna a movimentação (com `produto` carregado).

### Pós-condições

- Sucesso: exatamente 1 `Movimentacao` nova; `produto.quantidade_atual == mov.saldo_posterior`;
  `mov.saldo_anterior` igual ao saldo lido sob bloqueio.
- Qualquer exceção: **nada** gravado (rollback); saldo inalterado (FR-004, FR-011).
- Nenhum efeito de interface (eventos, mensagens): responsabilidade das views/comando.

### Exceções (`apps/movimentacoes/services.py`)

| Classe | Base | Atributos | `str(exc)` |
|--------|------|-----------|------------|
| `MovimentacaoError` | `Exception` | — | — |
| `MovimentacaoInvalidaError` | `MovimentacaoError` | — | mensagem da regra violada |
| `EstoqueInsuficienteError` | `MovimentacaoError` | `disponivel: int`, `solicitado: int` | `"Saldo insuficiente: disponível {X}, solicitado {Y}"` |
| `SaldoMaximoExcedidoError` | `MovimentacaoError` | `atual: int`, `entrada: int` | `"Saldo máximo excedido: atual {X}, entrada {Y}, máximo 2.147.483.647"` |

`MovimentacaoImutavelError` (base `Exception`) fica em `apps/movimentacoes/models.py`.
Números nas mensagens usam separador de milhar `.` (`formatar_numero`), ex.:
"Saldo insuficiente: disponível 1.200, solicitado 1.500".

### Exemplos

| Saldo antes | Chamada | Resultado |
|-------------|---------|-----------|
| 10 | `ENTRADA, 5` | mov 10 → 15; saldo 15 |
| 15 | `SAIDA, 4, "NF 123"` | mov 15 → 11; observação "NF 123" |
| 11 | `SAIDA, 11` | mov 11 → 0; saldo 0 (permitido) |
| 3 | `SAIDA, 5` | `EstoqueInsuficienteError` "disponível 3, solicitado 5"; nada gravado |
| 10 | `SAIDA, 0` / `-1` / `1_000_001` | `MovimentacaoInvalidaError`; nada gravado |
| 2.147.483.000 | `ENTRADA, 1.000` | `SaldoMaximoExcedidoError`; nada gravado |
| 0, sem histórico | `INICIAL, 0` | mov 0 → 0 |

## Extensão — `produtos.services.cadastrar_produto` (feature 002)

```python
def cadastrar_produto(*, nome: str, quantidade_inicial: int, estoque_minimo: int) -> Produto
```

(assinatura proposta ao contrato; se a 002 usar outra, mantém-se a dela.) Com a 003:

1. `with transaction.atomic():`
2. cria o `Produto` com `quantidade_atual=0` (validações de nome/mínimo da 002 inalteradas);
3. `registrar_movimentacao(produto_id=produto.pk, tipo=TipoMovimentacao.INICIAL,
   quantidade=quantidade_inicial)` — inclusive quando `quantidade_inicial == 0`;
4. `produto.refresh_from_db()` e retorna.

Falha em qualquer passo → nem produto nem `INICIAL` gravados (FR-027).

## Leitura — `apps/movimentacoes/selectors.py`

| Função | Retorno | Uso |
|--------|---------|-----|
| `listar_movimentacoes(*, produto_id=None, tipo=None, de=None, ate=None)` | `QuerySet[Movimentacao]` ordenado `-criado_em, -id`, com `select_related("produto")` | página Movimentações (FR-022, FR-023) |
| `historico_do_produto(produto_id, *, limite=10)` | `list[Movimentacao]` (até `limite`, mais recentes primeiro) | detalhe do produto (FR-025) |
| `auditar_saldos()` | `list[DivergenciaSaldo]` — vazia quando consistente | invariantes (FR-029, SC-004), quickstart |

`DivergenciaSaldo` é um `NamedTuple(produto_id: int, saldo_atual: int, saldo_calculado: int,
motivo: str)`; motivos: `"soma"` (saldo ≠ Σ), `"continuidade"` (quebra anterior/posterior),
`"inicial"` (zero ou mais de um `INICIAL`, ou `INICIAL` não é o primeiro).
