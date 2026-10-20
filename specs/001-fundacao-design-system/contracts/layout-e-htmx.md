# Contrato — layout base, eventos HTMX e utilitários do `core`

**Feature**: `001-fundacao-design-system`. Este documento é o que as features 002–004 consomem
para encaixar suas páginas na casca do Consus. Complementa a seção "Convenções HTMX" de
`docs/arquitetura.md` (propostas de ajuste em [research.md](../research.md#propostas-de-ajuste-ao-contrato)).

---

## 1. `templates/base.html`

### 1.1 Estrutura e identificadores estáveis

```text
<html lang="pt-BR">
<head>
  <meta charset> <meta viewport> <meta name="color-scheme" content="light">
  <meta name="htmx-config" content='{…ver §2…}'>
  <title>{% block titulo %}{% endblock %} — Consus</title>
  <link rel="preload" … IBMPlexSans-Regular-Latin1.woff2>
  <link rel="stylesheet" tokens.css> base.css components.css utilities.css
  <script defer src="vendor/htmx.min.js"> <script defer src="js/consus.js">
  {% block head_extra %}
</head>
<body hx-boost="true" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
  <a class="pular-conteudo" href="#conteudo">Pular para o conteúdo</a>     ← 1º focável (FR-011)
  <header class="cabecalho-app">  marca (link core:painel) + {% include "components/navegacao.html" %}
  <main id="conteudo" tabindex="-1">
     <div data-mensagens>…mensagens do Django como components/aviso.html…</div>
     <header class="cabecalho-pagina"> blocos sobretitulo / titulo / descricao / acoes </header>
     {% block conteudo %}{% endblock %}
  </main>
  <footer class="rodape-app"> "Consus v{{ versao }}" · Catálogo de design (/design/) · Saúde do sistema (/saude/)
  <div id="toasts" class="toasts" role="status" aria-live="polite" aria-relevant="additions"
       hx-preserve data-duracao-ms="5000" data-maximo="3"></div>
  <template id="modelo-toast">{% include "components/toast.html" %}</template>
  <dialog id="dialogo" class="dialogo" aria-labelledby="dialogo-titulo"></dialog>
</body>
```

| Id / seletor | Dono | Uso pelas outras features |
|--------------|------|---------------------------|
| `#conteudo` | 001 | alvo do link de pular; não usar como `hx-target` de navegação |
| `[data-mensagens]` | 001 | não usar diretamente; use o framework de mensagens |
| `#toasts` | 001 | não renderizar toasts manualmente; use `disparar_toast` ou mensagens |
| `#modelo-toast` | 001 | interno do `consus.js` |
| `#dialogo` | 001 | **alvo** de `hx-get` para abrir formulários em diálogo |
| `#badge-alertas` | 001 (slot) / 004 (conteúdo) | ver §5 |
| `#painel-kpis` | 001 (região) / 004 (conteúdo) | a 004 substitui o estado vazio pelos KPIs |
| `#resultados` | cada feature | convenção do contrato para listas com busca/paginação |

### 1.2 Blocos para páginas

| Bloco | Obrigatório | Conteúdo |
|-------|-------------|----------|
| `titulo` | sim | texto do `<h1>` e do `<title>` ("<titulo> — Consus", FR-019) |
| `sobretitulo` | não | rótulo curto em caixa alta (ex.: "PRODUTOS / #0012") |
| `descricao` | não | uma frase em `ink-muted` |
| `acoes` | não | botões; no máximo um `.botao--primario` |
| `conteudo` | sim | corpo da página, normalmente em `.grade` |
| `head_extra` | não | metadados extras (ex.: `noindex` no catálogo) |

### 1.3 Contexto global (context processor `apps.core.context_processors.consus`)

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `itens_navegacao` | lista de itens resolvidos | ver [data-model §4](../data-model.md#4-item-de-navegação) |
| `badge_alertas_url` | str \| None | URL de `alertas:contador` ou `None` |
| `versao` | str | `config.__version__` |

---

## 2. Configuração HTMX (`<meta name="htmx-config">`)

```json
{
  "responseHandling": [
    {"code": "204", "swap": false},
    {"code": "[23]..", "swap": true},
    {"code": "422", "swap": true},
    {"code": "[45]..", "swap": false, "error": true}
  ],
  "includeIndicatorStyles": false,
  "historyCacheSize": 0
}
```

- `hx-boost="true"` no `<body>`: links e formulários viram requisições AJAX que recebem a
  **página completa** (variante *Boost*).
- CSRF: `hx-headers` no `<body>` envia `X-CSRFToken` em toda requisição HTMX.
- Botões que disparam requisição usam `hx-disabled-elt="this"`; o CSS mostra o estado
  *carregando* via `.htmx-request` (design-system §4.1).
- Regiões que recarregam usam `hx-indicator` ou `aria-busy` — o CSS aplica `--opacity-busy`.

## 3. Regra de renderização nas views (todas as features)

```python
from apps.core.htmx import eh_parcial

def lista(request):
    contexto = {...}
    if eh_parcial(request):          # HX-Request e não boost
        return render(request, "produtos/partials/resultados.html", contexto)
    return render(request, "produtos/lista.html", contexto)
```

Formulário com HTMX: inválido → re-render do parcial com **status 422**; válido → resposta de
sucesso + eventos (§4). Sem HTMX: inválido → página com status 422; válido → `redirect()` +
`messages.success(...)`.

## 4. Eventos (cabeçalho `HX-Trigger`)

| Evento | Payload | Emitido por | Escutado por |
|--------|---------|-------------|--------------|
| `toast` | `{"nivel": "sucesso"\|"info"\|"alerta"\|"erro", "texto": str}` | `apps.core.htmx.disparar_toast(response, texto, nivel="sucesso")` | `consus.js` (região global ou interna do diálogo) |
| `fechar-dialogo` | `{}` | `apps.core.htmx.fechar_dialogo(response)` | `consus.js` → `dialog.close()` |
| `estoque-alterado` | `{}` (definido pela 003) | feature 003 | slot do badge (§5); Painel (004) |

Os utilitários usam `django_htmx.http.trigger_client_event`, que **mescla** eventos no mesmo
cabeçalho: `disparar_toast(fechar_dialogo(resp), "Entrada registrada.")` gera
`{"fechar-dialogo": {}, "toast": {...}}`.

API de `apps/core/htmx.py`:

| Função | Assinatura | Comportamento |
|--------|-----------|---------------|
| `eh_parcial` | `(request) -> bool` | `bool(request.htmx) and not request.htmx.boosted` |
| `disparar_toast` | `(response, texto, nivel="sucesso") -> HttpResponse` | valida `nivel` ∈ `sucesso\|info\|alerta\|erro` e `texto` com 1–200 caracteres (senão `ValueError`), acrescenta o evento `toast`, devolve a mesma resposta |
| `fechar_dialogo` | `(response) -> HttpResponse` | acrescenta o evento `fechar-dialogo` |

## 5. Navegação e slot do badge

- Itens: Painel (`core:painel`), Produtos (`produtos:lista`), Movimentações
  (`movimentacoes:lista`), Alertas (`alertas:relatorio`). **Registrar a rota com esse nome é tudo
  o que a feature precisa fazer** para o item virar link (FR-013). Ativo: Painel na rota exata;
  demais pelo namespace da rota atual (FR-012).
- Item indisponível: `<span class="navegacao__item" aria-disabled="true">Produtos <span
  class="navegacao__breve">(em breve)</span></span>`.
- Slot do badge (FR-014), dentro do item Alertas:
  - sem `alertas:contador`: `<span id="badge-alertas" class="navegacao__badge"></span>` (vazio,
    sem atributos HTMX);
  - com `alertas:contador`: `<span id="badge-alertas" class="navegacao__badge"
    hx-get="/alertas/contador/" hx-trigger="load, estoque-alterado from:body, every 60s"
    hx-swap="innerHTML"></span>`.
  - O fragmento de `alertas:contador` (feature 004) devolve **só o conteúdo interno**: vazio
    (quantidade 0) ou a marcação do badge da navegação (design-system §4.16), com texto
    acessível "N produtos com reposição necessária".
  - Atualização OOB numa resposta de movimentação: `<span hx-swap-oob="innerHTML:#badge-alertas">
    …</span>` — **nunca** `outerHTML` (apagaria `hx-get`/`hx-trigger` do slot).

## 6. Diálogo

- Gatilho: `<a class="botao botao--primario" href="{% url 'produtos:novo' %}"
  hx-get="{% url 'produtos:novo' %}" hx-target="#dialogo">Cadastrar produto</a>` (sem JS, o link
  abre a página).
- Fragmento: `{% extends "components/dialogo.html" %}` com blocos `titulo`, `descricao`,
  `corpo` (formulário com `hx-post`, `hx-target="#dialogo"`), `rodape` (ações; primário à
  direita). O primeiro campo leva `autofocus`.
- Sucesso: resposta com `fechar_dialogo` + `disparar_toast` (+ `estoque-alterado`, OOB de
  linha/badge quando aplicável). Erro de validação: 422 com o fragmento.
- Comportamento do cliente (`consus.js`): `showModal()` após a troca; `Esc`/botão fechar fecham;
  clique no fundo não fecha; foco volta ao acionador; conteúdo é limpo ao fechar; toasts vão para
  `[data-toasts]` do diálogo enquanto ele está aberto.

## 7. Mensagens de página inteira

`messages.success(request, "Produto cadastrado.")` antes de `redirect()`. `MESSAGE_TAGS` mapeia os
níveis do Django para `sucesso|info|alerta|erro`. Sem JS: avisos inline no topo do `<main>`. Com
JS: `consus.js` converte em toasts (no `DOMContentLoaded` e no `htmx:load` de navegação boostada).

## 8. `static/js/consus.js` (< 100 linhas, sem dependências além do HTMX)

Responsabilidades, e somente elas: (1) criar toasts a partir do evento `toast` e das mensagens do
servidor, respeitando `data-duracao-ms`, `data-maximo`, pausa em hover/foco e `role="alert"` para
`alerta`/`erro`; (2) abrir/fechar o `#dialogo` e devolver o foco; (3) toast de erro em
`htmx:responseError` ("Não foi possível concluir a ação (erro N).") e `htmx:sendError` ("Sem
conexão com o servidor."). Nenhuma regra de negócio no cliente.
