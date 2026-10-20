# Consus — Pesquisa de referências de design

> Documento de pesquisa que fundamenta o design system **High-Density Neo-Brutalism Sóbrio /
> Swiss Grid Enterprise** do Consus. A especificação implementável (tokens, componentes, estados)
> está em [`design-system.md`](design-system.md), que é a **fonte de verdade visual**. Este arquivo
> explica **de onde** veio cada decisão e **o que foi recusado**.
>
> Data da pesquisa: 2026-10-20 · Feature: `specs/001-fundacao-design-system`

## Método

1. Clones rasos e esparsos (`git clone --depth 1 --filter=blob:none --sparse` +
   `git sparse-checkout set --no-cone <caminhos>`) em um diretório temporário fora do repositório.
   Somente arquivos-fonte de tema, tokens e componentes foram baixados; **nenhum script dos
   repositórios foi executado** — o conteúdo foi tratado como dado (leitura de CSS/TSX/SCSS/JSON).
2. Para cada fonte: o que foi estudado (caminhos), o que foi **adotado** (e como foi traduzido para
   HTML + CSS sem build, conforme a constituição) e o que foi **rejeitado** (e por quê).
3. Os valores numéricos adotados (espaçamentos, tamanhos de linha de tabela, escala tipográfica,
   durações) foram conferidos nos arquivos de tokens das fontes, não de memória.

| Fonte | Revisão estudada | Licença | Observação |
|-------|------------------|---------|------------|
| `shadcn-ui/ui` | `ba1503c` (2026-10-19) | MIT | — |
| `tremorlabs/tremor` (Tremor Raw) | `ca4d588` (2025-10-10) | Apache-2.0 | KPI card e delta não existem no Raw; ver `tremor-npm` |
| `tremorlabs/tremor-npm` (Tremor v3, legado) | `7613bff` (2025-01-13) | Apache-2.0 | consultado só para `BadgeDelta` e `Metric` |
| `IBM/carbon` → `carbon-design-system/carbon` | `c3d6496` (2026-10-20) | Apache-2.0 | **Limitação**: `github.com/IBM/carbon` não existe como repositório público (o clone pediu autenticação = 404). O Carbon é mantido em `carbon-design-system/carbon`, que foi o repositório estudado. |
| `bradtraversy/design-resources-for-developers` | `035bac3` (2026-10-18) | MIT | curadoria (lista de links), lida integralmente nas seções relevantes |
| *Refactoring UI* (Adam Wathan & Steve Schoger) | livro, 2018 | proprietário | **Não há código-fonte**: o resumo abaixo é uma paráfrase dos princípios, escrita com palavras próprias, sem reprodução de trechos. |

Nada foi copiado literalmente para o Consus: os componentes de referência são React/Tailwind; o
Consus usa templates Django + CSS puro com custom properties. Adotamos **ideias, proporções e
valores de escala**, não código.

---

## 1. shadcn-ui/ui

### Estudado

- `apps/v4/app/globals.css` — contrato de tokens semânticos (`--background`, `--foreground`,
  `--card`, `--popover`, `--primary`/`--primary-foreground`, `--secondary`, `--muted`/
  `--muted-foreground`, `--accent`, `--destructive`, `--border`, `--input`, `--ring`,
  `--chart-1..5`, `--radius` com derivados `--radius-sm..4xl`).
- `apps/v4/registry/themes.ts` (temas `stone`, `taupe`, `neutral`) e `apps/v4/registry/base-colors.ts`.
- `apps/v4/registry/new-york-v4/ui/`: `button.tsx`, `input.tsx`, `native-select.tsx`, `field.tsx`
  (`FieldLabel`, `FieldDescription`, `FieldError` com `role="alert"`), `table.tsx`, `badge.tsx`,
  `dialog.tsx`, `sonner.tsx` (toaster), `empty.tsx`, `pagination.tsx`, `alert.tsx`, `card.tsx`.

### Adotado

