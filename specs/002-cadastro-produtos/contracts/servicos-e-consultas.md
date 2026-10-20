# Contrato Python — serviços e consultas de `produtos` (002)

API pública da app `apps/produtos` consumida pelas views desta feature e pelas features 003 e
004. Escrita em `services.py`, leitura em `selectors.py` e `ProdutoQuerySet` (`models.py`),
conforme `docs/arquitetura.md`.

## `apps/produtos/models.py`

```python
QUANTIDADE_MAXIMA: int = 2_147_483_647

class ProdutoQuerySet(models.QuerySet):
    def buscar(self, q: str | None) -> "ProdutoQuerySet": ...
    def em_alerta(self) -> "ProdutoQuerySet": ...      # quantidade_atual <= estoque_minimo
    def sem_alerta(self) -> "ProdutoQuerySet": ...     # quantidade_atual >  estoque_minimo
    def com_situacao(self) -> "ProdutoQuerySet": ...   # anota alerta: bool

class Produto(models.Model):
    # campos e restrições: ver data-model.md
    objects = ProdutoQuerySet.as_manager()
    @property
    def codigo(self) -> str: ...        # "#0001"
    @property
    def em_alerta(self) -> bool: ...
    @property
    def situacao(self) -> str: ...      # "alerta" | "ok"
    def get_absolute_url(self) -> str: ...
    def __str__(self) -> str: ...       # "#0001 — Caneta Azul"
```

### `buscar(q)` — tabela de verdade (FR-013)

| `q` (após normalizar espaços) | Filtro aplicado | Exemplo de resultado |
|-------------------------------|-----------------|----------------------|
| vazio | nenhum | todos |
| `#12`, `#0012`, `# 12` | `pk = 12` | só `#0012` |
| `#0`, `#99999999999999999999999` | nenhum produto | vazio |
| `12`, `0012` | `pk = 12` **ou** `nome` contém `"12"`/`"0012"` (sem diferenciar maiúsculas/minúsculas) | `#0012` e "Bucha 12 mm" |
| `99999999999999999999999` | só `nome` contém (acima do máximo de `BigAutoField`) | nomes com esse texto |
| `cAnEtA`, `50%`, `a_b`, `#abc` | `nome` contém o texto literal | "Caneta Azul", … |

## `apps/produtos/services.py` (escrita)

```python
def normalizar_nome(valor: str | None) -> str:
    """Remove espaços das extremidades e colapsa espaços internos (FR-004)."""

def cadastrar_produto(*, nome: str, quantidade_inicial: int, estoque_minimo: int) -> Produto:
    """Cadastra um produto (FR-001, FR-029)."""

def editar_produto(*, produto_id: int, nome: str, estoque_minimo: int) -> Produto:
    """Altera nome e estoque mínimo; nunca a quantidade (FR-024, FR-025)."""
```

### `cadastrar_produto`

- **Pré-condições**: argumentos só por nome; `quantidade_inicial` e `estoque_minimo` do tipo
  `int` (não `bool`).
- **Validação** (lança `django.core.exceptions.ValidationError` com dicionário por campo e os
  códigos de [data-model.md](../data-model.md#mensagens-de-validação-fr-007)): nome normalizado
  obrigatório e ≤ 120; nome único (`Lower`); inteiros entre 0 e `QUANTIDADE_MAXIMA`.
- **Efeito**: em `transaction.atomic()`, cria o `Produto` com
  `quantidade_atual = quantidade_inicial`. `IntegrityError` de `produto_nome_unico_ci` (corrida)
  → mesma `ValidationError` `nome_duplicado`, citando o código do produto existente.
- **Pós-condições invariantes** (verificadas pelos testes da 002 e que a 003 DEVE preservar):
  1. retorna um `Produto` persistido com `pk` novo, maior que todos os anteriores;
  2. `produto.quantidade_atual == quantidade_inicial`;
  3. `produto.nome == normalizar_nome(nome)`; `produto.estoque_minimo == estoque_minimo`;
  4. em caso de erro, nada é gravado.
- **Ponto de extensão da 003 (FR-030)**: a 003 altera o corpo desta função para, na mesma
  transação, registrar `Movimentacao(tipo=INICIAL, quantidade=quantidade_inicial)` via
  `movimentacoes.services.registrar_movimentacao`, mantendo assinatura e pós-condições
  (ex.: criar com `quantidade_atual=0` e deixar a movimentação `INICIAL` levar o saldo a
  `quantidade_inicial`).
- **Consumidores**: `produtos.views.novo`; dados de demonstração da 004.

### `editar_produto`

- **Efeito**: em `transaction.atomic()`, `select_for_update()` do produto; normaliza e valida
  como no cadastro (unicidade excluindo o próprio `pk`); grava com
  `save(update_fields=["nome", "estoque_minimo", "atualizado_em"])`.
- **Erros**: `Produto.DoesNotExist` (inexistente); `ValidationError` (como acima).
- **Garantia**: nunca escreve `quantidade_atual` (não perde movimentação concorrente da 003).

## `apps/produtos/selectors.py` (leitura)

```python
ORDEM_PADRAO = "-id"
ORDENS_VALIDAS = {"id", "nome", "quantidade", "minimo", "situacao"}  # com "-" opcional
SITUACOES_VALIDAS = {"alerta", "ok"}
POR_PAGINA = 25

def normalizar_ordem(ordem: str | None) -> str: ...          # inválida → "-id"
def normalizar_situacao(situacao: str | None) -> str: ...    # inválida → ""
def listar_produtos(*, q: str = "", situacao: str = "", ordem: str = "") -> QuerySet[Produto]:
    """com_situacao() + buscar(q) + filtro de situação + ordenação com desempate por -id."""
def obter_produto(produto_id: int) -> Produto:
    """Lança Produto.DoesNotExist, inclusive para IDs acima do máximo de BigAutoField."""
```

| `ordem` | Expressão | Observação |
|---------|-----------|------------|
| `id` / `-id` | `id` / `-id` | `-id` é o padrão |
| `nome` / `-nome` | `Lower("nome")` asc/desc | sem diferenciar maiúsculas/minúsculas |
| `quantidade` / `-quantidade` | `quantidade_atual` | |
| `minimo` / `-minimo` | `estoque_minimo` | |
| `situacao` / `-situacao` | `F("alerta").desc()` / `.asc()` | crescente = em alerta primeiro |

Desempate final sempre `-id`.
