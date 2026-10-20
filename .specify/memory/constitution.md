# Consus Constitution

> *Consus* — divindade romana guardiã dos grãos armazenados nos celeiros subterrâneos.
> O sistema guarda o estoque com o mesmo zelo: nada entra ou sai sem registro.

## Core Principles

### I. Integridade do Estoque (NÃO-NEGOCIÁVEL)

- O saldo de um produto MUST nunca ficar negativo. A regra é garantida em três camadas
  independentes: validação de formulário, serviço de domínio transacional com bloqueio de
  linha (`select_for_update`) e `CheckConstraint` no banco de dados.
- Toda alteração de saldo MUST acontecer por meio de uma Movimentação registrada
  (entrada ou saída). É proibido editar o saldo diretamente por formulário, admin ou shell.
- Movimentações são imutáveis (livro-razão *append-only*): guardam saldo anterior e
  posterior, e nunca são editadas ou apagadas pela interface.
- Quantidades são números inteiros; quantidade de movimentação MUST ser maior que zero.

*Racional*: o requisito central da atividade é "o estoque não pode ficar negativo". Uma
única camada de validação falha sob concorrência (duas saídas simultâneas); três camadas
e um histórico imutável tornam o saldo auditável e reproduzível.

### II. Interface Dirigida pelo Servidor (Django + HTMX)

- O HTML é renderizado no servidor (Django Templates). Interatividade usa HTMX 2:
  respostas parciais (`partials/`), `hx-swap-oob` para atualizar regiões dependentes
  (saldo, badge de alertas, toasts) e `HX-Trigger` para eventos.
- Sem SPA, sem framework JavaScript e sem etapa de build Node. JavaScript próprio é
  limitado a pequenos utilitários progressivos (< 100 linhas no total).
- Toda ação MUST funcionar sem HTMX (aprimoramento progressivo): formulários fazem POST
  normal com redirect; com HTMX recebem apenas o fragmento.
- Views detectam `request.htmx` (django-htmx) para escolher template completo ou parcial.

*Racional*: HTML sobre o fio mantém a lógica em um só lugar (Python), reduz a superfície
de erros e é o stack pedido para o projeto.

### III. Testes Primeiro nas Regras de Negócio (NÃO-NEGOCIÁVEL)

- Cada requisito funcional (FR-xxx) MUST ter ao menos um teste automatizado que o
  referencie no nome ou docstring.
- Regras de domínio (cadastro, movimentação, saldo, alerta) são escritas em serviços /
  querysets testados *antes* da view (Red → Green → Refactor).
- Cobertura mínima: 90% em `services.py`, `models.py` e `selectors.py`; a suíte completa
  MUST passar antes de qualquer merge em `develop`.
- Testes de view verificam as duas variantes: requisição comum e requisição HTMX.

*Racional*: a atividade é avaliada pelo comportamento das regras; testes provam isso.

### IV. Design System — High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise

A interface segue um sistema visual próprio, derivado das referências
**shadcn-ui/ui** (tokens semânticos e anatomia de componentes), **tremorlabs/tremor**
(KPIs, BarList, CategoryBar, Tracker para dados), **IBM/carbon** (grid 2x de 8px, IBM Plex,
densidade de tabelas, tokens de camada) e **bradtraversy/design-resources-for-developers**
(curadoria de fontes/ícones/paletas), aplicando os princípios do **Refactoring UI**
(Adam Wathan & Steve Schoger). Regras obrigatórias:

- **Tokens primeiro**: cores, espaçamentos, tipografia, bordas e sombras MUST vir de CSS
  custom properties em um único arquivo de tokens; valores mágicos em componentes são
  proibidos.
- **Grid suíço**: grade de 12 colunas, espaçamento em múltiplos de 4/8px, alinhamento à
  esquerda, sem centralização decorativa.
- **Neo-brutalismo sóbrio**: bordas sólidas de 1px (2px em foco/destaque), raio 0–2px,
  sombras sólidas deslocadas sem desfoque apenas em elementos elevados/interativos,
  paleta neutra (tinta sobre papel) com UMA cor de acento e cores semânticas
  (sucesso, alerta, perigo). Sem gradientes, sem glassmorphism, sem emojis como ícones.
