# Consus — Matriz de rastreabilidade da atividade

Liga cada requisito da atividade proposta (SENAI-SP) aos requisitos funcionais das features,
às tarefas de implementação, às tarefas de teste e aos critérios de sucesso que o comprovam.
Gerada na auditoria de especificações de 2026-10-20, sobre `develop` após a consolidação do
contrato `docs/arquitetura.md` v1.1 e as correções registradas em
[`auditoria-especificacoes.md`](auditoria-especificacoes.md).

**Legenda**

- `002/FR-013` = requisito funcional FR-013 de `specs/002-cadastro-produtos/spec.md`;
  `002/T030` = tarefa T030 de `specs/002-cadastro-produtos/tasks.md`; `002/SC-002` = critério de
  sucesso. Prefixos: `001` fundação, `002` cadastro, `003` movimentação, `004` alerta.
- **Veredito**: **Coberto** = há FR, tarefa de implementação, tarefa de teste automatizado que cita
  o FR (constituição III) e critério de sucesso mensurável; **Parcial** = falta um desses elos;
  **Ausente** = não há FR.
- Toda tarefa de teste citada é escrita antes da implementação (Red → Green) e cita o FR no nome
  ou na docstring.

## Texto de origem

> Desenvolver um sistema focado em **Controle de Estoque Simples**, porém altamente funcional e
> eficaz (Engenheiro de Software Sênior especialista em Python).
>
> 1. **Cadastro de Novos Produtos** — registrar produto informando Nome, Quantidade Inicial e
>    Estoque Mínimo de Segurança; cada produto ganha um ID numérico automático para facilitar a
>    busca.
> 2. **Controle de Movimentação** — função para atualizar o saldo; registrar Entrada (soma ao
>    estoque atual); registrar Saída/Venda (subtrai do estoque atual); regra de validação: o
>    estoque de um produto não pode ficar negativo.
> 3. **Sistema Automatizado de Alerta de Baixa** — opção de relatório ou varredura automática;
>    cruzar Quantidade Atual com Estoque Mínimo de Segurança; se quantidade ≤ mínimo, exibir um
>    alerta visual destacado (ex.: ⚠ REPOSIÇÃO NECESSÁRIA) para aquele produto.

## Resumo dos vereditos

| ID | Requisito atômico | Veredito |
|----|-------------------|----------|
| G1 | Sistema simples de executar, "altamente funcional" em qualquer máquina | **Coberto** |
| G2 | Eficácia e qualidade de engenharia (Python, testes, gates) | **Coberto** |
| R1.1 | Registrar produto informando **Nome** | **Coberto** |
| R1.2 | … informando **Quantidade Inicial** | **Coberto** |
| R1.3 | … informando **Estoque Mínimo de Segurança** | **Coberto** |
| R1.4 | Cada produto ganha **ID numérico automático** | **Coberto** |
| R1.5 | O ID serve **para facilitar a busca** | **Coberto** |
| R2.1 | **Função** (única) para atualizar o saldo | **Coberto** |
| R2.2 | Registrar **Entrada** (soma ao estoque atual) | **Coberto** |
| R2.3 | Registrar **Saída/Venda** (subtrai do estoque atual) | **Coberto** |
| R2.4 | Validação: o estoque **não pode ficar negativo** | **Coberto** |
| R3.1 | Opção de **relatório** | **Coberto** |
| R3.2 | (ou) **varredura automática** | **Coberto** |
| R3.3 | **Cruzar** Quantidade Atual com Estoque Mínimo de Segurança | **Coberto** |
| R3.4 | Condição **≤** (igual ao mínimo já é alerta) | **Coberto** |
| R3.5 | Exibir **alerta visual destacado** "⚠ REPOSIÇÃO NECESSÁRIA" | **Coberto** |
| R3.6 | Alerta exibido **para aquele produto** | **Coberto** |

