# Contrato: comando de terminal `movimentar`

**Arquivo**: `apps/movimentacoes/management/commands/movimentar.py` | **Requisito**: FR-031
(SHOULD, US5/P3) | **Pesquisa**: R14

## Sintaxe

```text
python manage.py movimentar <produto> <tipo> <quantidade> [--obs "texto"]
```

| Argumento | Formato | Regra |
|-----------|---------|-------|
| `produto` | `12`, `#12` ou `#0012` | ID de produto existente |
| `tipo` | `entrada` \| `saida` (sem diferenciar maiúsculas; `saída` também aceito) | `inicial` é recusado |
| `quantidade` | inteiro | mesma regra do formulário: só dígitos, `1..1.000.000` |
| `--obs` | texto | opcional, até 200 caracteres (aparado) |

Executa `registrar_movimentacao` — mesmas regras, mesma transação, mesmo histórico da web.

## Saídas

| Caso | stdout / stderr | Código de saída | Gravação |
|------|-----------------|-----------------|----------|
| sucesso | stdout: `Entrada registrada: #0001 Parafuso — saldo 10 → 15` | 0 | 1 movimentação |
| saldo insuficiente | stderr: `CommandError: Saldo insuficiente: disponível 7, solicitado 50` | 1 | nada |
| saldo máximo | stderr: `CommandError: Saldo máximo excedido: atual X, entrada Y, máximo 2.147.483.647` | 1 | nada |
| produto inexistente | stderr: `CommandError: Produto #0099 não encontrado.` | 1 | nada |
| tipo inválido | stderr: `CommandError: Tipo inválido: use "entrada" ou "saida".` | 1 | nada |
| quantidade inválida | stderr: `CommandError: Informe um número inteiro, sem casas decimais nem separadores.` (ou a mensagem de mínimo/máximo) | 1 | nada |

## Exemplos

```bash
docker compose exec app python manage.py movimentar 1 entrada 5 --obs "NF 4521"
docker compose exec app python manage.py movimentar "#0001" saida 3 --obs "Venda balcão"
docker compose exec app python manage.py movimentar 1 saida 999   # recusa, código 1
```

O comando não emite eventos de interface; quem estiver com a página aberta vê o novo saldo ao
recarregar (ou no próximo *polling* do `#contador-alertas` da 004, a cada 30 s). A partir da 004,
o comando também imprime o aviso de reposição (`alertas.regras.confirmacao_com_alerta`).
