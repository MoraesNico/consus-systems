# Data Model: Alerta de Reposição (feature 004)

**Data**: 2026-10-20 · **Fonte**: [spec.md](spec.md), [research.md](research.md), `docs/arquitetura.md`

Esta feature **não cria tabelas, colunas, índices nem migrações** (Clarificação 1). Ela lê
`produtos.Produto` e `movimentacoes.Movimentacao` e deriva tudo o mais em consulta ou em memória.

## 1. Entidades persistidas usadas (somente leitura)

### `produtos.Produto` (feature 002)

| Campo | Uso nesta feature |
|-------|-------------------|
| `id` / `codigo` (propriedade da 002) | identificação; exibido `#0001`; último critério de desempate |
| `nome` | exibição; chave natural do `popular_demo` (`nome__iexact`) |
| `quantidade_atual` | entrada da regra (inteiro 0…2.147.483.647) |
| `estoque_minimo` | entrada da regra (inteiro 0…2.147.483.647) |
| `em_alerta`, `situacao` (propriedades da 002) | `em_alerta` = mesma regra; `situacao` binária (`"alerta"`/`"ok"`) usada pelo filtro da 002 — a 004 não a altera |

### `movimentacoes.Movimentacao` (feature 003)

| Campo | Uso nesta feature |
|-------|-------------------|
| `tipo` | `ENTRADA`/`SAIDA` contam no KPI de 24 h; `INICIAL` não conta e nunca gera aviso |
| `quantidade`, `saldo_anterior`, `saldo_posterior` | "últimas movimentações"; transição de situação do toast |
| `produto` | nome/ID nas listas; `estoque_minimo` vigente para a transição |
| `criado_em` | janela móvel de 24 h; ordenação das últimas movimentações (`-criado_em`, `-id`) |

## 2. Anotações de `ProdutoQuerySet` (contrato)

Definidas em `apps/produtos/models.py`. `q = Cast(quantidade_atual, bigint)`,
`m = Cast(estoque_minimo, bigint)` — o cast é obrigatório (R2). A anotação booleana chama-se
`alerta` (nome já adotado pela 002), porque `Produto.em_alerta` é uma propriedade.

| Método / anotação | Tipo | Definição |
|-------------------|------|-----------|
| `em_alerta()` | QuerySet | `filter(quantidade_atual__lte=F("estoque_minimo"))` |
| `com_situacao()` → `alerta` (002) | bool | `quantidade_atual <= estoque_minimo` |
| `com_situacao()` → `deficit` | bigint ≥ 0 | `Greatest(m − q, 0)` |
| `com_situacao()` → `cobertura_percentual` | bigint ≥ 0 ou `NULL` | `0` se `q = 0`; `NULL` se `m = 0` (e `q > 0`); senão `(q × 100) / m` (divisão inteira = arredondamento para baixo) |

Anotações adicionais de uso interno, aplicadas em `apps/alertas/selectors.py`:

| Anotação | Tipo | Definição |
|----------|------|-----------|
| `gravidade` | int | `2` se `q = 0`; `1` se `alerta`; senão `0` |
| `sugestao_reposicao` | bigint ou `NULL` | se `alerta`: `Least(Greatest(2·m − q, 1), QUANTIDADE_MAXIMA − q)`; senão `NULL` |

**Ordem de criticidade** (FR-006): `gravidade DESC, deficit DESC, cobertura_percentual ASC NULLS LAST, id ASC`.

## 3. Funções puras (`apps/alertas/regras.py`)

Espelham as anotações para uso sem consulta. Tabela-verdade de referência (usada nos testes):

| atual | mínimo | situação | déficit | cobertura | sugestão |
|------:|-------:|----------|--------:|----------:|---------:|
| 5 | 10 | REPOSIÇÃO NECESSÁRIA | 5 | 50 | 15 |
| 9 | 10 | REPOSIÇÃO NECESSÁRIA | 1 | 90 | 11 |
| 10 | 10 | REPOSIÇÃO NECESSÁRIA | 0 | 100 | 10 |
| 11 | 10 | OK | 0 | 110 | — |
| 0 | 8 | SEM ESTOQUE | 8 | 0 | 16 |
| 0 | 0 | SEM ESTOQUE | 0 | 0 | 1 |
| 3 | 0 | OK | 0 | — (não se aplica) | — |
| 999 | 1.000 | REPOSIÇÃO NECESSÁRIA | 1 | 99 | 1.001 |
| 2.147.483.647 | 2.147.483.647 | REPOSIÇÃO NECESSÁRIA | 0 | 100 | 0 (teto de saldo) |