**17/17 requisitos atômicos cobertos (2 do pedido geral + 5 do item 1 + 4 do item 2 + 6 do item 3); nenhum Parcial ou Ausente.** A auditoria acrescentou um
teste ponta a ponta que percorre os três itens em sequência pela interface e pelo terminal
(`004/T064`), ligando as quatro features num único cenário verificável.

## Matriz detalhada

### Pedido geral

| ID | Requisito | FRs | Implementação | Testes | Critério de sucesso |
|----|-----------|-----|---------------|--------|---------------------|
| G1 | Sistema simples de executar, "altamente funcional" | 001/FR-001…FR-007 (um comando, migrações automáticas, espera do banco, configuração por ambiente, persistência), 001/FR-036 (prontidão), 001/FR-018 e FR-045 (funciona sem JS; atalhos) | 001/T004, T013, T041, T042, T043, T071, T036, T039 | 001/T010, T027, T028, T067, T068, T023 | 001/SC-001 (no ar em ≤ 10 min com ≤ 2 comandos), 001/SC-005 |
| G2 | Eficácia e qualidade de engenharia em Python | 001/FR-040…FR-042 (lint, formatação, testes em SQLite e PostgreSQL, cobertura ≥ 90 %, lock, migrações); constituição III (teste por FR) | 001/T002, T003, T009, T080, T081, T083; gates finais 002/T066–T068, 003/T052–T053, 004/T061–T062 | 001/T078, T079; rastreabilidade FR→teste 002/T065, 003/T052 | 001/SC-009 |

### Item 1 — Cadastro de Novos Produtos

| ID | Requisito | FRs | Implementação | Testes | Critério de sucesso |
|----|-----------|-----|---------------|--------|---------------------|
| R1.1 | Registrar produto informando **Nome** | 002/FR-001, FR-004 (obrigatório, normalizado, ≤ 120), FR-005 (único sem diferenciar maiúsculas), FR-007 (mensagens), FR-009/FR-011 (página, diálogo, sem JS), FR-029 (`cadastrar_produto`) | 002/T006, T012, T013, T019, T020, T021, T022, T023 | 002/T005, T008 (`test_fr001_…`, `test_fr004_…`, `test_fr005_…`), T009, T010 | 002/SC-001, SC-004, SC-006 |
| R1.2 | … informando **Quantidade Inicial** | 002/FR-001, FR-006 (inteiro 0…2.147.483.647, só dígitos), FR-008 (saldo = inicial), FR-030 (vira o primeiro registro do histórico); 003/FR-027, FR-028 (movimentação "Saldo inicial" na mesma transação) | 002/T012, T013; 003/T043, T044, T045 | 002/T008 (`test_fr008_…`, `test_fr030_…`), T009 (`test_fr006_…`); 003/T040, T041, T042 | 002/SC-004; 003/SC-004 (saldo = Σ movimentações) |
| R1.3 | … informando **Estoque Mínimo de Segurança** | 002/FR-001, FR-006, FR-024 (editável depois, sem tocar o saldo) | 002/T006, T012, T013, T052, T053, T056 | 002/T005 (`test_fr006_constraint_estoque_minimo…`), T008, T049, T051 | 002/SC-004 |
| R1.4 | **ID numérico automático** | 002/FR-002 (automático, crescente, nunca reutilizado), FR-003 (exibido `#0001`), FR-026 (ID nunca muda; sem exclusão) | 002/T006 (`BigAutoField`, `Produto.codigo`), T016 | 002/T005 (`test_fr002_…`, `test_fr003_…`), T008 (`test_fr002_…`), T011 (`test_fr003_…`, inclusive IDs ≥ 1000 sem separador) | 002/SC-002 |
| R1.5 | ID **para facilitar a busca** | 002/FR-013 (busca por `12`, `#12`, `#0012` ou nome), FR-014 (instantânea), FR-018 (URL reproduzível); 003/FR-012 (seleção "#0001 — Nome"), 003/FR-031 (`movimentar #0012`) | 002/T030, T031, T032, T036; 003/T018, T048 | 002/T027 (`test_fr013_…`), T028; 003/T014, T047; ponta a ponta 004/T064 | 002/SC-002, SC-003 (≤ 1 s com 10 mil produtos), SC-009 |

