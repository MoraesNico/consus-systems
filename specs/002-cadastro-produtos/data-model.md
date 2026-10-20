# Data Model: Cadastro de Produtos (002)

**Fonte**: [spec.md](./spec.md) (Key Entities, FR-001…FR-031) · contrato `docs/arquitetura.md`
(modelo `produtos.Produto`) · decisões em [research.md](./research.md).

## Entidade `produtos.Produto`

Arquivo: `apps/produtos/models.py` · Migração: `apps/produtos/migrations/0001_initial.py`

| Campo | Tipo | Nulo | Regras | FR |
|-------|------|------|--------|----|
| `id` | `BigAutoField(primary_key=True)` | não | Automático, crescente, nunca reutilizado; lacunas aceitáveis; nunca editado. Exibido como `#0001` (`Produto.codigo`). | FR-002, FR-003, FR-026 |
| `nome` | `CharField(max_length=120)` | não | Obrigatório; normalizado (extremidades aparadas, espaços internos consecutivos colapsados); 1–120 caracteres após normalização; único sem diferenciar maiúsculas/minúsculas; acentos significativos; grafia digitada preservada. | FR-004, FR-005 |
| `quantidade_atual` | `PositiveIntegerField` | não | Inteiro de 0 a `QUANTIDADE_MAXIMA`; definido no cadastro igual à Quantidade Inicial; depois **só** muda por `Movimentacao` (003). Nunca aparece em formulário editável. | FR-006, FR-008, FR-025 |
| `estoque_minimo` | `PositiveIntegerField` | não | Inteiro de 0 a `QUANTIDADE_MAXIMA`; obrigatório no cadastro; editável. | FR-006, FR-024 |
| `criado_em` | `DateTimeField(auto_now_add=True)` | não | Data/hora do cadastro; exibida `dd/mm/aaaa HH:MM`. | FR-021 |
| `atualizado_em` | `DateTimeField(auto_now=True)` | não | Data/hora da última alteração (edição ou movimentação). | FR-021 |

**Constante de módulo**: `QUANTIDADE_MAXIMA = 2_147_483_647`.

**Campo de entrada não persistido**: `quantidade_inicial` (formulário e serviço de cadastro) — é
copiada para `quantidade_atual` e, com a 003, vira a `Movimentacao` `INICIAL`.

### Restrições no banco (`Meta.constraints`)

| Nome | Definição | Garante |
|------|-----------|---------|
| `produto_quantidade_atual_nao_negativa` | `CheckConstraint(condition=Q(quantidade_atual__gte=0))` | Saldo nunca negativo (constituição I; SC-006) |
| `produto_estoque_minimo_nao_negativo` | `CheckConstraint(condition=Q(estoque_minimo__gte=0))` | FR-006 |
| `produto_nome_nao_vazio` | `CheckConstraint(condition=~Q(nome=""))` | FR-004 |
| `produto_nome_unico_ci` | `UniqueConstraint(Lower("nome"))` | FR-005 sob concorrência (SC-006) |

`Meta.ordering = ["-id"]` (ordenação padrão da clarificação); `verbose_name = "produto"`.

### Índices

- PK (`id`) — ordenação padrão `-id` e busca por ID.
- Índice funcional único `produto_nome_unico_ci` (`LOWER(nome)`) — unicidade e ordenação por
  nome.
- Nenhum índice adicional (volume de referência de 10 mil linhas — research R15).

### Propriedades e métodos de instância

| Membro | Retorno | Regra |
|--------|---------|-------|
| `codigo` | `str` | `f"#{pk:04d}"` → `#0001`, `#12345` |
| `__str__()` | `str` | `"#0001 — Caneta Azul"` |
| `em_alerta` | `bool` | `quantidade_atual <= estoque_minimo` |
| `situacao` | `str` | `"alerta"` se `em_alerta`, senão `"ok"` |
| `get_absolute_url()` | `str` | `reverse("produtos:detalhe", args=[pk])` |

### `ProdutoQuerySet` (manager `Produto.objects = ProdutoQuerySet.as_manager()`)

