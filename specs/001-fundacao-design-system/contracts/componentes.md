# Contrato — componentes do design system

**Feature**: `001-fundacao-design-system`. API pública dos componentes que as features 002–004
usam. Visual, anatomia e estados: [`docs/design/design-system.md`](../../../docs/design/design-system.md) §4.
Todos são demonstrados em `/design/` com o trecho abaixo.

Regras gerais: parâmetros em português; textos já traduzidos; números passados como inteiros (o
componente formata com separador de milhar); nenhum componente consulta o banco; todo componente
renderiza sem JavaScript.

---

## 1. API de classes (marcação simples)

| Componente | Classes | Estados por atributo |
|------------|---------|----------------------|
| Botão | `.botao` + `--primario` \| `--secundario` \| `--fantasma` \| `--perigo`; tamanho `--sm`; só-ícone `--icone` (+ `--sm`/`--xs`) | `:disabled` / `aria-disabled="true"`, `aria-busy="true"` ou `.htmx-request` (carregando) |
| Tabela densa | `.tabela-contenedor` > `table.tabela` (+ `.tabela--compacta`); célula numérica `.num`; ID `.tabela__id`; linha `.tabela__linha--alerta` \| `--sem-estoque` | `aria-selected="true"` (linha), `tbody[aria-busy="true"]` |
| Badge genérico | `.badge` + `--neutro` \| `--info` \| `--sucesso` \| `--alerta` \| `--perigo` | — |
| Cartão | `.cartao` (+ `--amplo`, `--interativo`); `.cartao__cabecalho`, `.cartao__titulo` | interativo: hover/foco/ativo |
| Grade | `.grade` > filhos com `.col-md-{1..8}` (≥ 672 px) e `.col-lg-{1..12}` (≥ 1056 px); abaixo de 672 px cada filho ocupa a linha inteira | — |
| Utilitários | `.visualmente-oculto`, `.num`, `.mono`, `.pilha`, `.cluster`, `.texto-atenuado`, `.texto-sutil` | — |

Exemplo (botão que abre diálogo):

```django
<a class="botao botao--primario" href="{% url 'produtos:novo' %}"
   hx-get="{% url 'produtos:novo' %}" hx-target="#dialogo">
  {% icone "plus" %} Cadastrar produto
</a>
```

## 2. Templates (`templates/components/`)

