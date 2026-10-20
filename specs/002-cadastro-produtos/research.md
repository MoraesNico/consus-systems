# Research: Cadastro de Produtos (002)

**Feature**: [spec.md](./spec.md) · **Plano**: [plan.md](./plan.md) · **Data**: 2026-10-20

O Technical Context do plano não tem itens "NEEDS CLARIFICATION": stack, banco e testes estão
fixados pela constituição e por `docs/arquitetura.md`. Esta pesquisa registra as decisões de
desenho necessárias para cumprir a spec sem divergir do contrato, as armadilhas encontradas e as
propostas de ajuste ao contrato.

---

## R1. Restrições do modelo `Produto` no banco

- **Decision**: `id = BigAutoField(primary_key=True)` declarado explicitamente; `nome =
  CharField(max_length=120)`; `quantidade_atual` e `estoque_minimo` como
  `PositiveIntegerField`; `criado_em` (`auto_now_add`) e `atualizado_em` (`auto_now`). Em
  `Meta.constraints`:
  - `CheckConstraint(condition=Q(quantidade_atual__gte=0), name="produto_quantidade_atual_nao_negativa")`
  - `CheckConstraint(condition=Q(estoque_minimo__gte=0), name="produto_estoque_minimo_nao_negativo")`
  - `CheckConstraint(condition=~Q(nome=""), name="produto_nome_nao_vazio")`
  - `UniqueConstraint(Lower("nome"), name="produto_nome_unico_ci")`
- **Rationale**: a constituição (princípio I) exige `CheckConstraint` explícito como terceira
  camada; nomes estáveis permitem testes que verifiquem a restrição específica. Django 5.2 usa o
  argumento `condition=` (o antigo `check=` está depreciado desde 5.1). O índice funcional
  `Lower("nome")` existe em PostgreSQL 17 e SQLite e também atende a ordenação por nome.
- **Alternatives considered**: confiar só no `CHECK` implícito do `PositiveIntegerField`
  (rejeitado: nome não controlável e a constituição pede a restrição explícita); `unique=True`
  gravando o nome em minúsculas (rejeitado: perde a grafia digitada); coluna extra
  `nome_normalizado` (rejeitado: campo fora do contrato — ver R3).

## R2. Faixa numérica e parsing estrito de inteiros

- **Decision**: constante `QUANTIDADE_MAXIMA = 2_147_483_647` em `apps/produtos/models.py`
  (limite do `integer` do PostgreSQL). Campo de formulário próprio `InteiroNaoNegativoField`
  que aceita apenas `^[0-9]+$` (após remover espaços das extremidades) e aplica
  `MaxValueValidator(QUANTIDADE_MAXIMA)`; o serviço repete a validação de tipo e faixa. O widget
  é `<input type="text" inputmode="numeric" pattern="[0-9]*">` e o formulário usa `novalidate`.
- **Rationale**: o `forms.IntegerField` do Django remove sufixos decimais nulos antes do
  `int()` — `"2.0"` vira 2 e **`"1.000"` vira 1**, o que contraria FR-006 (separador de milhar e
  casas decimais devem ser recusados). No SQLite, valores acima do limite seriam gravados sem
  erro; no PostgreSQL, gerariam `DataError` (500). Com `type="number"`, navegadores enviam string
  vazia para entradas como "2,5", trocando a mensagem correta por "Informe a quantidade
  inicial."; com `type="text"` + `inputmode="numeric"` o teclado numérico continua no celular e o
  servidor recebe o texto original. `novalidate` garante que todas as mensagens venham do
  servidor, em pt-BR e idênticas nas variantes com e sem HTMX.
- **Alternatives considered**: `forms.IntegerField` padrão (rejeitado pelos casos acima);
  validação nativa do navegador (rejeitado: mensagens fora do controle e diferentes por
  navegador); teto de negócio menor (rejeitado na clarificação de 2026-10-20).

## R3. Normalização e unicidade do nome sem diferenciar maiúsculas/minúsculas

