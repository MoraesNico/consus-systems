# Research: Alerta de Reposição (feature 004)

**Data**: 2026-10-20 · **Entrada**: [spec.md](spec.md) (com 5 esclarecimentos) · [plan.md](plan.md)

O Technical Context não tinha itens `NEEDS CLARIFICATION`; esta pesquisa registra as decisões de
desenho que resolvem as incógnitas de integração e de comportamento, as boas práticas adotadas e
as propostas de ajuste ao contrato compartilhado (`docs/arquitetura.md`).

**Alinhamento com as features paralelas** (lidos em 2026-10-20, somente leitura): os contratos
publicados pela 002 (`servicos-e-consultas.md`, `fragmentos-e-eventos.md`) e pela 003
(`servico-movimentacao.md`, `rotas-movimentacoes.md`, `integracao-produtos.md`, `tasks.md`)
fixaram nomes que esta feature adota: `Produto.em_alerta`/`situacao`/`codigo` (propriedades),
anotação `alerta` em `com_situacao()`, `QUANTIDADE_MAXIMA`, `cadastrar_produto`,
`produtos/partials/situacao.html`, `Movimentacao.mensagem_confirmacao`, `registrar_movimentacao`,
`auditar_saldos`, campo `origem` (`pagina|lista|detalhe`), `sucesso_dialogo.html`, comando
`movimentar` e a carga útil de `estoque-alterado` (`{produto_id, saldo_anterior, saldo_posterior}`).

---

## R1. Onde e como a regra de alerta é expressa

- **Decision**: a regra fica em dois lugares, com teste de equivalência obrigatório:
  1. **SQL** — `ProdutoQuerySet.em_alerta()` (filtro `quantidade_atual <= estoque_minimo`, da
     002) e `ProdutoQuerySet.com_situacao()` (anotação `alerta` da 002 + `deficit` e
     `cobertura_percentual` acrescentadas pela 004). O booleano não pode se chamar `em_alerta`
     porque a 002 já define `Produto.em_alerta` como `@property` (colisão → `AttributeError`).
  2. **Python puro** — `apps/alertas/regras.py` (`classificar`, `deficit`,
     `cobertura_percentual`, `sugestao_reposicao`, `transicao`), sem acesso a ORM.
  `apps/alertas/tests/test_equivalencia_regra.py` cadastra uma grade de produtos
  (quantidade 0…6 × mínimo 0…6, mais valores extremos 2.147.483.647) e compara, produto a produto,
  as anotações do banco com o resultado das funções Python.
- **Rationale**: contar/filtrar/ordenar precisa ser feito no banco (contador em 1 `COUNT`,
  ordenação por criticidade sem carregar tudo); a transição do toast parte de
  `saldo_anterior`/`saldo_posterior` da movimentação recém-criada e não deve exigir nova consulta.
  O teste em grade cobre os limites exigidos (igual, +1, 0/0) e impede divergência.
- **Alternatives considered**: (a) só Python, carregando todos os produtos — simples, mas o
  contador faria leitura completa da tabela a cada 30 s por aba aberta; (b) só SQL — o toast
  faria uma consulta extra e a exportação dependeria de anotações para valores triviais;
  (c) campo persistido `em_alerta` atualizado por sinal — viola FR-001 (situação nunca armazenada)
  e cria risco de dessincronização.

## R2. Aritmética sem estouro de inteiro

- **Decision**: em `com_situacao()` e na anotação de sugestão, `quantidade_atual` e
  `estoque_minimo` são convertidos com `Cast(..., BigIntegerField())` **antes** de multiplicar
  (`× 100` na cobertura, `× 2` na sugestão). A cobertura usa divisão inteira de `bigint`
  (trunca para baixo em valores não negativos — "arredondado para baixo", Clarificação 5).
- **Rationale**: `PositiveIntegerField` é `integer` (32 bits) no PostgreSQL. Sem o cast,
  `quantidade_atual * 100` estoura a partir de 21.474.837 unidades e `2 * estoque_minimo` a partir
  de 1.073.741.824 — o PostgreSQL lança `integer out of range` e o relatório inteiro cai. A 002
  aceita valores até 2.147.483.647 e a 003 até esse teto de saldo, então o caso é alcançável.
  O SQLite usa inteiros de 64 bits e não acusaria o problema — por isso o teste de valores
  extremos roda nos dois bancos (constituição: "a suíte MUST passar nos dois").
