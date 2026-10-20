# Contrato HTTP — rotas do app `core`

**Feature**: `001-fundacao-design-system` · Namespace `core` (montado em `""` por `config/urls.py`).
Convenções gerais (boost, 422, eventos) em [layout-e-htmx.md](layout-e-htmx.md).

Legenda de variantes: **Normal** = requisição sem `HX-Request`; **Boost** = `HX-Request: true` +
`HX-Boosted: true` (navegação/formulário boostado — recebe página completa); **Parcial** =
`HX-Request: true` sem `HX-Boosted` (fragmento).

---

## `GET /` — `core:painel`

| Variante | Status | Template | Corpo |
|----------|--------|----------|-------|
| Normal | 200 | `core/painel.html` (estende `base.html`) | página completa |
| Boost | 200 | `core/painel.html` | página completa (o HTMX troca o `<body>` e o `<title>`) |
| Parcial | 200 | `core/painel.html` | página completa (o Painel não tem fragmento na 001; a 004 acrescenta `core/partials/painel_kpis.html`, com raiz `#painel-kpis`) |

Conteúdo garantido: `<title>Painel — Consus</title>`; `<h1>Painel</h1>`; região
`<section id="painel-kpis" aria-labelledby="painel-kpis-titulo">` contendo o componente
`estado_vazio` (título "Os indicadores aparecem aqui"); ação "Cadastrar produto" →
`url_se_existir("produtos:novo")` (sem rota ⇒ botão secundário desabilitado com "(em breve)").
Contexto: `url_cadastro_produto: str | None`. Métodos ≠ GET/HEAD → 405.

---

## `GET /design/` — `core:design`

| Query | Variante | Status | Template | Observações |
|-------|----------|--------|----------|-------------|
| — | Normal/Boost | 200 | `core/design.html` | catálogo completo; `<meta name="robots" content="noindex, nofollow">` |
| — | Parcial | 200 | `core/design.html` | página completa |
| `?exemplo=dialogo` | Parcial | 200 | `core/partials/design_dialogo.html` (estende `components/dialogo.html`) | alvo do cliente: `#dialogo`; contém `FormularioExemplo` com `autofocus` no 1º campo |
| `?exemplo=dialogo` | Normal/Boost | 200 | `core/design_dialogo_pagina.html` (estende `base.html`, inclui o mesmo corpo) | fallback sem JS (FR-032) |
| `?exemplo=<outro>` | qualquer | 400 | `400.html` | |

Contexto do catálogo: `tokens` (por categoria, valores lidos de `tokens.css`), `pares_contraste`
(com `razao` calculada e `aprovado`), `componentes` (lista `COMPONENTES_CATALOGO` — 18 itens com
âncoras do [data-model](../data-model.md#7-componente-do-catálogo)), dados fictícios rotulados
"Exemplo" para tabela, KPIs, BarList, CategoryBar, Tracker, ProgressBar e paginação.
Disponível com `DEBUG` verdadeiro ou falso (FR-033). Link de acesso: rodapé. Como `?exemplo=dialogo`
tem variantes página × fragmento, a view declara `Vary: HX-Request, HX-Target` (contrato v1.1).

## `POST /design/` — `core:design` (demonstrações)

Requer CSRF (cabeçalho `X-CSRFToken` via `hx-headers` ou campo do formulário).

### `exemplo=toast&nivel=<sucesso|info|alerta|erro>`

| Variante | Status | Cabeçalhos | Corpo |
|----------|--------|-----------|-------|
| Parcial | 204 | `HX-Trigger: {"toast": {"nivel": "<nivel>", "texto": "Exemplo de toast de <nivel>."}}` | vazio |
| Normal/Boost | 302 → `/design/#toast` | — | mensagem do Django no nível correspondente (vira aviso inline / toast) |
| `nivel` inválido | 400 | — | `400.html` |

### `exemplo=formulario` (`nome`, `quantidade`)

| Resultado | Variante | Status | Cabeçalhos | Corpo |
|-----------|----------|--------|-----------|-------|
| inválido | Parcial | **422** | — | `core/partials/design_dialogo.html` re-renderizado com erros (`aria-invalid`, mensagens ligadas por `aria-describedby`); o HTMX troca porque 422 está configurado para troca |
| válido | Parcial | 200 | `HX-Trigger: {"fechar-dialogo": {}, "toast": {"nivel": "sucesso", "texto": "Exemplo enviado: <nome> × <quantidade>."}}` | vazio (o diálogo fecha) |
| inválido | Normal/Boost | 422 | — | `core/design_dialogo_pagina.html` com erros |
| válido | Normal/Boost | 302 → `/design/#dialogo` | — | mensagem de sucesso (toast/aviso) |

`exemplo` ausente ou desconhecido → 400.

---

## `GET|HEAD /saude/` — `core:saude`

| Situação | Status | Corpo (`application/json`) |
|----------|--------|----------------------------|
| banco responde (`SELECT 1` em conexão nova, ≤ `DATABASE_CONNECT_TIMEOUT` s) | 200 | `{"status": "ok", "banco": "ok", "versao": "0.1.0"}` |
| banco indisponível / tempo esgotado / erro de banco | 503 | `{"status": "erro", "banco": "indisponivel", "versao": "0.1.0"}` |
| `HEAD` | 200/503 | sem corpo, mesmos cabeçalhos |
| `POST`/`PUT`/`PATCH`/`DELETE`/`OPTIONS`… | 405 | — (`Allow: GET, HEAD`) |

Cabeçalhos: `Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private`
(`@never_cache`); `Content-Type: application/json`. Sem sessão, sem cookie novo, sem CSRF. Nenhuma
variante HTMX (endpoint de máquina). Consumidores: healthcheck do Compose (FR-036), operador.

---

## Rotas inexistentes e tratadores de erro

| Situação | Status | Template | Base | Contexto de requisição |
|----------|--------|----------|------|------------------------|
| URL inexistente | 404 | `404.html` | `base.html` (com navegação) | sim — mostra `request.path` em mono |
| `PermissionDenied` | 403 | `403.html` | `base.html` | sim |
| Falha de CSRF | 403 | `403_csrf.html` | `erro_base.html` (autônomo) | não — orienta "Recarregue a página e tente de novo." |
| `SuspiciousOperation`/requisição malformada | 400 | `400.html` | `erro_base.html` | não |
| Exceção não tratada (`DEBUG` falso) | 500 | `500.html` | `erro_base.html` | não — não acessa banco nem context processors |
| `/admin/` (qualquer subcaminho) | 404 | `404.html` | `base.html` | admin não montado (FR-044) |

Em **requisição parcial** com status 4xx/5xx o HTMX não troca o conteúdo (configuração de
`responseHandling`) e `consus.js` exibe toast de erro: "Não foi possível concluir a ação
(erro <status>)." (FR-018, US4 cenário 3).

## Cabeçalhos comuns a todas as respostas HTML

`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`
(FR-043); documento com `<html lang="pt-BR">` (FR-020).
