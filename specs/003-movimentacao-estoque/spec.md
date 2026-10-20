# Feature Specification: Controle de Movimentação — Entradas e Saídas

**Feature Branch**: `003-movimentacao-estoque`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Controle de Movimentação — Entradas e Saídas (item 2 da atividade). A função de atualizar o saldo do estoque. O operador registra uma Entrada (soma itens ao estoque atual) ou uma Saída/Venda (subtrai itens). Regra de validação: o estoque de um produto nunca pode ficar negativo. Inclui: formulário de movimentação (produto, tipo, quantidade inteira > 0, observação opcional até 200 caracteres), acessível por ações rápidas '+ Entrada' / '− Saída' na lista e no detalhe do produto (diálogo com produto e tipo preenchidos, saldo atual e prévia do saldo resultante) e por uma página de nova movimentação com seleção de produto; ao confirmar, saldo atualizado na hora, aviso de sucesso com saldo anterior → novo e aviso de 'estoque alterado' para o contador de alertas e o painel; saída maior que o saldo bloqueada sem gravar nada, com a mensagem 'Saldo insuficiente: disponível X, solicitado Y'; integridade sob concorrência; histórico imutável (livro-razão) com filtros por produto, tipo e período, paginação e histórico no detalhe do produto; a Quantidade Inicial do cadastro passa a gerar a movimentação de saldo inicial na mesma operação; paridade de terminal opcional (comando movimentar)."

## Contexto

Esta feature implementa o **item 2 da atividade** (SENAI-SP): *"O app precisa de uma função para
atualizar o saldo do estoque. Deve ser possível registrar uma Entrada (somando novos itens ao
estoque atual) e uma Saída/Venda (subtraindo itens do estoque atual). Regra de validação: o
sistema não pode permitir que o estoque de um produto fique negativo."*

Ela depende do cadastro de produtos (feature 002), que fornece o produto com ID numérico, nome,
saldo atual e estoque mínimo, e alimenta o alerta de reposição (feature 004), que reage a toda
mudança de saldo. Toda mudança de saldo passa a ser explicada por um registro de movimentação
imutável (livro-razão).

## Clarifications

### Session 2026-10-20

- Q: Quando a Quantidade Inicial informada no cadastro for 0, o sistema deve registrar mesmo assim a movimentação "Saldo inicial"? → A: Sim — todo produto começa o histórico com exatamente uma movimentação "Saldo inicial", inclusive de quantidade 0 (saldo 0 → 0).
- Q: Depois de registrar uma movimentação com sucesso pela página Nova movimentação, o que o operador deve ver? → A: A própria página Nova movimentação, pronta para o próximo registro: mesmo produto e tipo pré-selecionados, quantidade e observação vazias, saldo atual já atualizado e o aviso de sucesso — igual com ou sem o aprimoramento interativo.
- Q: Quantas movimentações o detalhe do produto deve exibir? → A: As 10 mais recentes, com o link "Ver histórico completo" que abre a página Movimentações já filtrada por aquele produto.
- Q: Existe limite máximo para a quantidade de uma movimentação e para o saldo? → A: Sim — Entrada e Saída aceitam no máximo 1.000.000 unidades por movimentação, e nenhum saldo pode passar de 2.147.483.647 unidades (uma Entrada que ultrapassaria esse teto é recusada com "Saldo máximo excedido: atual X, entrada Y, máximo 2.147.483.647"); o Saldo inicial respeita apenas o teto de saldo.
- Q: Quando duas saídas do mesmo produto são confirmadas ao mesmo tempo, o que acontece com a que chega em segundo lugar? → A: Ela aguarda a primeira terminar e é avaliada com o saldo já atualizado — aceita se couber, recusada com "Saldo insuficiente: disponível X, solicitado Y" se não couber; o operador nunca recebe um erro genérico de "tente novamente".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar Entrada e Saída sem jamais negativar o saldo (Priority: P1)

