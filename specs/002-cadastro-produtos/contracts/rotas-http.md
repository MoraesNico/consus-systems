# Contrato HTTP — rotas de `produtos` (002)

Rotas fixadas em `docs/arquitetura.md`; app `apps/produtos`, `app_name = "produtos"`, incluídas
em `config/urls.py` como `path("produtos/", include("apps.produtos.urls"))`. Todas as views
aceitam apenas `GET` e `POST` (`require_http_methods`); qualquer outro método → **405** (não há
exclusão — FR-026).

## Convenções comuns

**Variantes de requisição** (research R8):

| Variante | Cabeçalhos recebidos | Tratamento |
|----------|----------------------|------------|
| Comum | nenhum `HX-*` | página completa; `302` após POST válido |
| *Boosted* | `HX-Request: true`, `HX-Boosted: true` | igual à comum (o HTMX segue o `302` e troca o `<body>`) |
| Restauração de histórico | `HX-History-Restore-Request: true` | igual à comum |
| Parcial | `HX-Request: true`, sem `HX-Boosted`, com `HX-Target` reconhecido | somente o fragmento indicado abaixo |

- **Erro de validação**: sempre **422** (página completa ou fragmento, conforme a variante).
- **CSRF**: token em `hx-headers` no `<body>` (001) e campo oculto `csrfmiddlewaretoken` nos
  formulários (funciona sem scripts).
- **Notificação**: variante parcial → `HX-Trigger` `toast`; comum/boosted →
  `django.contrib.messages` (renderizado como toast pelo layout da 001).
- Eventos e IDs de fragmentos: ver [fragmentos-e-eventos.md](./fragmentos-e-eventos.md).

---

## `GET /produtos/` — `produtos:lista`

**Parâmetros de consulta** (todos opcionais; inválidos são ignorados ou ajustados):

| Parâmetro | Valores | Padrão | Regra |
|-----------|---------|--------|-------|
| `q` | texto | vazio | `ProdutoQuerySet.buscar(q)` — ver [servicos-e-consultas.md](./servicos-e-consultas.md) |
| `situacao` | `alerta` \| `ok` | todos | outro valor → todos |
| `ordem` | `id`, `nome`, `quantidade`, `minimo`, `situacao`, com `-` opcional | `-id` | fora da lista branca → padrão; desempate `-id` |
| `pagina` | inteiro ≥ 1 | 1 | `Paginator.get_page` (inválido → 1; acima do total → última) |

**Respostas**:

| Variante | Condição | Status | Template | Cabeçalhos |
|----------|----------|--------|----------|------------|
| Comum / boosted / restauração | — | 200 | `produtos/lista.html` | `Vary: HX-Request, HX-Target` |
| Parcial | `HX-Target: resultados` | 200 | `produtos/partials/resultados.html` (+ `#contagem-produtos` OOB) | `HX-Push-Url: <URL canônica>`, `Vary` |

- **URL canônica**: `/produtos/` + somente os parâmetros não vazios e diferentes do padrão, na
  ordem `q`, `situacao`, `ordem`, `pagina` (ex.: `/produtos/?q=caneta&situacao=alerta`).
- **Contexto**: `page_obj`, `produtos` (com `alerta` anotado), `q`, `situacao`, `ordem`,
  `total_geral` (contagem sem filtros — distingue os dois estados vazios), `destaque_id`.
- **Destaque**: a view consome (`session.pop`) `produtos_destaque`; a linha correspondente sai
  marcada só nessa resposta (FR-010).
- **Estados vazios** (FR-019): `total_geral == 0` → "Nenhum produto cadastrado" + ação
  "Cadastrar produto"; resultado vazio com filtros → "Nenhum produto encontrado" citando `q` +
  ação "Limpar busca" (link para `/produtos/`).
- **Consultas ao banco**: no máximo 4 (sessão, contagem filtrada, página e — só quando há
  filtro e o resultado é vazio — contagem total), independentemente do número de produtos;
  verificado com `django_assert_max_num_queries`.

## `GET /produtos/novo/` — `produtos:novo`

