# Feature 005 — Movimento, transições e paleta sóbria

**Origem**: pedido do cliente ("pouca animação e transição"; "um pouco mais sobre a paleta de cores") · **Contrato**: `docs/arquitetura.md` v1.2, "Movimento e paleta (005)".

## História
Como usuário, quero que o sistema responda com movimento discreto (o que mudou, o que está
carregando, para onde fui) e com uma paleta menos saturada, que canse menos em telas cheias de números.

## Requisitos
- **FR-001** Tokens de movimento (durações até 400 ms, curvas, distâncias) e tokens financeiros (`--color-receita/despesa`, `--color-serie-1…5`).
- **FR-002** Com `prefers-reduced-motion`, durações e distâncias viram 0, e `motion.css` zera o resto.
- **FR-003** `static/css/motion.css` traz os keyframes `consus-*`, as classes `.animar-surgir/tremer/destacar`, o destaque `.htmx-added`, as barras que crescem, o `<dialog>` com `@starting-style` e as View Transitions.
- **FR-004** A casca carrega `motion.css` entre `components.css` e `utilities.css`. A barra `#barra-carregamento` aparece após 150 ms, e `globalViewTransitions` fica ligado.
- **FR-005** Os toasts saem animados (`.toast--saindo`).
- **FR-006** Paleta v2 "sóbria": acento azul-tinta, semânticas terrosas (musgo, ocre, tijolo) e selos de alerta com fundo suave + borda forte. Os 31 pares seguem WCAG AA.

Documentação: `docs/design/design-system.md` v2.0.0 (§2.1 com o porquê de cada cor; §2.11 movimento).
O JavaScript próprio continua abaixo de 200 linhas (constituição 1.1.0).
