# Feature Specification: Alerta de Reposição — varredura, relatório, contador automático e painel

**Feature Branch**: `004-alerta-reposicao`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Sistema Automatizado de Alerta de Baixa (item 3 da atividade). O sistema cruza a Quantidade Atual com o Estoque Mínimo de Segurança; se a quantidade for menor ou igual ao mínimo, exibe um alerta visual destacado ⚠ REPOSIÇÃO NECESSÁRIA para aquele produto. A atividade pede 'relatório OU varredura automática' — o Consus entrega os DOIS: Relatório de Reposição com botão 'Executar varredura' (data/hora, total analisado, total em alerta; somente produtos em alerta, ordenados por criticidade; colunas #ID, nome, quantidade atual, mínimo, déficit, sugestão de reposição e barra de cobertura; estado vazio positivo; ação rápida '+ Entrada'; exportação CSV); varredura automática (contador de alertas no menu atualizado sozinho a cada ~30 s e imediatamente após cada movimentação; selo '⚠ REPOSIÇÃO NECESSÁRIA' / 'SEM ESTOQUE' na lista e no detalhe de produtos; aviso de reposição na confirmação da movimentação que faz um produto entrar em alerta); Painel com KPIs (produtos cadastrados, unidades em estoque, produtos em alerta, movimentações nas últimas 24 h), lista dos 5 mais críticos, lista de cobertura e últimas movimentações; paridade de terminal (`varrer_estoque` com formatos texto/csv/json e opção de falhar se houver alerta); dados de demonstração idempotentes (`popular_demo`). Regra central: em alerta ⇔ quantidade atual ≤ estoque mínimo (igual ao mínimo → alerta; mínimo + 1 → sem alerta; mínimo 0 e quantidade 0 → alerta/sem estoque). Acessibilidade: alerta nunca só por cor; mudanças do contador anunciadas a leitores de tela."

## Clarifications

### Session 2026-10-20

- Q: A varredura de reposição deve ficar registrada em um histórico consultável ou é apenas calculada e exibida no momento? → A: Apenas calculada no momento em que é executada; nada é gravado e a data/hora exibida é a do cálculo (histórico de varreduras fica fora de escopo).
- Q: Qual regra define a sugestão de reposição exibida para cada produto em alerta? → A: Repor até um estoque-alvo de 2× o estoque mínimo: sugestão = 2 × mínimo − quantidade atual, com no mínimo 1 unidade (caso de mínimo 0 e quantidade 0).
- Q: Quando a confirmação de uma movimentação deve trazer o aviso de reposição? → A: Quando a movimentação piora a situação do produto (OK → REPOSIÇÃO NECESSÁRIA, OK → SEM ESTOQUE ou REPOSIÇÃO NECESSÁRIA → SEM ESTOQUE); quando a movimentação tira o produto do alerta, a confirmação informa que ele saiu do alerta; nos demais casos não há aviso extra.
- Q: Qual formato o CSV exportado deve seguir para abrir corretamente em planilhas em português? → A: Separador ";", codificação UTF-8 com BOM, cabeçalho em português, números inteiros sem separador de milhar e arquivo `reposicao-AAAAMMDD-HHMM.csv`; a saída csv do terminal usa o mesmo layout, sem BOM.
- Q: Como calcular a cobertura e o déficit quando o estoque mínimo é 0? → A: Quantidade 0 → cobertura 0% e déficit 0 (produto SEM ESTOQUE); quantidade > 0 com mínimo 0 → cobertura "não se aplica" (exibida como "—" e excluída da lista de cobertura do painel); nos demais casos a cobertura é o percentual arredondado para baixo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Relatório de reposição sob demanda (Priority: P1)

Como operador de estoque, quero abrir o **Relatório de Reposição** e executar uma varredura a
qualquer momento para ver, em ordem de criticidade, todos os produtos cuja quantidade atual está
menor ou igual ao estoque mínimo de segurança — com quanto falta, quanto repor e quanto do mínimo
ainda está coberto — para decidir as compras do dia e repor direto dali.

**Why this priority**: é a forma mínima e completa do item 3 da atividade ("opção de relatório"
que cruza a Quantidade Atual com o Estoque Mínimo de Segurança e exibe "⚠ REPOSIÇÃO NECESSÁRIA"
para cada produto afetado). Sozinha, esta história já atende o requisito do professor.

**Independent Test**: cadastrar produtos em situações conhecidas (abaixo do mínimo, exatamente
no mínimo, um acima do mínimo, zerado com mínimo positivo, zerado com mínimo 0), abrir o
relatório, executar a varredura e conferir quais produtos aparecem, em que ordem, com quais
valores calculados e com qual selo.

**Acceptance Scenarios**:

1. **Given** os produtos A (atual 5, mínimo 10), B (atual 10, mínimo 10) e C (atual 11,
   mínimo 10), **When** executo a varredura, **Then** A e B aparecem com o selo
   "⚠ REPOSIÇÃO NECESSÁRIA" e C não aparece.
2. **Given** os produtos D (atual 0, mínimo 0) e E (atual 0, mínimo 8) além de A e B,
   **When** executo a varredura, **Then** D e E aparecem com o selo "SEM ESTOQUE" antes de
   todos os demais, e E vem antes de D (maior déficit).
3. **Given** vários produtos em alerta, **When** o relatório é exibido, **Then** a ordem é:
   sem estoque primeiro; depois maior déficit; depois menor cobertura; depois menor ID.
4. **Given** qualquer varredura executada, **When** o resultado aparece, **Then** vejo a data
   e hora da varredura (dd/mm/aaaa HH:MM), o total de produtos analisados, o total em alerta e
   quantos deles estão sem estoque.
5. **Given** o relatório aberto, **When** aciono "Executar varredura", **Then** o resultado é
   recalculado sem sair da página e a data/hora da varredura é atualizada.
6. **Given** produtos cadastrados e nenhum em alerta, **When** executo a varredura, **Then**
   vejo um estado vazio positivo ("Nenhum produto precisa de reposição") com o total analisado.
7. **Given** nenhum produto cadastrado, **When** abro o relatório, **Then** vejo um estado vazio
   que orienta a cadastrar o primeiro produto.
8. **Given** um produto em alerta no relatório, **When** aciono "+ Entrada" na linha dele e
   confirmo uma entrada que o leva acima do mínimo, **Then** o relatório se atualiza sozinho e o
   produto deixa a lista, sem recarregar a página.
9. **Given** o navegador com scripts desativados, **When** abro o relatório e aciono
   "Executar varredura", **Then** a página é recarregada com o resultado recalculado.

---

### User Story 2 - Alerta automático em toda a interface (Priority: P2)

Como operador, quero que o sistema sinalize **sozinho** os produtos que precisam de reposição —
com um contador no menu, um selo em cada produto da lista e do detalhe e um aviso na confirmação
da movimentação que provocou o alerta — sem precisar abrir o relatório.

**Why this priority**: atende a alternativa "varredura automática" do item 3 e faz o alerta ser
percebido no momento em que nasce. Depende da mesma regra da história 1, mas é testável sem o
relatório.

**Independent Test**: com o sistema aberto em qualquer página, registrar uma saída que leve um
produto ao mínimo e verificar contador, selo e aviso; depois alterar o estoque por outro meio
(outra janela ou terminal) e verificar que o contador muda sozinho em até 30 segundos.

**Acceptance Scenarios**:

1. **Given** o contador do menu mostra 2, **When** registro uma saída que leva um produto de 11
   para 10 unidades (mínimo 10), **Then** o contador passa a mostrar 3 imediatamente, sem
   recarregar a página, e a confirmação da movimentação inclui o aviso "REPOSIÇÃO NECESSÁRIA"
   para aquele produto.
2. **Given** um produto com 3 unidades e mínimo 5, **When** registro uma saída de 3 unidades,
   **Then** a confirmação traz o aviso "SEM ESTOQUE" para aquele produto.
3. **Given** um produto em alerta, **When** registro uma entrada que o leva acima do mínimo,
   **Then** a confirmação informa que o produto saiu do alerta e o contador diminui.
4. **Given** um produto em alerta com 2 unidades e mínimo 10, **When** registro uma entrada de 3
   unidades, **Then** a confirmação não traz aviso extra (a situação continua REPOSIÇÃO
   NECESSÁRIA) e o produto segue no contador e no relatório com os valores atualizados.
5. **Given** uma página aberta e nenhuma interação, **When** o estoque é alterado em outra
   janela ou pelo terminal, **Then** o contador reflete a nova contagem em até 30 segundos.
6. **Given** a lista de produtos, **When** ela é exibida, **Then** cada produto em alerta mostra
   o selo "⚠ REPOSIÇÃO NECESSÁRIA", cada produto zerado mostra "SEM ESTOQUE" e os demais mostram
   a situação "OK" de forma discreta; o detalhe do produto mostra o mesmo selo.
7. **Given** um usuário de leitor de tela, **When** o contador muda de valor, **Then** a nova
   contagem é anunciada uma única vez; **When** uma verificação automática não muda o valor,
   **Then** nada é anunciado.

---

### User Story 3 - Painel de controle (Priority: P3)

Como operador ou gestor, quero que a página inicial mostre um retrato do estoque — indicadores,
os produtos mais críticos, a cobertura do mínimo e as últimas movimentações — e que esse retrato
se atualize sozinho quando o estoque muda.

**Why this priority**: torna a situação visível logo na entrada do sistema e substitui o painel
provisório da fundação; agrega valor, mas o requisito da atividade já é atendido pelas
histórias 1 e 2.

**Independent Test**: com um conjunto conhecido de produtos e movimentações, abrir a página
inicial e conferir cada indicador e cada lista; registrar uma movimentação e ver o painel se
atualizar.

**Acceptance Scenarios**:

1. **Given** 12 produtos, 4 deles em alerta (1 sem estoque), somando 1.250 unidades, e 7
   entradas/saídas nas últimas 24 h, **When** abro a página inicial, **Then** vejo os indicadores
   "12 produtos cadastrados", "1.250 unidades em estoque", "4 em alerta (1 sem estoque)" e
   "7 movimentações nas últimas 24 h".
2. **Given** 7 produtos em alerta, **When** abro o painel, **Then** a lista "Reposição
   necessária" mostra os 5 mais críticos (mesma ordem do relatório) e um atalho para o relatório
   completo com o total (7).
3. **Given** produtos com diferentes coberturas do mínimo, **When** abro o painel, **Then** a
   lista de cobertura mostra até 8 produtos, do menor para o maior percentual, cada um com uma
   barra horizontal proporcional.
4. **Given** movimentações registradas, **When** abro o painel, **Then** vejo as 5 mais
   recentes com tipo, produto, quantidade, saldo resultante e data/hora.
5. **Given** o painel aberto, **When** registro uma movimentação, **Then** indicadores e listas
   se atualizam sem recarregar a página.
6. **Given** nenhum produto cadastrado, **When** abro o painel, **Then** os indicadores mostram
   0 e um estado vazio convida a cadastrar o primeiro produto.

---

### User Story 4 - Varredura pelo terminal (Priority: P3)

Como operador técnico (ou o professor avaliando a proposta original de app de console), quero
executar a varredura pelo terminal e ver o relatório impresso — com "⚠ REPOSIÇÃO NECESSÁRIA" em
cada produto afetado — e poder usá-lo em rotinas agendadas que falham quando há alerta.

**Why this priority**: garante paridade com a proposta original em console e permite varredura
agendada; não é necessário para o uso diário pela interface.

**Independent Test**: com produtos em situações conhecidas, executar o comando nos três formatos
e com/sem a opção de falha, conferindo conteúdo, ordem e código de saída.

**Acceptance Scenarios**:

1. **Given** 2 produtos em alerta (1 sem estoque) entre 5 cadastrados, **When** executo
   `varrer_estoque`, **Then** o terminal mostra data/hora, "5 produtos analisados", "2 em alerta
   (1 sem estoque)" e uma linha por produto em alerta iniciada por "⚠ REPOSIÇÃO NECESSÁRIA", na
   mesma ordem do relatório web.
2. **Given** o mesmo estado, **When** executo com formato csv ou json, **Then** a saída contém
   os mesmos produtos, valores e totais do relatório web, em formato legível por máquina.
3. **Given** ao menos um produto em alerta, **When** executo com a opção de falhar se houver
   alerta, **Then** o comando termina com código de saída 1; **Given** nenhum produto em alerta,
   **Then** termina com código 0.
4. **Given** uma opção ou formato inválido, **When** executo o comando, **Then** ele explica o
   erro e termina com código 2, sem imprimir relatório.
5. **Given** a opção para listar todos, **When** executo o comando, **Then** os produtos fora de
   alerta também aparecem, marcados "OK", depois dos produtos em alerta.

---

### User Story 5 - Exportar o relatório em CSV (Priority: P4)

Como gestor, quero baixar o relatório de reposição como planilha para enviar ao setor de compras.

**Why this priority**: conveniência sobre a história 1; não altera a regra nem a tela principal.

**Independent Test**: com produtos em alerta conhecidos, acionar "Exportar CSV" e abrir o arquivo
em uma planilha, conferindo colunas, ordem, acentuação e valores.

**Acceptance Scenarios**:

1. **Given** 3 produtos em alerta, **When** aciono "Exportar CSV", **Then** baixo um arquivo com
   uma linha de cabeçalho e 3 linhas, na mesma ordem e com os mesmos valores da tela.
2. **Given** nenhum produto em alerta, **When** exporto, **Then** o arquivo contém apenas o
   cabeçalho.
3. **Given** um produto com acentos, ponto e vírgula ou aspas no nome, **When** exporto e abro em
   uma planilha em português, **Then** o nome aparece íntegro, em uma única célula.

---

### User Story 6 - Dados de demonstração (Priority: P4)

Como aluno apresentando o projeto, quero popular o sistema com um conjunto realista de produtos e
movimentações — incluindo produtos em alerta, um sem estoque e casos de limite — com um único
comando que posso repetir sem duplicar nada.

**Why this priority**: facilita a apresentação e os testes manuais; não é requisito da atividade.

**Independent Test**: executar `popular_demo` em uma base vazia, conferir a composição dos dados
nas telas; executar de novo e conferir que nada mudou.

**Acceptance Scenarios**:

1. **Given** uma base vazia, **When** executo `popular_demo`, **Then** passam a existir ao menos
   12 produtos, ao menos 3 em alerta, exatamente 1 sem estoque, ao menos 1 exatamente no mínimo e
   ao menos 1 exatamente um acima do mínimo, cada um com histórico de entradas e saídas.
2. **Given** a demonstração já populada, **When** executo `popular_demo` novamente, **Then**
   nenhum produto ou movimentação é criado e o comando informa que tudo já existia.
3. **Given** produtos cadastrados pelo usuário, **When** executo `popular_demo`, **Then** esses
   produtos não são alterados.

---

### Edge Cases

- **Exatamente no mínimo** (atual = mínimo): em alerta; déficit 0; cobertura 100%; sugestão igual
  ao mínimo (estoque-alvo 2× o mínimo).
- **Um abaixo do mínimo com mínimo grande** (ex.: atual 999, mínimo 1.000): cobertura exibida 99%
  (arredondamento para baixo), nunca 100%.
- **Um acima do mínimo** (atual = mínimo + 1): fora de alerta em todas as telas, no contador, no
  terminal e no CSV.
- **Mínimo 0 e quantidade 0**: em alerta, variação "SEM ESTOQUE"; déficit 0; cobertura 0%;
  sugestão de 1 unidade.
- **Mínimo 0 e quantidade positiva**: nunca em alerta; cobertura "não se aplica" ("—"); fora da
  lista de cobertura do painel.
- **Entrada que tira de "SEM ESTOQUE" mas mantém em alerta** (ex.: 0 → 4 com mínimo 10): situação
  melhora para REPOSIÇÃO NECESSÁRIA, sem aviso extra na confirmação.
- **Nenhum produto cadastrado**: relatório e painel mostram estado vazio de orientação; contador
  0; terminal informa "Nenhum produto cadastrado" e termina com código 0 mesmo com a opção de
  falhar se houver alerta.
- **Todos os produtos em alerta**: relatório lista todos; painel mostra os 5 mais críticos.
- **Empates na criticidade**: desempate sempre determinístico pelo menor ID; duas varreduras
  sobre o mesmo estado produzem exatamente a mesma ordem.
- **Mudança feita fora da página** (outra janela, outro usuário, terminal): o contador converge
  em até 30 s; o relatório aberto mantém a data/hora da última varredura até ser re-executado ou
  até ocorrer uma movimentação na própria janela.
- **Alteração do estoque mínimo** (edição do produto): muda a situação imediatamente para toda
  nova varredura ou exibição; o contador reflete a mudança na próxima verificação automática.
- **Produto cadastrado já com quantidade inicial ≤ mínimo**: aparece em alerta em todas as telas
  desde o cadastro.
- **Movimentação que não muda a situação** (ex.: saída em produto que continua OK): nenhuma
  advertência adicional na confirmação.
- **Saída que zera um produto que já estava em alerta**: agravamento para "SEM ESTOQUE", com aviso
  "SEM ESTOQUE" na confirmação.
- **Falha temporária na verificação automática** (servidor indisponível): o contador mantém o
  último valor exibido, sem mensagem de erro intrusiva, e a verificação seguinte tenta de novo.
- **Terminal sem suporte ao símbolo ⚠**: o comando substitui o símbolo por um marcador textual
  equivalente e mantém o texto "REPOSIÇÃO NECESSÁRIA".
- **Nome de produto iniciado por `=`, `+`, `-` ou `@`** no CSV: exportado de forma que a planilha
  não o interprete como fórmula.
- **Nome longo** (até 120 caracteres): exibido por inteiro, com quebra de linha, no relatório e
  no painel; no formato texto do terminal o nome é encurtado com "…" para manter as colunas
  alinhadas, enquanto csv e json trazem o nome completo.
- **Quantidades grandes** (ex.: 1.000.000): exibidas com separador de milhar na interface; a
  barra de cobertura nunca ultrapassa o limite visual.
- **Sugestão acima do limite por movimentação** (1.000.000 unidades na feature 003): a sugestão é
  exibida integralmente; a reposição exigirá mais de uma entrada.
- **Saldo próximo do teto** (2.147.483.647): a sugestão é reduzida para não ultrapassar o teto e
  todos os cálculos continuam corretos, sem erro na tela.

## Requirements *(mandatory)*

### Functional Requirements

**Regra de alerta (núcleo — vale para todas as telas, o terminal e a exportação)**

- **FR-001** *(Atividade, item 3 — "cruzar a Quantidade Atual com o Estoque Mínimo de
  Segurança")*: O sistema MUST determinar a situação de reposição de cada produto cruzando a
  quantidade atual com o estoque mínimo de segurança no momento da consulta; a situação é sempre
  derivada do saldo vigente e nunca digitada nem armazenada separadamente.
- **FR-002** *(Atividade, item 3 — "menor ou igual ao mínimo")*: Um produto MUST estar em alerta
  de reposição se, e somente se, quantidade atual ≤ estoque mínimo. Limites obrigatórios:
  quantidade = mínimo → em alerta; quantidade = mínimo + 1 → fora de alerta; mínimo 0 e
  quantidade 0 → em alerta.
- **FR-003**: Um produto em alerta com quantidade atual 0 MUST ser classificado na variação mais
  grave "SEM ESTOQUE". As situações possíveis são mutuamente exclusivas: **OK**, **REPOSIÇÃO
  NECESSÁRIA** e **SEM ESTOQUE**.
- **FR-004**: Para cada produto, o sistema MUST calcular o **déficit** = máx(estoque mínimo −
  quantidade atual, 0) e a **cobertura** = ⌊quantidade atual × 100 ÷ estoque mínimo⌋ (percentual
  inteiro arredondado para baixo). Casos especiais: quantidade 0 → cobertura 0%; estoque mínimo 0
  com quantidade > 0 → cobertura "não se aplica" (exibida como "—").
- **FR-005**: Para cada produto em alerta, o sistema MUST calcular a **sugestão de reposição** =
  máx(2 × estoque mínimo − quantidade atual, 1), isto é, a quantidade que leva o produto a um
  estoque-alvo de 2× o mínimo (ao menos 1 unidade). Exemplos: atual 4 e mínimo 10 → 16; atual 10
  e mínimo 10 → 10; atual 0 e mínimo 0 → 1. A sugestão nunca leva o saldo acima do teto de
  2.147.483.647 unidades (feature 003); respeitado esse teto, registrar a sugestão como entrada
  MUST sempre tirar o produto do alerta.
- **FR-006**: O sistema MUST ordenar os produtos em alerta por **criticidade**: (1) sem estoque
  primeiro; (2) maior déficit; (3) menor cobertura; (4) menor ID. A mesma ordem MUST ser usada no
  relatório, no painel, no terminal e na exportação.

**Relatório de reposição (História 1)**

- **FR-007** *(Atividade, item 3 — "opção de relatório ou varredura")*: O sistema MUST oferecer
  a página "Relatório de Reposição", acessível pelo menu principal, que executa a varredura ao ser
  aberta e novamente sempre que o usuário acionar "Executar varredura", sem sair da página.
  Enquanto a varredura está em andamento, o botão MUST indicar o estado "em andamento" e não
  aceitar um segundo acionamento.
- **FR-008**: Cada varredura MUST exibir a data e a hora em que foi executada (dd/mm/aaaa HH:MM),
  o total de produtos analisados, o total em alerta e quantos destes estão sem estoque. A
  varredura é calculada no momento em que é executada e não é registrada em histórico; a data/hora
  exibida é a do cálculo. O resultado de cada varredura acionada pelo usuário MUST ser anunciado a
  tecnologias assistivas (ex.: "Varredura concluída: 5 produtos em alerta (1 sem estoque) de 42
  analisados").
- **FR-009** *(Atividade, item 3 — "exibir um alerta visual destacado para aquele produto")*: O
  relatório MUST listar somente os produtos em alerta, na ordem de FR-006, com as colunas, nesta
  ordem: ID no formato `#0001`, nome, selo de situação ("⚠ REPOSIÇÃO NECESSÁRIA" ou
  "SEM ESTOQUE"), quantidade atual, estoque mínimo, déficit, cobertura (barra horizontal +
  percentual), sugestão de reposição e ações.
- **FR-010**: Quando houver produtos e nenhum em alerta, o relatório MUST exibir um estado vazio
  positivo ("Nenhum produto precisa de reposição") com o total analisado; quando não houver
  produtos cadastrados, MUST exibir um estado vazio que oriente a cadastrar o primeiro produto.
- **FR-011**: Cada linha do relatório MUST oferecer a ação rápida "+ Entrada", que abre o registro
  de entrada (feature 003) com o produto e o tipo "Entrada" já selecionados, sem sair do relatório.
- **FR-012**: Após qualquer movimentação confirmada na mesma janela, o relatório aberto MUST se
  atualizar sozinho (nova varredura), sem recarregar a página.
- **FR-013**: O relatório e a ação "Executar varredura" MUST funcionar também com os scripts do
  navegador desativados, por recarregamento completo da página.

**Alerta automático (História 2)**

- **FR-014** *(Atividade, item 3 — "varredura automática")*: O menu principal MUST exibir, em
  todas as páginas, um contador de produtos em alerta, recalculado automaticamente a cada 30
  segundos sem ação do usuário. Com os scripts do navegador desativados, o contador exibe o valor
  do momento em que a página foi carregada.
- **FR-015**: O contador MUST ser atualizado imediatamente após qualquer movimentação confirmada
  na mesma janela, sem recarregar a página, e MUST exibir o mesmo total da varredura mais recente
  executada no relatório.
- **FR-016**: Com 0 produtos em alerta, o contador MUST ficar oculto (o item de menu permanece);
  com 1 ou mais, MUST exibir ícone de alerta + número e um texto acessível
  ("N produtos em alerta de reposição").
- **FR-017**: Mudanças de valor do contador MUST ser anunciadas a tecnologias assistivas uma única
  vez por mudança; verificações que não mudam o valor MUST NOT gerar anúncio.
- **FR-018** *(Atividade, item 3 — "para aquele produto")*: A lista de produtos e o detalhe do
  produto MUST exibir, para cada produto, o selo de situação: "⚠ REPOSIÇÃO NECESSÁRIA" (em alerta
  com quantidade > 0), "SEM ESTOQUE" (quantidade 0) ou "OK" discreto, sem cor de alerta.
- **FR-019**: Quando uma movimentação (entrada ou saída) **piorar** a situação de um produto —
  OK → REPOSIÇÃO NECESSÁRIA, OK → SEM ESTOQUE ou REPOSIÇÃO NECESSÁRIA → SEM ESTOQUE — a mensagem
  de confirmação MUST incluir, em destaque de alerta, o aviso correspondente ("REPOSIÇÃO
  NECESSÁRIA" ou "SEM ESTOQUE") com o nome do produto, o saldo resultante e o mínimo. Quando a
  movimentação tirar o produto do alerta (→ OK), a confirmação MUST informar que ele saiu do
  alerta de reposição. Nos demais casos (situação inalterada, ou SEM ESTOQUE → REPOSIÇÃO
  NECESSÁRIA), MUST NOT haver aviso extra. O aviso vale tanto para a confirmação com a página
  atualizada parcialmente quanto para a confirmação após recarregamento.
- **FR-020**: O selo de situação MUST ser idêntico (texto, ícone, cor) em todas as telas onde
  aparece: relatório, lista e detalhe de produtos, painel. "SEM ESTOQUE" MUST ter destaque mais
  forte que "REPOSIÇÃO NECESSÁRIA" (cor de perigo em vez de cor de alerta), mantendo ícone e texto.
- **FR-021**: Nenhum alerta pode depender apenas de cor: todo selo ou contador de alerta MUST
  combinar ícone, texto e cor, com contraste mínimo WCAG 2.1 AA. Todas as ações desta feature
  ("Executar varredura", "Exportar CSV", "+ Entrada", atalhos do painel) MUST ser operáveis só
  pelo teclado, com foco visível.

**Painel (História 3)**

- **FR-022**: A página inicial MUST exibir quatro indicadores: produtos cadastrados; unidades em
  estoque (soma das quantidades atuais); produtos em alerta (com quantos sem estoque);
  movimentações de entrada e saída registradas nas últimas 24 horas.
- **FR-023**: O painel MUST exibir a lista "Reposição necessária" com até 5 produtos mais
  críticos (ordem de FR-006), cada um com selo e ação "+ Entrada", e um atalho para o relatório
  completo com o total em alerta; sem alertas, um estado vazio positivo.
- **FR-024**: O painel MUST exibir a lista de cobertura com até 8 produtos de menor cobertura, do
  menor para o maior percentual (empates pelo menor ID), cada um com barra horizontal
  proporcional (limitada visualmente a 100%) e o percentual; produtos com cobertura "não se
  aplica" ficam fora da lista; sem nenhum produto elegível, a lista exibe "Sem produtos com
  estoque mínimo definido".
- **FR-025**: O painel MUST exibir as 5 movimentações mais recentes (tipo, produto, quantidade,
  saldo resultante, data/hora); sem movimentações, exibe "Nenhuma movimentação registrada".
- **FR-026**: Indicadores e listas do painel MUST se atualizar sozinhos após qualquer
  movimentação confirmada na mesma janela, sem recarregar a página.

**Terminal (História 4)**

- **FR-027** *(Atividade, item 3 — paridade com a proposta original em console)*: O comando
  `varrer_estoque` MUST imprimir no terminal o relatório de reposição: data/hora, total analisado,
  total em alerta (e sem estoque) e uma linha por produto em alerta iniciada por
  "⚠ REPOSIÇÃO NECESSÁRIA" (com a indicação "SEM ESTOQUE" quando for o caso), na ordem de FR-006.
- **FR-028**: O comando MUST aceitar os formatos de saída texto (padrão), csv e json, todos com
  os mesmos produtos, valores e totais do relatório web.
- **FR-029**: Com a opção "falhar se houver alerta", o comando MUST terminar com código 1 quando
  existir ao menos um produto em alerta e 0 caso contrário; sem a opção, MUST terminar com 0;
  uso inválido (opção ou formato desconhecido) ou falha ao consultar o estoque MUST terminar com 2,
  sem imprimir relatório parcial.
- **FR-030**: O comando MUST oferecer uma opção para listar também os produtos fora de alerta,
  marcados "OK", após os produtos em alerta.
- **FR-031**: O comando MUST ser somente leitura: não altera saldos nem cria registros.

**Exportação (História 5)**

- **FR-032**: O relatório MUST oferecer "Exportar CSV", gerando um arquivo com as mesmas linhas,
  a mesma ordem e os mesmos valores da tela no momento da exportação. Formato: separador ";",
  codificação UTF-8 com BOM, uma linha de cabeçalho em português (ID; Produto; Quantidade atual;
  Estoque mínimo; Déficit; Cobertura (%); Sugestão de reposição; Situação), ID no formato `#0001`,
  números inteiros sem separador de milhar, cobertura vazia quando "não se aplica", e nome de
  arquivo `reposicao-AAAAMMDD-HHMM.csv` (data/hora da varredura). A saída csv do terminal
  (FR-028) MUST usar o mesmo layout, sem BOM.
- **FR-033**: Valores textuais exportados MUST ser protegidos contra interpretação como fórmula
  por planilhas (nomes iniciados por `=`, `+`, `-` ou `@`).

**Dados de demonstração (História 6)**

- **FR-034**: O comando `popular_demo` MUST criar um conjunto realista de pelo menos 12 produtos,
  com ao menos 3 em alerta, exatamente 1 sem estoque, ao menos 1 exatamente no mínimo e ao menos 1
  exatamente um acima do mínimo, com histórico de entradas e saídas; todo saldo MUST resultar de
  movimentações registradas (nenhum saldo definido diretamente).
- **FR-035**: O comando `popular_demo` MUST ser idempotente: execuções repetidas não criam
  duplicatas nem movimentações novas, não alteram produtos existentes e informam quantos itens
  foram criados e quantos já existiam.

**Transversais**

- **FR-036**: Datas e horas MUST ser exibidas no formato dd/mm/aaaa HH:MM no fuso horário do
  sistema; números na interface com separador de milhar "."; arquivos e saídas para máquina usam
  números sem separador.
- **FR-037**: Nenhuma função desta feature MUST alterar saldo de estoque, exceto `popular_demo`,
  que o faz exclusivamente por meio do registro de movimentações.

### Key Entities *(include if feature involves data)*

- **Produto** *(feature 002)*: ID numérico, nome, quantidade atual, estoque mínimo de segurança.
  Esta feature apenas lê esses dados.
- **Movimentação** *(feature 003)*: tipo (saldo inicial, entrada, saída), quantidade, saldo
  anterior e posterior, data/hora. Usada para os indicadores do painel, as últimas movimentações e
  para detectar mudanças de situação na confirmação.
- **Situação de estoque** *(derivada)*: OK, REPOSIÇÃO NECESSÁRIA ou SEM ESTOQUE, calculada pela
  regra de FR-002/FR-003.
- **Item de reposição** *(derivado)*: produto em alerta + déficit + cobertura + sugestão de
  reposição + situação.
- **Resultado de varredura** *(derivado, não armazenado)*: data/hora do cálculo, total
  analisado, total em alerta, total sem estoque e a lista ordenada de itens de reposição.
- **Indicadores do painel** *(derivados)*: totais de produtos, unidades, alertas e movimentações
  das últimas 24 h.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para os 5 casos de limite (abaixo, igual, um acima do mínimo; zerado com mínimo
  positivo; zerado com mínimo 0), 100% das telas, o contador, o terminal e o CSV apresentam a
  mesma situação para o mesmo produto.
- **SC-002**: Ao abrir o relatório, o produto mais crítico é sempre a primeira linha; um operador
  identifica o que repor primeiro em até 5 segundos.
- **SC-003**: Após confirmar uma movimentação, contador, relatório e painel abertos refletem a
  nova situação em até 1 segundo, sem recarregar a página.
- **SC-004**: Sem nenhuma interação do usuário, uma mudança de estoque feita em outra janela ou
  pelo terminal aparece no contador em até 30 segundos.
- **SC-005**: Com 1.000 produtos cadastrados, o relatório completo é exibido em até 2 segundos e
  o contador em até 0,5 segundo.
- **SC-006**: Para o mesmo estado do estoque, terminal (nos três formatos), relatório web e CSV
  listam exatamente os mesmos produtos, na mesma ordem e com os mesmos totais (concordância de
  100%).
- **SC-007**: 100% dos alertas exibidos combinam ícone + texto + cor; nenhum depende só de cor.
- **SC-008**: Registrar a sugestão de reposição como entrada tira o produto do alerta em 100% dos
  casos em que o dobro do mínimo cabe no teto de saldo.
- **SC-009**: Após `popular_demo` em base vazia, a apresentação mostra ao menos 3 alertas e 1
  produto sem estoque; uma segunda execução não altera nenhuma contagem.

## Assumptions

- As features 001 (fundação e design system), 002 (cadastro de produtos) e 003 (movimentações)
  estão implementadas antes desta; esta feature reutiliza o layout, os componentes, o diálogo de
  movimentação e o aviso de confirmação já existentes.
- Não há autenticação nem perfis nesta versão (como nas demais features): todos que acessam o
  sistema veem os mesmos alertas.
- Volume esperado de até cerca de 1.000 produtos; o relatório não é paginado.
- Uso principal em telas de computador; em telas estreitas a tabela do relatório rola
  horizontalmente dentro do próprio contêiner, sem rolagem horizontal da página.
- O intervalo de 30 segundos da verificação automática é um padrão ajustável por configuração do
  ambiente.
- O fuso horário do sistema é o de São Paulo (America/Sao_Paulo), configurado pela fundação.
- Por padrão o comando de terminal lista apenas produtos em alerta (como o relatório web); a
  listagem completa é opcional.
- A identidade de um produto de demonstração é o seu nome (sem diferenciar maiúsculas de
  minúsculas), coerente com a regra de nome único da feature 002.
- Movimentações de "saldo inicial" (cadastro) não contam como movimentação no indicador de 24 h,
  que considera apenas entradas e saídas; elas aparecem, porém, em "últimas movimentações".
- Fora de escopo: notificações externas (e-mail, mensagens), pedidos de compra automáticos,
  previsão de demanda, histórico de varreduras ou de alertas por produto e configuração do mínimo
  nesta feature (feita na 002).