- **Alternatives considered**: calcular em `Decimal`/`float` (arredondamento ambíguo e sujeito a
  0,999… → 99%); limitar os valores na 002 (fora do escopo desta feature e contradiz a 002).

## R3. Sugestão de reposição (Clarificação 2)

- **Decision**: `sugestao = min(max(2 × mínimo − atual, 1), 2.147.483.647 − atual)`, apenas para
  produtos em alerta (fora de alerta → sem sugestão). Constante `FATOR_ESTOQUE_ALVO = 2` em
  `regras.py`.
- **Rationale**: regra explicável ("repor até o dobro do mínimo"), garante saída do alerta
  (atual + sugestão = 2 × mínimo > mínimo para mínimo ≥ 1; 0 + 1 > 0 para mínimo 0) e dá folga igual
  ao próprio estoque de segurança. O `min(…)` só atua no caso extremo de saldo próximo do teto da
  003, evitando sugerir uma entrada que a 003 recusaria por "Saldo máximo excedido".
- **Alternatives considered**: mínimo + 1 (sai do alerta, mas volta a ele na próxima venda);
  mínimo + 50% (exige arredondamento e é menos intuitivo); fator configurável por produto (exige
  campo novo — fora de escopo).

## R4. Cobertura e déficit com mínimo 0 (Clarificação 5)

- **Decision**: `deficit = max(mínimo − atual, 0)`; `cobertura_percentual` = `0` se atual = 0;
  `NULL` ("não se aplica", exibido "—") se mínimo = 0 e atual > 0; senão `⌊atual × 100 ÷ mínimo⌋`.
  Em ordenações, `NULL` vai por último (`nulls_last=True`).
- **Rationale**: evita divisão por zero, mantém a semântica "zerado = 0% coberto" e não inventa
  um percentual para produtos sem estoque de segurança definido. Arredondar para baixo impede
  exibir "100%" para quem está abaixo do mínimo (ex.: 999/1.000 → 99%).
- **Alternatives considered**: tratar mínimo 0 como 100% (falso conforto) ou como infinito
  (quebra a barra e a ordenação).

## R5. Ordenação por criticidade no banco

- **Decision**: `alertas.selectors` ordena com
  `order_by(gravidade.desc(), deficit.desc(), cobertura_percentual.asc(nulls_last=True), id.asc())`,
  em que `gravidade` é um `Case` (2 = SEM ESTOQUE, 1 = REPOSIÇÃO NECESSÁRIA, 0 = OK). A mesma chave
  serve para `--todos` no terminal (os OK ficam depois, por cobertura crescente).
- **Rationale**: uma única chave determinística, idêntica para relatório, painel, CSV e terminal
  (FR-006, SC-006); o desempate por ID torna duas varreduras do mesmo estado idênticas.
- **Alternatives considered**: ordenar em Python (exigiria carregar tudo); ordenar só por déficit
  (produtos zerados com mínimo pequeno ficariam atrás de déficits maiores — contraria a spec).

## R6. Varredura não persistida (Clarificação 1)

- **Decision**: `selectors.varrer(agora=None)` calcula e devolve um `ResultadoVarredura`
  imutável (dataclass); `executada_em = agora or timezone.now()`. Nenhuma tabela, nenhuma
  migração. `total_em_alerta` e `total_sem_estoque` são calculados a partir dos itens retornados
  (mesma consulta), e `total_analisado` por `COUNT` (2 consultas no total).
- **Rationale**: YAGNI (constituição V); a data/hora exibida é a do cálculo; totais e lista são
  coerentes entre si por virem da mesma consulta.
- **Alternatives considered**: modelo `Varredura` com histórico (fora de escopo pela
  Clarificação 1 e exigiria mudança no contrato de dados).

## R7. Contador automático: renderização, polling, evento e anúncio acessível