- **Decision**: `normalizar_nome(valor) = " ".join(valor.split())` (remove espaços das
  extremidades e colapsa espaços internos, inclusive tabulação e espaço não separável). O
  serviço verifica duplicidade com a **mesma expressão do índice**:
  `Produto.objects.annotate(nome_ci=Lower("nome")).filter(nome_ci=Lower(Value(nome)))`
  (excluindo o próprio produto na edição). A gravação ocorre dentro de
  `transaction.atomic()`; um `IntegrityError` de `produto_nome_unico_ci` (corrida entre dois
  cadastros) é convertido na mesma `ValidationError` de nome duplicado, consultando o produto
  existente para citar seu código.
- **Rationale**: usar `Lower()` na verificação e no índice dá semântica idêntica nas duas
  camadas, em qualquer banco (o `iexact` usa `UPPER()` no PostgreSQL, que difere de `LOWER()` em
  casos raros). O bloco atômico cria um *savepoint*, então o erro de integridade pode ser tratado
  sem invalidar a transação externa (inclusive em testes).
- **Limitação conhecida**: no SQLite, `lower()` e `LIKE` só tratam letras ASCII ("ÁGUA" ≠
  "água"); no PostgreSQL (produção, constituição) a comparação cobre Unicode. Testes com
  acentos maiúsculos/minúsculos rodam somente no PostgreSQL
  (`skipif(connection.vendor != "postgresql")`); os demais rodam nos dois bancos.
- **Alternatives considered**: coluna `nome_normalizado` com `casefold()` (rejeitado: campo
  fora do contrato e dado redundante — pode virar proposta se a paridade no SQLite se tornar
  necessária); *collation* não determinística do PostgreSQL (rejeitado: no PostgreSQL 17 não
  suporta `LIKE`, quebrando a busca, e não existe no SQLite); sobrescrever `lower()` no SQLite
  (rejeitado: complexidade sem ganho em produção).

## R4. Exibição do ID como `#0001`

- **Decision**: propriedade `Produto.codigo` → `f"#{self.pk:04d}"`; `__str__` →
  `"#0001 — Caneta Azul"`. IDs em URLs sempre via `{% url %}`; em atributos HTML, com
  `|unlocalize`.
- **Rationale**: um único ponto de formatação reutilizável por 003/004 e pelo shell; `:04d`
  não trunca IDs ≥ 10000 (`#12345`). Com `USE_THOUSAND_SEPARATOR` ativo, `{{ produto.pk }}`
  seria renderizado como "1.234", quebrando `id="produto-1.234"` e URLs montadas à mão.
- **Alternatives considered**: filtro de template (rejeitado: não serve a `__str__` nem a outras
  apps); coluna persistida com o código (rejeitado: redundante).

## R5. Algoritmo de busca `ProdutoQuerySet.buscar(q)`

- **Decision**:
  1. `termo = normalizar_nome(q or "")`; vazio → sem filtro.
  2. `#` + algarismos (`^#\s*([0-9]+)$`) → somente `pk = int(...)`.
  3. Só algarismos (`^[0-9]+$`) → `Q(pk=n) | Q(nome__icontains=termo)`.
  4. Qualquer outro termo → `Q(nome__icontains=termo)`.
  Número maior que o máximo de `BigAutoField` (9.223.372.036.854.775.807) não gera filtro por
  ID (no passo 2 resulta em `none()`; no passo 3 só busca no nome).
- **Rationale**: implementa a clarificação de 2026-10-20. `[0-9]` em vez de `\d`/`isdigit()`
  evita algarismos Unicode ("²", "٣"). O guarda de estouro evita `OverflowError` do driver
  SQLite. `icontains` já escapa `%` e `_`, tratando-os literalmente.
- **Alternatives considered**: busca textual completa / `pg_trgm` (rejeitado: YAGNI para 10 mil
  linhas, dependência de extensão); campos separados para ID e nome (rejeitado: a spec pede uma
  única caixa de busca).

## R6. Situação derivada (regra única para 002 e 004)