O operador de estoque abre a página **Nova movimentação**, escolhe o produto (identificado por
#ID e nome), escolhe o tipo **Entrada** ou **Saída/Venda**, informa a quantidade e, se quiser, uma
observação (nº da nota, cliente). Ao confirmar, o saldo do produto é somado (Entrada) ou subtraído
(Saída) e o operador vê a confirmação com o saldo anterior e o novo. Se a saída pedir mais do que
existe em estoque, o sistema recusa, não grava nada e explica quanto há disponível.

**Why this priority**: é o coração do item 2 da atividade — a função de atualizar o saldo com a
regra de que o estoque nunca fica negativo. Sem ela não há controle de estoque.

**Independent Test**: com um produto de saldo 10 já cadastrado, registrar uma Entrada de 5
(saldo 15), uma Saída de 15 (saldo 0) e tentar uma Saída de 1 (recusada, saldo continua 0, nenhum
registro novo). Entrega valor sozinha: o operador já controla o saldo de qualquer produto.

**Acceptance Scenarios**:

1. **Given** o produto #0001 com saldo 10, **When** o operador registra uma Entrada de 5,
   **Then** o saldo passa a 15, é exibida a confirmação "Entrada registrada: #0001 … — saldo 10 → 15"
   e a página Nova movimentação volta pronta para o próximo registro (mesmo produto e tipo
   pré-selecionados, quantidade e observação vazias, saldo atual 15).
2. **Given** o produto #0001 com saldo 15, **When** o operador registra uma Saída/Venda de 4 com a
   observação "NF 123", **Then** o saldo passa a 11 e a movimentação guarda a observação.
3. **Given** o produto #0001 com saldo 11, **When** o operador registra uma Saída de 11,
   **Then** a saída é aceita e o saldo fica 0 (zerar é permitido).
4. **Given** o produto #0001 com saldo 3, **When** o operador tenta uma Saída de 5,
   **Then** nada é gravado, o saldo continua 3, o formulário é reapresentado com os valores
   digitados e a mensagem "Saldo insuficiente: disponível 3, solicitado 5".
5. **Given** qualquer produto, **When** o operador informa quantidade 0, negativa, fracionária,
   não numérica, vazia ou acima de 1.000.000, **Then** nada é gravado e o campo quantidade exibe
   uma mensagem específica.
6. **Given** o produto #0001 com saldo 10, **When** duas saídas de 6 unidades são confirmadas ao
   mesmo tempo (por dois operadores), **Then** a segunda aguarda a primeira, apenas uma é aceita,
   a outra é recusada com "Saldo insuficiente: disponível 4, solicitado 6" e o saldo final é 4.
7. **Given** o navegador sem o aprimoramento interativo, **When** o
   operador registra uma movimentação pela página, **Then** o fluxo funciona por envio
   tradicional, com as mesmas regras e mensagens.

---

### User Story 2 - Ações rápidas a partir do produto com atualização imediata (Priority: P2)

Na lista de produtos e na página de detalhe de um produto, cada produto oferece as ações rápidas
**"+ Entrada"** e **"− Saída"**. Elas abrem um diálogo já com o produto e o tipo preenchidos,
mostrando o saldo atual e uma prévia do saldo resultante enquanto o operador digita a quantidade.
Ao confirmar, o diálogo fecha, o saldo exibido na linha (ou no detalhe) muda na hora, sem
recarregar a página, aparece um aviso de sucesso com saldo anterior → novo, e os indicadores de
alerta de reposição (contador e painel) se atualizam sozinhos.

**Why this priority**: é o caminho mais rápido do dia a dia (registrar a venda direto da linha do
produto), mas depende do fluxo da US1 já funcionar.

**Independent Test**: na lista de produtos, clicar "− Saída" no produto de saldo 10, digitar 3,
ver a prévia "saldo após: 7", confirmar e observar a linha mostrar 7 sem recarregar, o aviso de
sucesso "10 → 7" e o contador de alertas reagir.

**Acceptance Scenarios**:

1. **Given** a lista de produtos, **When** o operador aciona "+ Entrada" no produto #0002,
   **Then** abre um diálogo com o produto #0002 e o tipo Entrada já selecionados, o saldo atual
   visível e o foco no campo quantidade.
2. **Given** o diálogo de Saída aberto para um produto de saldo 10, **When** o operador digita 3,
   **Then** a prévia mostra "saldo após: 7"; **When** digita 12, **Then** a prévia avisa que o
   saldo é insuficiente (disponível 10, solicitado 12) antes de confirmar.
3. **Given** o diálogo preenchido corretamente, **When** o operador confirma, **Then** o diálogo
   fecha, o saldo da linha (ou do detalhe) é atualizado sem recarregar a página, um aviso de
   sucesso mostra o saldo anterior → novo e os indicadores dependentes do estoque são avisados
   da mudança.
4. **Given** o diálogo de Saída com quantidade acima do saldo, **When** o operador confirma,
   **Then** o diálogo continua aberto com a mensagem "Saldo insuficiente: disponível X,
   solicitado Y", os valores digitados preservados e o saldo exibido inalterado.
5. **Given** o navegador sem o aprimoramento interativo, **When** o operador aciona "+ Entrada"
   ou "− Saída", **Then** ele é levado à página Nova movimentação com o produto e o tipo
   pré-selecionados.
6. **Given** a página de detalhe do produto, **When** uma movimentação é confirmada pelo diálogo,
   **Then** o saldo e o histórico exibidos no detalhe passam a refletir a nova movimentação.

---

### User Story 3 - Consultar o histórico imutável (livro-razão) (Priority: P2)

O operador (ou o professor, ao avaliar) abre a página **Movimentações** e vê todas as
movimentações, das mais recentes para as mais antigas: data/hora, produto (#ID + nome), tipo
(selo), quantidade com sinal (+/−), saldo anterior → posterior e observação. Pode filtrar por
produto, por tipo e por período, e navegar por páginas. No detalhe de cada produto aparece o
histórico daquele produto. Nenhuma movimentação pode ser editada ou apagada pela interface.

**Why this priority**: dá rastreabilidade e auditoria ao saldo (por que o saldo é 7?), essencial
para confiar no controle, mas o registro (US1) vem antes.

**Independent Test**: com movimentações de dois produtos em datas diferentes, abrir a página
Movimentações, filtrar pelo produto #0001 e pelo tipo Saída num período e conferir que só as
linhas correspondentes aparecem, com sinais e saldos corretos, e que não há ação de editar ou
excluir.

**Acceptance Scenarios**:

1. **Given** 30 movimentações registradas, **When** o operador abre a página Movimentações,
   **Then** vê as 25 mais recentes na primeira página e consegue ir à página seguinte.
2. **Given** movimentações de vários produtos e tipos, **When** o operador filtra por produto
   #0001 e tipo Saída/Venda, **Then** só aparecem saídas do produto #0001, e o endereço da página
   reflete os filtros (pode ser compartilhado ou recarregado com o mesmo resultado).
3. **Given** movimentações em dias diferentes, **When** o operador filtra o período de 01/10/2026 a
   15/10/2026, **Then** aparecem apenas as movimentações registradas nesses dias, inclusive os
   dias das pontas.
4. **Given** filtros sem resultado, **When** a lista é exibida, **Then** aparece um estado vazio
   explicativo com a opção de limpar os filtros.
5. **Given** qualquer movimentação exibida, **When** o operador procura editar ou excluir,
   **Then** não existe essa opção em nenhuma tela.
6. **Given** o detalhe do produto #0001 com 14 movimentações, **When** o operador o abre,
   **Then** vê as 10 movimentações mais recentes desse produto, das mais recentes para as mais
   antigas, e o link "Ver histórico completo", que abre a página Movimentações já filtrada pelo
   produto #0001.

---

### User Story 4 - Saldo inicial registrado como primeira movimentação (Priority: P2)

Quando um produto é cadastrado (feature 002) com uma Quantidade Inicial, o sistema registra
automaticamente a primeira movimentação do histórico, do tipo **Saldo inicial**, com saldo
anterior 0 e saldo posterior igual à quantidade informada, na mesma operação do cadastro. Assim,
o saldo de qualquer produto é sempre explicado pela soma das suas movimentações.

**Why this priority**: fecha a auditoria do saldo desde o primeiro dia; sem ela o histórico não
explica o saldo de produtos cadastrados com estoque.

**Independent Test**: cadastrar o produto "Parafuso" com Quantidade Inicial 10 e conferir que o
histórico dele tem exatamente uma movimentação "Saldo inicial" 0 → 10 e que o saldo atual é 10.

**Acceptance Scenarios**:

1. **Given** o cadastro de produto, **When** o operador cadastra "Parafuso" com Quantidade
   Inicial 10, **Then** o produto nasce com saldo 10 e uma movimentação "Saldo inicial" de 10
   (0 → 10).
2. **Given** o cadastro de produto, **When** o operador cadastra "Arruela" com Quantidade
   Inicial 0, **Then** o produto nasce com saldo 0 e uma movimentação "Saldo inicial" de 0 (0 → 0).
3. **Given** um cadastro que falha por qualquer motivo, **When** a operação é desfeita, **Then**
   nem o produto nem a movimentação de saldo inicial ficam gravados.
4. **Given** a página Nova movimentação, **When** o operador escolhe o tipo, **Then** "Saldo
   inicial" não está entre as opções (só o cadastro o gera).
5. **Given** produtos cadastrados antes desta feature existir (sem histórico), **When** a feature
   é instalada, **Then** cada um recebe uma movimentação "Saldo inicial" equivalente ao seu saldo
   atual (inclusive 0), de modo que o histórico explique o saldo.

---

### User Story 5 - Movimentar pelo terminal (Priority: P3)

Para manter a paridade com o formato de console da atividade, o operador pode registrar uma
movimentação pelo terminal com o comando `movimentar <id> entrada|saida <quantidade> [--obs "..."]`,
sujeito às mesmas regras, mensagens e histórico da interface web.

**Why this priority**: opcional; útil para demonstração e automação, mas a interface web já
cobre o requisito.

**Independent Test**: executar `movimentar 1 saida 3 --obs "Venda balcão"` para um produto de
saldo 10 e ver a resposta "Saída registrada: #0001 … — saldo 10 → 7"; executar
`movimentar 1 saida 50` e ver a recusa "Saldo insuficiente: disponível 7, solicitado 50" com
código de saída de erro.

**Acceptance Scenarios**:

1. **Given** o produto #0001 com saldo 10, **When** o operador executa `movimentar 1 entrada 5`,
   **Then** o terminal exibe "Entrada registrada: #0001 … — saldo 10 → 15" e o comando termina
   com sucesso.
2. **Given** o produto #0001 com saldo 7, **When** o operador executa `movimentar 1 saida 50`,
   **Then** o terminal exibe "Saldo insuficiente: disponível 7, solicitado 50", nada é gravado e
   o comando termina com código de erro.
3. **Given** um ID inexistente ou quantidade inválida, **When** o comando é executado, **Then**
   uma mensagem clara é exibida, nada é gravado e o comando termina com código de erro.

---

### Edge Cases

- Saída exatamente igual ao saldo: aceita; o saldo vai a 0 e o produto passa a satisfazer a
  condição de alerta de reposição (feature 004), que reage ao aviso de estoque alterado.
- Saída com saldo 0: a ação "− Saída" continua disponível; o diálogo mostra saldo 0, a prévia
  avisa a insuficiência e a confirmação é recusada com "Saldo insuficiente: disponível 0,
  solicitado Y".
- Quantidade 0, negativa, fracionária (2,5 ou 2.5), com letras, vazia ou só espaços: recusada
  com mensagem no campo; nada gravado.
- Quantidade digitada com separador de milhar ("1.000"): recusada com a orientação de digitar
  só algarismos (evita que "1.000" seja lido como 1); nada gravado.
- Quantidade acima de 1.000.000 em uma Entrada ou Saída: recusada com mensagem no campo
  ("Informe no máximo 1.000.000"); nada gravado.
- Entrada que levaria o saldo acima de 2.147.483.647: recusada com "Saldo máximo excedido: atual
  X, entrada Y, máximo 2.147.483.647"; nada gravado.
- Observação com mais de 200 caracteres: recusada com mensagem; observação só com espaços é
  tratada como vazia; espaços nas pontas são removidos.
- Produto inexistente (ID manipulado no endereço ou no formulário): recusado com mensagem no
  campo produto; pré-seleção inválida no endereço é ignorada (formulário abre sem produto).
- Tipo inválido ou "Saldo inicial" enviado manualmente pelo formulário: recusado.
- O saldo mudou entre abrir o diálogo e confirmar (outro operador movimentou): a decisão usa o
  saldo no momento da confirmação; se insuficiente, a mensagem mostra o disponível atualizado e o
  formulário reapresentado exibe o saldo atual.
- Duplo clique em "Confirmar": com o aprimoramento interativo, o botão fica indisponível durante
  o processamento; sem ele, recarregar a página após o sucesso não reenvia o formulário
  (FR-020).
- Duas ou mais saídas simultâneas do mesmo produto: são processadas uma de cada vez sobre o
  saldo mais recente; nunca levam o saldo abaixo de zero e as excedentes recebem a mensagem de
  saldo insuficiente (nunca um erro genérico).
- Falha inesperada durante o registro: nada é gravado (nem movimentação nem alteração de saldo).
- Histórico vazio (nenhuma movimentação, ou filtros sem resultado): estado vazio projetado com
  orientação e ação.
- Período invertido (data inicial depois da final), data em formato inválido, produto ou tipo
  inexistente no endereço: o operador é avisado e o filtro inválido não é aplicado (os demais
  continuam valendo).
- Página do histórico fora do intervalo (ex.: página 999): exibe a última página existente.
- Produtos cadastrados antes desta feature: recebem a movimentação de saldo inicial retroativa.

## Requirements *(mandatory)*

### Functional Requirements

**Registro de movimentação (núcleo do item 2 da atividade)**

- **FR-001**: O sistema MUST oferecer uma função única para atualizar o saldo de estoque de um
  produto, por meio do registro de uma movimentação; nenhuma outra via (cadastro/edição de
  produto, administração ou acesso direto) pode alterar o saldo. *(Atividade, item 2: "função
  para atualizar o saldo do estoque".)*
- **FR-002**: O operador MUST poder registrar uma **Entrada**, que soma a quantidade informada ao
  saldo atual do produto. *(Atividade, item 2: "registrar uma Entrada (somando novos itens ao
  estoque atual)".)*
- **FR-003**: O operador MUST poder registrar uma **Saída/Venda**, que subtrai a quantidade
  informada do saldo atual do produto. *(Atividade, item 2: "registrar uma Saída/Venda
  (subtraindo itens do estoque atual)".)*
- **FR-004**: O sistema MUST impedir que o saldo de qualquer produto fique negativo: uma saída
  cuja quantidade exceda o saldo disponível é recusada por inteiro, nada é gravado (nem a
  movimentação nem a alteração de saldo) e o operador vê a mensagem
  "Saldo insuficiente: disponível X, solicitado Y". Uma saída igual ao saldo é permitida e zera o
  saldo. *(Atividade, item 2 — regra de validação: "não pode permitir que o estoque de um produto
  fique negativo".)*
- **FR-005**: A quantidade de uma Entrada ou Saída MUST ser um número inteiro entre 1 e
  1.000.000, digitado apenas com algarismos (sem separador de milhar nem casas decimais); valores
  zero, negativos, fracionários, com separadores (ex.: "1.000"), não numéricos, vazios ou acima de
  1.000.000 são recusados com mensagem específica no campo e nada é gravado. Nenhum saldo pode ultrapassar
  2.147.483.647 unidades: uma Entrada que levaria o saldo acima desse teto é recusada com
  "Saldo máximo excedido: atual X, entrada Y, máximo 2.147.483.647" e nada é gravado.
- **FR-006**: A observação MUST ser opcional, com no máximo 200 caracteres (ex.: nº da nota
  fiscal, cliente); espaços nas pontas são removidos e textos maiores são recusados com mensagem.
- **FR-007**: O registro MUST exigir um produto existente e um tipo entre **Entrada** e
  **Saída/Venda**; o tipo **Saldo inicial** nunca é selecionável pelo operador.
- **FR-008**: O sistema MUST manter a regra do FR-004 mesmo quando várias movimentações do mesmo
  produto são confirmadas ao mesmo tempo: elas são processadas uma de cada vez, cada uma
  aguardando a anterior e sendo avaliada sobre o saldo já atualizado; as saídas aceitas nunca
  somam mais do que o saldo disponível e as excedentes são recusadas com a mensagem do FR-004,
  nunca com um erro genérico.
- **FR-009**: A regra do FR-004 MUST ser garantida em camadas independentes — na validação do
  formulário, na regra de negócio executada ao confirmar e no próprio armazenamento de dados —,
  de modo que nenhuma gravação que deixe saldo negativo seja aceita, mesmo que contorne a
  interface.
- **FR-010**: Cada movimentação MUST registrar: produto, tipo, quantidade, saldo anterior, saldo
  posterior, observação e data/hora do registro; o saldo posterior é o anterior somado à
  quantidade (Entrada e Saldo inicial) ou subtraído dela (Saída/Venda).
- **FR-011**: O registro da movimentação e a atualização do saldo MUST acontecer como uma única
  operação indivisível: ou ambos são gravados, ou nenhum.

**Ações rápidas, diálogo e retorno ao operador**

- **FR-012**: O sistema MUST oferecer a página **Nova movimentação**, com seleção do produto
  (lista ordenada por nome, cada opção exibida como "#0001 — Nome"), do tipo, da quantidade e da observação, que pode ser aberta já com
  produto e/ou tipo pré-selecionados. Após um registro bem-sucedido nessa página, ela é
  reapresentada pronta para o próximo registro — mesmo produto e tipo pré-selecionados,
  quantidade e observação vazias e saldo atual atualizado —, com e sem o aprimoramento
  interativo.
- **FR-013**: Cada linha da lista de produtos e a página de detalhe do produto MUST oferecer as
  ações rápidas **"+ Entrada"** e **"− Saída"**, que abrem um diálogo com produto e tipo
  preenchidos; sem o aprimoramento interativo, as mesmas ações levam à página Nova movimentação
  com produto e tipo pré-selecionados.
- **FR-014**: O formulário (página e diálogo) MUST exibir o saldo atual do produto selecionado e
  uma prévia do saldo resultante conforme a quantidade digitada, avisando antes da confirmação
  quando a saída excederia o saldo ou a entrada ultrapassaria o saldo máximo (com o mesmo texto da
  recusa); sem produto selecionado, a prévia orienta a escolher um, e com quantidade vazia ou
  inválida mostra só o saldo atual. A prévia é anunciada de forma discreta a leitores de tela, é
  informativa e a decisão final é sempre feita no momento da confirmação.
- **FR-015**: Após uma movimentação bem-sucedida pelo diálogo, o sistema MUST fechar o diálogo e
  atualizar imediatamente, sem recarregar a página, o saldo exibido na linha da lista ou no
  detalhe do produto (e o histórico exibido no detalhe).
- **FR-016**: Após toda Entrada ou Saída bem-sucedida, o sistema MUST exibir um aviso de sucesso
  com o tipo, o produto (#ID e nome) e o saldo anterior → novo (ex.: "Saída registrada: #0001 Parafuso —
  saldo 10 → 7").
- **FR-017**: Após toda Entrada ou Saída bem-sucedida, o sistema MUST avisar a interface de que o
  estoque foi alterado, para que o contador de alertas de reposição e o painel (feature 004) se
  atualizem sem recarregar a página. O mesmo aviso após o cadastro de produto (que gera o Saldo
  inicial) é responsabilidade da tela de cadastro da feature 002.
- **FR-018**: Em caso de recusa (saldo insuficiente ou dado inválido), o sistema MUST reapresentar
  o formulário no mesmo lugar (diálogo ou página), com os valores digitados preservados, a
  mensagem de erro associada ao campo e o saldo atual exibido; nada é gravado e o saldo exibido
  em outras partes da tela não muda.
- **FR-019**: Todo o fluxo de registro MUST funcionar sem o aprimoramento interativo (envio
  tradicional de formulário), com as mesmas regras, mensagens e resultado gravado.
- **FR-020**: Com o aprimoramento interativo ativo, o botão de confirmar MUST ficar indisponível
  durante o processamento, evitando o envio duplicado acidental. Sem o aprimoramento, o
  redirecionamento após o envio bem-sucedido impede o reenvio ao recarregar a página; o duplo
  clique nesse modo é um risco residual aceito (cada envio é uma movimentação válida e visível no
  histórico, corrigível com uma movimentação oposta).

**Histórico imutável (livro-razão)**

- **FR-021**: As movimentações MUST ser imutáveis: nenhuma tela permite editar ou excluir uma
  movimentação, e o sistema recusa qualquer tentativa de alterá-la ou apagá-la depois de gravada;
  correções são feitas registrando uma nova movimentação de sentido oposto, com observação.
- **FR-022**: O sistema MUST oferecer a página **Movimentações**, listando as movimentações das
  mais recentes para as mais antigas, com as colunas: data/hora (dd/mm/aaaa HH:MM), produto (#ID
  com 4 dígitos + nome, com acesso ao detalhe do produto), tipo (selo com texto: "Saldo inicial",
  "Entrada", "Saída/Venda"), quantidade com sinal (+ para Entrada e Saldo inicial, − para Saída),
  saldo anterior → posterior e observação.
- **FR-023**: A página Movimentações MUST permitir filtrar por produto, por tipo e por período
  (data inicial e data final, inclusivas), de forma combinável; os filtros ficam refletidos no
  endereço da página e são preservados ao navegar entre páginas.
- **FR-024**: A página Movimentações MUST ser paginada com 25 movimentações por página.
- **FR-025**: A página de detalhe do produto MUST exibir as 10 movimentações mais recentes daquele
  produto, das mais recentes para as mais antigas, com as mesmas colunas da página Movimentações
  exceto a coluna produto, e o link "Ver histórico completo", que abre a página Movimentações
  filtrada por esse produto.
- **FR-026**: Listas de movimentação sem resultado MUST exibir um estado vazio explicativo com uma
  ação (limpar filtros ou registrar movimentação); filtros inválidos — produto inexistente, tipo
  desconhecido, data malformada ou data inicial posterior à final — são sinalizados ao operador e
  não são aplicados, mantendo-se os demais filtros válidos.

**Saldo inicial e consistência do saldo**

- **FR-027**: Ao cadastrar um produto (feature 002), a Quantidade Inicial MUST gerar
  automaticamente a movimentação **Saldo inicial** (saldo anterior 0, saldo posterior igual à
  quantidade inicial) na mesma operação indivisível do cadastro, inclusive quando a Quantidade
  Inicial é 0. *(Atividade, item 1: "Quantidade Inicial", integrada ao item 2.)*
- **FR-028**: A movimentação Saldo inicial MUST ser gerada apenas pelo cadastro (ou pela carga
  retroativa do FR-030), exatamente uma vez por produto, e ser sempre a primeira do histórico do
  produto.
- **FR-029**: Para todo produto, o saldo atual MUST ser igual à soma das suas movimentações
  (Saldo inicial + Entradas − Saídas), e o saldo posterior de cada movimentação MUST ser igual ao
  saldo anterior da movimentação seguinte do mesmo produto, na ordem de registro (data/hora do
  registro e, em empate, ordem de gravação).
- **FR-030**: Produtos que já existirem sem histórico quando esta feature for instalada MUST
  receber uma movimentação Saldo inicial equivalente ao seu saldo atual (inclusive 0).

**Terminal, acessibilidade e apresentação**

- **FR-031**: O sistema SHOULD oferecer o comando de terminal
  `movimentar <id> entrada|saida <quantidade> [--obs "..."]`, que aplica as mesmas regras da
  interface, informa o saldo anterior → novo em caso de sucesso e, em caso de recusa, exibe a
  mesma mensagem, não grava nada e termina com código de erro.
- **FR-032**: Mensagens de sucesso e de erro MUST ser anunciadas a leitores de tela; o diálogo MUST
  ser operável por teclado (foco inicial no campo quantidade, Esc fecha, o foco volta à ação que o
  abriu); as ações rápidas MUST ter nome acessível que inclua o produto (ex.: "Registrar saída de
  #0001 Parafuso").
- **FR-033**: Entradas e saídas MUST ser diferenciadas por sinal e texto, nunca apenas por cor;
  números são exibidos com separador de milhar "." e datas no formato dd/mm/aaaa HH:MM.

### Key Entities *(include if feature involves data)*

- **Movimentação**: registro imutável de uma mudança de saldo de um produto. Atributos: produto,
  tipo (Saldo inicial, Entrada, Saída/Venda), quantidade (inteiro; maior que zero, exceto no
  Saldo inicial, que aceita 0; no máximo 1.000.000 em Entrada e Saída), saldo anterior, saldo
  posterior, observação (até 200 caracteres, opcional) e data/hora do registro. Pertence a
  exatamente um produto; todo produto tem exatamente uma movimentação de Saldo inicial (a
  primeira) e zero ou mais Entradas e Saídas.
- **Produto** *(definido na feature 002)*: item de estoque com ID numérico automático (exibido
  como #0001), nome, saldo atual (nunca negativo) e estoque mínimo de segurança. Nesta feature, o
  saldo atual só muda por meio de movimentações, e um produto com movimentações não pode ser
  removido.
- **Tipo de movimentação**: Saldo inicial (gerado só pelo cadastro), Entrada (soma) e
  Saída/Venda (subtrai).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir da lista de produtos, o operador registra uma entrada ou uma saída em no
  máximo 3 interações (acionar a ação rápida, digitar a quantidade, confirmar) e em menos de 15
  segundos.
- **SC-002**: Em 100% das tentativas de saída maior que o saldo, o saldo permanece inalterado e
  maior ou igual a zero, nenhuma movimentação é gravada e a mensagem informa o disponível e o
  solicitado.
- **SC-003**: Sob tentativas simultâneas de saída do mesmo produto, o saldo nunca fica negativo:
  com saldo 10 e 20 saídas simultâneas de 1 unidade, exatamente 10 são aceitas, 10 são recusadas
  com a mensagem de saldo insuficiente, o saldo final é 0 e o histórico tem exatamente 10 saídas
  novas; com saldo 10 e duas saídas simultâneas de 6, exatamente uma é aceita e o saldo final é
  4. O resultado se repete em 100% de 20 execuções consecutivas da verificação, sem nenhum erro
  inesperado.
- **SC-004**: Em qualquer momento, para 100% dos produtos, o saldo atual é igual à soma das suas
  movimentações e a sequência de saldos anterior → posterior do histórico é contínua.
- **SC-005**: Após a confirmação de uma movimentação, o saldo exibido e os indicadores de alerta
  de reposição refletem a mudança em até 1 segundo, sem recarregar a página.
- **SC-006**: Nenhuma tela oferece edição ou exclusão de movimentação, e 100% das tentativas de
  alterar ou apagar uma movimentação gravada são recusadas.
- **SC-007**: O operador encontra as movimentações de um produto em um período em no máximo 3
  interações, e a primeira página do histórico é exibida em menos de 1 segundo com até 100.000
  movimentações registradas.
- **SC-008**: 100% dos fluxos de registro (entrada, saída, recusa) e de consulta do histórico
  funcionam com o aprimoramento interativo desativado.

## Assumptions

- Não há autenticação nem perfis de usuário nesta versão (igual às demais features): o operador
  é confiável e a movimentação não registra o autor.
- A feature 001 fornece o layout base, os componentes (diálogo, aviso/toast, selo, tabela, campo,
  estado vazio) e a exibição de mensagens; a feature 002 fornece o produto, a lista, o detalhe e
  o serviço de cadastro, que esta feature estende para gerar o Saldo inicial.
- Endereços das páginas, nomes de eventos de interface e códigos de resposta seguem o contrato de
  arquitetura do projeto (`docs/arquitetura.md`) e são detalhados no plano.
- Quantidades são unidades inteiras, sem unidade de medida, custo ou preço (fora de escopo).
- Não há estorno automático nem exclusão de produtos; correções são feitas com uma movimentação
  de sentido oposto, com observação explicativa.
- Datas e horas são exibidas e filtradas no fuso horário de Brasília (America/Sao_Paulo).
- Volume esperado: até cerca de 1.000 produtos e 100.000 movimentações; a seleção de produto por
  lista simples (#ID — nome) é adequada a esse volume.
- Exportação do histórico (CSV, PDF) está fora de escopo.