### Enumeração `Situacao`

| Código | Rótulo exibido | Gravidade | Variante visual |
|--------|----------------|----------:|-----------------|
| `OK` | OK | 0 | selo `neutro` (texto atenuado, sem cor de alerta, sem ícone); barra `sucesso` |
| `REPOSICAO_NECESSARIA` | REPOSIÇÃO NECESSÁRIA | 1 | selo e barra `alerta` — ícone SVG ⚠ + texto + cor de alerta |
| `SEM_ESTOQUE` | SEM ESTOQUE | 2 | selo e barra `perigo` — ícone SVG ⚠ + texto + cor de perigo |

### Transições de situação (aviso na confirmação — FR-019)

`transicao(saldo_anterior, saldo_posterior, minimo)` compara as gravidades antes/depois:

| De → Para | Resultado | Efeito na confirmação |
|-----------|-----------|-----------------------|
| OK → REPOSIÇÃO NECESSÁRIA | `PIOROU` | nível `alerta`; "REPOSIÇÃO NECESSÁRIA: #0003 Parafuso M6 ficou com 10 un. (mínimo 10)." |
| OK → SEM ESTOQUE | `PIOROU` | nível `alerta`; "SEM ESTOQUE: #0003 Parafuso M6 zerou (mínimo 10)." |
| REPOSIÇÃO NECESSÁRIA → SEM ESTOQUE | `PIOROU` | idem SEM ESTOQUE |
| REPOSIÇÃO NECESSÁRIA → OK, SEM ESTOQUE → OK | `SAIU_DO_ALERTA` | nível `sucesso`; "#0003 Parafuso M6 saiu do alerta de reposição." |
| SEM ESTOQUE → REPOSIÇÃO NECESSÁRIA | `NENHUMA` | sem aviso extra |
| mesma situação | `NENHUMA` | sem aviso extra |
| tipo `INICIAL` | `NENHUMA` | sem aviso (cadastro é da 002) |

O texto final é `"<Movimentacao.mensagem_confirmacao da 003>. <aviso>"`, ex.: "Saída registrada:
#0003 Parafuso M6 — saldo 11 → 10. REPOSIÇÃO NECESSÁRIA: #0003 Parafuso M6 ficou com 10 un.
(mínimo 10)."

## 4. Objetos derivados (não persistidos)

### Item de reposição = `Produto` anotado

Os itens da varredura e do painel são instâncias reais de `Produto` (para reutilizar
`produto.codigo`, `get_absolute_url()` e o parcial de situação da 002), vindas de
`produtos_por_criticidade()`:

| Atributo | Tipo | Origem |
|----------|------|--------|
| `id`, `codigo`, `nome`, `quantidade_atual`, `estoque_minimo` | — | modelo (002) |
| `alerta` | bool | anotação (002) |
| `deficit` | int ≥ 0 | anotação (004) |
| `cobertura_percentual` | int \| None | anotação (004); `None` = "não se aplica" |
| `gravidade` | 0 \| 1 \| 2 | anotação (selectors) |
| `sugestao_reposicao` | int \| None | anotação (selectors); `None` quando OK |
| `situacao_estoque` | `Situacao` | atribuído em Python por `regras.classificar` após a consulta |

### `ResultadoVarredura` (dataclass imutável)

| Campo | Tipo | Observação |
|-------|------|------------|
| `executada_em` | datetime (aware) | instante do cálculo |
| `total_analisado` | int | `COUNT` de produtos |
| `total_em_alerta` | int | `len` dos itens em alerta |
| `total_sem_estoque` | int | itens com `situacao = SEM_ESTOQUE` |
| `itens` | tuple[Produto, …] | Produtos anotados; só em alerta (ou todos com `incluir_ok=True`), ordem de criticidade |
| `sem_produtos` (prop.) | bool | `total_analisado == 0` |
| `sem_alertas` (prop.) | bool | `total_em_alerta == 0` |

### `ResumoPainel` (dataclass imutável)

