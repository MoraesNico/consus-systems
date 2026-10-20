# Consus — Auditoria das especificações (pré-implementação)

**Data**: 2026-10-20 · **Branch**: `auditoria-especificacoes` (a partir de `develop`) ·
**Escopo**: `specs/001-fundacao-design-system`, `specs/002-cadastro-produtos`,
`specs/003-movimentacao-estoque`, `specs/004-alerta-reposicao` (spec, plan, tasks, data-model,
contracts, research, quickstart, checklists).

**Fontes de verdade, em ordem**: (1) a atividade do professor (SENAI-SP); (2)
`.specify/memory/constitution.md` v1.0.0; (3) `docs/arquitetura.md`, seção "Decisões consolidadas
(v1.1)"; (4) `docs/design/design-system.md`.

**Método**: `/speckit-analyze` (`.claude/skills/speckit-analyze/SKILL.md`) aplicado manualmente a
cada feature — inventário de FR/SC, mapeamento FR → tarefa → teste, passes de duplicação,
ambiguidade, subespecificação, alinhamento à constituição, cobertura e inconsistência — seguido
de uma passada **entre features** (002↔003, 002↔004, 003↔004 e 001↔todas) com busca textual
pelos nomes do contrato (rotas, templates, funções, eventos, IDs, parâmetros e campos). Os
ganchos `before_analyze`/`after_analyze` da extensão git são opcionais (auto-commit); os commits
foram feitos manualmente, separados por assunto. A atividade foi rastreada em
[`rastreabilidade.md`](rastreabilidade.md).

Severidade (heurística do `/speckit-analyze`): **CRITICAL** = viola um MUST da constituição ou
bloqueia funcionalidade básica; **HIGH** = conflito entre artefatos que quebraria a integração;
**MEDIUM** = deriva de terminologia, lacuna não funcional ou caso de borda subespecificado;
**LOW** = redação ou melhoria menor. Todos os achados abaixo foram **corrigidos**, exceto os
marcados como pendência consciente.

---

## 1. Achados por feature

### 1.1 Transversais (entre features)

| ID | Sev. | Local | Resumo | Ação tomada |
|----|------|-------|--------|-------------|
| X1 | CRITICAL | 001/T024, T026; 002/T039, T028; 003/T050; `apps/core/tests/test_painel.py` (001) × 004 | Testes de uma feature que quebram quando a seguinte é integrada: navegação/painel da 001 testados no urlconf **real** "sem seções"; região de histórico da 002 testada como vazia (a 003 a preenche); orçamentos de consultas medidos na página completa (a 004 acrescenta o `COUNT` do contador); painel da 001 substituído pela 004 sem tarefa de atualizar o teste. A suíte completa não passaria no merge seguinte — viola a constituição III ("a suíte completa MUST passar antes de qualquer merge em `develop`"). | 001 ganha o urlconf de teste `urls_somente_core` (T022/T024/T026); 002/T039 pula quando `apps.movimentacoes` está instalado; orçamentos medidos no fragmento (002/T028, 003/T050); 004/T045 atualiza `test_painel.py`; a tag do contador não renderiza sem a rota `alertas:contador`. |
| X2 | MEDIUM | todas as `tasks.md` | Nenhum teste percorria a atividade de ponta a ponta (cadastro → movimentação → alerta) atravessando as features. | Nova tarefa 004/T064 (fluxo da atividade por HTTP e terminal, variantes comum e HTMX) e matriz `docs/rastreabilidade.md`. |
| X3 | LOW | `docs/arquitetura.md` (árvore de diretórios) | Erro objetivo do contrato: o comentário de `templates/components/` lista "botões" e "tabela" como templates, contradizendo a própria decisão v1.1 "botões e tabelas são classes CSS". | Comentário corrigido — **única** alteração no contrato. |
| X4 | LOW | `docs/design/design-system.md` §4.4.1, §4.10, §4.15, §4.16 | Textos divergentes do contrato v1.1: situação "calculada pela 004", contador "com reposição necessária", paginação sem `pagina`/`outerHTML`, badge da navegação ligado ao contêiner. | Design system 1.1.0 (MINOR: parâmetro opcional `sufixo` no ProgressBar, classe `.contador-alertas`; sem mudança de token nem de contraste). |

