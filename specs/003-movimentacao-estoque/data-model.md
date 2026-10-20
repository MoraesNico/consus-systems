# Data Model: Controle de Movimentação — Entradas e Saídas

**Feature**: `003-movimentacao-estoque` | **Date**: 2026-10-20 | **Plan**: [plan.md](plan.md)

Fonte dos nomes: `docs/arquitetura.md` (contrato compartilhado). Decisões em
[research.md](research.md).

## Visão geral

```text
produtos.Produto (feature 002)                movimentacoes.Movimentacao (feature 003, imutável)
┌───────────────────────────────┐ 1      0..*  ┌───────────────────────────────────────────┐
│ id (BigAutoField)  "#0001"    │◄──────────────│ produto  FK PROTECT related_name=          │
│ nome                          │               │          "movimentacoes"                   │
│ quantidade_atual  (>= 0) ◄────┼── só muda via │ tipo     INICIAL | ENTRADA | SAIDA         │
│ estoque_minimo                │   registrar_  │ quantidade                                 │
│ criado_em / atualizado_em     │   movimentacao│ saldo_anterior → saldo_posterior           │
└───────────────────────────────┘               │ observacao (≤ 200)                         │
                                                │ criado_em (indexado)                       │
                                                └───────────────────────────────────────────┘
```

## Constantes (`apps/movimentacoes/models.py`)

| Nome | Valor | Uso |
|------|-------|-----|
| `QUANTIDADE_MAXIMA_MOVIMENTACAO` | `1_000_000` | Máximo por Entrada/Saída (FR-005, esclarecimento Q4). Nome distinto de `produtos.models.QUANTIDADE_MAXIMA` para não colidir (contrato v1.1) |
| `SALDO_MAXIMO` | `= apps.produtos.models.QUANTIDADE_MAXIMA` (2.147.483.647) | Teto de saldo; importado da 002, nunca redefinido como literal (contrato v1.1, "Limites") |
| `OBSERVACAO_MAX` | `200` | Tamanho máximo da observação (FR-006) |
| `HISTORICO_DETALHE` | `10` | Movimentações no detalhe do produto (FR-025, esclarecimento Q3) |
| `ITENS_POR_PAGINA` | `25` | Paginação da página Movimentações (FR-024) |

## `TipoMovimentacao` (`models.TextChoices`)

| Valor | Rótulo | Efeito no saldo | Quem gera | Selo |
|-------|--------|-----------------|-----------|------|
| `INICIAL` | "Saldo inicial" | `0 + quantidade` (aceita 0) | só `cadastrar_produto` e a migração 0002 | `.badge--neutro` |
| `ENTRADA` | "Entrada" | `+ quantidade` | operador (web/terminal) | `.badge--info` + ícone `arrow-down-to-line` |
| `SAIDA` | "Saída/Venda" | `− quantidade` (nunca abaixo de 0) | operador (web/terminal) | `.badge--neutro` + ícone `arrow-up-from-line` |

`max_length=7` (maior valor: `ENTRADA`).

## Entidade `Movimentacao` (`apps/movimentacoes/models.py`)

| Campo | Tipo Django | Regras |
|-------|-------------|--------|
| `id` | `BigAutoField` | automático |
| `produto` | `ForeignKey("produtos.Produto", on_delete=PROTECT, related_name="movimentacoes")` | obrigatório |
| `tipo` | `CharField(max_length=7, choices=TipoMovimentacao.choices)` | obrigatório |
| `quantidade` | `PositiveIntegerField` | `ENTRADA`/`SAIDA`: `1..QUANTIDADE_MAXIMA_MOVIMENTACAO`; `INICIAL`: `0..SALDO_MAXIMO` |
| `saldo_anterior` | `PositiveIntegerField` | snapshot do saldo antes, lido sob bloqueio |
| `saldo_posterior` | `PositiveIntegerField` | snapshot do saldo depois; `<= SALDO_MAXIMO` |
| `observacao` | `CharField(max_length=200, blank=True, default="")` | aparada; opcional |
| `criado_em` | `DateTimeField(default=timezone.now, db_index=True, editable=False)` | automático; `default` (e não `auto_now_add`) para a migração 0002 poder usar `produto.criado_em` |

