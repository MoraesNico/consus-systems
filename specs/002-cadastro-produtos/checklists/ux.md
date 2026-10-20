# Checklist de UX: Cadastro de Produtos

**Purpose**: Testar a qualidade dos requisitos de interação, apresentação, acessibilidade e estados da interface (lista, busca, cadastro, detalhe, edição, atalhos) — não a implementação.
**Created**: 2026-10-20
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [contracts/fragmentos-e-eventos.md](../contracts/fragmentos-e-eventos.md)

**Note**: Checklist gerado pelo fluxo `/speckit-checklist` a partir da spec, do plano e dos contratos. Profundidade: padrão; público: revisor de PR; foco: interação/estados e acessibilidade.
**Review Ownership**: Artefato de revisão da qualidade dos requisitos, de responsabilidade do revisor. Marque `[x]` somente quando o critério de qualidade do requisito estiver satisfeito.
**Marker Semantics**: `[x]` significa que o critério foi revisado e está satisfeito na especificação. Não significa que a implementação esteja pronta.

## Completude dos requisitos

- [x] CHK001 As colunas da lista, sua ordem e o alinhamento dos números estão especificados explicitamente? [Completude, Spec §FR-012]
- [x] CHK002 Os dois estados vazios (sem produtos × busca/filtro sem resultado) têm mensagem e ação definidas? [Completude, Spec §FR-019]
- [x] CHK003 Há requisitos de estado "em andamento" para a busca instantânea e para o envio do formulário (indicação de atualização, botão indisponível durante o envio)? [Gap]
- [x] CHK004 Estão definidos os requisitos de foco ao abrir e fechar o diálogo de cadastro (foco no primeiro campo; retorno ao controle que o abriu)? [Gap, Acessibilidade, Spec §FR-009]
- [x] CHK005 O conteúdo da página de detalhe (campos, formato de datas, ações) está enumerado? [Completude, Spec §FR-021]
- [x] CHK006 Todas as mensagens de erro de validação estão definidas textualmente em pt-BR? [Completude, Spec §FR-007]
- [x] CHK007 Os textos das notificações de cadastro e de edição estão especificados? [Completude, Spec §FR-010, §FR-027]
- [x] CHK008 O formato do indicador de paginação ("1–25 de 60") e a preservação do estado ao paginar estão especificados? [Completude, Spec §FR-017]

## Clareza dos requisitos

- [x] CHK009 "Instantânea" está quantificada com um limite de tempo mensurável? [Clareza, Spec §FR-014, §SC-003]
- [x] CHK010 O "destaque" do produto recém-cadastrado tem propriedades verificáveis (quando aparece, quando some, sinal além da cor)? [Clareza, Spec §FR-010]
- [x] CHK011 A interpretação de cada formato de termo de busca (`12`, `#12`, `#0012`, texto) é inequívoca? [Clareza, Spec §FR-013, Clarifications]
- [x] CHK012 A ordenação padrão e a regra de desempate estão definidas? [Clareza, Spec §FR-016]
- [x] CHK013 O indicador de situação é definido por comportamento (ícone + texto + cor), e não por estilo? [Clareza, Spec §FR-020]
- [x] CHK014 "Indicados discretamente" (dica dos atalhos) tem critério objetivo de onde e como a dica aparece? [Ambiguidade, Spec §FR-028]

## Consistência dos requisitos

- [x] CHK015 As regras e mensagens do cadastro são as mesmas na página própria e no diálogo? [Consistência, Spec §FR-009]
- [x] CHK016 O destino após o cadastro é o mesmo com e sem scripts no navegador? [Consistência, Spec §FR-010, §FR-011, US1 cenário 8]
- [x] CHK017 Os termos "Em alerta", "REPOSIÇÃO NECESSÁRIA" e "OK" são usados de forma consistente no filtro, no indicador e no detalhe? [Consistência, Spec §FR-015, §FR-020, US3]
- [x] CHK018 As regras de edição reutilizam as do cadastro sem contradição (campos vazios no cadastro × preenchidos na edição)? [Consistência, Spec §FR-006, §FR-024]

## Qualidade dos critérios de aceitação