| Ideia do shadcn | Como entra no Consus |
|-----------------|----------------------|
| **Pares semânticos `x` / `x-foreground`**: toda cor de fundo tem a cor de texto que vai sobre ela. | Tokens `--color-accent` + `--color-on-accent`, `--color-danger` + `--color-on-danger`, `--color-warning` + `--color-on-warning` etc. O componente nunca escolhe a cor do texto: usa o par. |
| Camadas `background` → `card`/`popover` → `muted`. | `--color-paper` (página) → `--color-surface` (cartões, tabelas, diálogos, campos) → `--color-muted` (cabeçalho de tabela, trilhas). Casado com o modelo de *layers* do Carbon. |
| `--ring` separado de `--border`: o foco tem cor própria. | `--color-ring` (= acento) usado apenas em indicador de foco; `--color-border` (= tinta) é estrutural. |
| `--border` × `--input`: borda decorativa ≠ limite de controle. | `--color-border-subtle` (filetes internos, sem requisito de contraste) × `--color-border` (limite de campo/botão, ≥ 3:1). |
| Variantes de botão `default / secondary / outline / ghost / destructive` com `size` `sm / default / icon`. | Botão `primario / secundario / fantasma / perigo`, tamanhos `sm` (32 px) e `md` (40 px), variante só-ícone. |
| Estados declarados por atributo (`aria-invalid`, `disabled`, `data-state`). | Estilos de erro e desabilitado ligados a `[aria-invalid="true"]` e `:disabled`, não a classes extras — o servidor só precisa marcar acessibilidade e o visual vem junto. |
| Anatomia de `Field`: rótulo → controle → descrição → erro (`role="alert"`, ligado por `aria-describedby`). | Componente `campo` (template `components/campo.html`) com a mesma ordem e ligações ARIA. |
| Anatomia de `Dialog`: header (título + descrição), corpo, footer com ações alinhadas à direita e botão fechar no canto. | `components/dialogo.html` com a mesma anatomia, sobre `<dialog>` nativo. |
| `Empty` com mídia (ícone em caixa), título, descrição e ações. | Componente `estado_vazio`, porém **alinhado à esquerda** (ver rejeitados). |
| `Pagination` como `<nav aria-label>` com `aria-current="page"` e rótulos acessíveis em anterior/próxima. | Componente `paginacao` (com a densidade da paginação do Carbon). |
| Ícones de status no toaster (`CircleCheck`, `Info`, `TriangleAlert`, `OctagonX`), todos Lucide. | Mesma família (Lucide) e o mesmo mapeamento ícone ↔ nível no toast do Consus. |

### Rejeitado

| Elemento | Motivo |
|----------|--------|
| `--radius: 0.625rem` (10 px) e derivados até `2.6×`. | Neo-brutalismo sóbrio usa raio 0–2 px (constituição IV). Raio grande é o principal sinal visual do "visual shadcn genérico". |
| `shadow-xs` / `shadow-lg` difusas (com desfoque) em botões, cards e diálogo. | Substituídas por **sombras sólidas deslocadas** sem desfoque (`4px 4px 0 tinta`). Sombra difusa sugere material translúcido; o Consus é "papel e tinta". |
| Anel de foco translúcido `ring-[3px] ring-ring/50`. | 50 % de opacidade sobre fundos variados não garante 3:1 (WCAG 2.4.11/1.4.11). Foco é contorno sólido de 2 px com `outline-offset` de 2 px na cor do acento. |
| Overlay `bg-black/50` com animação `zoom-in-95`. | Mantido o escurecimento (tinta a 60 %, valor do Carbon), sem zoom e sem desfoque (constituição: sem glassmorphism). |
| Badge `rounded-full` (pílula). | Pílula é decorativa e disputa atenção com os dados; badge do Consus é retangular, 2 px de raio, caixa alta. |
| Paleta neutra **acromática** (`oklch(L 0 0)`) do tema `neutral`. | Cinza puro parece frio e "sem marca". Adotamos neutros **quentes** (matiz ≈ 40°), como sugerem os temas `stone`/`taupe` e o Refactoring UI. |
| `Empty` centralizado com `text-center`. | Grid suíço: alinhamento à esquerda, sem centralização decorativa (constituição IV). |
| Dependência de Radix/React/Tailwind/`class-variance-authority`. | Constituição II: sem SPA, sem build Node. Variantes viram classes BEM (`.botao--primario`). |
| `oklch()` como formato de token. | Ótimo para gerar rampas, mas a verificação de contraste automática do Consus e a documentação ficam mais simples com hex sRGB. As rampas foram desenhadas em HSL e publicadas em hex. |

---

## 2. tremorlabs/tremor (Tremor Raw) e tremor-npm (legado)

### Estudado

- `src/components/BarList/BarList.tsx` — barras de 32 px (`h-8`), largura proporcional ao máximo
  com mínimo de 2 %, rótulo **dentro** da barra à esquerda, valor fora à direita, ordenação
  descendente padrão, `aria-sort`.