- **Decision**:
  - O contador é renderizado **no servidor** em toda página por uma *inclusion tag*
    `{% contador_alertas %}` dentro do contêiner `#badge-alertas` que a 001 reserva no item
    Alertas de `templates/components/navegacao.html` (funciona sem JS e em navegação `hx-boost`;
    mecanismo único do contrato v1.1 — o contêiner não tem atributos HTMX).
  - O fragmento `#contador-alertas` é autocontido: carrega
    `hx-get="/alertas/contador/?anterior=<total>"`,
    `hx-trigger="every <ALERTAS_INTERVALO_SEGUNDOS>s, estoque-alterado from:body"` e
    `hx-swap="outerHTML"`. Serve igualmente para polling e para `hx-swap-oob`.
  - `GET /alertas/contador/?anterior=N` responde **204** quando o total não mudou (o HTMX não troca
    nada) e **200** com o novo fragmento quando mudou — acompanhado de um fragmento OOB para a
    região viva `#anuncio-alertas` (`role="status"`, `aria-live="polite"`) com o texto
    "Alertas de reposição: 4 produtos (antes 3)." Sem `anterior` (ou inválido), responde 200 sem
    anúncio.
  - Falha de rede/5xx: o HTMX não troca o conteúdo e o polling continua no próximo ciclo
    (edge case "falha temporária").
- **Rationale**: a região viva é estável (não é substituída), então o anúncio é confiável; o 204
  elimina anúncios repetidos a cada 30 s (FR-017) e reduz trabalho de DOM; nenhuma linha de JS.
- **Alternatives considered**: `role="status"` no próprio contador com `innerHTML` (leitores de
  tela podem reanunciar valor idêntico a cada troca); `hx-trigger="load"` (pisca vazio e não
  funciona sem JS); SSE/WebSocket (exige infraestrutura ASGI — desproporcional); OOB do contador
  enviado pela resposta da 003 (acoplaria a 003 a um template da 004; o evento já resolve).

## R8. Fragmento × página completa

- **Decision**: views da 004 devolvem fragmento somente quando `apps.core.htmx.eh_fragmento(request)`
  (helper da 001, contrato v1.1: HTMX, não *boosted*, não restauração de histórico); navegação
  `hx-boost` e requisições sem HTMX recebem a página completa. Respostas variam por cabeçalho
  (`Vary: HX-Request, HX-Target`) e não são cacheadas (`Cache-Control: no-store` via
  `never_cache`).
- **Rationale**: com `hx-boost="true"` no `<body>`, a navegação também envia `HX-Request`; usar só
  `request.htmx` devolveria um fragmento no lugar da página. `Vary` impede que o navegador sirva o
  fragmento ao voltar no histórico.
- **Alternatives considered**: checar `HX-Target` (frágil se o alvo mudar de id).

## R9. Exportação CSV na mesma rota (Clarificação 4)

- **Decision**: `GET /alertas/?formato=csv` (valores aceitos: `html` — padrão — e `csv`; outro →
  400). `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment;
  filename="reposicao-AAAAMMDD-HHMM.csv"`, BOM UTF-8, separador `;`, `\r\n`, aspas mínimas.
  Proteção contra fórmula: valores textuais iniciados por `=`, `+`, `-`, `@`, TAB ou CR recebem
  apóstrofo inicial (recomendação OWASP "CSV Injection"). O link usa `hx-boost="false"` e
  `download` para não ser capturado pelo `hx-boost` do `<body>`.
- **Rationale**: mantém a tabela de rotas do contrato intacta (sem rota nova); `;` + BOM abre
  corretamente no Excel/LibreOffice em pt-BR; o mesmo `exportacao.para_csv()` alimenta o terminal
  (sem BOM), garantindo SC-006.
- **Alternatives considered**: rota `/alertas/exportar.csv` (altera o contrato de rotas);
  separador `,` RFC 4180 puro (Excel pt-BR abre tudo numa coluna); XLSX (dependência nova).

## R10. Comando `varrer_estoque`

- **Decision**: `BaseCommand` com `--formato {texto,csv,json}` (padrão `texto`), `--todos` e
  `--falhar-se-alerta`. Saída em `self.stdout`; texto com `self.style.WARNING` nas linhas em alerta
  (respeita `--no-color` e terminais sem cor). Códigos: 0 sucesso; 1 = há alerta **e**
  `--falhar-se-alerta` (via `CommandError(..., returncode=1)` com mensagem só no stderr, mantendo
  csv/json limpos no stdout); 2 = uso inválido (o `CommandParser` do Django já sai com 2 pelo
  argparse) ou erro de banco (`DatabaseError` → `CommandError(returncode=2)`). Se a codificação do
  stdout não representar "⚠", usa "(!)" mantendo "REPOSIÇÃO NECESSÁRIA".