### 1.2 Feature 001 — Fundação e design system

| ID | Sev. | Local | Resumo | Ação tomada |
|----|------|-------|--------|-------------|
| A1 | HIGH | spec FR-014; contracts/layout-e-htmx §5; data-model §4; research R9; tasks T024, T031, T033 | O "slot do badge" fazia polling próprio (`load, …, every 60s`, `innerHTML`) e previa OOB `innerHTML:#badge-alertas`; a 004 desenha `#contador-alertas` (30 s, `outerHTML`, 204) — dois mecanismos e dois *pollers* para a mesma região. | Mecanismo único (v1.1): `#badge-alertas` é contêiner vazio, sem `hx-*`; a 004 renderiza `{% contador_alertas %}` dentro dele; OOB mira `#contador-alertas`. FR-014 reescrito (30 s); `badge_alertas_url` removido. |
| A2 | HIGH | contracts/layout-e-htmx §3–§4; research R6–R8; tasks T025, T029, T061 | API HTMX divergente da v1.1: `eh_parcial` (ignorava restauração de histórico), `fechar_dialogo(response)` e `disparar_toast(response, texto, nivel="sucesso")`. | `eh_fragmento`, `disparar_evento(response, nome, dados=None)` e `disparar_toast(response, nivel, texto)` em contrato, pesquisa, testes e implementação. |
| A3 | HIGH | contracts/componentes (`paginacao.html`); T046, T058 | O componente compartilhado gerava `{% querystring page=n %}` — as listas da 002/003 leem `pagina`: a paginação quebraria. | `pagina` + `hx-swap="outerHTML"` (fragmento com o alvo como raiz); teste em T046. |
| A4 | HIGH | contracts/componentes (`badge_estoque.html`) | O exemplo `situacao=produto.situacao` passa o valor binário da 002 (`"alerta"`/`"ok"`) a um componente que espera `ok\|reposicao\|sem_estoque` e não renderiza valor desconhecido — o alerta obrigatório sumiria em silêncio. | Exemplo corrigido; o mapeamento fica no selo único `produtos/partials/situacao.html` (002). |
| A5 | HIGH | contracts/layout-e-htmx §1, §8; tasks T023, T036, T039 | Pontos fixos da v1.1 ausentes na dona do `base.html`/`consus.js`: região `#anuncio-alertas` e manipulador genérico `data-atalho`; 002 e 004 planejavam acrescentá-los "se ausentes" em arquivos da 001. | Novo **FR-045** (atalhos), `#anuncio-alertas` em FR-014/T036, testes em T023; 002/004 apenas verificam. |
| A6 | MEDIUM | tasks T002, T009, T078 | Marcador `postgres` (v1.1) não registrado pela dona do `pyproject.toml`; a 003 planejava editá-lo e a 002 usava `skipif`. | Registro + pulo automático no SQLite pelo `conftest.py` raiz; T078 verifica. |
| A7 | LOW | spec (Assumptions); checklists/ux CHK042 | "Situação calculada pela feature 004" — pela v1.1 a regra é da 002. | Corrigido. |
| A8 | LOW | contracts/rotas-core; T047, T061 | `/design/?exemplo=dialogo` tem variantes sem `Vary: HX-Request, HX-Target`. | `vary_on_headers` e teste. |
| A9 | LOW | data-model §8; T060 | O formulário de exemplo (`IntegerField`) aceitaria "+5", diferente da regra "só dígitos" que ele demonstra às features. | Regra `^[0-9]+$`. |
| A10 | LOW | contracts/layout-e-htmx §5 | Texto acessível do contador ("com reposição necessária") diferente do da 004 ("em alerta de reposição"). | Alinhado ao da 004. |