- [x] CHK019 Cada história tem um teste independente descrito e cenários Dado/Quando/Então verificáveis? [Mensurabilidade, Spec §User Scenarios]
- [x] CHK020 Os critérios de sucesso de UX (SC-001, SC-007, SC-009) têm métrica, população e limite definidos? [Mensurabilidade, Spec §SC-001, §SC-007, §SC-009]

## Cobertura de cenários

- [x] CHK021 A conclusão de todas as tarefas apenas com teclado está exigida? [Cobertura, Spec §SC-007]
- [x] CHK022 Recarregar, Voltar/Avançar e abrir a URL em outra aba estão cobertos para a lista filtrada? [Cobertura, Spec §FR-018, §SC-008]
- [x] CHK023 O fechamento do diálogo sem salvar está coberto? [Cobertura, Spec US1 cenário 7]
- [x] CHK024 O cadastro pelo diálogo com busca/filtro ativos que excluiriam o novo produto está tratado? [Cobertura, Spec §FR-010, Edge Cases]
- [x] CHK025 Há requisito de anunciar a leitores de tela a mudança no número de resultados da busca/filtro? [Gap, Acessibilidade, Spec §FR-014]
- [x] CHK026 Estão definidos requisitos para telas estreitas (ex.: comportamento da tabela densa em celular)? [Gap]

## Requisitos não funcionais (acessibilidade e localização)

- [x] CHK027 A associação acessível entre mensagem de erro e campo está exigida? [Acessibilidade, Spec §FR-007]
- [x] CHK028 Os formatos de número (milhar ".") e data (`dd/mm/aaaa HH:MM`) estão especificados? [Localização, Spec §FR-012, §FR-021]
- [x] CHK029 A regra "nunca apenas cor" se aplica a todos os indicadores de estado, inclusive ao destaque de linha? [Acessibilidade, Spec §FR-010, §FR-020]
- [x] CHK030 A indicação da coluna/sentido de ordenação para tecnologias assistivas está exigida? [Acessibilidade, Spec §FR-016]

## Casos de borda e dependências

- [x] CHK031 O comportamento dos atalhos está totalmente especificado para conflitos (teclas modificadoras, campo editável, diálogo já aberto)? [Caso de borda, Spec §FR-028]
- [x] CHK032 Parâmetros inválidos na URL (situação, ordenação, página) têm comportamento definido? [Caso de borda, Spec Edge Cases]
- [x] CHK033 Os componentes do design system dos quais a feature depende estão listados como dependência da 001? [Dependência, Spec §Assumptions]
- [x] CHK034 A região reservada no detalhe para a 003 tem comportamento definido enquanto a 003 não existe? [Dependência, Spec §FR-022]

## Notes

- Marque itens `[x]` somente após a revisão confirmar que o critério de qualidade do requisito está satisfeito.
- Deixe itens desmarcados quando ainda exigirem esclarecimento, correção ou avaliação do revisor.
- `/speckit-implement` lê o estado das caixas como portão e não deve alterá-las.
- `checklists/requirements.md` tem ciclo de vida próprio, mantido por `/speckit-specify` e `/speckit-clarify`.
- **Avaliação inicial (2026-10-20)**: 28/34 atendidos. Lacunas: CHK003 (estado em andamento),
  CHK004 (foco do diálogo), CHK014 e CHK031 (dica e conflitos dos atalhos — falta o caso
  "diálogo aberto"), CHK025 (anúncio do número de resultados), CHK026 (telas estreitas). O plano
  já prevê `hx-disabled-elt`, `autofocus` e `#contagem-produtos` com `role="status"`, mas a spec
  ainda não os exige — encaminhado para a autoanálise.
- **Após a autoanálise (2026-10-20)**: 34/34. A spec passou a exigir: indicação de atualização
  e anúncio do número de resultados (FR-014 → CHK003, CHK025); foco ao abrir/fechar o diálogo e
  "Salvar" indisponível durante o envio (FR-009 → CHK003, CHK004); dica visível da tecla junto à
  busca e a "Novo produto" e bloqueio com diálogo aberto (FR-028, US5 cenário 4 → CHK014,
  CHK031); premissa de telas estreitas (Assumptions → CHK026).