- **Rationale**: códigos distintos permitem uso em cron/CI ("falhou por alerta" ≠ "não rodou");
  o serializador é o mesmo da web.
- **Alternatives considered**: `sys.exit(1)` direto (não testável com `call_command` de forma
  limpa); imprimir com `print` (ignora `--no-color` e o redirecionamento do `call_command`).

## R11. Aviso no toast da movimentação (Clarificação 3)

- **Decision**: `alertas.regras.transicao(saldo_anterior, saldo_posterior, minimo)` devolve
  `PIOROU`, `SAIU_DO_ALERTA` ou `NENHUMA` (gravidade OK=0 < REPOSIÇÃO=1 < SEM ESTOQUE=2).
  `aviso_movimentacao(mov)` produz `Aviso(nivel, texto)` e `confirmacao_com_alerta(mov)` compõe
  a propriedade `Movimentacao.mensagem_confirmacao` da 003 ("Saída registrada: #0001 Parafuso —
  saldo 11 → 10") com o aviso ("REPOSIÇÃO NECESSÁRIA: #0001 Parafuso ficou com 10 un. (mínimo
  10)."). Nível do toast: `alerta` quando piora; `sucesso` nos demais. A view `nova_movimentacao`
  da 003 passa a usar `confirmacao_com_alerta` no `HX-Trigger: {"toast": …}` e no framework
  `messages` (fluxo sem HTMX, com nível `WARNING` quando piora); o comando `movimentar` da 003
  imprime o mesmo aviso. `INICIAL` nunca gera aviso (cadastro é da 002).
- **"+ Entrada" a partir do relatório/painel**: o diálogo da 003 recebe `origem=alertas` e
  `quantidade=<sugestão, limitada a 1.000.000>` (ambos entregues pela 003 — contrato v1.1), cuja
  resposta de sucesso não traz fragmentos OOB de produto (`HX-Reswap: none` +
  `estoque-alterado`, `toast`, `fechar-dialogo`).
  Com `origem=lista`, a 003 enviaria um `<tr id="produto-<id>" hx-swap-oob>` que, no relatório,
  não teria alvo (erro `htmx:oobErrorNoTarget`) ou — pior — substituiria uma linha com colunas
  diferentes se o id coincidisse; por isso as linhas do relatório usam `id="reposicao-<id>"`.
- **Rationale**: a transição usa dados já presentes na movimentação (snapshot imutável), sem
  consulta extra; um só ponto de composição garante o mesmo texto com e sem HTMX.
- **Alternatives considered**: sinal `post_save` (não alcança a resposta HTTP); segundo toast
  (o contrato define um único evento `toast` com `{nivel, texto}`).

## R12. Painel

- **Decision**: a view `core:painel` (da 001) passa a chamar `alertas.selectors.resumo_painel(agora=None)`
  e renderiza `core/painel.html` (completo) ou `core/partials/painel_kpis.html` (fragmento cuja
  raiz é a região `#painel-kpis` reservada pela 001, com `hx-trigger="estoque-alterado
  from:body"`). KPIs em uma única
  agregação (`Count`, `Sum` com `Coalesce`, `Count(filter=…)`); movimentações 24 h com
  `tipo__in=[ENTRADA, SAIDA]` e janela móvel `criado_em >= agora − 24 h`; "Reposição necessária" =
  5 primeiros itens da ordem de criticidade; cobertura = 8 menores `cobertura_percentual` não nulas;
  últimas 5 movimentações com `select_related("produto")`.
- **Rationale**: a rota e o nome pertencem à 001 ("placeholder → 004"); os dados ficam em
  `alertas.selectors` para serem testados sem HTTP; ≤ 7 consultas fixas.
- **Alternatives considered**: mover a view para `alertas` e re-apontar `core:painel` (quebra o
  contrato de nomes); polling também no painel (desnecessário — o contador já cobre mudanças
  externas e o evento cobre as locais).

## R13. Componentes visuais (Tremor → design system)