### 1.3 Feature 002 — Cadastro de produtos

| ID | Sev. | Local | Resumo | Ação tomada |
|----|------|-------|--------|-------------|
| B1 | HIGH | plan; contracts/fragmentos-e-eventos, rotas-http; research R10; tasks T010, T022 | Evento `dialogo-fechar`; o `consus.js` da 001 escuta `fechar-dialogo` — o diálogo de cadastro não fecharia. | Renomeado para `fechar-dialogo`. |
| B2 | HIGH | contracts/fragmentos-e-eventos, rotas-http; research R12; tasks T039, T043, T045 | IDs `#produto-resumo` (`<div>`) e `#produto-movimentacoes` ≠ `#produto-<id>-resumo` e `#produto-<id>-historico` usados pela 003 nos OOB — trocas sem alvo. | IDs da v1.1, raiz `<section>`, suporte a `oob` em `linha.html` e `resumo.html`. |
| B3 | MEDIUM | spec FR-020; contracts (selo); T011, T015 | Selo sem a variação SEM ESTOQUE da v1.1 e sem delegar ao `badge_estoque` da 001; a 004 planejava editar o parcial depois. | Selo único com as três variações na 002 (SEM ESTOQUE composto); a 004 não o altera. |
| B4 | MEDIUM | spec FR-031; contracts/rotas-http, fragmentos | A edição não emitia `estoque-alterado` (v1.1: "cadastro, movimentação e edição do estoque mínimo") e a regra não distinguia fragmento × página inteira. | FR-031: toda resposta parcial de cadastro/edição emite o evento; página inteira re-renderiza o contador. |
| B5 | MEDIUM | tasks T022 | Helper local `_variante` e `HX-Trigger` via `django_htmx.http` em vez dos helpers da 001. | `eh_fragmento`, `disparar_evento`, `disparar_toast`. |
| B6 | MEDIUM | plan; tasks T024, T025, T060 | Edições condicionais ("se ausente") em `templates/base.html`, `static/js/consus.js` e `components.css` da 001; estados visuais novos ("linha nova", `kbd`) sem proposta prévia no design system. | `base.html`/`consus.js` não são tocados (tarefas viram testes de verificação); T025 propõe a variante no design system (MINOR) e só então estende o CSS. |
| B7 | MEDIUM | contracts/fragmentos; T034 | Paginação própria em vez do componente `paginacao.html` da 001. | Usa o componente (`alvo="#resultados"`). |
| B8 | MEDIUM | quickstart; T067 | `docker compose exec web pytest`: o serviço é `app` e a imagem de produção não tem `pytest`. | Serviço `testes` (perfil) e `app`. |
| B9 | LOW | contracts/rotas-http, fragmentos | `estoque-alterado` com carga `{}`; v1.1 define `{produto_id, saldo_anterior, saldo_posterior}` (opcional). | Carga preenchida no cadastro. |
| B10 | LOW | T008 | Teste só-PostgreSQL com `skipif` em vez do marcador `postgres`. | Marcador. |
| B11 | LOW | T011 | Decisão `\|unlocalize` (IDs ≥ 1000 em atributos) sem teste. | Teste acrescentado (cobertura). |
| B12 | LOW | T002, T003 | Condicional "ou módulo base equivalente" (a 001 define um único `config/settings.py`). | Removida; tarefas dizem "estender". |

### 1.4 Feature 003 — Movimentação de estoque