### Item 2 — Controle de Movimentação

| ID | Requisito | FRs | Implementação | Testes | Critério de sucesso |
|----|-----------|-----|---------------|--------|---------------------|
| R2.1 | **Função** para atualizar o saldo (única via) | 003/FR-001 (`registrar_movimentacao` é a única escrita de saldo), FR-010, FR-011 (atômica); 002/FR-025 (quantidade nunca editável), 001/FR-044 (sem admin); constituição I | 003/T017, T009; 002/T052, T053 | 003/T011, T012 (`FR-001`: edição adulterada e admin); 002/T049 (`test_fr025_…`), T051 | 003/SC-004; 002/SC-005 |
| R2.2 | Registrar **Entrada** (soma) | 003/FR-002, FR-012 (página), FR-013 (ação rápida "+ Entrada"), FR-014 (prévia), FR-015/FR-016 (atualização e aviso), FR-019 (sem JS) | 003/T017, T018, T019, T020, T024, T025, T026, T027, T028 | 003/T011 (`FR-002`), T015, T016, T021, T022, T023; ponta a ponta 004/T064 | 003/SC-001, SC-005, SC-008 |
| R2.3 | Registrar **Saída/Venda** (subtrai) | 003/FR-003, FR-012, FR-013 ("− Saída"), FR-016, FR-022 (tipo "Saída/Venda"), 003/FR-031 (terminal) | 003/T017, T018, T020, T024, T027, T048 | 003/T011 (`FR-003`), T015, T016, T022, T023, T047; ponta a ponta 004/T064 | 003/SC-001, SC-008 |
| R2.4 | Estoque **não pode ficar negativo** | 003/FR-004 (saída > saldo recusada com "Saldo insuficiente: disponível X, solicitado Y"), FR-008 (concorrência), FR-009 (três camadas), FR-018; 002/FR-006 e SC-006 (`CheckConstraint` no produto); constituição I | 003/T009 (restrições `mov_*`), T017 (`select_for_update`), T018 (`clean()`); 002/T006 (`produto_quantidade_atual_nao_negativa`) | 003/T007, T011, T013 (concorrência no PostgreSQL), T014, T015, T023; 002/T005 (`test_fr006_sc006_constraint…`); ponta a ponta 004/T064 | 003/SC-002, SC-003; 002/SC-006 |

### Item 3 — Sistema Automatizado de Alerta de Baixa