| Método | Efeito | Uso |
|--------|--------|-----|
| `buscar(q)` | `#`+dígitos → só ID; só dígitos → ID exato **ou** nome contém; outro texto → nome contém (sem diferenciar maiúsculas/minúsculas, literal); vazio → sem filtro; número acima do máximo de `BigAutoField` nunca filtra por ID. | Lista (002) |
| `em_alerta()` | `quantidade_atual <= estoque_minimo` | Filtro "Em alerta" (002); varredura/relatório/contador (004) |
| `sem_alerta()` | `quantidade_atual > estoque_minimo` | Filtro "OK" (002) |
| `com_situacao()` | anota `alerta: bool` | Ordenação por situação (002); 004 |

## Entidade derivada: Situação

Não persistida. Calculada sempre a partir dos valores atuais:

```text
             quantidade_atual <= estoque_minimo
   ┌────┐  ───────────────────────────────────▶  ┌────────┐
   │ OK │                                        │ ALERTA │  (⚠ REPOSIÇÃO NECESSÁRIA)
   └────┘  ◀───────────────────────────────────  └────────┘
             quantidade_atual >  estoque_minimo
```

Gatilhos de transição: cadastro (estado inicial), edição de `estoque_minimo` (002), movimentação
de Entrada/Saída (003). Exemplo de borda: quantidade 0 e mínimo 0 → **ALERTA**.

## Ciclo de vida do `Produto`

| Evento | Quem | Campos alterados | Observações |
|--------|------|------------------|-------------|
| Cadastro | `cadastrar_produto` (002) | todos | `quantidade_atual = quantidade_inicial`; com a 003, também `Movimentacao(tipo=INICIAL)` na mesma transação |
| Edição | `editar_produto` (002) | `nome`, `estoque_minimo`, `atualizado_em` | `save(update_fields=...)`; nunca grava `quantidade_atual` |
| Movimentação | `registrar_movimentacao` (003) | `quantidade_atual`, `atualizado_em` | `select_for_update`; fora do escopo desta feature |
| Exclusão | — | — | **Não existe** (FR-026); a FK da 003 usa `on_delete=PROTECT` |

## Relacionamentos

- `Produto 1 ── 0..* Movimentacao` (feature 003, `related_name="movimentacoes"`,
  `on_delete=PROTECT`). Nesta feature não há outras entidades.

## Regras de validação × camadas

| Regra | Formulário (`forms.py`) | Serviço (`services.py`) | Banco |
|-------|------------------------|-------------------------|-------|
| Nome obrigatório/normalizado/≤ 120 | `NomeProdutoField` | `normalizar_nome` + checagem | `produto_nome_nao_vazio`, `max_length` |
| Nome único (case-insensitive) | via serviço (erro anexado ao campo) | `Lower(nome)` + conversão de `IntegrityError` | `produto_nome_unico_ci` |
| Inteiro 0…2.147.483.647 | `InteiroNaoNegativoField` (`^[0-9]+$`) | checagem de tipo e faixa | `CheckConstraint` ≥ 0; `integer` (PostgreSQL) |
| Quantidade não editável | `ProdutoEdicaoForm` sem o campo | `update_fields` sem `quantidade_atual` | — |

## Mensagens de validação (FR-007)

| Código (`ValidationError.code`) | Campo | Mensagem |
|---------------------------------|-------|----------|
| `nome_obrigatorio` | `nome` | Informe o nome do produto. |
| `nome_longo` | `nome` | O nome deve ter no máximo 120 caracteres. |
| `nome_duplicado` | `nome` | Já existe um produto com este nome (#0001). |
| `quantidade_obrigatoria` | `quantidade_inicial` | Informe a quantidade inicial. |
| `estoque_minimo_obrigatorio` | `estoque_minimo` | Informe o estoque mínimo. |
| `inteiro_invalido` | ambos | Informe um número inteiro igual ou maior que zero. |
| `inteiro_maximo` | ambos | Informe um valor de no máximo 2.147.483.647. |