| ID | Sev. | Local | Resumo | Ação tomada |
|----|------|-------|--------|-------------|
| C1 | HIGH | plan; contracts/integracao-produtos; tasks T026, T028, T029 | Partials `linha_produto.html`/`resumo_produto.html` (inexistentes na 002) e tarefa "criar/ajustar" o resumo — dois arquivos para o mesmo papel. | `produtos/partials/linha.html` e `resumo.html`; tarefas "estender". |
| C2 | HIGH | contracts/integracao-produtos; T028, T029 | `{{ produto.id }}` em IDs e URLs sem `\|unlocalize`: com `USE_THOUSAND_SEPARATOR` o ID 1234 vira `produto-1.234` e o OOB falha. | `\|unlocalize` em todos os atributos. |
| C3 | HIGH | spec FR-012/013/015; contracts/rotas-movimentacoes; T018, T020, T022, T023, T026 | `movimentacoes:nova` sem `origem=alertas` e sem `quantidade` (v1.1); a 004 planejava alterar `forms.py` e `sucesso_dialogo.html` da 003. | A 003 implementa os dois (ramo sem OOB; pré-preenchimento 1…1.000.000), com testes; a 004 só usa. |
| C4 | MEDIUM | contracts/rotas-movimentacoes; research R11; T032, T037 | Paginação com `page` (v1.1: `pagina`). | `pagina` + componente da 001. |
| C5 | MEDIUM | research R6; contracts/rotas; T014, T018 | `QuantidadeField` aceitava "+5" (`^[+-]?\d+$`) e usava `type="number"` (o navegador descarta "2,5"/"+5" e troca a mensagem) — diverge da 002 e da v1.1. | `^[0-9]+$`, `type="text" inputmode="numeric"`, "+5" recusado e testado. |
| C6 | MEDIUM | data-model; T009, T017 | Constante `QUANTIDADE_MAXIMA = 1_000_000` homônima de `produtos.models.QUANTIDADE_MAXIMA = 2.147.483.647` (v1.1); `SALDO_MAXIMO` redefinido como literal. | `QUANTIDADE_MAXIMA_MOVIMENTACAO`; `SALDO_MAXIMO` importado da 002. |
| C7 | MEDIUM | data-model; research R15; T007 | Selo do tipo com variantes `sucesso`/`neutro-forte` inexistentes no design system. | Sugestão do design system §4.4.2 (`info` + ícone; `neutro`). |
| C8 | MEDIUM | contracts/rotas-movimentacoes; T036 | Lista trocava `#resultados` por `innerHTML`; a 002 usa `outerHTML` com o próprio alvo como raiz — o componente de paginação compartilhado não serviria às duas. | Convenção única: fragmento com raiz `#resultados` e `outerHTML`. |
| C9 | MEDIUM | plan; T002, T004, T005, T049 | Edições condicionais em `config/`, `pyproject.toml` e `templates/base.html` da 001 ("se ainda ausente"). | "Estender" sem condicional; marcador e navegação ficam na 001 (T005/T049 viram verificação). |
| C10 | MEDIUM | quickstart; contracts/comando-movimentar; T053 | `docker compose exec web` (serviço `app`; `pytest` só no serviço `testes`). | Corrigido. |
| C11 | MEDIUM | T028 | A célula de ações entrava na linha sem o cabeçalho correspondente em `resultados.html` (002). | T028 estende também o cabeçalho "Ações". |
| C12 | LOW | contracts/rotas; research R7, R9, R16; T020, T027, T037 | `request.htmx and not request.htmx.boosted` e `trigger_client_event` direto, sem `Vary`. | Helpers da 001 e `Vary: HX-Request, HX-Target`. |
| C13 | LOW | data-model; T007 | `mensagem_confirmacao` sem garantia frente ao limite de 200 caracteres do toast da 001. | Limite documentado e testado. |

### 1.5 Feature 004 — Alerta de reposição