- **Decision**: em `ProdutoQuerySet`: `em_alerta()` → `filter(quantidade_atual__lte=F("estoque_minimo"))`;
  `sem_alerta()` → `filter(quantidade_atual__gt=F("estoque_minimo"))`; `com_situacao()` →
  `annotate(alerta=ExpressionWrapper(Q(quantidade_atual__lte=F("estoque_minimo")), output_field=BooleanField()))`.
  No modelo: propriedades `em_alerta` (bool, calculada em Python) e `situacao` (`"alerta"` |
  `"ok"`, mesmos valores do parâmetro `?situacao=`).
- **Rationale**: a regra "≤" (atividade, item 3) é definida uma única vez e reutilizada pela
  004 (varredura, relatório, contador). A anotação chama-se `alerta`, e não `em_alerta`, porque o
  Django atribui anotações como atributos da instância e colidiria com a propriedade somente
  leitura de mesmo nome (`AttributeError`).
- **Alternatives considered**: campo booleano persistido (rejeitado: o contrato define a situação
  como derivada; risco de ficar desatualizado); `cached_property` com o mesmo nome da anotação
  (rejeitado: valor obsoleto após uma movimentação na mesma instância).

## R7. Ordenação, filtro e paginação

- **Decision**: parâmetro `ordem` com lista branca `id`, `nome`, `quantidade`, `minimo`,
  `situacao`, cada um com prefixo opcional `-`; padrão `-id`. Mapeamento: `nome` →
  `Lower("nome")`; `quantidade` → `quantidade_atual`; `minimo` → `estoque_minimo`; `situacao`
  (crescente) → em alerta primeiro (`F("alerta").desc()`). Desempate sempre por `-id`. Parâmetro
  `situacao` ∈ {`alerta`, `ok`}; qualquer outro valor = todos. Paginação com `Paginator(qs, 25)`
  e `get_page(pagina)` (parâmetro `pagina`), que ajusta valores inválidos ou fora do intervalo.
- **Rationale**: lista branca impede ordenação por campos arbitrários vindos da URL; desempate
  determinístico evita itens repetidos/perdidos entre páginas; `get_page` cumpre o caso de borda
  "parâmetros inválidos não causam erro".
- **Alternatives considered**: rolagem infinita/cursor (rejeitado: a spec exige páginas
  endereçáveis por URL); `?page=` (rejeitado em favor do vocabulário em português do domínio —
  ver proposta P3).

## R8. Variantes de resposta (comum, *boosted*, HTMX parcial)

- **Decision**: com `hx-boost="true"` no `<body>` (contrato), toda navegação e envio comum chega
  com `HX-Request: true` **e** `HX-Boosted: true`. Regra das views:
  - **parcial** somente se `request.htmx` e não `request.htmx.boosted` e não
    `request.htmx.history_restore_request`, escolhendo o fragmento pelo alvo (`HX-Target`):
    `resultados` (lista) e `dialogo` (cadastro em diálogo);
  - **comum/boosted**: template completo e `302` após POST bem-sucedido (o HTMX segue o
    redirect e troca o `<body>`);
  - **erro de validação**: status **422** em todas as variantes (a 001 configura o HTMX para
    trocar 422).
  A view de lista declara `Vary: HX-Request, HX-Target` (`vary_on_headers`) para que o cache do
  navegador nunca sirva um fragmento no lugar da página completa (Voltar/Avançar).
- **Rationale**: uma URL por recurso (contrato de rotas) com variantes por cabeçalho mantém o
  aprimoramento progressivo (princípio II). Tratar *boosted* como navegação comum evita devolver
  fragmento para uma troca de `<body>`.
- **Alternatives considered**: URLs separadas para fragmentos (rejeitado: diverge do contrato de
  rotas); decidir só por `request.htmx` (rejeitado: quebra com `hx-boost` e com restauração de
  histórico).

## R9. Estado na URL da lista