- `src/components/CategoryBar/CategoryBar.tsx` — barra segmentada de 8 px (`h-2`), `gap-0.5`
  entre segmentos, rótulos de limite com `tabular-nums`, marcador opcional (`marker`) com
  `aria-valuenow`.
- `src/components/Tracker/Tracker.tsx` — linha de blocos de 32 px de altura, 1 px entre blocos,
  tooltip por bloco, cor por estado.
- `src/components/ProgressBar/ProgressBar.tsx` — trilha de 8 px, variantes `default/neutral/
  warning/error/success`, rótulo à direita.
- `src/components/Badge/Badge.tsx` — badge com fundo `-50`, texto `-900` e `ring-1 ring-inset`
  de 30 % (variantes `default/neutral/success/error/warning`).
- `src/components/Card/Card.tsx`, `Table/Table.tsx`, `Toast/Toast.tsx`, `Callout/Callout.tsx`;
  `src/utils/focusRing.ts`, `focusInput.ts`, `hasErrorInput.ts`.
- tremor-npm: `src/components/icon-elements/BadgeDelta/styles.ts` (5 tipos de delta:
  `increase`, `moderateIncrease`, `unchanged`, `moderateDecrease`, `decrease`, com ícones de seta
  e cores verde/laranja/vermelho), `src/lib/constants.ts`, `src/components/text-elements/Metric/`.

> Limitação registrada: o "KPI card" do Tremor atual é distribuído como *block* (produto à parte),
> não como componente no repositório open source. A anatomia adotada foi composta a partir de
> `Card` + `Metric` + `BadgeDelta` + `ProgressBar`/`CategoryBar`, que é exatamente como os blocks
> são montados.

### Adotado

| Ideia do Tremor | Como entra no Consus |
|-----------------|----------------------|
| **Componentes de dados pequenos e textuais**, sem biblioteca de gráficos. | BarList, CategoryBar, Tracker e ProgressBar desenhados com `<div>`/`<ul>` + CSS (larguras em `style="--valor: 42%"`), renderizados no servidor. Zero JavaScript. |
| BarList: linha de 32 px, rótulo dentro da barra, valor à direita, mínimo de 2 % para valores > 0. | Igual, com valor em **IBM Plex Mono tabular** e barra em `--color-accent-subtle` com borda esquerda de 3 px em `--color-accent`. |
| CategoryBar: segmentos proporcionais com pequeno espaço entre eles + rótulos numéricos tabulares. | Barra de 12 px (8 px do Tremor + borda), segmentos OK / Reposição / Sem estoque, separador de 2 px e **legenda textual obrigatória** (cor nunca sozinha). |
| Tracker: um bloco por período com estado e tooltip. | "Rastreador" de 30 dias para histórico de movimentações/alertas (feature 003/004); tooltip via `title` + texto alternativo por bloco (`aria-label`) e resumo textual. |
| `BadgeDelta`: separar **direção** (subiu/desceu) de **juízo** (bom/ruim). | Badge delta com seta + número assinado (`+12`, `−5`); a cor vem de `data-sentido="positivo|negativo|neutro"`, não do sinal — "itens em alerta subiram" é ruim mesmo sendo `+`. |
| `Metric` grande e semibold; rótulo pequeno acima. | KPI: rótulo 12 px caixa alta atenuado, valor 32 px mono semibold, metadado 14 px atenuado. |
| `focusRing` com `outline` (não `box-shadow`). | Foco por `outline` (sobrevive ao modo de alto contraste do Windows; `box-shadow` não). |
| `hasErrorInput`: erro = borda vermelha + anel. | Erro = borda de 2 px `--color-danger` + mensagem com ícone. |
| Badge com fundo claro + texto escuro da mesma matiz. | Base dos badges semânticos (`--color-*-subtle` + `--color-*-ink`), que é também a recomendação do Refactoring UI para contraste sem cor berrante. |

### Rejeitado