| ID | Sev. | Local | Resumo | Ação tomada |
|----|------|-------|--------|-------------|
| D1 | CRITICAL | spec FR-018, FR-020, US1-2, US2-2, US2-6; contracts/fragmentos §1, §6; data-model §3; T011, T016; quickstart | Selo SEM ESTOQUE só com o texto "SEM ESTOQUE" (`badge--perigo`) e aviso de toast "SEM ESTOQUE: …" sem "REPOSIÇÃO NECESSÁRIA" — viola a constituição IV ("alerta de reposição SEMPRE com ícone + texto 'REPOSIÇÃO NECESSÁRIA' + cor") e a v1.1 (selo composto). | Selo composto "⚠ REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE" pelo selo único da 002; FR-003/009/018/020 reescritos; aviso "REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: …". |
| D2 | HIGH | contracts/fragmentos §2; plan; T024, T038 | Contador inserido em `templates/base.html` num `<a class="menu__item">` próprio, ignorando `components/navegacao.html` e o contêiner `#badge-alertas` da 001; a 004 também criava `#anuncio-alertas`. | Estende `navegacao.html` dentro de `#badge-alertas`; `#anuncio-alertas` é da 001. |
| D3 | HIGH | plan; contracts/fragmentos §3, http-alertas, http-painel; research R13; T022, T023, T044 | Componentes novos `barra_cobertura.html` e `bar_list.html` e classes `.selo-situacao`, `.barra-cobertura`, `.bar-list`, `.contador-alertas` duplicavam ProgressBar, BarList e badge da 001. | Reutiliza `barra_progresso.html` (+ parâmetro opcional `sufixo`, MINOR na 001) e `badge_estoque.html`; CSS do contador na 001; nenhuma classe nova. |
| D4 | HIGH | spec FR-019; contracts/fragmentos §6, consultas-e-regras | O toast composto (mensagem da 003 + aviso com o nome do produto) pode passar de 200 caracteres: `disparar_toast` levantaria `ValueError` (erro 500). | Limite de 200 com nome encurtado ("…", `#ID` mantido) e teste em T031. |
| D5 | MEDIUM | contracts/http-painel; research R12; T042, T045, T046 | Região `#painel-conteudo`/`painel_conteudo.html` ≠ `#painel-kpis`/`painel_kpis.html` previstos pela 001. | Nomes da 001; T045 atualiza o teste do painel. |
| D6 | MEDIUM | contracts/http-alertas; T029, T036 | Contador oculto por `:empty`, mas o template com quebras de linha nunca fica "vazio" para o CSS. | Atributo `hidden` quando o total é 0. |
| D7 | MEDIUM | contracts/fragmentos §1; T005, T016 | Ícone "SVG `alerta`" inexistente no sprite da 001 (`triangle-alert`, `octagon-x`). | Nomes do sprite. |
| D8 | MEDIUM | spec FR-011; contracts/fragmentos §4; T019, T021 | "+ Entrada" sem o parâmetro `quantidade` da v1.1; sugestão acima de 1.000.000 não tratada. | `quantidade = min(sugestão, 1.000.000)`; omitida se 0. |
| D9 | MEDIUM | quickstart; contracts/cli; plan | `docker compose exec web` e `DJANGO_DATABASE_URL` (variável inexistente na 001). | `app`, `testes` e `uv run pytest` (SQLite sem `DATABASE_URL`). |
| D10 | MEDIUM | plan; T025 | A 004 alterava `forms.py` e `sucesso_dialogo.html` da 003 — pela v1.1 o dono de `movimentacoes:nova` é a 003. | T025 vira verificação (ver C3). |
| D11 | LOW | contracts/http-*; research R8; T028, T046 | Fragmento por `request.htmx and not boosted` e `Vary: HX-Request` apenas. | `eh_fragmento` e `Vary: HX-Request, HX-Target`. |
| D12 | LOW | spec (Edge Cases), FR-015 | Edição do mínimo refletida "na próxima verificação automática"; v1.1 emite `estoque-alterado` também no cadastro e na edição. | Reescrito: imediato; FR-015 inclui cadastro e edição. |
| D13 | LOW | contracts/fragmentos §3–§4 | Classes inexistentes `botao--compacto` e `numero`. | `botao--secundario botao--sm`, `.num`. |
| D14 | LOW | contracts/consultas-e-regras; data-model; T006, T012 | `Situacao.variante`/`variante_barra` com vocabulário próprio (`neutro\|alerta\|perigo`) ≠ componentes (`ok\|reposicao\|sem_estoque`). | Vocabulário único em `Situacao.variante`. |
| D15 | LOW | T007 | Proibição da v1.1 de propriedades `alerta`/`deficit`/`cobertura_percentual` no modelo sem teste. | Teste acrescentado (cobertura). |
| D16 | LOW | checklists/ux CHK018 | Regra de singular/plural ("1 produto" × "produto(s)") não definida. | **Pendência consciente** (§4). |