- **Decision**: formulário GET `#filtros-produtos` (`role="search"`) com `q` e `situacao`; a
  ordem corrente fica em `<input type="hidden" id="ordem-atual" name="ordem"
  form="filtros-produtos">` dentro de `#resultados` (atualizada a cada troca do fragmento e
  enviada também sem scripts, pelo atributo `form`). O campo `q` usa `hx-get` para
  `produtos:lista`, `hx-trigger="input changed delay:300ms, search"`, `hx-target="#resultados"`,
  `hx-include="#filtros-produtos, #ordem-atual"`, `hx-sync="this:replace"` (descarta respostas
  antigas), `hx-indicator="#resultados"` (indicação de atualização) e `hx-push-url="true"`; o
  filtro de situação dispara em `change`. `#contagem-produtos` (`role="status"`) anuncia o
  número de resultados. A resposta parcial envia `HX-Push-Url` com a **URL canônica** (sem parâmetros vazios
  ou padrão), montada pela view. Links de ordenação e paginação usam `{% querystring %}` (Django
  5.1+) e também funcionam sem HTMX.
- **Rationale**: cumpre FR-014/FR-018 e a convenção HTMX do contrato; URL canônica evita
  `?q=&situacao=&ordem=` no histórico; sem scripts, o formulário GET produz a mesma URL.
- **Alternatives considered**: estado só em memória/JS (rejeitado: viola FR-018 e o princípio
  II); `hx-push-url="true"` sem canonicalização (rejeitado: URLs poluídas).

## R10. Fluxo pós-cadastro e diálogo

- **Decision**:
  - **Página própria (comum/boosted)**: `messages.success("Produto #0007 cadastrado")` +
    `request.session["produtos_destaque"] = produto.pk` → `302` para `produtos:lista`; a lista
    consome (`pop`) a chave e marca a linha somente nessa exibição.
  - **Diálogo (HTMX parcial, alvo `dialogo`)**: `200` com o fragmento `resultados` na visão
    padrão (página 1, `-id`, linha destacada) + `filtros` fora de banda (`hx-swap-oob`) para
    limpar busca/filtro; cabeçalhos `HX-Retarget: #resultados`, `HX-Reswap: outerHTML`,
    `HX-Push-Url: /produtos/` e `HX-Trigger` com `toast`, `estoque-alterado` e
    `dialogo-fechar`.
  - Erro no diálogo: `422` com o diálogo re-renderizado em `#dialogo`; o primeiro campo com erro
    recebe `autofocus` (o HTMX aplica o foco após a troca, sem JS próprio).
  - "Cancelar" usa `<button formmethod="dialog" formnovalidate>` e Esc fecha o `<dialog>`
    nativamente.
- **Rationale**: uma única resposta atualiza lista, filtros, URL, notificação e contador
  (princípio II), sem segundo pedido; o fluxo sem JS chega ao mesmo estado via redirect + sessão
  (FR-011). `estoque-alterado` é emitido porque um produto pode nascer em alerta (ex.: 0 ≤ 0).
- **Alternatives considered**: `204` + evento para a lista se recarregar (rejeitado: dois
  pedidos e o destaque precisaria ser propagado); `HX-Redirect` (rejeitado: recarrega a página
  inteira); `?novo=<id>` na URL (rejeitado: o destaque reapareceria ao recarregar).

## R11. Edição sem tocar no saldo

- **Decision**: `editar_produto(*, produto_id, nome, estoque_minimo) -> Produto` em
  `transaction.atomic()`, com `select_for_update()` no produto e
  `save(update_fields=["nome", "estoque_minimo", "atualizado_em"])`. O formulário de edição só
  declara `nome` e `estoque_minimo`; qualquer `quantidade_atual` enviada é ignorada por
  construção. A edição é feita na página própria (comum/boosted): sucesso → `302` para o detalhe
  com `messages.success("Produto #0007 atualizado")`.