| Elemento | Motivo |
|----------|--------|
| `rounded-full` em CategoryBar/ProgressBar; `rounded-md`/`rounded-lg` em Card e badge. | Raio 0–2 px. Barras com cantos retos leem como régua/instrumento, coerente com o grid suíço. |
| `shadow-xs` em Card. | Cartões estáticos (KPI sem link) não têm sombra; sombra é sinal de elevação/interação. |
| Paleta Tailwind (`blue-500`, `emerald`, `gray-900`, fundo escuro `#090E1A`). | Paleta própria "tinta sobre papel"; sem modo escuro nesta versão. |
| Tooltips via Radix HoverCard. | Sem JS de terceiros além do HTMX: `title` + texto acessível. |
| Animações de largura (`duration-800`) no BarList. | Movimento mínimo (constituição IV): sem animação de dados. |
| Gráficos (AreaChart/BarChart/LineChart via Recharts). | Exigiriam JS/SVG dinâmico; fora do escopo da atividade. Os componentes textuais cobrem os KPIs da feature 004. |

---

## 3. Carbon Design System (IBM) — `carbon-design-system/carbon`

### Estudado

- `packages/layout/tokens/layout.tokens.json` — `spacing-01..13`
  (2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96, 160 px), `size-xs..2xl` (24, 32, 40, 48, 64, 80 px),
  `icon-size-01/02` (16, 20 px), `border-radius-00..max`.
- `packages/layout/src/index.ts` — `miniUnit = 8`, breakpoints `sm 320 / md 672 / lg 1056 /
  xlg 1312 / max 1584` px com 4/8/16/16/16 colunas e margens 0/16/16/16/24 px.
- `packages/grid/scss/_config.scss` — `$grid-gutter: 32px`, `$grid-gutter-condensed: 1px`.
- `packages/type/src/fontFamily.ts`, `fontWeight.ts`, `scale.ts`, `styles.ts` — IBM Plex Sans/Mono,
  pesos 300/400/600, escala 12-14-16-18-20-24-28-32-36-42…, estilos `label-01`, `helper-text-01`,
  `body-compact-01/02`, `body-01/02`, `code-01/02`, `heading-compact-01/02`, `heading-03..05`
  (tamanho, `line-height` e `letter-spacing` de cada um).
- `packages/themes/tokens/themes/white/theme.tokens.json` e `notification.tokens.json` — tokens
  de camada (`background`, `layer-01/02`, `layer-accent-01`), bordas (`border-subtle-00/01`,
  `border-strong-01`), texto (`text-primary/secondary/helper/placeholder/error/disabled`),
  `focus`, `interactive`, `support-success/warning/error/info`, `overlay` (preto 60 %),
  `notification-background-*` (cores `-10`).
- `packages/colors/tokens/colors.tokens.json` — rampas `gray`, `warmGray`, `blue`, `red`,
  `green`, `yellow`, `orange` (10..100).
- `packages/styles/scss/_layer.scss` — modelo de camadas aninhadas (`layer-one/two/three`).
- `packages/styles/scss/components/data-table/_data-table.scss` — tamanhos de linha
  `xs 24 / sm 32 / md 40 / lg 48 / xl 64` px, cabeçalho em `layer-accent` com `heading-compact-01`,
  corpo `body-compact-01`, filete inferior `border-subtle`, hover `layer-hover`.
- `.../notification/_toast-notification.scss` e `_mixins.scss` — toast de 288 px (352 px no
  breakpoint `max`), barra lateral de 3–6 px na cor do status, variante *low contrast* com fundo
  `-10`.
- `.../text-input/_text-input.scss`, `.../button/_vars.scss`, `.../modal/_modal.scss`,
  `.../pagination/_pagination.scss`, `utilities/_focus-outline.scss` (contorno de 2 px,
  `outline-offset: -2px`, variante `invalid` em `support-error`).
- `packages/motion/tokens/motion.tokens.json` — `fast-01 70ms`, `fast-02 110ms`,
  `moderate-01 150ms`, `moderate-02 240ms`; curvas *productive* `standard (0.2,0,0.38,0.9)`,
  `entrance (0,0,0.38,0.9)`, `exit (0.2,0,1,0.9)`.

### Adotado