## 2. Métricas

| Feature | FRs | SCs | Tarefas | Tarefas de teste | FRs com ≥ 1 tarefa | FRs com teste | CRITICAL | HIGH | MEDIUM | LOW |
|---------|----:|----:|--------:|-----------------:|-------------------:|--------------:|---------:|-----:|-------:|----:|
| 001 | 45 (44 + FR-045) | 10 | 88 | 19 | 100 % | 100 % | 0 | 5 | 1 | 4 |
| 002 | 31 | 9 | 69 | 16 | 100 % | 100 % | 0 | 2 | 6 | 4 |
| 003 | 33 | 8 | 54 | 21 | 100 % | 100 % | 0 | 3 | 8 | 2 |
| 004 | 37 | 9 | 64 (63 + T064) | 29 | 100 % | 100 % | 1 | 3 | 6 | 6 |
| Transversais | — | — | — | — | — | — | 1 | 0 | 1 | 2 |
| **Total** | **146** | **36** | **275** | **85** | **100 %** | **100 %** | **2** | **13** | **22** | **18** |

- **Achados**: 55 (2 CRITICAL, 13 HIGH, 22 MEDIUM, 18 LOW); **corrigidos**: 54; **pendência
  consciente**: 1 (D16, LOW).
- **Por categoria**: inconsistência/terminologia 27 · subespecificação 13 (inclui A5, que também
  fecha uma lacuna de cobertura) · duplicação ou arquivo com dois donos 7 · constituição 2 (D1,
  X1) · cobertura 3 (X2, B11, D15) · ambiguidade 3 (B12, D12, D16).
- **FR → teste**: antes da auditoria, 145/145 FRs já tinham tarefa de teste; o FR novo (001/FR-045)
  nasceu com teste (001/T023). Critérios de sucesso que exigem trabalho construível têm tarefa;
  SC de medição manual (001/SC-001, SC-006, SC-008; 002/SC-009; 003/SC-001, SC-005) ficam nos
  quickstarts.
- **Atividade**: 17/17 requisitos atômicos **Cobertos** ([`rastreabilidade.md`](rastreabilidade.md)).

## 3. Correções aplicadas

Commits na branch `auditoria-especificacoes`:

1. `docs(specs): alinha as quatro features ao contrato v1.1` — consistência (achados X1, X3, X4,
   A1–A10, B1–B10, B12, C1–C13, D1–D14):
   - helpers `eh_fragmento`, `disparar_evento`, `disparar_toast(response, nivel, texto)` e
     `Vary: HX-Request, HX-Target` em todas as features;
   - `fechar-dialogo`; `estoque-alterado` no cadastro, na edição (respostas de fragmento) e na
     movimentação, com carga opcional;
   - `produtos/partials/linha.html` → `#produto-<id>`, `produtos/partials/resumo.html` →
     `#produto-<id>-resumo`, região `#produto-<id>-historico`, todos com `oob` e `|unlocalize`;
   - `pagina` em todas as listas e no componente de paginação; fragmento de lista com raiz
     `#resultados` e `hx-swap="outerHTML"`;
   - contador de alertas com mecanismo único (contêiner `#badge-alertas` da 001 +
     `#contador-alertas` da 004, 30 s, `outerHTML`, 204, `hidden` quando 0) e `#anuncio-alertas`
     na 001; atalhos `data-atalho` na 001 (FR-045);
   - selo único `produtos/partials/situacao.html` (002) com OK, REPOSIÇÃO NECESSÁRIA e SEM
     ESTOQUE composto; a 004 reutiliza `badge_estoque` e `barra_progresso` da 001;
   - 003 com `origem=alertas`, `quantidade` pré-preenchida, entrada só por dígitos e
     `QUANTIDADE_MAXIMA_MOVIMENTACAO`; painel da 004 em `#painel-kpis`;
   - marcador `postgres` na 001; serviços `app`/`testes` do Compose; tarefas que tocam arquivos
     de outra feature passam a "estender", sem condicionais "se ausente";
   - limite de 200 caracteres dos toasts compostos;
   - design system 1.1.0 e checklists afetados (001/ux, 002/ux, 002/integridade, 003/ux,
     003/integridade, 004/regra-alerta — CHK032 e CHK033 fechados —, 004/ux).
