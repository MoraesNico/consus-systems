# Checklist de Integridade de Dados: Cadastro de Produtos

**Purpose**: Testar a qualidade dos requisitos que protegem a consistência dos dados do produto — ID, nome único, quantidades, imutabilidade do saldo fora de movimentações e integração com o histórico (003) — à luz do princípio I da constituição.
**Created**: 2026-10-20
**Feature**: [spec.md](../spec.md) · [data-model.md](../data-model.md) · [contracts/servicos-e-consultas.md](../contracts/servicos-e-consultas.md)

**Note**: Checklist gerado pelo fluxo `/speckit-checklist` a partir da spec, do plano e dos contratos. Profundidade: padrão; público: revisor de PR; foco: regras de dados e concorrência.
**Review Ownership**: Artefato de revisão da qualidade dos requisitos, de responsabilidade do revisor. Marque `[x]` somente quando o critério de qualidade do requisito estiver satisfeito.
**Marker Semantics**: `[x]` significa que o critério foi revisado e está satisfeito na especificação. Não significa que a implementação esteja pronta.

## Completude dos requisitos

- [x] CHK001 A garantia de "quantidade nunca negativa" está exigida mesmo quando a validação da tela é contornada? [Completude, Spec §SC-006]
- [x] CHK002 A unicidade do nome está exigida também sob cadastros simultâneos? [Completude, Spec §FR-005, Edge Cases]
- [x] CHK003 Está especificado que a normalização do nome acontece antes das verificações de tamanho e de unicidade? [Completude, Spec §FR-004, §FR-005]
- [x] CHK004 Os limites inferior e superior das quantidades estão definidos? [Completude, Spec §FR-006, Clarifications]
- [x] CHK005 O ciclo de vida do ID (automático, crescente, nunca reutilizado, lacunas aceitáveis, imutável) está completo? [Completude, Spec §FR-002, §FR-026]
- [x] CHK006 Está exigido que a quantidade não mude por nenhum caminho, inclusive envios adulterados? [Completude, Spec §FR-025, §SC-005]
- [x] CHK007 A exclusão de produtos está explicitamente vedada em todas as interfaces? [Completude, Spec §FR-026]
- [x] CHK008 A atomicidade do cadastro (tudo ou nada) está exigida? [Completude, Spec §FR-029]
- [x] CHK009 A relação entre Quantidade Inicial e o primeiro registro do histórico, com invariantes que a extensão da 003 deve preservar, está especificada? [Completude, Spec §FR-030]
- [x] CHK010 A edição concorrente com uma movimentação está tratada (a edição não sobrescreve a quantidade)? [Completude, Spec Edge Cases, §Assumptions]

## Clareza dos requisitos

- [ ] CHK011 "Sem diferenciar maiúsculas/minúsculas" está claro para letras acentuadas (ex.: "ÁGUA" × "água")? [Ambiguidade, Spec §FR-005]
- [ ] CHK012 A lista de formatos numéricos aceitos/recusados é inequívoca para sinal "+", zeros à esquerda e espaços nas extremidades? [Clareza, Spec §FR-006, Edge Cases]
- [x] CHK013 O limite da regra de situação (igualdade conta como alerta) está explícito e exemplificado? [Clareza, Spec §FR-015, Edge Cases]
- [x] CHK014 Está exigido que a mensagem de nome duplicado identifique o produto existente? [Clareza, Spec §FR-005, §FR-007]

## Consistência dos requisitos

- [x] CHK015 As regras dos campos são as mesmas em Key Entities, FRs e Clarifications (limites, normalização)? [Consistência, Spec §Key Entities, §FR-004–FR-006]
- [x] CHK016 A situação é descrita de forma consistente como derivada e não armazenada? [Consistência, Spec §Key Entities, §Assumptions]
- [x] CHK017 A spec é compatível com o contrato `docs/arquitetura.md` (campos, regras, rotas), com extensões registradas como propostas? [Consistência, research.md §Propostas]

## Mensurabilidade

- [x] CHK018 "Zero duplicatas sob concorrência" e "zero quantidades negativas" são verificáveis objetivamente? [Mensurabilidade, Spec §SC-006]
- [x] CHK019 "Nenhum caminho altera a quantidade" é verificável por uma lista enumerável de telas e envios? [Mensurabilidade, Spec §SC-005]

## Casos de borda

- [x] CHK020 Números de ID grandes demais (na busca e no endereço) têm comportamento definido? [Caso de borda, Spec Edge Cases]
- [x] CHK021 O envio duplo do formulário de cadastro está tratado? [Caso de borda, Spec Edge Cases]
- [x] CHK022 Está definido o que acontece se o registro do saldo inicial (003) falhar durante o cadastro? [Exceção, Spec §FR-030 — "mesma operação atômica"]

## Dependências e premissas

- [x] CHK023 A divisão de responsabilidade da regra de alerta entre 002 (exibir/filtrar) e 004 (varredura/relatório) está documentada? [Premissa, Spec §FR-015, §Assumptions]
- [x] CHK024 A ausência de autenticação/perfis está registrada como premissa explícita? [Premissa, Spec §Assumptions]
- [x] CHK025 O aviso às regiões dependentes da situação (FR-031) está descrito de forma verificável na spec? [Clareza, Spec §FR-031, US1 cenário 9]

## Notes

- Marque itens `[x]` somente após a revisão confirmar que o critério de qualidade do requisito está satisfeito.
- Deixe itens desmarcados quando ainda exigirem esclarecimento, correção ou avaliação do revisor.
- `/speckit-implement` lê o estado das caixas como portão e não deve alterá-las.
- `checklists/requirements.md` tem ciclo de vida próprio, mantido por `/speckit-specify` e `/speckit-clarify`.
- **Avaliação inicial (2026-10-20)**: 23/25 atendidos. Lacunas: CHK011 (acentos maiúsculos ×
  minúsculos na unicidade — relevante pela limitação do SQLite em research R3) e CHK012 ("+5",
  "007", " 12 " não especificados; o plano aceita "007" e " 12 " e recusa "+5") — encaminhadas
  para a autoanálise.
