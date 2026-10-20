# Contrato HTTP: rotas `alertas`

`apps/alertas/urls.py` — `app_name = "alertas"`, incluído em `config/urls.py` como
`path("alertas/", include("apps.alertas.urls"))`.

Convenções comuns às duas rotas:

- Somente `GET` (`@require_GET`); outros métodos → **405**.
- `@never_cache` (`Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private`) e
  `Vary: HX-Request`.
- "Fragmento" = `request.htmx and not request.htmx.boosted`; qualquer outra requisição
  (sem HTMX ou navegação `hx-boost`) recebe a página completa.
- Nenhuma rota escreve no banco; não há CSRF envolvido.

---

## `GET /alertas/` — `alertas:relatorio`

Relatório de Reposição; cada requisição **executa uma varredura** (`selectors.varrer()`).

### Parâmetros

| Parâmetro | Valores | Padrão | Inválido |
|-----------|---------|--------|----------|
| `formato` | `html`, `csv` | `html` | **400** `text/plain`: "Formato não suportado. Use html ou csv." |

### Respostas

| Caso | Status | Content-Type | Template / corpo | Cabeçalhos extras |
|------|-------:|--------------|------------------|-------------------|
| Página completa (sem HTMX ou `HX-Boosted: true`) | 200 | `text/html; charset=utf-8` | `alertas/relatorio.html` (estende `base.html`, inclui `alertas/partials/relatorio.html`) | — |
| Fragmento (`HX-Request: true`, sem `HX-Boosted`) | 200 | `text/html; charset=utf-8` | `alertas/partials/relatorio.html` **+** OOB `alertas/partials/contador.html` (`hx-swap-oob="true"`) **+** OOB `alertas/partials/anuncio.html` | — |
| `?formato=csv` (com ou sem HTMX) | 200 | `text/csv; charset=utf-8` | `exportacao.para_csv(resultado, bom=True)` | `Content-Disposition: attachment; filename="reposicao-AAAAMMDD-HHMM.csv"` |
| `?formato=<outro>` | 400 | `text/plain; charset=utf-8` | mensagem acima | — |

### Contexto do template

| Variável | Tipo | Uso |
|----------|------|-----|
| `resultado` | `ResultadoVarredura` | resumo e linhas |
| `intervalo_contador` | int | repassado ao contador OOB |

### Estrutura da página (`alertas/relatorio.html`)

```text
<h1>Relatório de reposição</h1>
<form method="get" action="/alertas/"                     ← funciona sem JS (recarrega a página)
      hx-get="/alertas/" hx-target="#relatorio" hx-swap="outerHTML"
      hx-disabled-elt="find button">
  <button type="submit" class="botao botao--primario">Executar varredura</button>
</form>
<a href="/alertas/?formato=csv" hx-boost="false" download class="botao botao--secundario">Exportar CSV</a>
{% include "alertas/partials/relatorio.html" %}
```

### Região `#relatorio` (`alertas/partials/relatorio.html`)

```text
<section id="relatorio" aria-labelledby="titulo-resultado"
         hx-get="/alertas/" hx-trigger="estoque-alterado from:body" hx-swap="outerHTML">
  <p id="titulo-resultado" class="resumo-varredura">
    Varredura em 20/10/2026 14:32 · 42 produtos analisados · 5 em alerta (1 sem estoque)
  </p>
  ── se resultado.sem_produtos → estado vazio "Nenhum produto cadastrado" + link "Cadastrar produto" (produtos:novo)
  ── se resultado.sem_alertas  → estado vazio positivo (ícone de check) "Nenhum produto precisa de reposição"
                                  + "42 produtos analisados, todos acima do estoque mínimo."
  ── senão → <table> densa (linhas 40 px), <caption> visualmente oculta, <th scope="col">:
             ID | Produto | Situação | Atual | Mínimo | Déficit | Cobertura | Sugestão | Ações
             uma linha por item (alertas/partials/linha_reposicao.html), na ordem de criticidade
</section>
```