**Meta**: `ordering = ["-criado_em", "-id"]`; `verbose_name = "movimentação"`;
`verbose_name_plural = "movimentações"`.

**Propriedades de apresentação** (somente leitura): `eh_saida` (bool), `sinal` (`"+"` ou `"−"`
U+2212), `quantidade_assinada` (`-quantidade` em `SAIDA`), `variante_selo` e `icone_selo`
(design-system §4.4.2: `ENTRADA` → `"info"` + `arrow-down-to-line`; `SAIDA` → `"neutro"` +
`arrow-up-from-line`; `INICIAL` → `"neutro"`, sem ícone — classes `.badge--<variante>` da 001),
`mensagem_confirmacao` → por exemplo `"Saída registrada: #0001 Parafuso — saldo 10 → 7"`
(`"Entrada registrada"`, `"Saldo inicial registrado"`). `mensagem_confirmacao` tem no máximo
200 caracteres (limite do toast da 001): com nome de 120 caracteres e saldos de 10 dígitos o
texto chega a ~182; acima de 200, o nome é encurtado com "…" (o `#ID` permanece).

### Restrições de banco

| Nome | Tipo | Condição |
|------|------|----------|
| (implícitas) | `CHECK` de `PositiveIntegerField` | `quantidade >= 0`, `saldo_anterior >= 0`, `saldo_posterior >= 0` |
| `mov_tipo_valido` | `CheckConstraint` | `tipo IN ('INICIAL','ENTRADA','SAIDA')` |
| `mov_quantidade_positiva_exceto_inicial` | `CheckConstraint` | `quantidade > 0 OR tipo = 'INICIAL'` |
| `mov_saldo_posterior_consistente` | `CheckConstraint` | `(tipo IN ('INICIAL','ENTRADA') AND saldo_posterior = saldo_anterior + quantidade) OR (tipo = 'SAIDA' AND saldo_posterior = saldo_anterior - quantidade)` |
| `mov_inicial_parte_de_zero` | `CheckConstraint` | `tipo <> 'INICIAL' OR saldo_anterior = 0` |
| `mov_inicial_unica_por_produto` | `UniqueConstraint(fields=["produto"], condition=Q(tipo="INICIAL"))` | no máximo um `INICIAL` por produto |

Todas declaradas com `CheckConstraint(condition=…, name=…)` (Django 5.2). Do lado do `Produto`
(feature 002): `CheckConstraint(quantidade_atual >= 0)` — terceira camada da regra do FR-004.

### Índices

| Nome | Campos | Consulta atendida |
|------|--------|-------------------|
| (de `db_index`) | `criado_em` | página Movimentações ordenada por data e filtro de período |
| `mov_produto_criado_idx` | `produto`, `-criado_em` | histórico do produto e filtro por produto |

## `MovimentacaoQuerySet` / manager

| Método | Retorno | Observação |
|--------|---------|------------|
| `do_produto(produto_id)` | `QuerySet` | filtro por FK |
| `do_tipo(tipo)` | `QuerySet` | filtro por tipo |
| `no_periodo(de, ate)` | `QuerySet` | `de`/`ate` são `date` (inclusivos), convertidos para `[início(de), início(ate+1))` no fuso atual; qualquer um pode ser `None` |
| `recentes()` | `QuerySet` | `select_related("produto").order_by("-criado_em", "-id")` |
| `update(...)` / `delete()` | — | **lançam `MovimentacaoImutavelError`** |

## Imutabilidade (FR-021)

- `Movimentacao.save()` com registro já persistido → `MovimentacaoImutavelError`
  ("Movimentações são imutáveis; registre uma movimentação de sentido oposto.").