2. `docs(specs): acrescenta tarefas de teste para lacunas de cobertura` — cobertura (X2, B11,
   D15): 004/T064 (ponta a ponta da atividade), 004/T007 (propriedades proibidas), 002/T011
   (`|unlocalize`).
3. `docs: adiciona matriz de rastreabilidade da atividade` — `docs/rastreabilidade.md`.
4. `docs: adiciona relatório da auditoria de especificações` — este documento.

Os `research.md` mantêm as propostas originais como registro histórico, agora com uma nota de
**status** e os nomes superados riscados ao lado do nome do contrato v1.1.

## 4. Pendências conscientes

| Item | Por que fica | Quem decide |
|------|--------------|-------------|
| D16 — singular/plural nas contagens ("produto(s)") | Impacto baixo (texto); os contratos usam a forma neutra de forma consistente; definir a regra exigiria mexer em mensagens de três superfícies sem ganho funcional. | Revisor de UX, antes da 004. |
| Redação antiga em `docs/arquitetura.md` ("Convenções HTMX": "`hx-swap-oob` para atualizar … o badge de alertas"; "`estoque-alterado` (após qualquer movimentação)") | Não é erro objetivo: a seção "Decisões consolidadas (v1.1)" prevalece e as specs seguem a v1.1. Sugestão ao coordenador: reescrever essas duas linhas e explicitar que `estoque-alterado` é emitido nas respostas de **fragmento** (página inteira re-renderiza o contador). | Coordenador do contrato. |
| Formatação de `docs/arquitetura.md` (linha "Exibição do ID" da tabela v1.1) | A barra vertical de `\|unlocalize` dentro da célula não está escapada e divide a célula na renderização Markdown; o conteúdo é inequívoco e foi aplicado nas specs, então o contrato não foi tocado além de X3. Sugestão: escrever `\\|unlocalize`. | Coordenador do contrato. |
| Variante "linha recém-cadastrada", selo "NOVO" e `<kbd>` no design system | Decisão visual da 002, agora tarefa explícita (002/T025, MINOR no design system antes do CSS). | Implementação da 002. |
| Critérios de sucesso de medição manual (001/SC-001, SC-006, SC-008; 002/SC-009; 003/SC-001, SC-005) | Dependem de pessoas/cronômetro; ficam nos roteiros dos quickstarts. | Validação de cada PR. |
| `bulk_create` nos testes de volume (003/T050, 004/T059) | Apenas *setup* de teste com dados coerentes (justificado nos `research.md`); não é caminho de escrita da aplicação (constituição I preservada). | — |

## 5. Veredito

**Pronto para implementar.** Os dois achados CRITICAL (D1 — selo SEM ESTOQUE sem "REPOSIÇÃO
NECESSÁRIA"; X1 — testes que quebrariam no merge seguinte) e os 13 HIGH foram corrigidos nos
artefatos; as quatro features usam os mesmos nomes de rotas, templates, IDs, eventos, helpers,
parâmetros e limites do contrato v1.1; nenhum arquivo é planejado por duas features de formas
incompatíveis (quem toca arquivo de outra feature o **estende**); todos os FRs têm tarefa de
teste; e os 17 requisitos atômicos da atividade estão cobertos. Ordem de implementação mantida:
001 → 002 → 003 → 004, com a suíte completa verde (SQLite e PostgreSQL) antes de cada merge em
`develop`.
