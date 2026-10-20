# Contrato: consultas, regras e exportação (API Python interna)

Consumidores: views da 004, `core:painel` (001), lista/detalhe de produtos (002), view de
movimentação (003), comandos `varrer_estoque` e `popular_demo`. Fórmulas em
[../data-model.md](../data-model.md).

## 1. `apps/produtos/models.py` — `ProdutoQuerySet` (contrato compartilhado)

```python
class ProdutoQuerySet(models.QuerySet):
    def em_alerta(self) -> "ProdutoQuerySet": ...
    def com_situacao(self) -> "ProdutoQuerySet": ...   # anota em_alerta, deficit, cobertura_percentual
```

| Chamada | Garantia |
|---------|----------|
| `Produto.objects.em_alerta()` | somente produtos com `quantidade_atual <= estoque_minimo`; encadeável com `buscar(q)` e filtros da 002 |
| `Produto.objects.com_situacao()` | não filtra nem reordena; cada instância recebe `em_alerta: bool`, `deficit: int`, `cobertura_percentual: int \| None` |
| ambos | aritmética em `bigint` (sem `integer out of range` com valores até 2.147.483.647); resultado idêntico em PostgreSQL e SQLite |

Restrição: `Produto` **não** pode declarar atributos/propriedades chamados `em_alerta`, `deficit`
ou `cobertura_percentual` (colidiriam com as anotações).

## 2. `apps/alertas/regras.py` — regra em Python puro (sem ORM)

```python
TETO_SALDO: int = 2_147_483_647
FATOR_ESTOQUE_ALVO: int = 2

class Situacao(enum.StrEnum):          # valor = código; .rotulo, .gravidade
    OK = "OK"
    REPOSICAO_NECESSARIA = "REPOSICAO_NECESSARIA"
    SEM_ESTOQUE = "SEM_ESTOQUE"

class Transicao(enum.StrEnum):
    PIOROU = "PIOROU"
    SAIU_DO_ALERTA = "SAIU_DO_ALERTA"
    NENHUMA = "NENHUMA"

@dataclass(frozen=True)
class Aviso:
    nivel: str          # "sucesso" | "alerta"
    texto: str

def classificar(quantidade: int, minimo: int) -> Situacao: ...
def em_alerta(quantidade: int, minimo: int) -> bool: ...
def deficit(quantidade: int, minimo: int) -> int: ...
def cobertura_percentual(quantidade: int, minimo: int) -> int | None: ...
def sugestao_reposicao(quantidade: int, minimo: int) -> int | None: ...   # None se OK
def transicao(saldo_anterior: int, saldo_posterior: int, minimo: int) -> Transicao: ...
def aviso_movimentacao(movimentacao) -> Aviso | None: ...                 # None se NENHUMA ou INICIAL
def mensagem_confirmacao(texto_base: str, movimentacao) -> Aviso: ...     # texto da 003 + aviso
def codigo_produto(produto_id: int) -> str: ...                           # 7 -> "#0007"
```

| Função | Pré-condição | Pós-condição |
|--------|--------------|--------------|
| `classificar(q, m)` | `q, m ≥ 0` | `SEM_ESTOQUE` se `q == 0`; `REPOSICAO_NECESSARIA` se `0 < q ≤ m`; `OK` se `q > m` |
| `deficit(q, m)` | idem | `max(m − q, 0)` |
| `cobertura_percentual(q, m)` | idem | `0` se `q == 0`; `None` se `m == 0`; senão `q * 100 // m` |
| `sugestao_reposicao(q, m)` | idem | `None` se OK; senão `min(max(2*m − q, 1), TETO_SALDO − q)` |
| `transicao(a, p, m)` | `a, p, m ≥ 0` | conforme tabela de transições do data-model |
| `aviso_movimentacao(mov)` | `mov.produto` carregado | usa `mov.saldo_anterior`, `mov.saldo_posterior`, `mov.produto.estoque_minimo` |
| `mensagem_confirmacao(t, mov)` | — | `Aviso("alerta", f"{t.rstrip('.')}. {aviso.texto}")` se piorou; `Aviso("sucesso", f"{t.rstrip('.')}. {aviso.texto}")` se saiu do alerta; senão `Aviso("sucesso", t)` (texto da 003 intacto) |

`Situacao.rotulo`: `"OK"`, `"REPOSIÇÃO NECESSÁRIA"`, `"SEM ESTOQUE"`.
`Situacao.gravidade`: `0`, `1`, `2`.

## 3. `apps/alertas/selectors.py` — leitura

```python
@dataclass(frozen=True)
class ItemReposicao: ...          # campos no data-model §4

@dataclass(frozen=True)
class ResultadoVarredura: ...     # campos no data-model §4

@dataclass(frozen=True)
class ResumoPainel: ...           # campos no data-model §4

def produtos_por_criticidade(*, incluir_ok: bool = False) -> QuerySet[Produto]: ...
def varrer(*, incluir_ok: bool = False, agora: datetime | None = None) -> ResultadoVarredura: ...
def total_em_alerta() -> int: ...
def resumo_painel(*, agora: datetime | None = None) -> ResumoPainel: ...
```

| Função | Consultas SQL | Garantia |
|--------|--------------:|----------|
| `produtos_por_criticidade()` | 0 (lazy) | `com_situacao()` + `gravidade` + `sugestao_reposicao`, ordem `gravidade DESC, deficit DESC, cobertura ASC NULLS LAST, id ASC`; só em alerta salvo `incluir_ok=True` |
| `varrer()` | 2 | `executada_em = agora or timezone.now()`; totais coerentes com os itens (I-4) |
| `total_em_alerta()` | 1 | `Produto.objects.em_alerta().count()` |
| `resumo_painel()` | ≤ 5 | KPIs em 1 agregação + 24 h (1) + críticos (1) + cobertura (1) + últimas movimentações (1, `select_related`) |

## 4. `apps/alertas/exportacao.py` — serialização única (web e terminal)

```python
COLUNAS: tuple[str, ...] = ("ID", "Produto", "Quantidade atual", "Estoque mínimo", "Déficit",
                            "Cobertura (%)", "Sugestão de reposição", "Situação")

def para_csv(resultado: ResultadoVarredura, *, bom: bool) -> str: ...
def para_json(resultado: ResultadoVarredura) -> str: ...
def para_texto(resultado: ResultadoVarredura, *, simbolo: str = "⚠") -> list[tuple[str, bool]]: ...
def nome_arquivo_csv(resultado: ResultadoVarredura) -> str: ...   # "reposicao-20261020-1432.csv"
```

| Saída | Regras |
|-------|--------|
| CSV | `;`, `\r\n`, aspas mínimas, BOM só se `bom=True`; 1 linha de cabeçalho `COLUNAS`; números inteiros sem separador; cobertura e sugestão vazias quando `None`; `Situação` = rótulo; texto iniciado por `=`, `+`, `-`, `@`, TAB ou CR recebe `'` inicial |
| JSON | UTF-8 (`ensure_ascii=False`), indentado 2; ver esquema em [cli.md](cli.md#json) |
| Texto | lista de `(linha, eh_alerta)` para o comando aplicar estilo; números com separador de milhar "."; data `dd/mm/aaaa HH:MM` local |
