# Research: Controle de Movimentação — Entradas e Saídas

**Feature**: `003-movimentacao-estoque` | **Date**: 2026-10-20 | **Plan**: [plan.md](plan.md)

Todas as incógnitas do *Technical Context* foram resolvidas; não há `NEEDS CLARIFICATION`.
As decisões de produto vieram da sessão de esclarecimentos da [spec](spec.md#clarifications).

---

## R1. Estratégia de escrita do saldo: bloqueio pessimista de linha

- **Decision**: `registrar_movimentacao` executa tudo em `transaction.atomic()`; a primeira
  instrução é `Produto.objects.select_for_update().get(pk=produto_id)`. Com a linha bloqueada, lê o
  saldo, valida, grava o novo saldo em `Produto` (`save(update_fields=["quantidade_atual",
  "atualizado_em"])`) e cria a `Movimentacao` com os snapshots `saldo_anterior`/`saldo_posterior`.
- **Rationale**: é a forma exigida pela constituição (princípio I), dá snapshots exatos do saldo
  para o livro-razão e serializa as escritas por produto (não bloqueia outros produtos).
- **Alternatives considered**:
  - `UPDATE ... SET quantidade_atual = quantidade_atual - q WHERE quantidade_atual >= q`
    (atualização condicional atômica): sem bloqueio explícito, mas exige `RETURNING` para obter o
    snapshot e espalha a regra em SQL; rejeitada por clareza e por contrariar o contrato.
  - Controle otimista (coluna `versao` + retry): adiciona campo ao `Produto` (contrato da 002) e
    laço de repetição; rejeitada (YAGNI, poucos operadores).
  - `SERIALIZABLE` no banco inteiro: custo global e erros de serialização a tratar; rejeitada.

## R2. Comportamento sob concorrência: aguardar, não falhar rápido

- **Decision**: o bloqueio usa `select_for_update()` **sem** `nowait`/`skip_locked`: a segunda
  transação aguarda a primeira terminar e é avaliada com o saldo atualizado (esclarecimento Q5).
  A recusa é sempre `EstoqueInsuficienteError` com a mensagem padrão, nunca "tente novamente".
- **Rationale**: transações curtas (milissegundos) tornam a espera imperceptível; a mensagem
  continua útil para o operador (mostra o disponível real).
- **Alternatives considered**: `nowait=True` (erro imediato `DatabaseError` → mensagem genérica,
  rejeitada pelo esclarecimento); fila/assíncrono (desproporcional).
- **Nota SQLite**: `select_for_update()` é ignorado no SQLite; lá as escritas já são serializadas
  pelo próprio banco. O critério SC-003 é verificado no PostgreSQL (R13).

## R3. Três camadas da regra "saldo nunca negativo"

- **Decision**:
  1. **Formulário** — `MovimentacaoForm.clean()` compara a quantidade com o saldo do produto
     carregado e devolve a mesma mensagem do serviço (retorno rápido, sem bloqueio).
  2. **Serviço** — revalida sob bloqueio (R1); é a fonte da verdade.
  3. **Banco** — `CheckConstraint(quantidade_atual >= 0)` do `Produto` (feature 002) +
     restrições do `Movimentacao` (ver [data-model.md](data-model.md#restrições-de-banco)):
     `PositiveIntegerField` (Django cria `CHECK >= 0` em PostgreSQL e SQLite) para quantidade e
     saldos; `mov_quantidade_positiva_exceto_inicial`; `mov_saldo_posterior_consistente`
     (posterior = anterior ± quantidade conforme o tipo); `mov_inicial_parte_de_zero`;
     `mov_tipo_valido`; `mov_inicial_unica_por_produto` (único parcial).
- **Rationale**: atende ao princípio I e ao FR-009; uma gravação que contorne interface e serviço
  ainda é barrada pelo banco (`IntegrityError`).
- **Detalhe Django 5.2**: usar `CheckConstraint(condition=Q(...), name=...)` — o argumento
  `check=` está obsoleto desde o Django 5.1.
- **Alternatives considered**: só serviço (falha em gravação direta); gatilho (trigger) no banco
  recalculando saldo (lógica duplicada fora do Python, paridade difícil com SQLite).

## R4. Imutabilidade do livro-razão

- **Decision**: guardas no modelo — `Movimentacao.save()` lança `MovimentacaoImutavelError` se o
  registro já existe (`not self._state.adding`); `Movimentacao.delete()` lança a mesma exceção;
  `MovimentacaoQuerySet.update()` e `.delete()` também lançam. FK `produto` com
  `on_delete=PROTECT`. Nenhuma view, rota ou formulário de edição/exclusão; o modelo **não** é
  registrado no admin.
- **Rationale**: FR-021/SC-006 verificáveis por testes unitários, com custo mínimo e paridade
  PostgreSQL/SQLite.
- **Alternatives considered**: gatilhos `BEFORE UPDATE/DELETE` no PostgreSQL (não roda no SQLite,
  dificulta a suíte rápida); admin somente leitura (sem requisito que o justifique — YAGNI).

## R5. Saldo inicial (`INICIAL`) no cadastro e carga retroativa

- **Decision**:
  - `produtos.services.cadastrar_produto` passa a criar o `Produto` com `quantidade_atual=0` e, no
    mesmo `transaction.atomic()`, chamar
    `registrar_movimentacao(produto_id=produto.pk, tipo=TipoMovimentacao.INICIAL,
    quantidade=quantidade_inicial)`; devolve o produto recarregado (`refresh_from_db()`).
  - `INICIAL` é sempre gerado, inclusive com quantidade 0 (esclarecimento Q1); o serviço só o
    aceita se o produto não tiver nenhuma movimentação e estiver com saldo 0.
  - Migração de dados `0002_saldo_inicial_retroativo` (RunPython, com `reverse_code` no-op): para
    cada produto sem movimentações, cria `INICIAL` com `quantidade = quantidade_atual`,
    `saldo_anterior = 0`, `saldo_posterior = quantidade_atual` e `criado_em = produto.criado_em`,
    sem alterar o saldo.
- **Rationale**: mantém **um único caminho de escrita** de saldo (contrato), garante o invariante
  "saldo = Σ movimentações" (FR-029) para todo produto, inclusive os criados antes da 003
  (FR-030), e torna o histórico uniforme (toda linha do tempo começa em `INICIAL`).
- **Alternatives considered**: criar o produto já com o saldo e gravar a `Movimentacao` à parte
  (dois caminhos de escrita); gerar `INICIAL` só quando > 0 (histórico irregular, invariante com
  exceção) — rejeitadas.

## R6. Validação da quantidade e limites

- **Decision**: campo `QuantidadeField` (subclasse de `forms.IntegerField`) que aceita **apenas**
  `^[+-]?\d+$` (após aparar espaços) antes de converter; qualquer outro texto ("2,5", "2.5",
  "1.000", "abc") recebe "Informe um número inteiro, sem casas decimais nem separadores.". Depois,
  validadores de mínimo (1 → "Informe uma quantidade maior que zero.") e máximo
  (`QUANTIDADE_MAXIMA = 1_000_000` → "Informe no máximo 1.000.000."). Teto de saldo
  `SALDO_MAXIMO = 2_147_483_647` (limite de `PositiveIntegerField` no PostgreSQL) verificado no
  formulário e no serviço (`SaldoMaximoExcedidoError`). `INICIAL` aceita `0..SALDO_MAXIMO`.
  O `<input>` usa `type="number" inputmode="numeric" min="1" max="1000000" step="1"`.
- **Rationale**: o `IntegerField` do Django remove sufixos `.0*` (`re_decimal`), o que faria
  "1.000" (mil, em pt-BR) virar **1** silenciosamente — erro grave num controle de estoque. Os
  limites evitam estouro de inteiro (erro 500) e atendem ao esclarecimento Q4.
- **Alternatives considered**: `localize=True` (aceitaria "1.000" como mil, mas também "1.5"
  ambíguo); `DecimalField` (permite frações, contraria o princípio I).

## R7. Uma rota, várias variantes de resposta

- **Decision**: manter apenas as rotas do contrato (`movimentacoes:lista`, `movimentacoes:nova`)
  e despachar a variante na view:
  - parcial somente quando `request.htmx and not request.htmx.boosted`;
  - `GET nova`: `HX-Target: dialogo` → conteúdo do diálogo; `HX-Target: previa-saldo` → prévia;
    demais → página completa;
  - `POST nova`: campo oculto `origem` (`pagina` | `lista` | `detalhe`) define a resposta de
    sucesso (formulário limpo vs. OOB + fechar diálogo);
  - `GET lista`: `HX-Target: resultados` → só a tabela; demais → página completa.
- **Rationale**: não cria rotas fora do contrato; navegação com `hx-boost` continua recebendo a
  página completa.
- **Alternatives considered**: rotas extras `/movimentacoes/previa/` e `/movimentacoes/dialogo/`
  (mudança de contrato desnecessária).

## R8. Prévia do saldo renderizada no servidor

- **Decision**: `<output id="previa-saldo" aria-live="polite">` com `hx-get` para
  `movimentacoes:nova`, `hx-include="closest form"`, `hx-trigger="input changed delay:300ms from:closest form, change from:closest form"`
  e `hx-target="this"`; a view devolve `partials/previa_saldo.html` com "Saldo atual: X" e
  "Saldo após: Y" ou o aviso "Saldo insuficiente: disponível X, solicitado Y" (mesmo texto do
  serviço). Sem HTMX, o formulário mostra apenas o saldo atual do produto pré-selecionado.
- **Rationale**: zero JavaScript novo (princípio II e orçamento da 001), regra de cálculo num só
  lugar (Python), mensagem idêntica à da recusa.
- **Alternatives considered**: cálculo no cliente com `data-saldo` em `static/js/consus.js`
  (duplica regra, consome orçamento de JS da 001 e arquivo de outra feature).

## R9. Atualização pós-sucesso: OOB + eventos

- **Decision**:
  - **Diálogo** (`origem=lista|detalhe`): resposta 200 com `HX-Reswap: none` (o formulário não é
    trocado; os elementos OOB continuam sendo processados pelo HTMX 2) e corpo
    `partials/sucesso_dialogo.html` contendo:
    - `origem=lista`: `<template><tr id="produto-<id>" hx-swap-oob="true">…</tr></template>`
      renderizado com o partial de linha da 002 (o `<template>` é necessário para o parser aceitar
      `<tr>` solto);
    - `origem=detalhe`: `#produto-<id>-resumo` (partial da 002) e `#produto-<id>-historico`
      (partial da 003), ambos com `hx-swap-oob="true"`.
  - Cabeçalho `HX-Trigger` (via `django_htmx.http.trigger_client_event`) com
    `estoque-alterado` (`{produto_id, saldo_anterior, saldo_posterior}`), `toast`
    (`{nivel: "sucesso", texto: <mensagem de confirmação>}`) e, no diálogo, `fechar-dialogo`.
  - **Página** (`origem=pagina`) com HTMX: 200 com o formulário limpo (mesmo produto e tipo,
    saldo atualizado) + `HX-Trigger` `estoque-alterado` e `toast`.
  - O produto da linha é relido com `Produto.objects.com_situacao()` para que a situação de
    alerta (004) também seja atualizada.
- **Rationale**: uma única resposta atualiza tudo o que depende do saldo (princípio II); o
  contador e o painel da 004 reagem ao evento sem acoplamento direto.
- **Alternatives considered**: `HX-Refresh: true` (recarrega a página, viola SC-005/UX);
  incluir sempre todos os OOB (erros `htmx:oobErrorNoTarget` quando o alvo não existe na página).

## R10. Variante sem HTMX: PRG e status 422

- **Decision**: POST comum válido → `messages.success(texto)` + redirect (302) para
  `/movimentacoes/nova/?produto=<id>&tipo=<tipo>` (esclarecimento Q2). POST inválido (comum ou
  HTMX) → status **422** com a página completa (comum) ou só `partials/form_movimentacao.html`
  (HTMX, `hx-swap="outerHTML"` no próprio formulário). Ações rápidas são `<a href>` para a página
  com `hx-get` para o diálogo (aprimoramento progressivo).
- **Rationale**: princípio II ("toda ação MUST funcionar sem HTMX"), convenções do contrato
  (422 para erro de validação), mesmo resultado nas duas variantes.
- **Alternatives considered**: redirecionar para o detalhe do produto (rejeitado no
  esclarecimento Q2: quebra o fluxo de registros em sequência).

## R11. Histórico: filtros, período, ordenação e paginação

- **Decision**:
  - `FiltroMovimentacoesForm` (GET): `produto` (select "#0001 — Nome"), `tipo` (Todos, Saldo
    inicial, Entrada, Saída/Venda), `de` e `ate` (`type="date"`; aceita `aaaa-mm-dd` e
    `dd/mm/aaaa`). Campos inválidos e `de > ate` geram aviso e **não** filtram; os válidos
    continuam aplicados.
  - Período convertido em intervalo semiaberto no fuso atual:
    `criado_em >= início(de)` e `criado_em < início(ate + 1 dia)` (evita `__date`, que impede o uso
    do índice).
  - Ordenação `-criado_em, -id` (desempate estável). `select_related("produto")`.
  - `Paginator(…, 25).get_page(page)` (número inválido → primeira; acima do total → última);
    links de paginação preservam a querystring dos filtros.
  - Índices: `criado_em` (contrato) e `(produto, -criado_em)` para o histórico do produto.
  - Filtros com `hx-get` + `hx-target="#resultados"` + `hx-push-url="true"` +
    `hx-trigger="change, submit"`; avisos de filtro renderizados no topo de `#resultados`
    (`role="alert"`), pois o formulário de filtros não é trocado.
- **Rationale**: FR-022…FR-026 e SC-007; endereço compartilhável; desempenho com 100k linhas.
- **Alternatives considered**: busca textual de produto com autocomplete (YAGNI para ~1.000
  produtos); paginação por cursor (desnecessária nessa escala).

## R12. Integração com as páginas de produto por *inclusion tags*

- **Decision**: `apps/movimentacoes/templatetags/movimentacoes_tags.py` expõe
  `{% acoes_rapidas produto origem %}` (renderiza os dois botões-link) e
  `{% historico_produto produto %}` (consulta `historico_do_produto(produto.pk, limite=10)` e
  renderiza a seção). Os templates da 002 apenas carregam a biblioteca e chamam as tags.
- **Rationale**: nenhuma alteração nas views da 002; o conhecimento sobre movimentações fica no app
  dono; o mesmo partial é usado na página e na resposta OOB.
- **Alternatives considered**: acrescentar `historico` ao contexto da view de detalhe da 002
  (acopla a 002 ao app de movimentações e duplica a consulta na resposta OOB).

## R13. Teste de concorrência

- **Decision**: `apps/movimentacoes/tests/test_concorrencia.py` com
  `pytestmark = [pytest.mark.postgres, pytest.mark.django_db(transaction=True),
  pytest.mark.skipif(connection.vendor != "postgresql", reason="requer PostgreSQL")]`. Cenários:
  1. saldo 10, 20 *threads* sincronizadas por `threading.Barrier`, cada uma com saída de 1 →
     exatamente 10 sucessos, 10 `EstoqueInsuficienteError`, saldo final 0, 10 saídas gravadas,
     `auditar_saldos() == []`; parametrizado em 20 rodadas (SC-003);
  2. saldo 10, duas saídas simultâneas de 6 → uma aceita, outra recusada com
     "disponível 4, solicitado 6";
  3. espera comprovada: a *thread* A bloqueia o produto e segura a transação; a B inicia uma saída,
     só conclui depois do *commit* de A e registra `saldo_anterior` igual ao `saldo_posterior` de A.
  Cada *thread* fecha sua conexão (`connection.close()`) ao terminar. Complemento executável no
  SQLite: teste determinístico de "formulário com saldo desatualizado" (o serviço usa o saldo
  relido, não o do formulário).
  O marcador `postgres` é registrado em `pyproject.toml` (`--strict-markers`).
- **Rationale**: prova FR-008/SC-003 no banco de produção; o *skip* mantém a suíte rápida verde no
  SQLite, como exige a constituição.
- **Alternatives considered**: simular concorrência com *mocks* (não prova bloqueio real);
  `multiprocessing` (mais pesado, mesmo resultado).

## R14. Comando de terminal `movimentar`

- **Decision**: `BaseCommand` com argumentos posicionais `produto_id` (int), `tipo`
  (`entrada|saida`, sem diferenciar maiúsculas) e `quantidade` (validada com a mesma regra do
  `QuantidadeField`), opção `--obs`. Chama `registrar_movimentacao`; sucesso → imprime a mensagem
  de confirmação (`self.style.SUCCESS`); `MovimentacaoError` → `CommandError(mensagem)` (código de
  saída 1, nada gravado).
- **Rationale**: FR-031, paridade com o formato de console da atividade, sem lógica duplicada.
- **Alternatives considered**: script avulso fora do Django (duplicaria configuração e regras).

## R15. Formatação pt-BR e apresentação

- **Decision**: números nas mensagens de domínio formatados por um auxiliar
  `formatar_numero(n)` em `services.py` (`f"{n:,}".replace(",", ".")`) — usado nas exceções e na
  mensagem de confirmação; nos templates, o filtro de número da 001 (ou `intcomma` com
  `pt-br`). Sinal com `+` e `−` (U+2212). Datas com `|date:"d/m/Y H:i"` no fuso
  `America/Sao_Paulo`. Código do produto via `produto.codigo` ("#0001"). Selo do tipo:
  `INICIAL` → neutro, `ENTRADA` → sucesso, `SAIDA` → neutro forte (inverso), sempre com texto.
  Botões de ação rápida com `aria-label="Registrar entrada de #0001 Parafuso"`.
- **Rationale**: princípio IV (idioma, números tabulares, cor nunca sozinha); a cor de perigo fica
  reservada a erros e a cor de alerta à reposição (004).

## R16. Dependências

- **Decision**: nenhuma dependência nova. Usa `django-htmx` (já no stack) para
  `request.htmx`, `trigger_client_event` e `reswap`.
- **Rationale**: princípio V (YAGNI).

---

## Propostas de ajuste ao contrato

Registradas aqui (sem editar `docs/arquitetura.md`), para o coordenador consolidar:

1. **Alvos OOB e partials da 002** — fixar: linha da lista de produtos como
   `<tr id="produto-<id>">` renderizada por `apps/produtos/templates/produtos/partials/linha_produto.html`
   (contexto `produto` anotado por `com_situacao()`), e o bloco de saldo/mínimo/situação do
   detalhe como `<section id="produto-<id>-resumo">` em
   `apps/produtos/templates/produtos/partials/resumo_produto.html`; ambos aceitam a variável de
   contexto `oob` para emitir `hx-swap-oob="true"` na raiz. A 003 acrescenta
   `#produto-<id>-historico`.
2. **Fechamento do diálogo** — novo evento `fechar-dialogo` (via `HX-Trigger`) tratado pelo
   `static/js/consus.js` da 001 (`dialog.close()`), e confirmação de que o alvo de conteúdo é o
   elemento `id="dialogo"` (enviado pelo HTMX no cabeçalho `HX-Target: dialogo`).
3. **Exibição do ID** — fixar a propriedade `Produto.codigo` → `"#0001"` como forma canônica de
   exibir o ID (usada em mensagens de serviço, comandos e templates).
4. **Hierarquia de exceções** — `movimentacoes.services` expõe `MovimentacaoError` (base),
   `MovimentacaoInvalidaError`, `EstoqueInsuficienteError` (atributos `disponivel`,
   `solicitado`) e `SaldoMaximoExcedidoError`; `movimentacoes.models` expõe
   `MovimentacaoImutavelError`.
5. **Carga útil do evento** — `estoque-alterado` leva `{produto_id, saldo_anterior,
   saldo_posterior}` (opcional para quem escuta com `from:body`).
6. **Parâmetros de rota** — `/movimentacoes/?produto=<id>&tipo=INICIAL|ENTRADA|SAIDA&de=aaaa-mm-dd&ate=aaaa-mm-dd&page=<n>`
   e `/movimentacoes/nova/?produto=<id>&tipo=ENTRADA|SAIDA` (+ `origem=lista|detalhe` apenas no
   `hx-get` do diálogo); paginação com `page` em todas as listas.
7. **Limites numéricos** — quantidade por Entrada/Saída de 1 a 1.000.000; saldo máximo
   2.147.483.647; a validação da Quantidade Inicial na 002 deve aceitar `0..2.147.483.647`.
8. **Assinatura do cadastro** — fixar `produtos.services.cadastrar_produto(*, nome,
   quantidade_inicial, estoque_minimo) -> Produto` e atualizar a frase "Antes da feature 003
   existir, o serviço de cadastro apenas define `quantidade_atual`" para registrar que, com a 003,
   o produto nasce com 0 e o saldo vem do `INICIAL`. Os dados de demonstração da 004 devem usar
   `cadastrar_produto`/`registrar_movimentacao`, nunca gravar `quantidade_atual` diretamente.
9. **Marcador de teste** — registrar o marcador `postgres` em `pyproject.toml` para testes que
   exigem PostgreSQL (pulados automaticamente no SQLite).