| Ideia do Carbon | Como entra no Consus |
|-----------------|----------------------|
| **Grid 2x / mini-unidade de 8 px**, com meia-unidade de 4 px para ajustes finos. | Toda medida é múltiplo de 4 px; ritmo principal em 8 px. |
| Escala de espaçamento `spacing-01..13`. | `--space-1..13` com **os mesmos valores e a mesma numeração** (2 … 160 px) — quem conhece Carbon lê o Consus sem tabela de conversão. `--space-0` = 0. |
| Tamanhos de controle `size-xs/sm/md/lg`. | `--size-xs 24`, `--size-sm 32`, `--size-md 40`, `--size-lg 48` px. Botões e campos `md` em formulários, `sm` em barras de ferramentas e células. |
| Densidade de DataTable `xs/sm/md/lg/xl`. | Duas densidades dentro da faixa da constituição (32–40 px): `--table-row-sm` 32 px (compacta) e `--table-row-md` 40 px (padrão). |
| Tipografia **IBM Plex Sans + IBM Plex Mono**; *productive type* (compacto, para produto, não marketing). | Mesmas famílias; escala fixa 12/14/16/20/28/32/42 px derivada de `scale01..10`; corpo padrão 14 px (`body-compact-01`); rótulo 12 px (`label-01`) com tracking. |
| Pesos 400/600 (o Carbon evita 300 em UI). | 400, 500 e 600. Sem 300 (fino demais para alta densidade). |
| **Tokens de camada** (`background` → `layer-01` → `layer-accent`). | `--color-paper` → `--color-surface` → `--color-muted`/`--color-muted-strong`. Regra: um componente sempre usa a camada imediatamente acima de onde está. |
| Cabeçalho de tabela em camada de destaque, corpo em camada, filete inferior sutil. | Igual: `<thead>` em `--color-muted`, `<tbody>` em `--color-surface`, filete `--color-border-subtle`, borda externa em tinta. |
| Notificações com **barra lateral na cor do status** + ícone + fundo `-10` (low contrast). | Toast e aviso inline: borda esquerda de 4 px na cor do nível, ícone do nível, fundo `--color-surface` (toast) ou `--color-*-subtle` (aviso inline). |
| Toast com largura fixa (288–352 px), empilhado no canto. | Toast de 360 px no canto superior direito, abaixo do cabeçalho; largura total em telas < 672 px. |
| Overlay a 60 %. | `--color-overlay` = tinta a 60 % atrás do `<dialog>`. |
| Tokens de movimento *productive* curtos. | `--duration-fast 70ms`, `--duration-moderate 150ms`, curvas `standard/entrance/exit` copiadas em valor; tudo vai a 0 com `prefers-reduced-motion`. |
| Breakpoints `sm 320 / md 672 / lg 1056 / xlg 1312 / max 1584`. | Mesmos valores; grade de 4 → 8 → 12 colunas (o Consus usa **12**, não 16, por exigência da constituição). |
| Contorno de foco de 2 px; variante "invalid" com a cor de erro. | Foco 2 px no acento; campo inválido com borda de 2 px no perigo (distinto do foco). |
| Paginação "itens por página · 1–25 de 132 · página 1 de 6 ‹ ›". | Paginação do Consus mostra intervalo e total em mono à esquerda e navegação à direita. |

### Rejeitado