- **Rationale**: um `save()` sem `update_fields` regravaria a `quantidade_atual` lida antes de
  uma movimentação concorrente da 003, perdendo-a — violação direta do princípio I. O bloqueio de
  linha alinha a edição ao protocolo de concorrência da 003. Na navegação *boosted*, o `<body>`
  inteiro é re-renderizado pelo servidor, então o contador de alertas da 004 já chega atualizado
  (FR-031) sem evento extra.
- **Alternatives considered**: `ModelForm` com `fields="__all__"` (rejeitado: exporia a
  quantidade); edição em diálogo (rejeitado: não exigido; YAGNI).

## R12. Detalhe e região reservada para a 003

- **Decision**: `produtos/detalhe.html` inclui `produtos/partials/resumo.html`
  (`#produto-resumo`: código, nome, quantidade, mínimo, situação, datas) e uma
  `<section id="produto-movimentacoes" aria-label="Movimentações">` vazia. A 003 inclui ali seu
  fragmento e atualiza `#produto-resumo` e `#produto-<id>` por `hx-swap-oob`, renderizando os
  partials desta feature. Produto inexistente → `produtos/nao_encontrado.html` com status 404;
  ID acima do máximo de `BigAutoField` também resulta em 404 (sem `OverflowError`). URL não
  numérica não casa com `<int:produto_id>` e cai no 404 genérico da 001.
- **Rationale**: FR-022 proíbe controles sem função; IDs e partials estáveis formam o contrato
  de integração com a 003 sem que ela precise reescrever os templates desta feature.
- **Alternatives considered**: sobrescrever templates pela ordem de `INSTALLED_APPS` (rejeitado:
  acoplamento implícito); placeholder com texto "em breve" (rejeitado: ruído na interface).

## R13. Atalhos de teclado

- **Decision**: marcação declarativa `data-atalho="/"` (no campo de busca: foca) e
  `data-atalho="n"` (no link "Novo produto": aciona), com dica `<kbd>` visível. Um manipulador
  genérico de ~12 linhas em `static/js/consus.js` ignora o evento quando há modificador
  (Ctrl/Meta/Alt), quando o alvo é editável (`input`, `textarea`, `select`,
  `[contenteditable]`) ou quando há `<dialog open>`, e chama `preventDefault()` para que "/" não
  seja digitado.
- **Rationale**: aprimoramento progressivo dentro do orçamento de < 100 linhas de JS (princípio
  II); o link "Novo produto" continua funcionando sem scripts.
- **Alternatives considered**: `hx-trigger="keyup[key=='n'] from:body"` (rejeitado: não resolve
  o foco da busca e espalha expressões JS pelos templates); script inline por página
  (rejeitado: organização e CSP).

## R14. Notificações, números e datas

- **Decision**: notificações por `HX-Trigger` `toast` `{"nivel": "sucesso", "texto": ...}` em
  respostas parciais e por `django.contrib.messages` nas comuns/boosted (renderizadas como
  toast com `aria-live` pelo layout da 001). Quantidades com `|intcomma`
  (`django.contrib.humanize`, embutido no Django) → "1.000" em pt-BR; datas com
  `|date:"d/m/Y H:i"` no fuso configurado pela 001.
- **Rationale**: mesmo texto nas duas variantes; nenhuma dependência nova (princípio V).
- **Alternatives considered**: filtro próprio de milhar (rejeitado: reinventa o humanize);
  depender só de `USE_THOUSAND_SEPARATOR` global (rejeitado: afeta IDs em atributos — R4).

## R15. Testes e desempenho

- **Decision**: pytest-django em `apps/produtos/tests/`, um arquivo por camada
  (`test_models.py`, `test_services.py`, `test_selectors.py`, `test_forms.py`,
  `test_views_*.py`, `test_atalhos.py`). Nome ou docstring de cada teste cita o FR
  (`test_fr005_...`). Fixture `produto_factory` em `conftest.py` cria produtos **via
  `cadastrar_produto`** (sem factory_boy). Variantes HTMX simuladas com
  `client.get(url, headers={"HX-Request": "true", "HX-Target": "resultados"})` e
  `{"HX-Request": "true", "HX-Boosted": "true"}`. A lista é protegida contra N+1 com
  `django_assert_max_num_queries`. Os testes de 002 verificam só a pós-condição observável de
  `cadastrar_produto` (quantidade atual = inicial), para continuarem válidos quando a 003 a
  estender (FR-030). A suíte roda em SQLite (rápida) e PostgreSQL (Docker).
