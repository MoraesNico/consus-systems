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
  <div id="anuncio-alertas" class="visualmente-oculto" role="status" aria-live="polite"></div>
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
| `#anuncio-alertas` | 001 (região viva estável) / 004 (texto) | a 004 troca só o conteúdo (`hx-swap-oob="innerHTML"`); nunca substituir o elemento |
| `#badge-alertas` | 001 (contêiner) / 004 (renderiza `{% contador_alertas %}` → `#contador-alertas`) | ver §5 |
| `#painel-kpis` | 001 (região) / 004 (conteúdo) | a 004 substitui o estado vazio pelos KPIs; o parcial `core/partials/painel_kpis.html` mantém `#painel-kpis` como raiz |
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
from django.views.decorators.vary import vary_on_headers
from apps.core.htmx import eh_fragmento

@vary_on_headers("HX-Request", "HX-Target")
def lista(request):
    contexto = {...}
    if eh_fragmento(request):        # HX-Request, não boost e não restauração de histórico
        return render(request, "produtos/partials/resultados.html", contexto)
    return render(request, "produtos/lista.html", contexto)
```

Formulário com HTMX: inválido → re-render do parcial com **status 422**; válido → resposta de
sucesso + eventos (§4). Sem HTMX: inválido → página com status 422; válido → `redirect()` +
`messages.success(...)`.

## 4. Eventos (cabeçalho `HX-Trigger`)

| Evento | Payload | Emitido por | Escutado por |
|--------|---------|-------------|--------------|
| `toast` | `{"nivel": "sucesso"\|"info"\|"alerta"\|"erro", "texto": str}` | `apps.core.htmx.disparar_toast(response, nivel, texto)` | `consus.js` (região global ou interna do diálogo) |
| `fechar-dialogo` | `{}` | `apps.core.htmx.disparar_evento(response, "fechar-dialogo")` | `consus.js` → `dialog.close()` |
| `estoque-alterado` | opcional `{produto_id, saldo_anterior, saldo_posterior}` | respostas de fragmento após qualquer operação que altere saldo ou situação: cadastro e edição do mínimo (002), movimentação (003) | `#contador-alertas`, `#relatorio` e `#painel-kpis` (004), com `hx-trigger="… estoque-alterado from:body"` |

Os utilitários usam `django_htmx.http.trigger_client_event`, que **mescla** eventos no mesmo
cabeçalho: `disparar_toast(disparar_evento(resp, "fechar-dialogo"), "sucesso", "Entrada
registrada.")` gera `{"fechar-dialogo": {}, "toast": {...}}`. Respostas de página inteira
(comum/*boosted*) não precisam emitir eventos: o servidor re-renderiza o layout inteiro (inclusive
o contador da 004) com os dados atuais.

API de `apps/core/htmx.py`:

| Função | Assinatura | Comportamento |
|--------|-----------|---------------|
| `eh_fragmento` | `(request) -> bool` | `bool(request.htmx) and not request.htmx.boosted and not request.htmx.history_restore_request` |
| `disparar_evento` | `(response, nome, dados=None) -> HttpResponse` | acrescenta o evento `nome` com `dados` (padrão `{}`) ao `HX-Trigger`, preservando os já presentes; devolve a mesma resposta |
| `disparar_toast` | `(response, nivel, texto) -> HttpResponse` | valida `nivel` ∈ `sucesso\|info\|alerta\|erro` e `texto` com 1–200 caracteres (senão `ValueError`), acrescenta o evento `toast` via `disparar_evento`, devolve a mesma resposta |

Views com variantes (página × fragmento) declaram `Vary: HX-Request, HX-Target`.

## 5. Navegação e slot do badge

- Itens: Painel (`core:painel`), Produtos (`produtos:lista`), Movimentações
  (`movimentacoes:lista`), Alertas (`alertas:relatorio`). **Registrar a rota com esse nome é tudo
  o que a feature precisa fazer** para o item virar link (FR-013). Ativo: Painel na rota exata;
  demais pelo namespace da rota atual (FR-012).
- Item indisponível: `<span class="navegacao__item" aria-disabled="true">Produtos <span
  class="navegacao__breve">(em breve)</span></span>`.
- Contêiner do badge (FR-014), dentro do item Alertas — mecanismo único, igual ao da 004
  (contrato v1.1):
  - a 001 entrega `<span id="badge-alertas" class="navegacao__badge"></span>`: contêiner de
    layout, **sem** atributos HTMX e sem visual próprio; vazio até a 004 existir;
  - a 004 **estende** `templates/components/navegacao.html` para renderizar dentro dele
    `{% load alertas_tags %}{% contador_alertas %}`, que produz `<span id="contador-alertas"
    class="contador-alertas" hx-get="/alertas/contador/?anterior=<n>" hx-trigger="every 30s,
    estoque-alterado from:body" hx-swap="outerHTML">…</span>` (o intervalo vem de
    `ALERTAS_INTERVALO_SEGUNDOS`, padrão 30) — o polling e o evento ficam no `#contador-alertas`,
    nunca no contêiner;
  - `GET /alertas/contador/?anterior=<n>` responde **204** quando nada mudou e, quando mudou, o
    novo `#contador-alertas` (trocado por `outerHTML`) + OOB `innerHTML` em `#anuncio-alertas`;
  - atualizações fora de banda (ex.: resposta do relatório da 004) usam `<span
    id="contador-alertas" hx-swap-oob="true">` — o alvo é sempre `#contador-alertas`, nunca o
    contêiner `#badge-alertas`;
  - visual do badge (design-system §4.16) na classe `.contador-alertas` (definida pela 001 em
    `components.css`; com total 0 a 004 renderiza o elemento com `hidden`); texto acessível "N produtos em alerta de
    reposição".

## 6. Diálogo

- Gatilho: `<a class="botao botao--primario" href="{% url 'produtos:novo' %}"
  hx-get="{% url 'produtos:novo' %}" hx-target="#dialogo">Cadastrar produto</a>` (sem JS, o link
  abre a página).
- Fragmento: `{% extends "components/dialogo.html" %}` com blocos `titulo`, `descricao`,
  `corpo` (formulário com `hx-post`, `hx-target="#dialogo"`), `rodape` (ações; primário à
  direita). O primeiro campo leva `autofocus`.
- Sucesso: resposta com `disparar_evento(resp, "fechar-dialogo")` + `disparar_toast` (+
  `estoque-alterado` e OOB de linha/resumo quando aplicável). Erro de validação: 422 com o
  fragmento.
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
conexão com o servidor."); (4) atalhos de teclado genéricos (FR-045): no `keydown` do documento,
localizar `[data-atalho="<tecla>"]` e focar (campo) ou acionar (`click()`) o elemento, com
`preventDefault()`; ignorar quando houver Ctrl/Alt/Meta, alvo editável (`input`, `textarea`,
`select`, `[contenteditable]`) ou `dialog[open]`. Nenhuma regra de negócio no cliente.