| Campo | Tipo | Origem |
|-------|------|--------|
| `total_produtos` | int | `Count("id")` |
| `total_unidades` | int | `Coalesce(Sum("quantidade_atual"), 0)` |
| `total_em_alerta` | int | `Count("id", filter=Q(quantidade_atual__lte=F("estoque_minimo")))` |
| `total_sem_estoque` | int | `Count("id", filter=Q(quantidade_atual=0))` |
| `movimentacoes_24h` | int | `ENTRADA`+`SAIDA` com `criado_em >= agora − 24 h` |
| `criticos` | tuple[Produto, …] | 5 primeiros da ordem de criticidade (anotados, com `situacao_estoque`) |
| `cobertura` | tuple[Produto, …] | 8 menores `cobertura_percentual` não nulas (empate: menor ID; anotados, com `situacao_estoque`) |
| `ultimas_movimentacoes` | tuple[Movimentacao, …] | 5 mais recentes, com produto |

### `Aviso` (dataclass imutável)

`nivel: Literal["sucesso", "alerta"]`, `texto: str`.

## 5. Invariantes

- **I-1** Nenhum código da feature altera `Produto.quantidade_atual` ou `Movimentacao`, exceto
  `popular_demo`, e este apenas via `cadastrar_produto` e `registrar_movimentacao`.
- **I-2** Para todo produto, `anotações SQL == funções de regras.py` (teste de equivalência).
- **I-3** Para todo produto em alerta com `estoque_minimo < 1.073.741.824` (2 × mínimo cabe no
  teto de saldo): `classificar(atual + sugestao, minimo) == OK` (SC-008).
- **I-4** `ResultadoVarredura.total_em_alerta == len([i for i in itens if i.situacao_estoque != OK])` e é
  igual a `Produto.objects.em_alerta().count()` no mesmo estado.

## 6. Dados de demonstração

Roteiro fixo de `apps/alertas/demo.py` (cada linha: cadastro com quantidade inicial, depois as
movimentações na ordem). Situação final esperada em base vazia:

| # | Nome | Mínimo | Inicial | Movimentações | Final | Situação esperada |
|--:|------|-------:|--------:|---------------|------:|-------------------|
| 1 | Caneta esferográfica azul | 50 | 200 | S 60 "Venda balcão"; S 45 "Pedido 1042" | 95 | OK |
| 2 | Papel sulfite A4 (resma 500 fls) | 20 | 30 | S 18 "Pedido 1043"; E 40 "NF 88231" | 52 | OK |
| 3 | Parafuso sextavado M6 x 20 | 100 | 150 | S 90 "Obra Rua 7" | 60 | REPOSIÇÃO (déficit 40) |
| 4 | Fita adesiva transparente 48 mm | 24 | 24 | E 12 "NF 88302"; S 12 "Venda balcão" | 24 | REPOSIÇÃO (no mínimo) |
| 5 | Cola branca 90 g | 15 | 15 | S 10 "Escola Aurora"; S 5 "Venda balcão" | 0 | SEM ESTOQUE |
| 6 | Grampeador de mesa 26/6 | 5 | 8 | S 2 "Venda balcão" | 6 | OK (mínimo + 1) |
| 7 | Luva de nitrilo (caixa c/ 100) | 10 | 12 | S 9 "Clínica Bem-Estar" | 3 | REPOSIÇÃO (déficit 7) |
| 8 | Lâmpada LED 9 W | 30 | 80 | S 20 "Pedido 1044" | 60 | OK |
| 9 | Caderno universitário 96 fls | 40 | 100 | S 35 "Escola Aurora"; E 20 "NF 88410" | 85 | OK |
| 10 | Etiqueta adesiva 100x50 (rolo) | 0 | 12 | — | 12 | OK (cobertura não se aplica) |
| 11 | Toner HP 85A | 4 | 10 | S 3 "Pedido 1045" | 7 | OK |
| 12 | Pilha alcalina AA (par) | 60 | 100 | S 30 "Venda balcão" | 70 | OK |

Resultado esperado da varredura (base vazia): 12 analisados, **4 em alerta (1 sem estoque)**,
ordem: Cola branca 90 g → Parafuso sextavado M6 x 20 → Luva de nitrilo → Fita adesiva 48 mm.
Unidades em estoque: 474. Movimentações (E+S) nas últimas 24 h: 16 (mais 12 de saldo inicial,
que não contam no indicador).