- **Decision** (revista na auditoria de 2026-10-20): **nenhum componente novo**. A cobertura usa
  o ProgressBar da 001 (`components/barra_progresso.html`, `valor=cobertura_percentual`,
  `maximo=100`, parâmetro opcional `sufixo="%"`, `tom` = `Situacao.variante`), que já desenha a
  barra cheia acima do máximo e expõe `role="meter"`; a lista de cobertura do painel é um `<ul>`
  desses componentes (`{% lista_cobertura %}`). O selo de situação é **o parcial único da 002**
  (`produtos/partials/situacao.html` → `components/badge_estoque.html`), que já cobre SEM ESTOQUE
  como selo composto mantendo "⚠ REPOSIÇÃO NECESSÁRIA" (contrato v1.1, constituição IV) — um
  único selo para lista, detalhe, relatório e painel. A proposta original (`barra_cobertura.html`,
  `bar_list.html` e selo SEM ESTOQUE só com "SEM ESTOQUE") duplicava componentes do design system
  e omitia o texto obrigatório; foi substituída.
- **Rationale**: constituição IV (tokens primeiro, alerta nunca só por cor); a barra é decorativa
  para leitores de tela porque o número já está no texto.
- **Alternatives considered**: `<meter>` nativo (estilização inconsistente entre navegadores);
  biblioteca de gráficos (dependência nova e JS).

## R14. `popular_demo`