- **Desempenho**: para 10 mil linhas, `COUNT` + `SELECT … LIMIT 25` são da ordem de
  milissegundos; ordenação por `-id` e por `Lower(nome)` usa índices existentes (PK e
  `produto_nome_unico_ci`); `ILIKE '%termo%'` faz varredura sequencial de 10 mil linhas, bem
  abaixo de 1 s (SC-003). Nenhum índice extra (YAGNI); validação no quickstart com 10 mil
  produtos.
- **Alternatives considered**: factory_boy (rejeitado: dependência sem requisito — princípio V);
  testes de navegador (Playwright) para atalhos (rejeitado: exigiria Node/browsers; atalhos são
  validados por marcação + cenário manual do quickstart).

## R16. Sem cadastro no admin do Django

- **Decision**: `Produto` **não** é registrado no admin nesta feature.
- **Rationale**: o admin permitiria criar produtos sem `cadastrar_produto` (sem saldo inicial no
  histórico, quando a 003 existir), editar a quantidade e excluir — tudo vedado pelo princípio I
  e por FR-025/FR-026.
- **Alternatives considered**: admin somente leitura (rejeitado agora por YAGNI; pode ser
  adicionado depois com `has_add/change/delete_permission = False`).

---

## Propostas de ajuste ao contrato

Nenhuma proposta altera nomes já fixados em `docs/arquitetura.md`; todas acrescentam detalhes
que as features paralelas precisam combinar. **`docs/arquitetura.md` não foi editado.**

| # | Proposta | Afeta |
|---|----------|-------|
| P1 | Fixar `Produto.codigo` (`#0001`) como forma canônica de exibir o ID e `str(produto)` = `"#0001 — Nome"`. | 003, 004 |
| P2 | Fixar a API de situação: `ProdutoQuerySet.em_alerta()`, `sem_alerta()`, `com_situacao()` (anota `alerta: bool`); propriedades `Produto.em_alerta` e `Produto.situacao` (`"alerta"`/`"ok"`). A 004 consome, não redefine, a regra. | 004 |
| P3 | Padronizar parâmetros de listas: `ordem` (prefixo `-` = decrescente) e `pagina`, além de `q` e `situacao`. | 003 (`movimentacoes:lista`), 004 |
| P4 | Ampliar `estoque-alterado` para "após qualquer operação que altere saldo **ou situação**" (cadastro, movimentação, edição do estoque mínimo em resposta parcial). | 003, 004 |
| P5 | Padronizar o evento `dialogo-fechar` (via `HX-Trigger`, tratado pela 001) e o vocabulário de `toast.nivel`: `sucesso` \| `info` \| `alerta` \| `erro`. | 001, 003 |
| P6 | Incluir no contrato o manipulador genérico `data-atalho="<tecla>"` em `static/js/consus.js` (001), para que 002/003/004 declarem atalhos sem JS próprio. | 001 |
| P7 | Acrescentar à linha `nome` do modelo: "espaços internos consecutivos colapsados" (clarificação de 2026-10-20). | 004 (dados de demonstração) |
| P8 | Registrar `produtos.services.editar_produto(*, produto_id, nome, estoque_minimo) -> Produto` e `produtos.models.QUANTIDADE_MAXIMA = 2_147_483_647`; a 003 deve recusar entradas cujo saldo resultante ultrapasse esse limite. | 003 |
| P9 | Fixar IDs/partials de integração: `#resultados`, `#produto-<id>` (`produtos/partials/linha.html`), `#produto-resumo` (`produtos/partials/resumo.html`), `#produto-movimentacoes` (região da 003). | 003, 004 |