| Variante | Condição | Status | Template |
|----------|----------|--------|----------|
| Comum / boosted | — | 200 | `produtos/novo.html` |
| Parcial (diálogo) | `HX-Target: dialogo` | 200 | `produtos/partials/dialogo_novo.html` |

Formulário `ProdutoForm` vazio (campos numéricos **sem** valor inicial — clarificação
2026-10-20).

## `POST /produtos/novo/` — `produtos:novo`

**Corpo** (`application/x-www-form-urlencoded`): `nome`, `quantidade_inicial`,
`estoque_minimo`, `csrfmiddlewaretoken`. Chama
`cadastrar_produto(nome=..., quantidade_inicial=..., estoque_minimo=...)`; `ValidationError`
do serviço é anexada aos campos do formulário.

| Variante | Resultado | Status | Corpo | Cabeçalhos / efeitos |
|----------|-----------|--------|-------|----------------------|
| Comum / boosted | válido | **302** → `/produtos/` | — | `messages.success("Produto #0007 cadastrado")`; `session["produtos_destaque"] = 7` |
| Comum / boosted | inválido | **422** | `produtos/novo.html` com erros e valores preservados | — |
| Parcial (`HX-Target: dialogo`) | válido | **200** | `produtos/partials/resultados.html` na visão padrão (página 1, `-id`, `destaque_id=7`) + `produtos/partials/filtros.html` (campos limpos) e `produtos/partials/contagem.html`, ambos com `hx-swap-oob="true"` | `HX-Retarget: #resultados`; `HX-Reswap: outerHTML`; `HX-Push-Url: /produtos/`; `HX-Trigger: {"toast": {"nivel": "sucesso", "texto": "Produto #0007 cadastrado"}, "estoque-alterado": {}, "dialogo-fechar": {}}` |
| Parcial (`HX-Target: dialogo`) | inválido | **422** | `produtos/partials/dialogo_novo.html` com erros; primeiro campo inválido com `autofocus` | — |

## `GET /produtos/<int:produto_id>/` — `produtos:detalhe`

| Variante | Condição | Status | Template |
|----------|----------|--------|----------|
| Comum / boosted | produto existe | 200 | `produtos/detalhe.html` |
| Qualquer | produto inexistente (inclui ID acima do máximo de `BigAutoField`) | **404** | `produtos/nao_encontrado.html` |

- Exibe `produtos/partials/resumo.html` (`#produto-resumo`), ação "Editar" e a região vazia
  `#produto-movimentacoes` (sem controles — FR-022).
- `POST`/`DELETE` → **405** (não há exclusão).
- URL não numérica (ex.: `/produtos/abc/`) não casa com a rota → 404 genérico da 001.

## `GET /produtos/<int:produto_id>/editar/` — `produtos:editar`

| Variante | Condição | Status | Template |
|----------|----------|--------|----------|
| Comum / boosted | produto existe | 200 | `produtos/editar.html` (`ProdutoEdicaoForm` com `nome` e `estoque_minimo` atuais; quantidade atual somente leitura, com a nota "Muda apenas por movimentação") |
| Qualquer | produto inexistente | **404** | `produtos/nao_encontrado.html` |

## `POST /produtos/<int:produto_id>/editar/` — `produtos:editar`

**Corpo**: `nome`, `estoque_minimo`, `csrfmiddlewaretoken`. Campos extras (`quantidade_atual`,
`quantidade_inicial`, `id`) são **ignorados** (FR-025). Chama
`editar_produto(produto_id=..., nome=..., estoque_minimo=...)`.

| Variante | Resultado | Status | Corpo | Efeitos |
|----------|-----------|--------|-------|---------|
| Comum / boosted | válido | **302** → `/produtos/<id>/` | — | `messages.success("Produto #0007 atualizado")` |
| Comum / boosted | inválido | **422** | `produtos/editar.html` com erros | — |
| Qualquer | inexistente | **404** | `produtos/nao_encontrado.html` | — |

Na navegação *boosted* o `<body>` inteiro é re-renderizado, levando o contador de alertas da
004 já atualizado (FR-031), sem evento adicional.