- `Movimentacao.delete()` → `MovimentacaoImutavelError`.
- `MovimentacaoQuerySet.update()` / `.delete()` → `MovimentacaoImutavelError`.
- `produto` com `on_delete=PROTECT`: produto com histórico não pode ser apagado.
- Sem formulário, rota, view ou admin de edição/exclusão.

## Ciclo de vida

```text
          (não existe) ──registrar_movimentacao()──► GRAVADA (definitiva, imutável)
                         │
                         └─ falha de validação / EstoqueInsuficienteError / SaldoMaximoExcedidoError
                            → nada é gravado (rollback da transação)
```

Não há estados intermediários nem transições após a gravação. Correção = nova movimentação de
sentido oposto, com observação.

## Invariantes (verificadas por `selectors.auditar_saldos()` e testes)

1. **Saldo = Σ movimentações** (FR-029): para todo produto,
   `quantidade_atual = Σ(INICIAL + ENTRADA) − Σ(SAIDA)`.
2. **Continuidade**: ordenadas por `(criado_em, id)`, o `saldo_posterior` de cada movimentação é o
   `saldo_anterior` da seguinte; a última tem `saldo_posterior = quantidade_atual`.
3. **Origem única**: todo produto tem exatamente um `INICIAL`, e ele é a primeira movimentação.
4. **Não negatividade**: nenhum saldo (atual, anterior ou posterior) é negativo.

`auditar_saldos()` devolve a lista de divergências (`DivergenciaSaldo(produto_id, saldo_atual,
saldo_calculado, motivo)`); lista vazia = livro-razão consistente.

## Validações por camada

| Regra | Formulário (`forms.py`) | Serviço (`services.py`) | Banco |
|-------|-------------------------|-------------------------|-------|
| Produto existe | `ModelChoiceField` ("Selecione um produto válido.") | `MovimentacaoInvalidaError` ("Produto #0099 não encontrado.") | FK |
| Tipo permitido | `ENTRADA`/`SAIDA` apenas | `INICIAL` só sem histórico e com saldo 0 | `mov_tipo_valido`, `mov_inicial_*` |
| Quantidade inteira 1..1.000.000 | `QuantidadeField` | `MovimentacaoInvalidaError` | `mov_quantidade_positiva_exceto_inicial` |
| Saída ≤ saldo | `clean()` (saldo lido sem bloqueio) | `EstoqueInsuficienteError` (saldo sob bloqueio) | `CHECK quantidade_atual >= 0` e `saldo_posterior >= 0` |
| Saldo ≤ 2.147.483.647 | `clean()` | `SaldoMaximoExcedidoError` | limite do tipo inteiro |
| Observação ≤ 200 | `CharField(max_length=200, strip=True)` | `MovimentacaoInvalidaError` | `varchar(200)` |
| Saldo posterior coerente | — | calculado | `mov_saldo_posterior_consistente` |

## Migrações

- `apps/movimentacoes/migrations/0001_initial.py` — cria `Movimentacao`, restrições `mov_*` e
  índices; depende da última migração de `produtos`.
- `apps/movimentacoes/migrations/0002_saldo_inicial_retroativo.py` — `RunPython`: para cada
  `Produto` sem movimentações, cria `INICIAL(quantidade=quantidade_atual, saldo_anterior=0,
  saldo_posterior=quantidade_atual, criado_em=produto.criado_em)`; `reverse_code` no-op. Usa os
  modelos históricos (`apps.get_model`), então as guardas de imutabilidade não interferem.

## Extensão do `Produto` (feature 002) usada aqui

- `quantidade_atual` só é escrita por `registrar_movimentacao` (e pela criação com 0 em
  `cadastrar_produto`).
- `Produto.codigo` → `"#0001"` (proposta ao contrato, ver research).
- `ProdutoQuerySet.com_situacao()` usado para re-renderizar a linha da lista após a movimentação.