| ID | Requisito | FRs | Implementação | Testes | Critério de sucesso |
|----|-----------|-----|---------------|--------|---------------------|
| R3.1 | Opção de **relatório** | 004/FR-007 (Relatório de Reposição + "Executar varredura"), FR-008 (data/hora e totais), FR-009 (só produtos em alerta, colunas), FR-010 (estados vazios), FR-013 (sem JS), FR-032/FR-033 (CSV); paridade de console 004/FR-027…FR-031 (`varrer_estoque`) | 004/T014, T015, T026, T027, T028, T049, T050, T052, T053 | 004/T009, T010, T017, T018, T019, T020, T047, T048, T051 | 004/SC-002, SC-005, SC-006 |
| R3.2 | (ou) **varredura automática** | 004/FR-014 (contador no menu a cada 30 s), FR-015 (imediato após operações que mudam saldo/situação), FR-016, FR-017 (anúncio acessível), FR-012/FR-026 (relatório e painel se atualizam sozinhos), FR-022…FR-025 (painel); 001/FR-014 (contêiner `#badge-alertas` e `#anuncio-alertas`); 002/FR-031 e 003/FR-017 (evento `estoque-alterado`) | 004/T036, T037, T038, T039, T043, T044, T045, T046; 001/T033, T036, T037; 002/T022; 003/T020, T027 | 004/T029, T030, T034, T041, T042; 001/T023, T024; 002/T010 (`test_fr031_…`); 003/T016, T023 | 004/SC-003 (≤ 1 s), SC-004 (≤ 30 s sem interação) |
| R3.3 | **Cruzar** Quantidade Atual × Estoque Mínimo | 004/FR-001 (situação derivada no momento da consulta, nunca armazenada), FR-004/FR-005 (déficit, cobertura, sugestão); 002/FR-015 (regra única em `ProdutoQuerySet`) | 002/T006 (`em_alerta()`, `com_situacao()`); 004/T012, T013, T014 | 002/T005 (`test_fr015_queryset_…`); 004/T006, T007, T008 (equivalência SQL × Python) | 004/SC-001, SC-008 |
| R3.4 | Condição **≤** (igual ao mínimo é alerta) | 004/FR-002 (limites: = mínimo → alerta; mínimo + 1 → OK; 0/0 → alerta), FR-003 (SEM ESTOQUE como variação); 002/FR-015 | 002/T006; 004/T012, T013 | 002/T005 (`test_fr015_em_alerta_inclui_igualdade`); 004/T006, T007, T029, T057 | 004/SC-001 |
| R3.5 | **Alerta visual destacado** "⚠ REPOSIÇÃO NECESSÁRIA" | 001/FR-028 (componente: ícone desenhado + texto + cor; SEM ESTOQUE composto mantendo o texto), FR-024/FR-025 (contraste e cores forçadas), FR-029 (ícones); 002/FR-020 (selo único); 004/FR-009, FR-020, FR-021 (nunca só cor) | 001/T008, T032, T051, T059; 002/T015, T016; 004/T026 | 001/T011, T046 (`FR-028`); 002/T011 (`test_fr020_…`); 004/T011, T033, T058 | 004/SC-007; 001/SC-002 |
| R3.6 | Alerta **para aquele produto** | 004/FR-018 (selo em cada linha da lista e no detalhe), FR-019 (aviso na confirmação da movimentação que provoca o alerta), FR-011 ("+ Entrada" com sugestão na linha); 002/FR-020, FR-021 | 002/T015, T016, T043; 004/T026, T035, T040 | 002/T011, T039; 004/T019, T021, T031, T032, T033; ponta a ponta 004/T064 | 004/SC-003, SC-008 |

## Cenário ponta a ponta (`004/T064`)

Executado só pela interface HTTP (variantes comum e HTMX) e pelos comandos de terminal:

1. **Item 1** — cadastrar "Caneta Azul" com Quantidade Inicial 10 e mínimo 5 → `#0001`, saldo 10;
   o produto é encontrado por `1`, `#1` e `#0001`.
2. **Item 2** — Entrada de 5 → 15; Saída de 10 → 5; Saída de 6 → recusada ("Saldo insuficiente:
   disponível 5, solicitado 6"), saldo 5 e nenhuma movimentação nova.
3. **Item 3** — com 5 ≤ 5: selo "⚠ REPOSIÇÃO NECESSÁRIA" na lista e no detalhe, produto no
   relatório, contador 1, `varrer_estoque` imprime "⚠ REPOSIÇÃO NECESSÁRIA"; Saída de 5 → selo
   composto "REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE"; "+ Entrada" do relatório com a sugestão (10) →
   produto sai do alerta e o contador volta a 0; `auditar_saldos() == []`.

## Complementos além da atividade

Entregues porque reforçam "altamente funcional e eficaz", sem serem exigidos pelo enunciado:
histórico imutável de movimentações com filtros (003/FR-021…FR-026), saldo inicial retroativo
(003/FR-030), comando `movimentar` (003/FR-031), painel com KPIs (004/FR-022…FR-026), exportação
CSV (004/FR-032/FR-033), dados de demonstração `popular_demo` (004/FR-034/FR-035), catálogo vivo
do design system `/design/` (001/FR-031…FR-033) e verificação de saúde `/saude/`
(001/FR-034…FR-036).