- **Decision**: conjunto fixo de 12 produtos em `apps/alertas/demo.py` (ver
  [data-model.md](data-model.md#6-dados-de-demonstração)). Para cada item: se já existe produto com o
  mesmo nome (`nome__iexact`), conta como "já existia" e **não toca** nele; senão, em
  `transaction.atomic()`, chama `produtos.services.cadastrar_produto(nome=…, quantidade_inicial=…,
  estoque_minimo=…)` e depois `movimentacoes.services.registrar_movimentacao(...)` para cada
  movimento do roteiro. Não retroage datas, não apaga nada, não exige `DEBUG`.
- **Rationale**: idempotência por nome é coerente com a unicidade case-insensitive da 002; a
  transação por produto evita "meio produto" se algo falhar (re-executar completa o que faltou);
  passar pelos serviços respeita o Princípio I e gera o livro-razão completo.
- **Alternatives considered**: `bulk_create` com saldos prontos (viola o Princípio I);
  `--redefinir` apagando dados (produtos e movimentações não são excluíveis no Consus);
  fixtures JSON (`loaddata`) (contornaria os serviços e não é idempotente sem chaves naturais).

## R15. Configuração do intervalo

- **Decision**: `ALERTAS_INTERVALO_SEGUNDOS` lido do ambiente em `config/settings.py`
  (padrão 30, mínimo 5; valores inválidos caem no padrão) e documentado em `.env.example`.
- **Rationale**: 12-factor (constituição V); o mínimo evita sobrecarga acidental.
- **Alternatives considered**: constante no código (não ajustável sem deploy).

## R16. Estratégia de testes e dados de teste

- **Decision**: fábrica `criar_produto(nome, quantidade, minimo)` em `apps/alertas/tests/conftest.py`
  usando `produtos.services.cadastrar_produto` (gera o saldo inicial pelo caminho oficial). O teste
  de desempenho (1.000 produtos) usa `bulk_create` de `Produto` + `Movimentacao(INICIAL)`
  coerentes, apenas como *setup* de teste, e mede número de consultas (não tempo de relógio).
- **Rationale**: testes de regra exercitam o caminho real; o de volume precisa ser rápido.
- **Alternatives considered**: medir tempo de relógio (instável em CI).

---

## Propostas de ajuste ao contrato

> Não editei `docs/arquitetura.md` (regra do brief). Proponho ao coordenador:

> **Status (auditoria 2026-10-20)**: consolidadas em `docs/arquitetura.md` v1.1, que prevalece
> onde divergir: proposta 4 → nível de erro do toast é **`erro`** (não `perigo`); proposta 6 → o
> contador é renderizado **dentro do contêiner `#badge-alertas`** da navegação (001); proposta 7
> → **SEM ESTOQUE é selo composto que mantém "⚠ REPOSIÇÃO NECESSÁRIA"**; proposta 9 → o helper
> **`eh_fragmento`** também exclui a restauração de histórico; proposta 10 → `origem=alertas` e
> `quantidade` são implementados **pela 003**; proposta 11 → reconciliada: **`linha.html`** e
> **`resumo.html`**. Propostas 1, 2, 3, 5 e 8 foram aceitas como escritas.

1. **Nomes e dono das anotações de `ProdutoQuerySet`** — registrar no contrato que
   `com_situacao()` anota `alerta` (002) e `deficit`/`cobertura_percentual` (004, fórmulas de
   [data-model.md](data-model.md), com cast para `bigint`), e que o booleano **não** se chama
   `em_alerta` porque `Produto.em_alerta` é propriedade (002) — anotar um nome igual a uma
   `@property` sem *setter* gera `AttributeError`. Proibir propriedades chamadas `deficit` ou
   `cobertura_percentual` no modelo.
2. **Evento após cadastro e edição** — a 002 já emite `estoque-alterado` no cadastro parcial
   (alinhado à proposta 10 da 003). Propor que a **edição** parcial do estoque mínimo também o
   emita (a situação muda quando o mínimo muda); fluxos comuns/*boosted* já re-renderizam o
   contador no `base.html`.
3. **Parâmetro opcional `quantidade`** em `movimentacoes:nova`
   (`?produto=<id>&tipo=ENTRADA&quantidade=<n>`) para pré-preencher a sugestão de reposição no
   "+ Entrada" do relatório. Sem ele, a 004 funciona (a sugestão fica visível na linha).
4. **Vocabulário de `toast.nivel`** — fixar `sucesso | info | alerta | ~~perigo~~ erro` (v1.1) (a 004 usa
   `alerta` para o aviso de reposição).
5. **Rota de exportação** — registrar na tabela de rotas que `alertas:relatorio` aceita
   `?formato=csv`.
6. **Pontos fixos no `base.html` (001)** — reservar no menu o item "Alertas" com o slot
   `{% contador_alertas %}` e uma região viva `#anuncio-alertas` (`role="status"`,
   `aria-live="polite"`, visualmente oculta), além do `#dialogo` já previsto.
7. **Selo de situação único** — o contrato cita só "REPOSIÇÃO NECESSÁRIA"; registrar a variação
   "SEM ESTOQUE" e que o selo de todo o sistema é `produtos/partials/situacao.html` (002),
   estendido pela 004.
8. **Ponto de extensão do toast da 003** — a 003 já centraliza o texto em
   `Movimentacao.mensagem_confirmacao`; registrar no contrato que a view e o comando `movimentar`
   o publicam via `alertas.regras.confirmacao_com_alerta(mov)` a partir da 004.
9. **Helper de fragmento** — padronizar na 001 um helper `eh_fragmento(request)` para todas as
   features (v1.1: `request.htmx and not request.htmx.boosted and not
   request.htmx.history_restore_request`).
10. **`origem=alertas` em `movimentacoes:nova`** — acrescentar ao contrato de rotas o valor
    `alertas` do parâmetro `origem` (sucesso sem OOB de produto), usado pelo "+ Entrada" do
    relatório e do painel.
11. **Divergência 002 × 003 nos nomes de parciais** — a 002 planeja `produtos/partials/linha.html`
    e `resumo.html`; a 003 referenciava nomes diferentes. Reconciliada na v1.1 e na auditoria de
    2026-10-20: valem `linha.html` e `resumo.html`.

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| 002 implementar `com_situacao()` com fórmulas diferentes | Proposta 1 + `apps/produtos/tests/test_queryset_situacao.py` fixa os limites; a tarefa da 004 acrescenta `deficit`/`cobertura_percentual` sem alterar `alerta` |
| Estouro de `integer` no PostgreSQL | R2 (cast para `bigint`) + teste com 2.147.483.647 rodando também no PostgreSQL |
| Nomes de templates da 002/003 mudarem até a implementação | A 004 só depende de `produtos/partials/situacao.html`, `sucesso_dialogo.html` e das funções citadas; a tarefa de integração confere os nomes nos `plan.md` vigentes |
| Polling em muitas abas | 1 `COUNT` por ciclo + 204 quando nada muda; intervalo configurável |