| Elemento | Motivo |
|----------|--------|
| Grade de **16 colunas** e gutter de 32 px. | Constituição IV exige 12 colunas. Gutter de 16 px (< 1056 px) e 24 px (≥ 1056 px) por densidade. |
| Campo com **apenas borda inferior** e fundo cinza (`field-01`). | Em neo-brutalismo o limite do campo precisa ser inequívoco: borda de 1 px em tinta nos quatro lados, fundo branco. Campo "só sublinhado" também tem baixa descoberta para usuários iniciantes (público SENAI). |
| Cabeçalho da aplicação escuro (`g100`) e tema escuro. | "Tinta sobre papel": cabeçalho em superfície clara com filete de 2 px em tinta; só tema claro nesta versão. |
| Azul `blue-60` (#0f62fe) como cor interativa. | É a assinatura da IBM; o Consus tem acento próprio (ultramar `#2337C6`). |
| Toast `box-shadow: 0 2px 6px rgba(0,0,0,.2)`. | Sombra difusa → sombra sólida deslocada `4px 4px 0 tinta`. |
| Botões altos (48 px) com padding direito largo (64 px) para ícone. | Densidade: 40 px (md) e 32 px (sm), padding simétrico. |
| Raio de 8 px previsto para a v12 (`enable-v12-release`). | Raio 0–2 px. |
| Fluid type / expressive type. | Expressivo é para marketing; produto denso usa escala fixa. |

---

## 4. bradtraversy/design-resources-for-developers

### Estudado

`readme.md` — seções **Fonts**, **Colors**, **Icons**, **Icon Fonts**, **Design Systems & Style
Guides**, **Online Design Tools** e **Others** (acessibilidade). O repositório é uma curadoria de
links; a pesquisa consistiu em filtrar as opções compatíveis com as restrições do Consus
(licença livre, auto-hospedável, sem CDN, sem build) e justificar a escolha.

### Adotado (e justificativa da escolha)

| Necessidade | Opções da curadoria consideradas | Escolha | Por quê |
|-------------|----------------------------------|---------|---------|
| Família tipográfica de UI | Google Fonts (catálogo), Font Squirrel, Lexend, Fontjoy/FontPair (pareamento) | **IBM Plex Sans + IBM Plex Mono** (catálogo Google Fonts / releases oficiais IBM, licença SIL OFL 1.1) | Superfamília projetada para produto: Sans e Mono compartilham métricas e desenho, então números mono ao lado de texto sans não "pulam". Plex Mono tem largura fixa (tabelas e KPIs alinham sem truques); Plex Sans tem `tnum` como reserva. É a família do Carbon (coerência com a referência). Cobre Latin-1 completo (ã, õ, ç, á…). Pareamento Sans+Mono da mesma família dispensa ferramenta de pareamento. |
| Auto-hospedagem de fonte | Google Webfonts Helper ("self-host Google Fonts"), FontDrop (inspeção de arquivos) | Arquivos `woff2` subset Latin-1, servidos de `static/fonts/` | Constituição V: sem CDN em execução. FontDrop serve para conferir glifos/`tnum` do subset. |
| Ícones | Feather, **Lucide** (fork mantido do Feather), Tabler, Heroicons, Phosphor, Radix Icons, Iconoir, Remix, Bootstrap Icons | **Lucide** (licença ISC), subset em sprite SVG | Traço único de 2 px em grade de 24 px: casa com bordas de 1–2 px do neo-brutalismo; é a família usada pelo shadcn (os mesmos glifos de status); ativamente mantida (Feather está parado); licença permissiva e curta. Ajuste próprio: `stroke-linecap="square"` e `stroke-linejoin="miter"` para cantos retos. Tabler foi a segunda opção (mais ícones, mas traço e cantos arredondados em excesso para o tom sóbrio). Fontes de ícone (Icon Fonts) rejeitadas: SVG inline é mais acessível e nítido. |
| Paleta | Coolors, Adobe Color, Huemint, Color Hunt (inspiração); **Huetone** e **InclusiveColors** (sistemas acessíveis); Color Brewer 2 (daltonismo) | Rampas desenhadas em HSL com matiz fixa (~40° nos neutros) e conferidas em ferramentas de sistema acessível | Geradores aleatórios produzem paletas "bonitas", não sistemas; Huetone/InclusiveColors trabalham com rampas por luminância e mostram contraste WCAG por par — exatamente o que um design system precisa. Color Brewer usado para checar que as 3 cores de situação (OK/alerta/perigo) continuam distinguíveis em deuteranopia **quando acompanhadas de ícone e texto** (que são obrigatórios). |
| Contraste | **Colorable**, **whocanuse**, BrivTools Color Contrast Checker, A11ygator | Cálculo WCAG 2.1 automatizado no próprio repositório (teste + comando `checar_contraste`), conferido manualmente no Colorable/whocanuse | Ferramenta externa não roda no CI; a fórmula WCAG é simples e foi implementada como teste. whocanuse ajuda a explicar o impacto para baixa visão. |
| Grid | Grid Malven, Layoutit Grid Generator | CSS Grid nativo, 12 colunas | As ferramentas serviram de referência de sintaxe; não geram dependência. |
| Design systems de referência | Carbon, Primer, Polaris, Material, Ant, Atlassian | Carbon (já estudado em profundidade) | Carbon é o sistema "enterprise denso" mais próximo do objetivo. |

### Rejeitado

| Elemento | Motivo |
|----------|--------|
| Fontes decorativas/display (DaFont, 1001 Free Fonts, Leon Sans…). | Uso em UI densa exige família com vários pesos, métricas estáveis e números tabulares. |
| Font Awesome / fontes de ícones. | Ícone como fonte falha sem a fonte, é anunciado de forma errática por leitores de tela e não respeita `currentColor` tão bem quanto SVG. |
| Kits de UI e frameworks CSS (Bootstrap, Tailwind, Bulma…). | Constituição: tokens próprios, sem build; frameworks trazem a "cara genérica" que o projeto quer evitar. |
| Ícones 3D/animados (3DICONS, Lordicon, UseAnimations). | Incompatíveis com sobriedade e movimento mínimo. |
| Emojis (Emoji Guide). | Proibidos como ícones pela constituição; o "⚠" do alerta é um **SVG** (Lucide `triangle-alert`). |

---

## 5. Refactoring UI (Adam Wathan & Steve Schoger) — princípios resumidos

Resumo **com palavras próprias**; os rótulos `RUI-nn` são usados em
[`design-system.md`](design-system.md) para rastrear qual princípio sustenta cada regra.

| ID | Princípio (paráfrase) | Aplicação no Consus |
|----|----------------------|---------------------|
| RUI-01 | **Comece pela funcionalidade, não pelo layout.** Desenhe a tarefa real (cadastrar, movimentar) antes da "casca" da aplicação; a casca se ajusta depois. | O layout base é mínimo; a densidade foi decidida a partir da tarefa "ler muitos produtos rapidamente". |
| RUI-02 | **Escolha uma personalidade** — fonte, cor, raio e tom de voz comunicam seriedade ou descontração. | Personalidade: *sóbria, precisa, industrial*. Plex, raio 0–2 px, tinta sobre papel, textos curtos e diretos. |
| RUI-03 | **Limite as escolhas: defina sistemas antes** (escalas fixas de tipo, espaço, cor, sombra) e escolha só dentro delas. | Todos os valores vêm de `tokens.css`; valores mágicos são reprovados por teste. |
| RUI-04 | **Hierarquia é tudo, e tamanho não é a única ferramenta**: use peso e cor; dois pesos e dois ou três tons de texto bastam. | Texto primário/secundário/terciário = `ink`/`ink-muted`/`ink-subtle`; pesos 400/500/600; títulos não são gigantes. |
| RUI-05 | **Enfatize desenfatizando**: em vez de gritar o elemento principal, abaixe os concorrentes. | Ações secundárias como botão secundário/fantasma; navegação em `ink-muted`; só o item ativo em tinta. |
| RUI-06 | **Rótulos são o último recurso**: dados autoexplicativos dispensam rótulo; quando necessário, rótulo vira coadjuvante (pequeno, atenuado) ou se junta ao valor ("12 em estoque"). | KPIs com rótulo curto em caixa alta atenuado e valor dominante; metadados como frase ("de 120 produtos"). |
| RUI-07 | **Hierarquia visual ≠ hierarquia do documento**: um `<h1>` não precisa ser enorme; títulos de seção podem funcionar como rótulos. | `h1` de página 28 px; títulos de cartão 14–16 px semibold. Semântica HTML correta, tamanho pelo papel visual. |
| RUI-08 | **Equilibre peso e contraste**: elementos pesados (ícones cheios, bordas grossas) precisam de cor mais suave; elementos finos precisam de mais peso. | Ícones de 2 px de traço em `currentColor` atenuado ao lado de texto; borda de 2 px só em foco/destaque. |
| RUI-09 | **Semântica é secundária na hierarquia de botões**: primária sólida e evidente, secundária discreta, terciária como link; ação destrutiva só é grande e vermelha na confirmação. | 1 botão primário por contexto; "perigo" apenas no diálogo de confirmação. |
| RUI-10 | **Comece com espaço demais e retire.** Espaço em branco é mais fácil de reduzir do que de criar. | Layouts nascem com `--space-7/9` entre seções e são comprimidos só onde a densidade pede (tabelas). |
| RUI-11 | **Sistema de espaçamento não linear**: valores pequenos próximos, grandes espaçados (nenhum par adjacente a menos de ~25 %). | Escala 2-4-8-12-16-24-32-40-48-64-80-96-160 (Carbon). |
| RUI-12 | **Você não precisa preencher a tela**; nem tudo deve ser fluido: colunas de largura fixa convivem com áreas flexíveis. | Conteúdo limitado a 1312 px; formulários limitados a ~ 560 px; texto corrido a 65 ch. |
| RUI-13 | **Evite espaçamento ambíguo**: o espaço entre grupos deve ser claramente maior que o espaço dentro do grupo. | Rótulo a 4 px do campo; campos a 16–24 px entre si; seções a 48 px. |
| RUI-14 | **Escala tipográfica feita à mão** (não modular automática), em px/rem; `line-height` proporcional (texto pequeno → entrelinha maior; títulos → menor). | Escala fixa 12…42 px com entrelinhas na grade de 4 px. |
| RUI-15 | **Comprimento de linha de 45–75 caracteres**; alinhe pela linha de base quando misturar tamanhos; números alinhados à direita em tabelas. | `--measure: 65ch`; colunas numéricas à direita em mono tabular. |
| RUI-16 | **Tracking**: aperte títulos grandes, abra textos em caixa alta pequenos. | `--tracking-tight` em ≥ 20 px; `--tracking-caps` (0,06 em) em rótulos caixa alta. |
| RUI-17 | **Precisa de mais cores do que imagina, definidas de antemão** (8–10 tons de cinza, 5–10 do primário, tons por semântica); não derive com `lighten()` na hora. | Rampa neutra de 10 tons + 4 tons por cor semântica (`subtle`, base, `strong`/`hover`, `ink`). |
| RUI-18 | **Cinzas não precisam ser cinzas**: dê matiz (quente ou fria) e aumente a saturação perto dos extremos de luminosidade. | Neutros a ~40° de matiz, saturação de 8 % (meio) a 28 % (papel). |
| RUI-19 | **Não use texto cinza sobre fundo colorido**; use a mesma matiz mais escura/mais clara. | Badge OK usa verde-escuro sobre verde-claro, nunca cinza sobre verde. |
| RUI-20 | **Acessível não precisa ser feio**: inverta o contraste (texto escuro sobre fundo claro da mesma cor) quando o fundo forte não funcionar. | Badges/avisos semânticos em `*-ink` sobre `*-subtle`; badge de alerta em tinta sobre âmbar. |
| RUI-21 | **Não dependa só da cor**: acrescente ícone, texto ou forma. | Alerta = ícone + texto + cor (constituição IV); CategoryBar sempre com legenda textual. |
| RUI-22 | **Emule uma fonte de luz; sombra comunica elevação** — quanto mais alto, maior a sombra. Mesmo designs "chapados" podem ter profundidade com sombras sólidas e sobreposição. | Três níveis de sombra sólida deslocada (2/4/6 px): botão → cartão interativo/toast → diálogo. Botão "afunda" ao ser pressionado. |
| RUI-23 | **Use menos bordas**: separe com espaço, fundo diferente ou sombra antes de recorrer a mais uma borda. | Borda em tinta só no **contorno** de objetos (campo, cartão, tabela). Dentro da tabela: filetes horizontais sutis, sem linhas verticais nem zebra. |
| RUI-24 | **Adicione cor com bordas de destaque** (topo de cartão, lateral de alerta, sublinhado do item ativo). | Barra de 3 px no item de navegação ativo; borda lateral de 4 px em toasts/avisos; topo de 4 px no KPI em alerta; borda esquerda âmbar na linha de tabela em alerta. |
| RUI-25 | **Projete os estados vazios** — são a primeira impressão; ofereça a próxima ação e esconda controles inúteis (filtros, cabeçalhos) quando não houver dados. | Componente `estado_vazio` obrigatório em listas; o Painel nasce com estado vazio útil. |
| RUI-26 | **Supere os padrões do navegador**: substitua marcadores por ícones, dê hierarquia dentro de células, combine colunas. | Célula "Produto" com nome + ID atenuado; situação como badge; não há tabela "crua". |
| RUI-27 | **Ícones no tamanho para o qual foram desenhados**; não amplie ícones pequenos — envolva-os em uma forma. | Lucide a 16/20 px; ícone do estado vazio em caixa de 40 px com borda, não ampliado. |

---

## Síntese: como as referências se combinam

```text
        Refactoring UI ──► regras de decisão (hierarquia, espaço, cor, profundidade)
                │
   ┌────────────┼─────────────────────────────┐
   ▼            ▼                             ▼
 Carbon       shadcn/ui                     Tremor
 (escala,     (contrato semântico          (componentes de
  densidade,   de tokens, anatomia           dados textuais)
  camadas,     e estados)
  tipografia)
   └────────────┬─────────────────────────────┘
                ▼
   design-resources-for-developers ──► seleção de Plex, Lucide, ferramentas de contraste
                ▼
   Neo-brutalismo sóbrio (decisão própria): tinta 1 px, raio 0–2 px, sombras sólidas,
   papel quente, um acento ultramar, alerta âmbar inconfundível.
```

**O que torna o Consus "não genérico"**: (1) papel quente e tinta em vez de branco e cinza frio;
(2) sombras sólidas deslocadas em vez de sombras difusas; (3) cantos retos; (4) números em mono
tabular dominando KPIs e tabelas; (5) um único acento ultramar, usado com parcimônia (ação
primária, foco, item ativo, barras); (6) o alerta de reposição como o elemento mais forte da tela
(âmbar + tinta + ícone + caixa alta).
