# Consus — Design System

**High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise** · versão **1.0.0** · 2026-10-20

> **Fonte de verdade visual do Consus.** Todo valor visual usado pela aplicação está definido aqui
> e é implementado **uma única vez** em `static/css/tokens.css`. Componentes (`components.css`,
> `templates/components/`) só referenciam tokens. A origem de cada decisão (shadcn/ui, Tremor,
> Carbon, design-resources-for-developers, Refactoring UI) está em [`referencias.md`](referencias.md);
> os rótulos `RUI-nn` remetem aos princípios do Refactoring UI resumidos lá.
>
> Mudanças neste documento seguem o fluxo da constituição (princípio IV): PR que altera **este
> arquivo + `tokens.css` + testes de tokens** juntos, com incremento de versão (MAJOR: remoção ou
> renomeação de token/componente; MINOR: token/componente novo; PATCH: ajuste de valor que mantém
> os contrastes).

## Sumário

1. [Personalidade e princípios](#1-personalidade-e-princípios)
2. [Tokens](#2-tokens) — cor · tipografia · espaçamento · tamanhos · bordas e raios · sombras ·
   foco · grid e layout · tabela · camadas (z-index) · movimento · opacidade · iconografia ·
   cores forçadas
3. [Contraste (WCAG 2.1 AA)](#3-contraste-wcag-21-aa)
4. [Componentes](#4-componentes) — botão · campo · tabela densa · badge (status, semântico,
   delta) · cartão · KPI card · BarList · CategoryBar · Tracker · ProgressBar · diálogo · toast ·
   aviso inline · estado vazio · paginação · navegação com badge · cabeçalho de página · ícone
5. [Padrões de página](#5-padrões-de-página)
6. [Faça / Não faça](#6-faça--não-faça)
7. [Mapeamento regra → Refactoring UI](#7-mapeamento-regra--refactoring-ui)
8. [Implementação](#8-implementação)

---

## 1. Personalidade e princípios

**Personalidade (RUI-02):** *sóbria, precisa, industrial.* Um livro-razão de almoxarifado
impresso em papel bom: tinta escura, régua, carimbo âmbar quando algo precisa de atenção.

| # | Princípio | Consequência prática |
|---|-----------|----------------------|
| P1 | **Tinta sobre papel.** Fundo quente, texto quase preto quente, neutros com matiz. | Nada de branco puro como página, nada de cinza acromático. |
| P2 | **Estrutura visível, ornamento zero.** Bordas sólidas de 1 px desenham objetos; sem gradiente, sem vidro, sem desfoque, sem emoji. | Sombra só sólida e só em elemento elevado/interativo. |
| P3 | **Grade suíça.** 12 colunas, alinhamento à esquerda, ritmo de 8 px. | Nenhum bloco de conteúdo centralizado por estética. |
| P4 | **Densidade com hierarquia.** Muitos dados por tela, mas o olho sabe onde ir: peso e cor antes de tamanho. | Corpo 14 px; números mono tabulares; rótulos curtos em caixa alta. |
| P5 | **Um acento, usado com parcimônia.** Ultramar marca *a* ação, o foco e o item ativo. | Se tudo é azul, nada é. |
| P6 | **O alerta é o elemento mais forte da tela.** Âmbar + tinta + ícone + texto. | Nenhum outro componente usa fundo âmbar sólido. |
| P7 | **Acessível por construção.** AA em todos os pares, foco sempre visível, cor nunca sozinha. | Verificado por teste automático (§3). |

---

## 2. Tokens

Todos os tokens são CSS custom properties declaradas em `:root` em `static/css/tokens.css`.
Duas camadas:

- **Primitivas** (`--palette-*`): os valores brutos. **Só podem ser usadas dentro de `tokens.css`.**
- **Semânticas** (`--color-*`, `--space-*`, `--text-*`…): o que componentes usam.

### 2.1 Cor

#### 2.1.1 Primitivas

Neutros "tinta" — matiz fixa ≈ 40° (quente), saturação crescente para as pontas (RUI-18):

| Token | Hex | HSL aprox. | Papel típico |
|-------|-----|------------|--------------|
| `--palette-neutral-0` | `#FFFFFF` | — | superfície |
| `--palette-neutral-50` | `#F6F4EF` | 43° 28% 95% | papel (página) |
| `--palette-neutral-100` | `#EEEBE3` | 44° 24% 91% | camada atenuada |
| `--palette-neutral-200` | `#E3DFD5` | 43° 20% 86% | trilhas, desabilitado |
| `--palette-neutral-300` | `#CFCABF` | 41° 14% 78% | filetes |
| `--palette-neutral-400` | `#ADA89C` | 42° 9% 65% | (reserva — não usar para texto) |
| `--palette-neutral-500` | `#8A8579` | 42° 7% 51% | texto desabilitado |
| `--palette-neutral-600` | `#6B665C` | 40° 8% 39% | texto terciário |
| `--palette-neutral-700` | `#4F4B43` | 40° 8% 29% | texto secundário |
| `--palette-neutral-800` | `#36332D` | 40° 9% 19% | (reserva) |
| `--palette-neutral-900` | `#1A1814` | 40° 13% 9% | tinta |

Acento "ultramar" e semânticas (4 tons cada, RUI-17):

| Família | `-50` (fundo sutil) | base (preenchimento) | `strong`/`hover` | `ink` (texto sobre `-50`) |
|---------|--------------------|----------------------|------------------|---------------------------|
| `--palette-blue-*` (acento/info) | `-50` `#E6E9FA` | `-600` `#2337C6` | `-700` `#1B2A9E` | `-700` `#1B2A9E` |
| `--palette-green-*` (sucesso) | `-50` `#E3F2E7` | `-700` `#1F7A3E` | — | `-900` `#14532B` |
| `--palette-amber-*` (alerta) | `-50` `#FFF3CC` | `-400` `#F2B300` | `-700` `#A87400` | `-900` `#6B4400` |
| `--palette-red-*` (perigo) | `-50` `#FCE8E6` | `-600` `#C4261D` | `-700` `#A11F17` | `-800` `#8F1A13` |

#### 2.1.2 Semânticas (as únicas usadas por componentes)

| Token | Valor | Uso |
|-------|-------|-----|
| `--color-paper` | `neutral-50` `#F6F4EF` | fundo da página (camada 0) |
| `--color-surface` | `neutral-0` `#FFFFFF` | camada 1: cartões, tabelas, campos, diálogos, toasts, cabeçalho |
| `--color-surface-hover` | `neutral-50` `#F6F4EF` | hover de linha/cartão clicável sobre superfície |
| `--color-muted` | `neutral-100` `#EEEBE3` | camada de destaque: `<thead>`, hover de botão fantasma, código |
| `--color-muted-strong` | `neutral-200` `#E3DFD5` | trilhas (progress, tracker vazio), fundo desabilitado, pressionado do fantasma |
| `--color-ink` | `neutral-900` `#1A1814` | texto principal, **bordas estruturais**, **sombras** |
| `--color-ink-muted` | `neutral-700` `#4F4B43` | texto secundário, itens de navegação, cabeçalho de tabela |
| `--color-ink-subtle` | `neutral-600` `#6B665C` | texto terciário: ajuda, placeholder, rótulo de KPI, IDs, rodapé |
| `--color-ink-disabled` | `neutral-500` `#8A8579` | texto de controle desabilitado (isento de contraste) |
| `--color-border` | `= --color-ink` | contorno de campo, botão, cartão, tabela, diálogo |
| `--color-border-subtle` | `neutral-300` `#CFCABF` | filetes internos (linhas de tabela, divisores), borda tracejada de estado vazio |
| `--color-ring` | `= --color-accent` | indicador de foco (somente) |
| `--color-accent` | `blue-600` `#2337C6` | botão primário, links, item de navegação ativo, barras do BarList |
| `--color-accent-hover` | `blue-700` `#1B2A9E` | hover do primário |
| `--color-accent-subtle` | `blue-50` `#E6E9FA` | fundo de barra (BarList), linha selecionada, badge info |
| `--color-accent-ink` | `blue-700` `#1B2A9E` | texto sobre `accent-subtle` |
| `--color-on-accent` | `neutral-0` `#FFFFFF` | texto sobre `accent` |
| `--color-success` | `green-700` `#1F7A3E` | marcas gráficas e ícones de sucesso; borda de toast de sucesso |
| `--color-success-subtle` | `green-50` `#E3F2E7` | fundo de badge OK / aviso de sucesso |
| `--color-success-ink` | `green-900` `#14532B` | texto sobre `success-subtle` |
| `--color-on-success` | `neutral-0` `#FFFFFF` | texto sobre `success` (reserva) |
| `--color-warning` | `amber-400` `#F2B300` | **preenchimento do alerta de reposição** (badge, badge da navegação, segmento) |
| `--color-warning-strong` | `amber-700` `#A87400` | borda de destaque de alerta (linha de tabela, KPI, toast), ícone de alerta sobre superfície |
| `--color-warning-subtle` | `amber-50` `#FFF3CC` | fundo de aviso/toast de alerta |
| `--color-warning-ink` | `amber-900` `#6B4400` | texto sobre `warning-subtle` |
| `--color-on-warning` | `= --color-ink` | texto sobre `warning` |
| `--color-danger` | `red-600` `#C4261D` | botão perigo, erro de campo, segmento "sem estoque", ícone de erro |
| `--color-danger-hover` | `red-700` `#A11F17` | hover do botão perigo |
| `--color-danger-subtle` | `red-50` `#FCE8E6` | fundo de aviso/toast de erro, badge de perigo |
| `--color-danger-ink` | `red-800` `#8F1A13` | texto sobre `danger-subtle` |
| `--color-on-danger` | `neutral-0` `#FFFFFF` | texto sobre `danger` |
| `--color-info` | `= --color-accent` | ícone/borda de info (info reaproveita a matiz do acento, como no Carbon) |
| `--color-info-subtle` | `= --color-accent-subtle` | fundo de aviso/toast/badge info |
| `--color-info-ink` | `= --color-accent-ink` | texto sobre `info-subtle` |
| `--color-overlay` | `rgb(26 24 20 / 60%)` | `::backdrop` do diálogo (tinta a 60 %) |

> Não há tema escuro na v1. Os nomes são semânticos para que um tema futuro redefina só esta
> tabela.

### 2.2 Tipografia

**Famílias** (servidas de `static/fonts/`, `woff2` subset Latin-1, `font-display: swap`):

| Token | Valor |
|-------|-------|
| `--font-sans` | `"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` |
| `--font-mono` | `"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, "DejaVu Sans Mono", monospace` |

Arquivos: Plex Sans 400, 500, 600 e Plex Mono 400, 600 (5 arquivos). Sem itálico (não há uso),
sem 300 (fino demais para densidade — RUI-04).

**Pesos:** `--font-weight-regular: 400` · `--font-weight-medium: 500` · `--font-weight-semibold: 600`.

**Escala fixa** (RUI-14; derivada de `scale01..10` do Carbon; entrelinhas na grade de 4 px):

| Token tamanho | rem / px | Token entrelinha | px | Carbon equivalente |
|---------------|----------|------------------|----|--------------------|
| `--text-xs` | 0.75 / 12 | `--leading-xs` | 16 | `label-01`, `helper-text-01` |
| `--text-sm` | 0.875 / 14 | `--leading-sm` | 20 | `body-compact-01`, `heading-compact-01` |
| `--text-md` | 1 / 16 | `--leading-md` | 24 | `body-02`, `heading-compact-02` |
| `--text-lg` | 1.25 / 20 | `--leading-lg` | 28 | `heading-03` |
| `--text-xl` | 1.75 / 28 | `--leading-xl` | 36 | `heading-04` |
| `--text-2xl` | 2 / 32 | `--leading-2xl` | 40 | `heading-05` |
| `--text-3xl` | 2.625 / 42 | `--leading-3xl` | 48 | `scale10` |

**Tracking:** `--tracking-tight: -0.01em` (≥ 20 px) · `--tracking-normal: 0` ·
`--tracking-caps: 0.06em` (caixa alta ≤ 14 px) — RUI-16.

**Medida:** `--measure: 65ch` (texto corrido, descrições — RUI-15).

**Estilos compostos** (aplicados por classe/elemento em `base.css`; nunca inventar combinação nova):

| Estilo | Família | Tamanho/entrelinha | Peso | Extra | Cor padrão | Onde |
|--------|---------|--------------------|------|-------|-----------|------|
| corpo | sans | sm/sm (14/20) | 400 | — | ink | padrão da UI, células, campos, botões |
| corpo-longo | sans | md/md (16/24) | 400 | `max-inline-size: var(--measure)` | ink | textos explicativos longos |
| rótulo | sans | xs/xs (12/16) | 600 | caixa alta, `--tracking-caps` | ink-muted | `<th>`, rótulo de KPI, sobretítulo, badges |
| ajuda | sans | xs/xs (12/16) | 400 | — | ink-subtle | texto de ajuda e erro de campo |
| rótulo-campo | sans | sm/sm (14/20) | 500 | — | ink | `<label>` |
| título-página | sans | xl/xl (28/36) | 600 | `--tracking-tight` | ink | `<h1>` |
| título-seção | sans | lg/lg (20/28) | 600 | `--tracking-tight` | ink | `<h2>`, título de diálogo |
| título-cartão | sans | md/md (16/24) | 600 | — | ink | `<h3>`, título de estado vazio |
| número | mono | sm/sm (14/20) | 400 | `tabular-nums`, alinhado à direita em tabela | ink | quantidades, IDs, datas em tabela |
| número-kpi | mono | 2xl/2xl (32/40) | 600 | `tabular-nums`, `--tracking-tight` | ink | valor do KPI |
| código-erro | mono | 3xl/3xl (42/48) | 600 | — | ink | "404", "500" |
| marca | mono | md/md (16/24) | 600 | caixa alta, `--tracking-caps` | ink | "CONSUS" no cabeçalho |

Regras: texto secundário é **mais claro**, não menor (RUI-04); nunca abaixo de 12 px; caixa alta
só em rótulos curtos (≤ 3 palavras) e badges; números sempre em `--font-mono` com
`font-variant-numeric: tabular-nums` e separador de milhar "." (constituição IV).

### 2.3 Espaçamento

Base 4 px, ritmo 8 px; **mesma numeração e valores do Carbon `spacing-01..13`** (RUI-11).

| Token | rem | px | Uso típico |
|-------|-----|----|-----------|
| `--space-0` | 0 | 0 | — |
| `--space-1` | 0.125 | 2 | separador de segmentos, deslocamento fino |
| `--space-2` | 0.25 | 4 | rótulo→campo, ícone→texto em badge, entre linhas do BarList |
| `--space-3` | 0.5 | 8 | ícone→texto em botão, entre botões, padding de badge |
| `--space-4` | 0.75 | 12 | padding horizontal de célula e campo, padding do toast |
| `--space-5` | 1 | 16 | padding de cartão, entre campos, gutter < 1056 px, margem de página < 672 px |
| `--space-6` | 1.5 | 24 | padding de diálogo, gutter ≥ 1056 px, margem de página ≥ 672 px |
| `--space-7` | 2 | 32 | cabeçalho de página → conteúdo, entre grupos de campos, margem ≥ 1056 px |
| `--space-8` | 2.5 | 40 | — |
| `--space-9` | 3 | 48 | entre seções do Painel / do catálogo |
| `--space-10` | 4 | 64 | topo de páginas de erro |
| `--space-11` | 5 | 80 | — |
| `--space-12` | 6 | 96 | distância do topo do diálogo |
| `--space-13` | 10 | 160 | — |

**Regra de proximidade (RUI-13):** espaço *dentro* de um grupo < espaço *entre* grupos, sempre
com pelo menos um degrau da escala de diferença. **Regra de partida (RUI-10):** comece um layout
novo com `--space-7`/`--space-9` entre blocos e reduza só onde a densidade exigir.

### 2.4 Tamanhos

| Token | Valor | Uso |
|-------|-------|-----|
| `--size-xs` | 1.5rem (24 px) | badge, botão só-ícone em célula compacta, botão fechar do toast |
| `--size-sm` | 2rem (32 px) | botão/campo `sm`, linha do BarList, bloco do Tracker |
| `--size-md` | 2.5rem (40 px) | botão/campo `md` (padrão em formulários), caixa de ícone do estado vazio |
| `--size-lg` | 3rem (48 px) | — (reserva) |
| `--icon-sm` | 1rem (16 px) | ícone em texto 12–14 px, botões, badges |
| `--icon-md` | 1.25rem (20 px) | ícone em título, estado vazio, toast |
| `--header-h` | 3rem (48 px) | altura do cabeçalho da aplicação |
| `--container-max` | 82rem (1312 px) | largura máxima do conteúdo |
| `--form-max` | 35rem (560 px) | largura máxima de formulário em página |
| `--dialog-w-sm` | 25rem (400 px) | diálogo de confirmação |
| `--dialog-w-md` | 35rem (560 px) | diálogo de formulário (padrão) |
| `--toast-w` | 22.5rem (360 px) | largura do toast |

### 2.5 Bordas e raios

| Token | Valor | Uso |
|-------|-------|-----|
| `--border-width` | 1px | todas as bordas estruturais e filetes |
| `--border-width-strong` | 2px | filete do cabeçalho da aplicação, borda efetiva de campo com erro |
| `--border-width-accent` | 3px | indicador de item de navegação ativo, barra lateral de linha em alerta, borda do BarList |
| `--border-width-callout` | 4px | borda lateral de toast/aviso, topo de KPI em destaque |
| `--radius-0` | 0 | **padrão**: cartão, tabela, diálogo, toast, aviso, barras |
| `--radius-sm` | 2px | controles: botão, campo, badge, caixa de ícone |

Bordas em px (não rem) de propósito: filete não deve engrossar com zoom de fonte.
**Regra de uso (RUI-23):** borda em tinta desenha o **contorno de um objeto** (campo, botão,
cartão, tabela, diálogo, toast). Dentro de objetos, separar com espaço, fundo (`muted`) ou filete
`border-subtle` horizontal. Proibido: linhas verticais em tabela, zebra + filete juntos, borda
dupla (cartão dentro de cartão com borda).

### 2.6 Sombras (sólidas, deslocadas, sem desfoque)

| Token | Valor | Uso |
|-------|-------|-----|
| `--shadow-offset-sm` | 2px | |
| `--shadow-offset-md` | 4px | |
| `--shadow-offset-lg` | 6px | |
| `--shadow-none` | `0 0 0 0 transparent` | estado pressionado/desabilitado (transicionável) |
| `--shadow-sm` | `var(--shadow-offset-sm) var(--shadow-offset-sm) 0 0 var(--color-ink)` | botões primário/secundário/perigo |
| `--shadow-md` | `var(--shadow-offset-md) var(--shadow-offset-md) 0 0 var(--color-ink)` | cartão interativo (KPI com link), toast |
| `--shadow-lg` | `var(--shadow-offset-lg) var(--shadow-offset-lg) 0 0 var(--color-ink)` | diálogo |

**Regra de elevação (RUI-22):** quanto mais "acima" do papel, maior o deslocamento. **Nunca** em:
tabela, campo, badge, aviso inline, cartão estático, cabeçalho. (O `box-shadow: inset` usado como
**barra de destaque** — linha de tabela em alerta, borda de erro do campo — não é sombra de
elevação: não tem deslocamento externo e some sem perda de informação no modo de cores forçadas.) **Pressionar = afundar:** no
`:active`, o elemento translada `(offset, offset)` e a sombra vai a `--shadow-none` — o objeto
"encosta" no papel.

### 2.7 Foco

| Token | Valor |
|-------|-------|
| `--focus-width` | 2px |
| `--focus-offset` | 2px |
| `--focus-color` | `var(--color-ring)` |

Aplicado por `:focus-visible { outline: var(--focus-width) solid var(--focus-color);
outline-offset: var(--focus-offset); }` em todo elemento interativo; campos de texto usam
`:focus` (o foco em campo é sempre útil). Proibido `outline: none` sem substituto. Contraste do
anel ≥ 3:1 contra papel e superfície (§3).

### 2.8 Grid e layout

| Token | Valor | Observação |
|-------|-------|-----------|
| `--grid-columns` | 12 | ≥ 1056 px; 8 colunas de 672 a 1055 px; 4 abaixo de 672 px |
| `--grid-gutter` | `var(--space-5)` → `var(--space-6)` em ≥ 1056 px | 16 → 24 px |
| `--page-margin` | `var(--space-5)` → `var(--space-6)` (≥ 672) → `var(--space-7)` (≥ 1056) | 16 → 24 → 32 px |
| `--bp-md` | 42rem (672 px) | documentação; media queries usam o literal |
| `--bp-lg` | 66rem (1056 px) | idem |
| `--bp-xl` | 82rem (1312 px) | idem |
| `--bp-max` | 99rem (1584 px) | idem |

Media queries não aceitam `var()`: o literal em rem **deve** ser igual ao token documentado e vir
acompanhado de comentário `/* --bp-lg */` (única exceção à regra "sem valores mágicos").

`--grid-columns` vale 4 abaixo de 672 px, 8 de 672 a 1055 px e 12 a partir de 1056 px
(redefinido por media query em `tokens.css`).

Classes de grade (`utilities.css`): `.grade` (`display:grid;
grid-template-columns: repeat(var(--grid-columns), minmax(0, 1fr)); column-gap:
var(--grid-gutter); row-gap: var(--grid-gutter)`); abaixo de 672 px todo filho ocupa a linha
inteira (`grid-column: 1 / -1`); `.col-md-{1..8}` vale a partir de 672 px e `.col-lg-{1..12}` a
partir de 1056 px. Não há classe de span sem prefixo (evita exceder as 4 colunas do celular e
criar colunas implícitas). Tudo alinhado à esquerda; nenhum bloco usa `margin-inline: auto` para
centralizar conteúdo, exceto o contêiner da página.

### 2.9 Tabela

| Token | Valor | Uso |
|-------|-------|-----|
| `--table-row-sm` | `var(--size-sm)` 32 px | densidade compacta (`.tabela--compacta`) |
| `--table-row-md` | `var(--size-md)` 40 px | densidade padrão |
| `--table-cell-px` | `var(--space-4)` 12 px | padding horizontal de `th`/`td` |

Densidades do Carbon (`xs 24 / sm 32 / md 40 / lg 48 / xl 64`) reduzidas às duas que cabem na
faixa da constituição (32–40 px).

### 2.10 Camadas (z-index)

| Token | Valor | Uso |
|-------|-------|-----|
| `--z-base` | 0 | conteúdo |
| `--z-raised` | 1 | elemento "afundado"/elevado localmente |
| `--z-sticky` | 100 | cabeçalho da aplicação, `<thead>` fixo |
| `--z-dropdown` | 200 | (reserva) |
| `--z-toast` | 400 | região de toasts |

O `<dialog>` aberto com `showModal()` vai para a *top layer* do navegador (acima de qualquer
z-index); por isso o diálogo tem **região de toasts própria** (§4.12).

### 2.11 Movimento (mínimo)

| Token | Valor | Origem |
|-------|-------|--------|
| `--duration-instant` | 0ms | |
| `--duration-fast` | 70ms | Carbon `fast-01` |
| `--duration-moderate` | 150ms | Carbon `moderate-01` |
| `--ease-standard` | `cubic-bezier(0.2, 0, 0.38, 0.9)` | Carbon productive standard |
| `--ease-entrance` | `cubic-bezier(0, 0, 0.38, 0.9)` | Carbon productive entrance |
| `--ease-exit` | `cubic-bezier(0.2, 0, 1, 0.9)` | Carbon productive exit |

Só se anima `background-color`, `color`, `border-color`, `box-shadow`, `transform` e `opacity`.
Nada de animação de largura/altura/dados. Com `@media (prefers-reduced-motion: reduce)` as
durações viram `--duration-instant` e `transform` de hover/pressão é desligado.

### 2.12 Opacidade

| Token | Valor | Uso |
|-------|-------|-----|
| `--opacity-busy` | 0.55 | região aguardando resposta (`[aria-busy="true"]`, `.htmx-request`) |

Desabilitado **não** usa opacidade (usa cores próprias, para manter legibilidade).

### 2.13 Iconografia

- Conjunto: **Lucide** (ISC), subset em sprite `static/vendor/lucide/sprite.svg`, uso por
  `<svg><use href="…#nome"></use></svg>` via `{% icone "nome" %}`.
- Traço 2 px, `stroke-linecap: square`, `stroke-linejoin: miter`, cor `currentColor`.
- Tamanhos: `--icon-sm` (16) junto de texto 12–14 px; `--icon-md` (20) em títulos/estado
  vazio/toast. Nunca ampliar acima de 20 px; para destaque, envolver em caixa (RUI-27).
- Decorativo → `aria-hidden="true"` e `focusable="false"`. Ícone sozinho em botão → botão com
  `aria-label`.
- Subset v1 e significado fixo:

| Nome Lucide | Significado no Consus |
|-------------|-----------------------|
| `layout-dashboard` | Painel |
| `package` | Produtos |
| `arrow-left-right` | Movimentações |
| `bell` | Alertas (navegação) |
| `triangle-alert` | **Alerta de reposição** / nível alerta |
| `circle-check` | OK / sucesso |
| `info` | info |
| `octagon-x` | erro / sem estoque |
| `circle-alert` | erro de campo |
| `arrow-down-to-line` | entrada |
| `arrow-up-from-line` | saída/venda |
| `arrow-up` · `arrow-down` · `arrow-right` | delta (subiu / desceu / estável) |
| `plus` | criar |
| `search` | busca |
| `x` | fechar |
| `chevron-left` · `chevron-right` · `chevron-down` | paginação · select |
| `inbox` | estado vazio genérico |
| `loader-circle` | carregando |
| `activity` | saúde |

Ícone **nunca substitui texto** em status: se o sprite não carregar, badges, toasts e botões
continuam legíveis (o texto é obrigatório; o ícone é reforço).

### 2.14 Modo de cores forçadas (alto contraste do sistema)

No `@media (forced-colors: active)` o navegador substitui as cores do autor por cores do sistema e
**remove sombras e imagens de fundo**. Regras:

- `tokens.css` redefine `--color-border: CanvasText` e `--focus-color: Highlight` dentro desse
  bloco (cores de sistema só são permitidas em `tokens.css`).
- Todo componente cujo significado dependa de fundo (badges, botões preenchidos, segmentos de
  barra) **tem borda** — no modo forçado a borda permanece e delimita o objeto.
- Barras de destaque feitas com `box-shadow` (linha de tabela em alerta) somem nesse modo; por
  isso nunca são a única pista (o badge com texto continua na linha).
- O foco usa `outline` (preservado no modo forçado), nunca `box-shadow`.

---

## 3. Contraste (WCAG 2.1 AA)

Mínimos: **4.5:1** texto normal; **3:1** texto grande (≥ 24 px, ou ≥ 18.66 px em 600),
limites de componentes de UI, indicador de foco e marcas gráficas necessárias (WCAG 1.4.3 e
1.4.11). Fórmula: luminância relativa sRGB do WCAG 2.1; razão `(L1 + 0.05) / (L2 + 0.05)`.
Estes são **todos** os pares que o design system permite; um par fora desta tabela exige PR que
o acrescente aqui e no teste. A tabela é verificada automaticamente (teste de tokens e comando
`python manage.py checar_contraste`).

| Primeiro plano | Fundo | Razão | Mínimo | Resultado | Uso |
|----------------|-------|-------|--------|-----------|-----|
| `--color-ink` `#1A1814` | `--color-paper` `#F6F4EF` | 16.13:1 | 4.5:1 | AA | Texto principal sobre a página |
| `--color-ink` `#1A1814` | `--color-surface` `#FFFFFF` | 17.73:1 | 4.5:1 | AA | Texto principal em cartões, tabelas, campos, diálogos |
| `--color-ink` `#1A1814` | `--color-muted` `#EEEBE3` | 14.88:1 | 4.5:1 | AA | Texto sobre camada atenuada (linha hover, código) |
| `--color-ink-muted` `#4F4B43` | `--color-paper` `#F6F4EF` | 7.89:1 | 4.5:1 | AA | Texto secundário sobre a página |
| `--color-ink-muted` `#4F4B43` | `--color-surface` `#FFFFFF` | 8.68:1 | 4.5:1 | AA | Texto secundário em superfícies; itens de navegação |
| `--color-ink-muted` `#4F4B43` | `--color-muted` `#EEEBE3` | 7.28:1 | 4.5:1 | AA | Cabeçalho de tabela (caixa alta) |
| `--color-ink-subtle` `#6B665C` | `--color-surface` `#FFFFFF` | 5.71:1 | 4.5:1 | AA | Placeholder, texto de ajuda, rótulo de KPI |
| `--color-ink-subtle` `#6B665C` | `--color-paper` `#F6F4EF` | 5.19:1 | 4.5:1 | AA | Rodapé, metadados sobre a página |
| `--color-ink-subtle` `#6B665C` | `--color-muted` `#EEEBE3` | 4.79:1 | 4.5:1 | AA | Metadados em camada atenuada |
| `--color-accent` `#2337C6` | `--color-surface` `#FFFFFF` | 8.63:1 | 4.5:1 | AA | Links em superfícies |
| `--color-accent` `#2337C6` | `--color-paper` `#F6F4EF` | 7.85:1 | 4.5:1 | AA | Links sobre a página |
| `--color-on-accent` `#FFFFFF` | `--color-accent` `#2337C6` | 8.63:1 | 4.5:1 | AA | Botão primário |
| `--color-on-accent` `#FFFFFF` | `--color-accent-hover` `#1B2A9E` | 11.22:1 | 4.5:1 | AA | Botão primário (hover) |
| `--color-accent-ink` `#1B2A9E` | `--color-accent-subtle` `#E6E9FA` | 9.30:1 | 4.5:1 | AA | Badge/aviso/toast info; linha selecionada |
| `--color-ink` `#1A1814` | `--color-accent-subtle` `#E6E9FA` | 14.69:1 | 4.5:1 | AA | Rótulo dentro da barra do BarList |
| `--color-success-ink` `#14532B` | `--color-success-subtle` `#E3F2E7` | 7.87:1 | 4.5:1 | AA | Badge OK; toast/aviso de sucesso |
| `--color-on-warning` `#1A1814` | `--color-warning` `#F2B300` | 9.47:1 | 4.5:1 | AA | Badge REPOSIÇÃO NECESSÁRIA; badge da navegação |
| `--color-warning-ink` `#6B4400` | `--color-warning-subtle` `#FFF3CC` | 7.73:1 | 4.5:1 | AA | Toast/aviso de alerta |
| `--color-ink` `#1A1814` | `--color-warning-subtle` `#FFF3CC` | 15.99:1 | 4.5:1 | AA | Texto de linha de tabela em alerta |
| `--color-on-danger` `#FFFFFF` | `--color-danger` `#C4261D` | 5.77:1 | 4.5:1 | AA | Botão perigo; segmento SEM ESTOQUE |
| `--color-on-danger` `#FFFFFF` | `--color-danger-hover` `#A11F17` | 7.71:1 | 4.5:1 | AA | Botão perigo (hover) |
| `--color-danger-ink` `#8F1A13` | `--color-danger-subtle` `#FCE8E6` | 7.67:1 | 4.5:1 | AA | Toast/aviso de erro |
| `--color-danger` `#C4261D` | `--color-surface` `#FFFFFF` | 5.77:1 | 4.5:1 | AA | Mensagem de erro de campo |
| `--color-accent` `#2337C6` | `--color-paper` `#F6F4EF` | 7.85:1 | 3:1 | AA | Indicador de foco sobre a página (não-texto) |
| `--color-accent` `#2337C6` | `--color-surface` `#FFFFFF` | 8.63:1 | 3:1 | AA | Indicador de foco em superfícies (não-texto) |
| `--color-ink` `#1A1814` | `--color-surface` `#FFFFFF` | 17.73:1 | 3:1 | AA | Borda de campo/botão (limite de componente) |
| `--color-danger` `#C4261D` | `--color-surface` `#FFFFFF` | 5.77:1 | 3:1 | AA | Borda de campo com erro |
| `--color-warning-strong` `#A87400` | `--color-surface` `#FFFFFF` | 4.07:1 | 3:1 | AA | Borda de destaque de alerta; ícone de alerta sobre superfície |
| `--color-success` `#1F7A3E` | `--color-surface` `#FFFFFF` | 5.37:1 | 3:1 | AA | Marcas gráficas e ícones de sucesso |
| `--color-accent` `#2337C6` | `--color-surface` `#FFFFFF` | 8.63:1 | 3:1 | AA | Barras/marcas do acento |
| `--color-ink-disabled` `#8A8579` | `--color-muted-strong` `#E3DFD5` | 2.76:1 | — | isento | Texto desabilitado (isento — WCAG 1.4.3) |

**Pares proibidos** (falham AA): `--color-ink-subtle` sobre `--color-muted-strong` (4.29:1);
`--color-warning` sobre papel/superfície como marca isolada (1.70:1 / 1.87:1 — por isso todo
preenchimento âmbar é delimitado por borda em tinta); `--palette-neutral-400` como texto ou
limite de componente (2.16:1).

---

## 4. Componentes

Convenções: classes em português com BEM (`.bloco`, `.bloco__elemento`, `.bloco--variante`);
estados por atributo nativo/ARIA (`:disabled`, `[aria-invalid="true"]`, `[aria-current="page"]`,
`[aria-busy="true"]`, `[aria-disabled="true"]`) — o servidor marca a semântica e o visual vem
junto (padrão shadcn). Componentes com marcação simples são **API de classes**; compostos têm
**template** em `templates/components/` (contrato de parâmetros em
`specs/001-fundacao-design-system/contracts/componentes.md`).

Legenda das tabelas de estado: **D** default · **H** hover · **F** foco · **A** ativo/pressionado ·
**X** desabilitado · **E** erro · **C** carregando.

### 4.1 Botão — `.botao` (API de classes)

```text
 ┌──────────────────────┐
 │ [+]  Cadastrar produto│▌  ← 1px tinta, raio 2px, sombra sólida 2px (primário/secundário/perigo)
 └──────────────────────┘▌
  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

Anatomia: `[ícone 16 opcional] + rótulo` · gap `--space-3` · rótulo em corpo 14/20 peso 500,
**frase com verbo**, sem caixa alta ("Salvar produto", não "SALVAR").

| Tamanho | Classe | Altura | Padding horizontal |
|---------|--------|--------|--------------------|
| md (padrão) | — | `--size-md` 40 | `--space-5` 16 |
| sm | `.botao--sm` | `--size-sm` 32 | `--space-4` 12 |
| só ícone | `.botao--icone` (+ `--sm`/`--xs`) | 40 / 32 / 24 quadrado | 0 (exige `aria-label`) |

| Variante | D | H | F | A | X | C |
|----------|---|---|---|---|---|---|
| **primário** `.botao--primario` | fundo `accent`, texto `on-accent`, borda `border`, `--shadow-sm` | fundo `accent-hover` | anel 2 px `ring` + offset 2 px | translada (2px,2px), `--shadow-none` | fundo `muted-strong`, texto `ink-disabled`, borda `border-subtle`, sem sombra, `cursor: not-allowed` | `aria-busy="true"`: ícone `loader-circle` gira (estático com movimento reduzido), rótulo vira "Salvando…", largura mantida, clique bloqueado |
| **secundário** `.botao--secundario` | fundo `surface`, texto `ink`, borda `border`, `--shadow-sm` | fundo `muted` | idem | idem | idem | idem |
| **fantasma** `.botao--fantasma` | transparente, texto `ink`, sem borda, sem sombra | fundo `muted` | idem | fundo `muted-strong` (sem translação) | texto `ink-disabled`, sem fundo | idem |
| **perigo** `.botao--perigo` | fundo `danger`, texto `on-danger`, borda `border`, `--shadow-sm` | fundo `danger-hover` | idem | translada, `--shadow-none` | igual ao primário desabilitado | idem |

Regras (RUI-09): **um** primário por região (página, diálogo, cartão); o restante é
secundário/fantasma. Perigo **só** no passo de confirmação (diálogo `sm`), nunca na listagem.
Ordem no rodapé: secundário à esquerda, primário à direita (último). `<a class="botao">` para
navegação, `<button>` para ação; desabilitado em link = `aria-disabled="true"` sem `href`.

### 4.2 Campo — `components/campo.html` (renderizador padrão de formulário)

```text
Nome do produto                                   ← rótulo 14/20 peso 500, tinta
┌───────────────────────────────────────────┐      (campo opcional: "(opcional)" em ink-subtle)
│ Parafuso sextavado M8                     │   ← 40 px, fundo surface, 1px tinta, raio 2px, px 12
└───────────────────────────────────────────┘
Use o nome como aparece na nota fiscal.         ← ajuda 12/16 ink-subtle (gap 4 px)
(!) Já existe um produto com este nome.          ← erro 12/16 danger + ícone circle-alert 16 (gap 4 px)
```

Ordem: rótulo → controle → ajuda → erro (shadcn `Field`). Espaços: rótulo→controle `--space-2`;
controle→ajuda/erro `--space-2`; entre campos `--space-5`; entre grupos (`<fieldset>`)
`--space-7` (RUI-13). Ligações: `<label for>`; `aria-describedby` = ids da ajuda e do erro;
`aria-invalid="true"` quando há erro; erro com ícone + texto (nunca só borda vermelha).
Marcar **opcionais** ("(opcional)"), não obrigatórios — a maioria dos campos do Consus é
obrigatória (RUI-06: menos ruído). Largura: formulário em página até `--form-max`.

| Controle | Particularidades |
|----------|------------------|
| texto (`input`) | 40 px (`md`) ou 32 px (`sm` em filtros) |
| número | `font-family: var(--font-mono)`, `tabular-nums`, `inputmode="numeric"`, alinhado à esquerda (alinhamento à direita só em tabela) |
| select nativo | `appearance: none`, ícone `chevron-down` 16 px à direita (`--space-4`), padding direito `--space-8` |
| textarea | altura mínima 5 linhas, `resize: vertical` |
| busca | ícone `search` à esquerda, `type="search"` |

| Estado | Visual |
|--------|--------|
| D | fundo `surface`, borda `border` (tinta), texto `ink`, placeholder `ink-subtle` |
| H | inalterado (campo não "pula"); cursor de texto |
| F | anel `--focus-width` `ring` com `--focus-offset` (via `:focus`) |
| X (`disabled`) | fundo `muted-strong`, texto `ink-disabled`, borda `border-subtle`, `cursor: not-allowed` |
| somente leitura | fundo `muted`, borda `border-subtle` |
| E (`aria-invalid`) | borda `danger` + `box-shadow: inset 0 0 0 1px var(--color-danger)` (2 px efetivos sem deslocar layout) + mensagem de erro; ao focar, o anel de foco aparece **além** da borda de erro |

Erro de formulário (não de campo): `aviso` de perigo no topo do formulário com resumo ("Corrija os
2 campos destacados.").

### 4.3 Tabela densa — `.tabela` (API de classes)

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID      PRODUTO                         ATUAL    MÍNIMO   SITUAÇÃO                     ┃ ← thead: muted, rótulo 12 caps
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃ ← 1px tinta
┃ #0001   Parafuso sextavado M8           1.240       200   [✓ OK]                       ┃ 40 px
┃─────────────────────────────────────────────────────────────────────────────────────────┃ ← filete border-subtle
▌ #0002   Arruela lisa 8 mm                  48        50   [⚠ REPOSIÇÃO NECESSÁRIA]      ┃ ← barra 3px warning-strong
┃─────────────────────────────────────────────────────────────────────────────────────────┃
▌ #0003   Porca M8                            0        30   [⚠ REPOSIÇÃO NECESSÁRIA│SEM ESTOQUE] ← barra 3px danger
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

- Contêiner `.tabela-contenedor`: fundo `surface`, borda `border`, raio 0, `overflow-x: auto`
  (a página nunca rola na horizontal; a tabela rola dentro do contêiner).
- `<th>`: estilo **rótulo** (12/16, 600, caixa alta, `--tracking-caps`, `ink-muted`), fundo
  `muted`, altura = altura da linha, padding `0 var(--table-cell-px)`, borda inferior
  `--border-width` `border`; `position: sticky; top: 0; z-index: var(--z-sticky)`.
- `<td>`: corpo 14/20 `ink`, altura `--table-row-md` (40) ou `--table-row-sm` (32, com
  `.tabela--compacta`), filete inferior `border-subtle`; última linha sem filete.
- **Números** (`.num`): mono, `tabular-nums`, alinhados **à direita** — também o `<th>` da
  coluna (RUI-15). Separador de milhar ".".
- **ID**: mono `ink-subtle` no formato `#0001`.
- Texto longo: uma linha, reticências, nome completo em `title`.
- Hierarquia na célula (RUI-26): coluna "Produto" pode ter nome (500) + metadado (ink-subtle).
- Sem linhas verticais, sem zebra (RUI-23).
- `<caption>` obrigatório (pode ser `.visualmente-oculto`); `scope="col"` em `<th>`.

| Estado da linha | Visual |
|-----------------|--------|
| D | fundo `surface` |
| H (linha com ação/link) | fundo `surface-hover` |
| F (link/botão na linha) | anel de foco no controle, não na linha |
| selecionada (`aria-selected="true"`) | fundo `accent-subtle` |
| **em alerta** (`.tabela__linha--alerta`) | barra lateral `inset var(--border-width-accent) 0 0 var(--color-warning-strong)` + badge REPOSIÇÃO NECESSÁRIA |
| **sem estoque** (`.tabela__linha--sem-estoque`) | barra lateral `danger` + badge composto |
| C (região recarregando) | `tbody[aria-busy="true"]` → `opacity: var(--opacity-busy)` |
| vazia | **não renderizar a tabela**: usar estado vazio (RUI-25) |

Ações por linha: botões `sm` (linha padrão) ou só-ícone `xs` (compacta), na última coluna,
alinhadas à direita.

### 4.4 Badge — `.badge` e `components/badge_estoque.html`

Base: `inline-flex`, altura `--size-xs` (24), padding `0 var(--space-3)`, gap `--space-2`,
estilo **rótulo** (12/16, 600, caixa alta, tracking), raio `--radius-sm`, borda 1 px, ícone
`--icon-sm`. Sem sombra. Não interativo (se precisar de ação, é botão).

#### 4.4.1 Status de estoque (componente `badge_estoque`, parâmetro `situacao`)

| `situacao` | Visual | Texto visível | Nome acessível |
|------------|--------|---------------|----------------|
| `ok` | fundo `success-subtle`, texto e borda `success-ink`, ícone `circle-check` | `OK` | "Situação: OK" |
| `reposicao` | **fundo `warning`, texto `on-warning`, borda `border` (tinta)**, ícone `triangle-alert` | `REPOSIÇÃO NECESSÁRIA` | "Situação: reposição necessária" |
| `sem_estoque` | **badge composto**: segmento 1 idêntico a `reposicao` + divisor 1 px tinta + segmento 2 fundo `danger`, texto `on-danger`, ícone `octagon-x` | `REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE` | "Situação: reposição necessária, sem estoque" |

Por que composto: a constituição exige que o alerta de reposição seja **sempre** ícone + texto
"REPOSIÇÃO NECESSÁRIA" + cor. Quantidade 0 também é "≤ mínimo", logo é alerta; "SEM ESTOQUE" é
uma **extensão** de severidade, não um substituto. Assim o alerta tem sempre a mesma cara
(escaneável) e o zero ganha uma cauda vermelha. A situação é calculada pela feature 004; o
componente só a desenha.

O badge `reposicao` é o **elemento de maior destaque** de qualquer linha ou cartão onde aparece
(P6): nenhum outro componente usa fundo âmbar sólido nem a combinação âmbar + borda tinta.

#### 4.4.2 Semânticos genéricos (`.badge--neutro|--info|--sucesso|--alerta|--perigo`)

Fundo `*-subtle`, texto e borda `*-ink` (neutro: fundo `muted`, texto `ink-muted`, borda
`border-subtle`). Uso: tipo de movimentação (sugestão para a feature 003: ENTRADA = `--info` +
`arrow-down-to-line`; SAÍDA = `--neutro` + `arrow-up-from-line`; INICIAL = `--neutro`),
marcações informativas. `--alerta` (âmbar claro) **não** substitui o badge de reposição.

#### 4.4.3 Delta — `components/delta.html` (Tremor `BadgeDelta`)

`[↑ +12]` · ícone `arrow-up`/`arrow-down`/`arrow-right` + número **assinado** em mono tabular
(sinal de menos tipográfico "−"). A cor vem do **sentido** (juízo), não do sinal:
`sentido="positivo"` → sucesso (subtle/ink); `"negativo"` → perigo (subtle/ink); `"neutro"` →
neutro. Ex.: "produtos em alerta +3" é `negativo`. Nome acessível: "aumento de 12" /
"redução de 5" / "sem variação".

### 4.5 Cartão — `.cartao` (API de classes)

Camada 1 sobre o papel: fundo `surface`, borda `border`, raio 0, padding `--space-5` (16;
`--space-6` em `.cartao--amplo`). Cabeçalho opcional: título-cartão + ação fantasma à direita.
**Estático = sem sombra.** `.cartao--interativo` (o cartão inteiro é um link): `--shadow-md`;
H → fundo `surface-hover`; F → anel; A → translada (4px,4px) e `--shadow-none`. Nunca cartão com
borda dentro de cartão com borda (RUI-23).

### 4.6 KPI card — `components/kpi.html` (Tremor Card + Metric + BadgeDelta)

```text
┌─────────────────────────────────────┐ ← (destaque=alerta) topo 4 px warning-strong
│ PRODUTOS EM ALERTA                ⚠ │ ← rótulo 12 caps ink-subtle · ícone 16 opcional
│ 12                         [↑ +3]   │ ← número-kpi 32/40 mono 600 · delta
│ de 120 produtos cadastrados         │ ← meta 14 ink-muted (frase, não rótulo — RUI-06)
│ ▕████████░░░░░░░░░░░░░░░░░░░░░░░░▏   │ ← barra opcional (ProgressBar/CategoryBar)
└─────────────────────────────────────┘
```

Parâmetros: `rotulo`, `valor`, `meta`, `delta` (+ `delta_sentido`), `icone`, `href`,
`destaque` (`alerta`|`perigo`|vazio). Espaços: rótulo→valor `--space-2`; valor→meta `--space-2`;
meta→barra `--space-4`. Valor formatado com separador de milhar. Com `href` vira
`.cartao--interativo` (link com nome acessível = rótulo + valor). Grade: `col-lg-3` (4 por linha),
`col-md-4` (2 por linha em 8 colunas), 1 por linha abaixo. Hierarquia (RUI-04/06): o **número**
domina; rótulo é coadjuvante.

| Estado | Visual |
|--------|--------|
| D (estático) | cartão sem sombra |
| D (com link) | `--shadow-md` |
| H/F/A | como `.cartao--interativo` |
| destaque `alerta` | borda superior `--border-width-callout` `warning-strong` + ícone `triangle-alert` |
| destaque `perigo` | borda superior `danger` + ícone `octagon-x` |
| sem dado | valor "—" (travessão) e meta explicando ("sem produtos cadastrados") |

### 4.7 BarList — `components/lista_barras.html` (Tremor BarList)

```text
MAIS MOVIMENTADOS (30 DIAS)                          UNIDADES ← rótulos 12 caps
▌███████████████████████████ Parafuso sextavado M8        1.240
▌█████████████ Arruela lisa 8 mm                            612
▌████ Porca M8                                              180
```

`<ul>` de linhas com altura `--size-sm` (32) e gap `--space-2`. Barra: fundo `accent-subtle`,
borda esquerda `--border-width-accent` `accent`, largura `valor / máximo` (mínimo 2 % se
valor > 0; 0 → só a borda). Rótulo dentro da barra (padding `--space-3`), 14 px `ink`,
reticências. Valor em coluna à direita, mono tabular, `ink`. Ordenação decrescente feita pelo
servidor; até 10 itens. Com `href`: a linha inteira é um link; H → rótulo sublinhado; F → anel
na linha. Acessível: cada item lido como "Parafuso sextavado M8: 1.240 unidades". Vazio →
estado vazio compacto.

### 4.8 CategoryBar — `components/barra_categorias.html` (Tremor CategoryBar)

```text
SITUAÇÃO DO ESTOQUE                                           120 produtos
┌────────────────────────────────────────────┬─────────┬──┐
│████████████████████████████████████████████│▓▓▓▓▓▓▓▓▓│▒▒│ ← 12 px; divisores 1 px tinta
└────────────────────────────────────────────┴─────────┴──┘
■ OK 98 (82%)   ■ Reposição necessária 18 (15%)   ■ Sem estoque 4 (3%) ← legenda obrigatória
```

Barra de altura `--space-4` (12) com borda `border`, segmentos proporcionais separados por
divisor de 1 px em tinta (garante 3:1 entre segmentos vizinhos, inclusive âmbar), raio 0.
Tons: `ok` → `success`; `reposicao` → `warning`; `sem_estoque` → `danger`; `acento` → `accent`;
`neutro` → `muted-strong`. Segmento com valor 0 não é desenhado. **Legenda textual obrigatória**
(quadrado 12 px com borda tinta + rótulo + valor mono + percentual): a barra é `aria-hidden` e a
informação vive no texto (RUI-21).

### 4.9 Tracker — `components/rastreador.html` (Tremor Tracker)

```text
MOVIMENTAÇÕES — ÚLTIMOS 30 DIAS
│▮│▮│▯│▮│▮│▮│▯│▯│▮│▮│▮│▮│▮│▯│▮│▮│▮│▮│▮│▮│▮│▮│▯│▮│▮│▮│▮│▮│▮│▮│ ← blocos 32 px de altura, divisores 1 px tinta
18 dias com movimentação · 3 dias em alerta                      ← resumo textual obrigatório
```

Linha de N blocos (`flex: 1`, largura mínima `--space-2`), altura `--size-sm`, contorno e
divisores de 1 px em tinta, raio 0. Tons iguais ao CategoryBar + `vazio` (`muted-strong`). Cada
bloco tem `title` ("12/10/2026 — 2 entradas"). A linha tem `role="img"` e `aria-label` com o
resumo; o resumo também aparece visível abaixo. Uso previsto: histórico de um produto (003/004).

### 4.10 ProgressBar — `components/barra_progresso.html` (Tremor ProgressBar)

Trilha de altura `--space-3` (8) em `muted-strong` com borda `border`; preenchimento no tom
(`acento`|`ok`|`reposicao`|`sem_estoque`); rótulo à esquerda (14 `ink-muted`) e valor à direita
(mono: "48 / 50"). `role="meter"` com `aria-valuenow/min/max` e `aria-valuetext`. Uso: saldo
atual × estoque mínimo no detalhe do produto (002/004). Valores acima do máximo: barra cheia +
texto real.

### 4.11 Diálogo — `<dialog id="dialogo">` + `components/dialogo.html`

```text
        ┌──────────────────────────────────────────────────┐▌
        │ Registrar entrada                          [ × ] │▌ ← título-seção 20/28 · fechar fantasma ícone 32
        │ Parafuso sextavado M8 · saldo atual 1.240         │▌ ← descrição 14 ink-muted
        │                                                   │▌
        │ [região de toasts do diálogo]                     │▌
        │ Quantidade                                        │▌
        │ ┌──────────────┐                                  │▌ ← corpo: campos (padding 24)
        │ │ 10           │                                  │▌
        │ └──────────────┘                                  │▌
        │                          [Cancelar] [Registrar]   │▌ ← rodapé: alinhado à direita, gap 8
        └──────────────────────────────────────────────────┘▌
         ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ ← --shadow-lg (6 px)
```

- Shell: um único `<dialog id="dialogo" aria-labelledby>` no `base.html`; o conteúdo chega por
  `hx-get` com alvo `#dialogo` e é um template que **estende** `components/dialogo.html`
  (blocos `titulo`, `descricao`, `corpo`, `rodape`).
- Visual: fundo `surface`, borda `border`, raio 0, `--shadow-lg`, largura `--dialog-w-md` (560)
  ou `--dialog-w-sm` (400, confirmação), `max-inline-size: calc(100vw - 2 * var(--page-margin))`,
  `max-block-size: calc(100dvh - 2 * var(--space-9))` com rolagem só no corpo; distância do topo
  `--space-12`. Padding cabeçalho/corpo/rodapé `--space-6`; entre eles só espaço (sem filetes).
  `::backdrop` `--color-overlay`, **sem desfoque**.
- Comportamento: abre com `showModal()` quando recebe conteúdo; foco no elemento com `autofocus`
  (ou primeiro campo inválido; senão primeiro focável); `Esc` e botão fechar fecham; clique no
  fundo **não** fecha (evita perda de dados); ao fechar, o foco volta a quem abriu; evento
  `fechar-dialogo` (HX-Trigger) fecha após sucesso.
- Confirmação destrutiva: `--dialog-w-sm`, título em forma de pergunta, descrição da consequência,
  `[Cancelar]` secundário + ação `perigo` (RUI-09).
- Sem JavaScript: o mesmo template é renderizado como página (cartão com `--form-max`), e o
  "fechar" vira link "Voltar".
- Região de toasts interna (`[data-toasts]`, `aria-live="polite"`): enquanto o diálogo modal está
  aberto, toasts são exibidos dentro dele (a *top layer* cobriria a região global).

### 4.12 Toast — região `#toasts` + `components/toast.html`

```text
                                   ┃ (✓) Produto cadastrado.                    [×] ┃▌ ← surface, 1px tinta,
                                   ┃                                                ┃▌   borda esquerda 4 px no tom,
                                                                                         --shadow-md, 360 px
```

| Nível (`nivel`) | Ícone (cor) | Borda esquerda | Papel ARIA | Duração |
|-----------------|-------------|----------------|-----------|---------|
| `sucesso` | `circle-check` (`success`) | `success` | dentro da região `status`/`polite` | 5 s, pausa em hover/foco |
| `info` | `info` (`info`) | `info` | `status`/`polite` | 5 s, pausa em hover/foco |
| `alerta` | `triangle-alert` (`warning-strong`) | `warning-strong` | `role="alert"` (assertivo) | permanece até fechar |
| `erro` | `octagon-x` (`danger`) | `danger` | `role="alert"` (assertivo) | permanece até fechar |

- Região: `position: fixed`, topo `calc(var(--header-h) + var(--space-5))`, direita
  `--page-margin`, coluna com gap `--space-3`, `z-index: var(--z-toast)`, mais novo no topo,
  **máx. 3** (o mais antigo sai). Abaixo de 672 px ocupa a largura menos as margens.
- Toast: padding `--space-4`, gap ícone→texto `--space-3`, texto corpo 14/20 `ink` (frase curta,
  com ponto final), botão fechar só-ícone `xs` (`aria-label="Fechar notificação"`).
- Entrada: `opacity` 0→1 em `--duration-moderate` `--ease-entrance` (0 ms com movimento
  reduzido); sem deslizar.
- Origem: evento HTMX `toast` (`{"nivel": "...", "texto": "..."}`) ou mensagens de sessão do
  servidor. Sem JavaScript, as mensagens aparecem como **aviso inline** no topo do conteúdo.
- A região sobrevive à navegação com `hx-boost` (`hx-preserve`).

### 4.13 Aviso inline — `components/aviso.html` (Carbon inline notification / Tremor Callout)

Fundo `*-subtle` do nível, borda esquerda `--border-width-callout` (`success`, `info`,
`warning-strong`, `danger`), ícone do nível (`--icon-sm`), texto `*-ink`, padding
`--space-4 var(--space-5)`, raio 0, sem borda externa e sem sombra (RUI-23). Título opcional em
600. Usos: fallback sem JS das mensagens, resumo de erros de formulário, explicações no Painel.

### 4.14 Estado vazio — `components/estado_vazio.html` (shadcn Empty, alinhado à esquerda)

```text
┆┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┆ ← 1px tracejado border-subtle, padding 32
┆ ┌────┐                                                ┆
┆ │ ▢  │  ← caixa 40 px, 1px tinta, ícone 20            ┆
┆ └────┘                                                ┆
┆ Nenhum produto cadastrado                              ┆ ← título-cartão 16/24 600
┆ Cadastre o primeiro produto para acompanhar saldo     ┆ ← corpo 14 ink-muted, máx. --measure
┆ e alertas de reposição.                                ┆
┆ [+ Cadastrar produto]                                  ┆ ← botão primário md (uma ação)
┆┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┆
```

Parâmetros: `icone`, `titulo`, `descricao`, `acao_rotulo`, `acao_url` (ou ação secundária
"Limpar busca" para busca sem resultado). Alinhado à esquerda (grade suíça). `.estado-vazio--compacto`
(dentro de cartão): sem borda tracejada, padding `--space-5`. Texto (RUI-25): título diz o que
falta; descrição diz o próximo passo; a ação executa esse passo. Quando vazio, esconder filtros,
cabeçalho de tabela e paginação.

### 4.15 Paginação — `components/paginacao.html` (Carbon Pagination + shadcn a11y)

```text
1–25 de 132 produtos                          [‹ Anterior]  Página 2 de 6  [Próxima ›]
```

`<nav aria-label="Paginação">` logo abaixo do contêiner da tabela, `display: flex`,
`justify-content: space-between`, padding-block `--space-3`, texto 14 `ink-muted`, **números em
mono**. Botões secundários `sm` com ícone (`chevron-left/right`); nas pontas, desabilitados
(`aria-disabled="true"`, sem `href`). Links preservam os parâmetros da busca/filtro e, com HTMX,
usam `hx-get` + `hx-target="#resultados"` + `hx-push-url="true"` (contrato da arquitetura).
Página única → componente não é renderizado.

### 4.16 Navegação com badge — `components/navegacao.html`

```text
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ ■ CONSUS │ Painel   Produtos   Movimentações   Alertas [⚠ 3]                          │ 48 px, surface
└━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘ 2 px tinta
             ▔▔▔▔▔▔ ← item ativo: barra inferior 3 px accent
```

- Cabeçalho: fundo `surface`, altura `--header-h`, filete inferior `--border-width-strong`
  `border`, `position: sticky; top: 0; z-index: var(--z-sticky)`. Marca à esquerda: quadrado
  sólido 16 px em tinta + "CONSUS" no estilo **marca**, link para o Painel. Navegação logo à
  direita da marca (alinhada à esquerda, não centralizada).
- Item (`<a>` em `<nav aria-label="Principal">`): altura total do cabeçalho, padding `0
  var(--space-4)`, corpo 14 peso 500 `ink-muted`, ícone 16 opcional.

| Estado | Visual |
|--------|--------|
| D | texto `ink-muted` |
| H | texto `ink`, fundo `muted` |
| F | anel de foco (offset negativo `calc(-1 * var(--focus-width))` para caber no cabeçalho) |
| ativo (`aria-current="page"`) | texto `ink` peso 600 + barra inferior `--border-width-accent` `accent` (RUI-24) |
| indisponível (`aria-disabled="true"`, sem `href`) | texto `ink-disabled`, sufixo visível "(em breve)" em 12 px, sem hover, `cursor: not-allowed` |

- **Badge da navegação** (slot `#badge-alertas` no item Alertas): altura 20 px
  (`calc(var(--size-xs) - var(--space-2))`), `min-inline-size` igual, padding `0 var(--space-2)`,
  fundo `warning`, borda `border`, texto `on-warning` mono 12 600, ícone `triangle-alert` 12–16 px
  + número; texto acessível "3 produtos com reposição necessária". Quantidade 0 ou sem fonte de
  dados → slot vazio (nada visível, nada anunciado). Conteúdo é responsabilidade da feature 004.
- Abaixo de 672 px: marca em cima, itens em linha rolável horizontalmente (`overflow-x: auto`),
  sem menu hambúrguer (funciona sem JS).

### 4.17 Cabeçalho de página — blocos do `base.html`

```text
PRODUTOS / #0012                                       ← sobretítulo: rótulo 12 caps ink-subtle (opcional)
Parafuso sextavado M8                [Registrar saída] [Registrar entrada]  ← título-página 28/36 + ações
Cadastrado em 12/10/2026 14:30 · estoque mínimo 200   ← descrição 14 ink-muted, máx. --measure
```

Blocos: `sobretitulo`, `titulo` (também compõe o `<title>`: "Título — Consus"), `descricao`,
`acoes`. Ações alinhadas à direita em ≥ 672 px (abaixo, quebram para baixo do título), um único
primário. Margem inferior `--space-7`. Sem filete (RUI-23). `<h1>` único por página; o tamanho
vem do papel visual (RUI-07).

### 4.18 Ícone — `{% icone "nome" %}` → `components/icone.html`

Ver §2.13. Parâmetros: `nome`, `tamanho` (`sm`|`md`), `rotulo` (se informado, o SVG recebe
`role="img"` + `<title>`; senão `aria-hidden="true"`).

---

## 5. Padrões de página

### 5.1 Casca (todas as páginas)

```text
[Pular para o conteúdo]  (visível só no foco)
┌ cabeçalho (sticky, 48 px) ─ marca │ navegação ────────────────────────────────────────┐
├───────────────────────────────────────────────────────────────────────────────────────┤
│ <main id="conteudo">   contêiner: max --container-max, padding-inline --page-margin,   │
│                        padding-block --space-7                                        │
│   [avisos de mensagens — só sem JS]                                                    │
│   cabeçalho de página                                                                  │
│   conteúdo em .grade (12 colunas)                                                      │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ rodapé: "Consus v0.1.0 · Catálogo de design · Saúde do sistema"  (12 px ink-subtle)    │
└───────────────────────────────────────────────────────────────────────────────────────┘
#toasts (fixo, canto superior direito)      <dialog id="dialogo">
```

Fundo da página `paper`; `<html lang="pt-BR">`; corpo em `--font-sans` 14/20 `ink`.

### 5.2 Painel (feature 001 → 004)

Linha 1: até 4 KPIs (`col-lg-3`). Linha 2: CategoryBar da situação (`col-lg-6`) + BarList
(`col-lg-6`). Linha 3: tabela "Reposição necessária" (12 colunas). Em 001 a região
`#painel-kpis` mostra o estado vazio (§4.14) explicando que os indicadores aparecem quando houver
produtos.

### 5.3 Lista com busca (feature 002/003)

Cabeçalho de página com ação primária → barra de filtros (campos `sm` em linha, gap `--space-3`)
→ `#resultados` (tabela + paginação) **ou** estado vazio.

### 5.4 Formulário

Em diálogo (`--dialog-w-md`) com HTMX; como página (`--form-max`) sem JS. Botões no rodapé,
primário à direita. Erros 422 re-renderizam o mesmo formulário.

### 5.5 Página de erro (404 / 500 / 403 / 400)

Alinhada à esquerda nas colunas 1–8, topo `--space-10`: código no estilo **código-erro**
(`ink-subtle`), título-página, descrição curta sem jargão, caminho solicitado em mono (404), ação
primária "Voltar ao Painel". A 500 não depende de banco nem de contexto e usa os mesmos CSS.

---

## 6. Faça / Não faça

| Faça | Não faça | RUI |
|------|----------|-----|
| Use só tokens semânticos (`--color-*`, `--space-*`) em componentes. | Escrever `#2337C6`, `13px` ou `--palette-*` fora de `tokens.css`. | 03 |
| Diferencie texto por cor (`ink`/`ink-muted`/`ink-subtle`) e peso. | Diminuir a fonte abaixo de 12 px para "rebaixar" informação. | 04 |
| Um botão primário por região; secundário/fantasma para o resto. | Duas ações azuis lado a lado. | 09 |
| Botão perigo só na confirmação. | Botão vermelho "Excluir" em cada linha da tabela. | 09 |
| Números em mono tabular, alinhados à direita, com "." de milhar. | Números em sans proporcional ou centralizados. | 15 |
| Separe grupos com mais espaço do que elementos do grupo. | Rótulo equidistante do campo de cima e do de baixo. | 13 |
| Borda em tinta no contorno do objeto; filete sutil dentro. | Grade completa de linhas na tabela ou cartão dentro de cartão com borda. | 23 |
| Sombra sólida deslocada só em elemento elevado/interativo. | Sombra difusa, sombra em tabela/badge/campo, gradiente, desfoque. | 22 |
| Alerta = ícone + "REPOSIÇÃO NECESSÁRIA" + âmbar com borda tinta. | Só pintar a linha de amarelo, ou usar emoji ⚠. | 21 |
| Texto escuro da mesma matiz sobre fundo claro semântico. | Texto cinza sobre fundo verde/âmbar/vermelho. | 19 |
| Estado vazio com explicação e uma ação. | Tabela vazia com cabeçalho e "Nenhum registro". | 25 |
| Rótulos curtos e só quando o dado não se explica. | "Nome:" antes de um nome óbvio no cabeçalho do produto. | 06 |
| Alinhar à esquerda, na grade. | Centralizar blocos de conteúdo por estética. | 12 |
| Ícone Lucide a 16/20 px; caixa ao redor para destacar. | Ampliar ícone para 48 px. | 27 |
| Raio 0 em contêineres, 2 px em controles. | Pílulas e cantos de 8 px+. | 02 |
| Acento em ação primária, foco, item ativo, barras. | Acento em títulos, ícones decorativos ou fundos grandes. | 05 |
| Respeitar `prefers-reduced-motion`. | Animar números, larguras ou entrada deslizante. | — |

---

## 7. Mapeamento regra → Refactoring UI

| Regra do Consus | Seção | Princípio |
|-----------------|-------|-----------|
| Personalidade sóbria/industrial: Plex, raio 0–2 px, tinta sobre papel | §1, §2.5 | RUI-02 |
| Todos os valores em escalas fixas de tokens; teste reprova valores mágicos | §2 | RUI-03 |
| Três tons de texto e três pesos; secundário mais claro, não menor | §2.2 | RUI-04 |
| Navegação em `ink-muted`; só o ativo em tinta | §4.16 | RUI-05 |
| KPI: rótulo pequeno atenuado, número dominante, meta em frase | §4.6 | RUI-06 |
| `<h1>` de 28 px; títulos de cartão de 16 px | §2.2, §4.17 | RUI-07 |
| Ícones de traço em `currentColor` atenuado; borda 2 px só em foco/destaque | §2.13, §2.5 | RUI-08 |
| Hierarquia de botões; perigo só na confirmação | §4.1 | RUI-09 |
| Layout começa com `--space-7/9` | §2.3 | RUI-10 |
| Escala de espaçamento não linear (Carbon) | §2.3 | RUI-11 |
| Contêiner 1312 px, formulário 560 px, texto 65 ch | §2.4 | RUI-12 |
| Proximidade: 4 px rótulo→campo, 16 px entre campos, 32 px entre grupos | §4.2 | RUI-13 |
| Escala tipográfica feita à mão com entrelinhas proporcionais | §2.2 | RUI-14 |
| `--measure`; números à direita em mono | §2.2, §4.3 | RUI-15 |
| Tracking negativo em títulos, positivo em caixa alta | §2.2 | RUI-16 |
| 10 neutros + 4 tons por semântica definidos de antemão | §2.1 | RUI-17 |
| Neutros quentes com saturação nas pontas | §2.1.1 | RUI-18 |
| Badges semânticos com texto escuro da mesma matiz | §4.4 | RUI-19, RUI-20 |
| Alerta com ícone + texto + cor; CategoryBar com legenda; Tracker com resumo | §4.4, §4.8, §4.9 | RUI-21 |
| Três níveis de sombra sólida; pressionar = afundar | §2.6 | RUI-22 |
| Borda só no contorno; tabela sem linhas verticais/zebra; aviso sem borda externa | §2.5, §4.3, §4.13 | RUI-23 |
| Barras de destaque: nav ativa, toast, aviso, KPI, linha em alerta | §4 | RUI-24 |
| Estado vazio obrigatório e com ação; esconder controles inúteis | §4.14 | RUI-25 |
| Célula com hierarquia interna; badge na coluna de situação | §4.3 | RUI-26 |
| Ícones a 16/20 px; caixa no estado vazio | §2.13, §4.14 | RUI-27 |
| Layout mínimo; densidade derivada da tarefa | §5 | RUI-01 |

---

## 8. Implementação

| Arquivo | Conteúdo |
|---------|----------|
| `static/css/tokens.css` | **única** fonte de valores: `:root { --palette-*; --color-*; --font-*; --text-*; --leading-*; --tracking-*; --space-*; --size-*; --icon-*; --border-*; --radius-*; --shadow-*; --focus-*; --grid-*; --page-margin; --bp-*; --table-*; --z-*; --duration-*; --ease-*; --opacity-*; --measure; … }` + media queries que trocam `--grid-gutter`/`--page-margin` + bloco `prefers-reduced-motion` |
| `static/css/base.css` | `@layer` (ordem: `base, components, utilities`); `@font-face` das 5 fontes; reset mínimo; elementos (`html`, `body`, `h1–h3`, `a`, `table`, `input/select/textarea`); foco global; casca (cabeçalho, navegação, `main`, rodapé, link de pular) |
| `static/css/components.css` | um bloco por componente da §4, só com tokens semânticos |
| `static/css/utilities.css` | `.visualmente-oculto`, `.num`, `.mono`, `.grade`, `.col-md-*`, `.col-lg-*`, `.pilha` (gap vertical por token), `.cluster`, `.texto-atenuado`, `.texto-sutil` |
| `static/vendor/lucide/sprite.svg` | subset da §2.13 + `LICENSE` (ISC) |
| `static/fonts/` | `IBMPlexSans-{Regular,Medium,SemiBold}-Latin1.woff2`, `IBMPlexMono-{Regular,SemiBold}-Latin1.woff2` + `OFL.txt` |
| `templates/components/` | `icone`, `campo`, `formulario`, `badge_estoque`, `delta`, `kpi`, `lista_barras`, `barra_categorias`, `rastreador`, `barra_progresso`, `dialogo`, `toast`, `aviso`, `estado_vazio`, `paginacao`, `navegacao` |

**Verificações automáticas** (testes da feature 001): (1) todo par da §3 atinge o mínimo
calculado a partir de `tokens.css`; (2) nenhum arquivo CSS além de `tokens.css` contém cor
literal (`#hex`, `rgb()`, `hsl()`, nomes de cor) nem medida literal em `px`/`rem`/`em` diferente
de 0 (exceto prelúdios de `@media` com comentário do token); (3) componentes não usam
`--palette-*`; (4) `/design/` exibe todos os componentes desta seção; (5) `tokens.css` contém os
blocos `prefers-reduced-motion` e `forced-colors`. Comando para humanos:
`python manage.py checar_contraste` (imprime a tabela da §3 recalculada).

**Catálogo vivo:** `/design/` mostra cada token (amostra, nome, valor, contraste calculado) e cada
componente da §4 em todos os estados aplicáveis, com o trecho de template para copiar. Ele é o
teste visual deste documento: se algo aqui mudar, o catálogo muda junto.