| Template | Uso | Parâmetros (`with …`) | Saída / acessibilidade |
|----------|-----|-----------------------|------------------------|
| `icone.html` | `{% icone "nome" %}` / `{% icone "nome" tamanho="md" rotulo="Alerta" %}` | `nome` (obrigatório, do sprite), `tamanho` `sm`\|`md` (padrão `sm`), `rotulo` | `<svg class="icone icone--sm" aria-hidden="true" focusable="false"><use href="…/sprite.svg#nome"/></svg>`; com `rotulo`: `role="img"` + `<title>` |
| `formulario.html` | automático via `FORM_RENDERER` (`{{ form }}`) | — | erros não ligados a campo como `aviso` de erro; campos via `campo.html` |
| `campo.html` | automático via `{{ form.x.as_field_group }}` | (BoundField) | `<label for>`, controle com `aria-describedby` (ajuda + erro) e `aria-invalid="true"` se houver erro; "(opcional)" se `required=False`; erro com ícone `circle-alert` |
| `badge_estoque.html` | `{% include "components/badge_estoque.html" with situacao=produto.situacao %}` | `situacao`: `"ok"` \| `"reposicao"` \| `"sem_estoque"` | ok → `OK`; reposicao → ícone `triangle-alert` + `REPOSIÇÃO NECESSÁRIA`; sem_estoque → badge composto `REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE`; nome acessível "Situação: …" (FR-028). Valor desconhecido → nada é renderizado |
| `delta.html` | `{% include "components/delta.html" with valor=3 sentido="negativo" %}` | `valor` (int, assinado), `sentido`: `positivo` \| `negativo` \| `neutro`, `sufixo` (opcional, ex.: "%") | seta conforme o sinal; cor conforme `sentido`; menos tipográfico "−"; texto acessível "aumento de 3" / "redução de 3" / "sem variação" |
| `kpi.html` | `{% include "components/kpi.html" with rotulo="Produtos em alerta" valor=12 meta="de 120 produtos cadastrados" destaque="alerta" href=url %}` | `rotulo`, `valor` (int ou `None` → "—"), `meta`, `delta`, `delta_sentido`, `icone`, `href`, `destaque` (`alerta`\|`perigo`\|vazio) | com `href`: `<a class="cartao cartao--interativo kpi">`; valor em mono tabular |
| `lista_barras.html` | `… with titulo="Mais movimentados" rotulo_valor="Unidades" itens=lista` | `titulo`, `rotulo_valor`, `itens`: lista de `{"rotulo": str, "valor": int, "href": str opcional}` **já ordenada** (máx. 10) | `<ul>`; largura `--valor` calculada no template (mín. 2 % se > 0); vazio → `estado_vazio` compacto |
| `barra_categorias.html` | `… with titulo="Situação do estoque" segmentos=lista total=120 unidade="produtos"` | `segmentos`: lista de `{"rotulo": str, "valor": int, "tom": "ok"\|"reposicao"\|"sem_estoque"\|"acento"\|"neutro"}` | barra `aria-hidden="true"` + legenda textual com valor e percentual |
| `rastreador.html` | `… with titulo="Últimos 30 dias" blocos=lista resumo="18 dias com movimentação"` | `blocos`: lista de `{"tom": "ok"\|"reposicao"\|"sem_estoque"\|"acento"\|"vazio", "rotulo": str}`; `resumo` (obrigatório) | linha `role="img"` com `aria-label=resumo`; `title` por bloco; resumo visível |
| `barra_progresso.html` | `… with rotulo="Saldo × mínimo" valor=48 maximo=50 tom="reposicao"` | `rotulo`, `valor`, `maximo` (> 0), `tom` (`acento`\|`ok`\|`reposicao`\|`sem_estoque`) | `role="meter"` com `aria-valuenow/min/max/valuetext`; valor "48 / 50" em mono; acima do máximo → barra cheia |
| `dialogo.html` | **estendido** por fragmentos: `{% extends "components/dialogo.html" %}` | blocos `titulo`, `descricao`, `corpo`, `rodape`; variável `tamanho` (`sm`\|`md`, padrão `md`) | `<h2 id="dialogo-titulo">`; botão fechar `<form method="dialog">` com `aria-label="Fechar"` (com HTMX) ou link "Voltar" (página); região `[data-toasts]` |
| `toast.html` | usado em `#modelo-toast` e pelo `consus.js` | `nivel`, `texto` (opcionais no modelo) | `.toast.toast--<nivel>` com ícone do nível, texto e botão fechar `aria-label="Fechar notificação"` |
| `aviso.html` | `… with nivel="alerta" titulo="Atenção" texto="…"` | `nivel` (`sucesso`\|`info`\|`alerta`\|`erro`), `titulo` (opcional), `texto` | bloco com ícone; `role="alert"` para `erro` quando renderizado após envio de formulário |
| `estado_vazio.html` | `… with icone="package" titulo="Nenhum produto cadastrado" descricao="…" acao_rotulo="Cadastrar produto" acao_url=url compacto=False` | `icone`, `titulo`, `descricao`, `acao_rotulo`, `acao_url` (None → ação desabilitada "(em breve)"), `acao_secundaria` (opcional, ex.: "Limpar busca"), `compacto` | alinhado à esquerda; uma ação |
| `paginacao.html` | `… with pagina=page_obj rotulo_itens="produtos" alvo="#resultados"` | `pagina` (`Page` do Django), `rotulo_itens`, `alvo` (opcional → links com `hx-get`, `hx-target`, `hx-push-url="true"`) | `<nav aria-label="Paginação">`; "1–25 de 132 produtos"; preserva a query string via `{% querystring page=n %}`; não renderiza se só há uma página |
| `navegacao.html` | incluído pelo `base.html` | contexto `itens_navegacao`, `badge_alertas_url` | `<nav aria-label="Principal">`; `aria-current="page"` no ativo; `aria-disabled="true"` + "(em breve)" nos indisponíveis; slot `#badge-alertas` |

## 3. Template tags (`apps/core/templatetags/consus.py`, `{% load consus %}`)

| Tag/filtro | Assinatura | Uso |
|------------|-----------|-----|
| `icone` | inclusion tag `(nome, tamanho="sm", rotulo="")` | ícones do sprite |

Formatação de números e datas usa o próprio Django (`USE_THOUSAND_SEPARATOR`, formatos pt-BR em
`config/formatos/`): `{{ produto.quantidade_atual }}` → `1.240`;
`{{ mov.criado_em|date:"SHORT_DATETIME_FORMAT" }}` → `20/10/2026 14:30`.

## 4. Compatibilidade e evolução

- Parâmetros novos devem ser opcionais (MINOR do design system); renomear/remover parâmetro é
  MAJOR e exige atualizar `/design/` e as features consumidoras no mesmo PR.
- Uma feature que precise de variação visual nova propõe o token/variante em
  `docs/design/design-system.md` antes de escrever CSS (constituição IV — tokens primeiro).