### Linha (`alertas/partials/linha_reposicao.html`)

Raiz `<tr id="reposicao-<id>">` (nunca `produto-<id>`, ver fragmentos §4). Contexto: `produto`
(Produto anotado de `ResultadoVarredura.itens`).

| Coluna | Conteúdo | Alinhamento |
|--------|----------|-------------|
| ID | `produto.codigo` (`#0003`), link para `produto.get_absolute_url` | esquerda, mono |
| Produto | nome | esquerda |
| Situação | `{% include "produtos/partials/situacao.html" %}` (ícone SVG + "REPOSIÇÃO NECESSÁRIA" / "SEM ESTOQUE") | esquerda |
| Atual / Mínimo / Déficit | inteiros com separador de milhar | direita, mono tabular |
| Cobertura | `components/barra_cobertura.html` com `percentual=produto.cobertura_percentual`, `variante=produto.situacao_estoque.variante` + "40%" | direita |
| Sugestão | `+16` (inteiro com separador) | direita, mono tabular |
| Ações | "+ Entrada" conforme [fragmentos-e-eventos.md §4](fragmentos-e-eventos.md#4-ação--entrada-do-relatório-e-do-painel) (`origem=alertas`) | direita |

Após a entrada confirmada pelo diálogo da 003, a resposta da 003 dispara `estoque-alterado`; a
região `#relatorio` se recarrega sozinha (nova varredura) e o contador também.

---

## `GET /alertas/contador/` — `alertas:contador`

Fragmento do contador do menu (polling HTMX e evento `estoque-alterado`).

### Parâmetros

| Parâmetro | Valores | Inválido |
|-----------|---------|----------|
| `anterior` | inteiro ≥ 0 (total exibido no momento) | ausente, vazio, negativo ou não numérico → tratado como ausente |

### Respostas

| Caso | Status | Corpo |
|------|-------:|-------|
| `anterior` presente e igual ao total atual | **204** | vazio (HTMX não troca nada) |
| `anterior` presente e diferente | 200 | `alertas/partials/contador.html` (novo total) **+** OOB `alertas/partials/anuncio.html` com "Alertas de reposição: N produto(s) (antes M)." |
| `anterior` ausente/inválido | 200 | `alertas/partials/contador.html` (sem anúncio) |

Mesma resposta com ou sem `HX-Request` (é sempre um fragmento). Orçamento: 1 consulta SQL.

### Fragmento (`alertas/partials/contador.html`)

```text
<span id="contador-alertas" class="contador-alertas"
      hx-get="/alertas/contador/?anterior={{ total }}"
      hx-trigger="every {{ intervalo }}s, estoque-alterado from:body"
      hx-swap="outerHTML"
      {% if oob %}hx-swap-oob="true"{% endif %}>
  {% if total %}
    <svg aria-hidden="true" …>(ícone alerta)</svg>
    <span class="contador-alertas__numero">{{ total }}</span>
    <span class="visualmente-oculto">produto(s) em alerta de reposição</span>
  {% endif %}
</span>
```

Com `total == 0` o elemento existe vazio (continua fazendo polling) e fica oculto por CSS
(`.contador-alertas:empty { display: none }`).

### Anúncio (`alertas/partials/anuncio.html`)

```text
<div id="anuncio-alertas" hx-swap-oob="innerHTML">{{ texto }}</div>
```

`innerHTML` (e não `true`/`outerHTML`) é obrigatório: só o **conteúdo** da região viva estável do
`base.html` (`<div id="anuncio-alertas" class="visualmente-oculto" role="status"
aria-live="polite"></div>`) muda; substituir o próprio elemento faria leitores de tela perderem o
anúncio.

Textos: contador — "Alertas de reposição: 4 produtos (antes 3)."; varredura manual —
"Varredura concluída: 5 produtos em alerta (1 sem estoque) de 42 analisados."