- **Alta densidade**: tabelas com linhas de 32–40px, números em fonte mono tabular
  (`font-variant-numeric: tabular-nums`) alinhados à direita, rótulos curtos em caixa alta
  com tracking.
- **Hierarquia (Refactoring UI)**: hierarquia por peso e cor antes de tamanho; texto
  secundário com cor atenuada e não com fonte menor; ações primárias evidentes, secundárias
  discretas, destrutivas apenas na confirmação; estados vazios projetados; rótulos só
  quando necessários.
- **Acessibilidade**: contraste mínimo WCAG 2.1 AA; foco visível; alerta de reposição
  SEMPRE com ícone + texto ("REPOSIÇÃO NECESSÁRIA") + cor — nunca apenas cor;
  `aria-live` para mensagens dinâmicas.
- **Idioma**: interface em português do Brasil; datas `dd/mm/aaaa HH:MM`, números com
  separador de milhar `.`.

*Racional*: evitar a aparência genérica de templates; densidade e clareza servem ao
operador de estoque que precisa ler muitos itens rapidamente.

### V. Simplicidade, Containers e Configuração 12-Factor

- O sistema inteiro MUST subir com `docker compose up --build` (app + PostgreSQL), sem
  passos manuais além de copiar `.env.example`.
- Configuração exclusivamente por variáveis de ambiente; segredos nunca versionados.
- Sem dependências que não resolvam um requisito explícito (YAGNI). Toda dependência nova
  é justificada no `plan.md` da feature.
- Assets de terceiros (HTMX, fontes) são servidos localmente (vendorizados), sem CDN em
  tempo de execução.

*Racional*: o professor e os colegas precisam rodar o projeto em qualquer máquina.

## Restrições Técnicas

- **Linguagem/Runtime**: Python 3.13.
- **Framework**: Django 5.2 LTS + django-htmx; HTMX 2.x vendorizado em `static/vendor/`.
- **Banco**: PostgreSQL 17 no Docker; SQLite permitido apenas para desenvolvimento local e
  testes rápidos (a suíte MUST passar nos dois).
- **Servidor**: Gunicorn + WhiteNoise para estáticos.
- **Qualidade**: pytest + pytest-django + pytest-cov; Ruff (lint + format).
- **Domínio em português**: entidades e campos de domínio em português (`Produto`,
  `Movimentacao`, `estoque_minimo`); infraestrutura pode usar termos em inglês.
- **Estrutura**: projeto `config/`, apps em `apps/` (`core`, `produtos`, `movimentacoes`,
  `alertas`), templates por app, design system em `static/css/`.

## Fluxo de Desenvolvimento

- **Spec-Driven Development (GitHub Spec Kit)**: cada atividade da proposta vira uma
  feature `specs/NNN-slug/` com `spec.md` → `plan.md` → `tasks.md` antes de qualquer código.
  `/speckit-analyze` MUST ser executado antes da implementação.
- **Branches**: cada feature usa a branch `NNN-slug` (padrão Spec Kit), criada a partir de `develop`; merge `--no-ff` em
  `develop` após testes verdes; `main` recebe apenas merges de `develop` (releases).
  Commits diretos em `main` são proibidos.
- **Commits**: Conventional Commits em português (`feat:`, `fix:`, `docs:`, `test:`,
  `chore:`), um assunto por commit.
- **Quality gates** antes de merge: `ruff check`, `ruff format --check`, `pytest` verde,
  `python manage.py makemigrations --check`, build Docker bem-sucedido.

## Governance

- Esta constituição prevalece sobre qualquer outra prática do repositório. Planos
  (`plan.md`) MUST conter a seção *Constitution Check* e justificar qualquer violação na
  tabela *Complexity Tracking*.
- Emendas: alteração via PR para `develop` contendo o motivo, o impacto nos templates e o
  incremento de versão semântico (MAJOR: remoção/redefinição de princípio; MINOR: novo
  princípio ou seção; PATCH: redação).
- Revisões verificam: princípio I em toda mudança que toque saldo; princípio IV em toda
  mudança de interface; princípio III em toda mudança de regra.
- Orientação de execução para agentes fica em `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-10-20 | **Last Amended**: 2026-10-20
