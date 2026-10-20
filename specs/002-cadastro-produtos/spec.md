# Feature Specification: Cadastro de Produtos

**Feature Branch**: `002-cadastro-produtos`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Cadastro de Novos Produtos (item 1 da atividade). O operador registra um produto informando Nome, Quantidade Inicial e Estoque Mínimo de Segurança; o sistema atribui um ID numérico automático (exibido como `#0001`) que facilita a busca. Inclui: formulário de cadastro (página própria e diálogo aberto a partir da lista) com validação inline — nome obrigatório, aparado, até 120 caracteres, único sem diferenciar maiúsculas/minúsculas; quantidade inicial e estoque mínimo inteiros ≥ 0; mensagens em pt-BR junto ao campo; após salvar, o novo produto aparece no topo da lista com destaque e um toast 'Produto #0007 cadastrado'; listagem densa (ID, nome, quantidade atual, estoque mínimo, situação) com busca instantânea por ID (`12`, `#12`, `#0012`) ou parte do nome, filtro por situação (todos / em alerta / ok), ordenação por colunas, paginação de 25, URL refletindo busca/filtro e estado vazio projetado; página de detalhe com espaço reservado para Entrada/Saída e histórico (feature 003); edição de nome e estoque mínimo (quantidade não editável; exclusão fora de escopo); atalhos `/` (focar busca) e `n` (novo produto). Contrato `produtos.services.cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo) -> Produto`, que nesta feature apenas define a quantidade atual."

## Clarifications

### Session 2026-10-20

- Q: Quando o termo de busca é formado só por algarismos (ex.: `12`), a busca deve trazer apenas o produto com esse ID ou também produtos cujo nome contém esse número? → A: Ambos — o produto de ID exato 12 e os produtos cujo nome contém "12"; com o prefixo `#` (`#12`, `#0012`) a busca considera somente o ID.
- Q: Qual deve ser a ordenação padrão da lista de produtos? → A: ID decrescente (cadastrados mais recentemente primeiro); em qualquer ordenação, empates são desfeitos pelo ID decrescente.
- Q: Existe um valor máximo para Quantidade Inicial e Estoque Mínimo? → A: Não há teto de negócio; vale o limite técnico de 2.147.483.647, e valores acima dele são recusados com mensagem em português.
- Q: Na comparação de nomes, espaços internos repetidos e acentos contam como diferença? → A: Espaços internos consecutivos são reduzidos a um só ao gravar ("Caneta  Azul" vira "Caneta Azul"); acentos contam como diferença ("Café" ≠ "Cafe"); maiúsculas/minúsculas não.
- Q: Quantidade Inicial e Estoque Mínimo podem ficar em branco e assumir zero? → A: Não — ambos são obrigatórios e começam vazios no formulário; o operador digita 0 explicitamente quando for o caso.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar um novo produto (Priority: P1)

O operador de estoque passa a controlar um novo item. Ele informa **Nome**, **Quantidade
Inicial** e **Estoque Mínimo de Segurança** — numa página própria ou num diálogo aberto a
partir da lista, sem perder o contexto. O sistema valida os dados campo a campo, atribui um
**ID numérico automático** e confirma o cadastro exibindo o produto no topo da lista, com
destaque, e a notificação "Produto #0007 cadastrado".

**Why this priority**: é o requisito 1 da atividade e a base de todo o sistema — sem produto
cadastrado não há movimentação (feature 003) nem alerta de reposição (feature 004). Sozinha,
esta história já entrega um catálogo de produtos com ID utilizável.

**Independent Test**: com a base vazia, cadastrar três produtos (dois pela página própria e um
pelo diálogo) e verificar que recebem `#0001`, `#0002` e `#0003`, que cada um aparece no topo da
lista com destaque e notificação, e que entradas inválidas são recusadas com mensagens junto ao
campo, sem gravar nada.

**Acceptance Scenarios**:

1. **Dado** que não há produtos cadastrados, **Quando** o operador informa Nome "Caneta Azul",
   Quantidade Inicial 50 e Estoque Mínimo 10 e salva, **Então** o produto é criado com ID
   `#0001`, quantidade atual 50 e estoque mínimo 10, aparece no topo da lista com destaque e a
   notificação "Produto #0001 cadastrado" é exibida.
2. **Dado** que o último produto cadastrado é o `#0006`, **Quando** um novo produto válido é
   salvo, **Então** ele recebe o ID `#0007`, sem que o operador informe ou possa alterar o ID.
3. **Dado** que existe o produto `#0001` "Caneta Azul", **Quando** o operador tenta cadastrar
   "  caneta   AZUL  ", **Então** o cadastro é recusado com a mensagem "Já existe um produto com
   este nome (#0001)." junto ao campo Nome, e os valores digitados nos demais campos são
   preservados.
4. **Dado** o formulário de cadastro, **Quando** o operador deixa o Nome vazio, informa
   Quantidade Inicial "-5" e Estoque Mínimo "2,5" e salva, **Então** nada é gravado e cada campo
   exibe sua própria mensagem de erro em português (FR-007).
5. **Dado** o formulário de cadastro recém-aberto, **Quando** o operador observa os campos
   numéricos, **Então** eles estão vazios; **e quando** salva sem preenchê-los, **Então** recebe
   "Informe a quantidade inicial." e "Informe o estoque mínimo." junto aos campos.
6. **Dado** que o operador está na lista, **Quando** abre o cadastro em diálogo e salva dados
   válidos, **Então** o diálogo fecha, a lista é atualizada sem recarregar a página inteira e o
   novo produto aparece no topo, com destaque e notificação.
7. **Dado** que o diálogo de cadastro está aberto, **Quando** o operador o fecha (tecla Esc ou
   ação "Cancelar") sem salvar, **Então** nenhum produto é criado e a lista permanece como estava.
8. **Dado** um navegador com scripts desativados, **Quando** o operador aciona "Novo produto",
   preenche e salva, **Então** é levado à página de cadastro, o envio aplica as mesmas
   validações e, em caso de sucesso, retorna à lista com o produto destacado e a notificação.
9. **Dado** que outra região da tela depende da situação dos produtos (ex.: contador de alertas
   da feature 004), **Quando** um produto é cadastrado pelo diálogo, **Então** essa região é
   avisada para se atualizar, sem recarregar a página.

---

### User Story 2 - Localizar produtos na lista (Priority: P2)

O operador precisa encontrar rapidamente um produto entre muitos: digita o ID (`12`, `#12` ou
`#0012`) ou parte do nome e vê o resultado enquanto digita; filtra por situação (todos / em
alerta / ok); ordena pelas colunas e navega em páginas de 25 itens. O endereço da página reflete
busca, filtro, ordenação e página, permitindo recarregar, voltar ou compartilhar o resultado.

**Why this priority**: a atividade justifica o ID automático "para facilitar a busca" (item 1).
Depois do cadastro, localizar um produto é a tarefa mais frequente do operador e o ponto de
partida para movimentar estoque (feature 003).

**Independent Test**: com cerca de 60 produtos de nomes e situações variados, buscar por cada
formato de ID e por parte do nome, combinar com filtro e ordenação, paginar, copiar o endereço
para outra aba e obter exatamente o mesmo resultado; com a base vazia, ver o estado vazio.

**Acceptance Scenarios**:

1. **Dado** o produto `#0012` "Parafuso Sextavado", **Quando** o operador busca `#12` ou
   `#0012`, **Então** apenas esse produto é listado.
2. **Dado** o produto `#0012` "Parafuso Sextavado" e o produto `#0040` "Bucha 12 mm",
   **Quando** o operador busca `12`, **Então** ambos aparecem (o primeiro pelo ID, o segundo pelo
   nome); **e quando** busca `#12`, **Então** apenas o `#0012` aparece.
3. **Dado** os produtos "Caneta Azul", "Caneta Preta" e "Lápis", **Quando** o operador digita
   "cAnEtA", **Então** a lista passa a mostrar apenas as duas canetas, atualizada enquanto ele
   digita, sem recarregar a página.
4. **Dado** produtos em alerta e produtos ok, **Quando** o operador filtra "Em alerta",
   **Então** apenas produtos com quantidade atual menor ou igual ao estoque mínimo são listados,
   cada um com o indicador "REPOSIÇÃO NECESSÁRIA"; o filtro pode ser combinado com a busca.
5. **Dado** a lista, **Quando** o operador aciona o cabeçalho "Quantidade", **Então** a lista é
   ordenada por quantidade crescente; ao acionar de novo, decrescente; a coluna e o sentido
   ativos ficam indicados visualmente e para leitores de tela.
6. **Dado** 60 produtos, **Quando** o operador abre a lista, **Então** vê os 25 cadastrados mais
   recentemente (ordenação padrão: ID decrescente), a indicação "1–25 de 60" e controles de
   página; ao avançar, busca, filtro e ordenação são mantidos.
7. **Dado** uma lista com busca, filtro, ordenação e página aplicados, **Quando** o operador
   recarrega a página, usa Voltar/Avançar do navegador ou abre o endereço em outra aba,
   **Então** vê exatamente o mesmo resultado.
8. **Dado** que não há nenhum produto cadastrado, **Quando** o operador abre a lista, **Então**
   vê o estado vazio "Nenhum produto cadastrado" com a ação primária "Cadastrar produto".
9. **Dado** uma busca sem correspondência, **Quando** o resultado é exibido, **Então** a
   mensagem "Nenhum produto encontrado" cita o termo buscado e oferece a ação "Limpar busca".

---

### User Story 3 - Consultar os dados de um produto (Priority: P3)

A partir da lista, o operador abre a página de um produto e vê seus dados completos: código,
nome, quantidade atual, estoque mínimo, situação e datas de cadastro e de última alteração. A
página reserva o espaço onde a feature 003 colocará as ações de Entrada/Saída e o histórico de
movimentações.

**Why this priority**: concentra as informações de um item e é a âncora de integração para a
feature 003; tem menos valor isolado do que cadastrar e localizar.

**Independent Test**: abrir o detalhe de um produto pela lista e pelo endereço direto, conferir
todos os dados exibidos, e abrir o endereço de um ID inexistente para ver a página "Produto não
encontrado".

**Acceptance Scenarios**:

1. **Dado** o produto `#0007` "Fita Isolante" com quantidade 3 e mínimo 5, **Quando** o operador
   o abre a partir da lista, **Então** vê código `#0007`, nome, quantidade atual 3, estoque
   mínimo 5, situação "REPOSIÇÃO NECESSÁRIA" e as datas de cadastro e de última alteração.
2. **Dado** a página de detalhe, **Quando** a feature 003 ainda não existe, **Então** a região
   reservada às movimentações não exibe nenhum botão ou controle sem função.
3. **Dado** que não existe produto com ID 9999, **Quando** o operador abre o endereço do detalhe
   desse ID, **Então** vê a página "Produto não encontrado", em português, com caminho de volta
   para a lista.

---

### User Story 4 - Corrigir nome e estoque mínimo (Priority: P4)

O operador corrige um nome digitado errado ou ajusta o estoque mínimo de segurança de um produto.
A quantidade atual aparece apenas como informação: ela só muda por movimentação (Entrada/Saída,
feature 003). Produtos não podem ser excluídos, para preservar o histórico.

**Why this priority**: corrige erros de cadastro e acompanha mudanças de política de estoque;
é menos frequente que cadastrar e localizar.

**Independent Test**: editar nome e estoque mínimo de um produto e conferir os novos valores na
lista e no detalhe; tentar repetir o nome de outro produto; tentar alterar a quantidade por envio
adulterado e confirmar que ela não muda; confirmar que não há opção de exclusão.

**Acceptance Scenarios**:

1. **Dado** o produto `#0003` "Cadeado 30mn", **Quando** o operador corrige o nome para
   "Cadeado 30mm" e salva, **Então** o novo nome aparece no detalhe e na lista, com a
   notificação "Produto #0003 atualizado".
2. **Dado** o produto com quantidade 8 e mínimo 5 (situação ok), **Quando** o operador altera o
   estoque mínimo para 10, **Então** a situação passa imediatamente a "REPOSIÇÃO NECESSÁRIA".
3. **Dado** o formulário de edição, **Quando** o operador o abre, **Então** a quantidade atual é
   exibida apenas para leitura, com a indicação de que muda somente por movimentação; um envio
   adulterado contendo nova quantidade é aceito para os demais campos, mas a quantidade não muda.
4. **Dado** que existem "Caneta Azul" e "Caneta Preta", **Quando** o operador renomeia
   "Caneta Preta" para "CANETA AZUL", **Então** a alteração é recusada por nome duplicado.
5. **Dado** o produto "caneta azul", **Quando** o operador altera apenas as maiúsculas para
   "Caneta Azul", **Então** a alteração é aceita.
6. **Dado** qualquer tela da feature, **Quando** o operador procura uma forma de excluir um
   produto, **Então** não encontra nenhuma.

---

### User Story 5 - Acesso rápido pelo teclado (Priority: P5)

Na lista de produtos, o operador experiente usa `/` para ir direto à busca e `n` para abrir o
cadastro de novo produto, sem usar o mouse. Os atalhos são um aprimoramento opcional: sem eles,
tudo continua funcionando.

**Why this priority**: acelera o uso diário, mas não é necessário para cumprir a atividade.

**Independent Test**: na lista, pressionar `/` e verificar que o foco vai para a busca; pressionar
`n` e verificar que o cadastro abre; digitar "n" dentro da busca e verificar que nada além da
digitação acontece; desativar os scripts do navegador e verificar que a lista segue utilizável.

**Acceptance Scenarios**:

1. **Dado** a lista de produtos sem nenhum campo em foco, **Quando** o operador pressiona `/`,
   **Então** o foco vai para o campo de busca, sem que o caractere "/" seja digitado nele.
2. **Dado** a lista sem nenhum campo em foco, **Quando** o operador pressiona `n`, **Então** o
   cadastro de novo produto é aberto.
3. **Dado** o foco em um campo de texto, **Quando** o operador digita "n" ou "/", **Então** o
   caractere é digitado normalmente e nenhum atalho é acionado.
4. **Dado** a lista, **Quando** o operador observa a busca e o botão "Novo produto", **Então**
   vê a indicação discreta das teclas de atalho correspondentes.

---

### Edge Cases

- Nome com exatamente 120 caracteres (após remover espaços das extremidades) é aceito; com 121,
  é recusado com "O nome deve ter no máximo 120 caracteres."
- Nome formado só por espaços é tratado como vazio ("Informe o nome do produto.").
- Nome que difere de um existente apenas por maiúsculas/minúsculas, por espaços nas
  extremidades ou pela quantidade de espaços entre as palavras é duplicado; a mensagem identifica
  o código do produto já existente. Nomes que diferem por acento ("Café" e "Cafe") são distintos.
- Dois operadores cadastram o mesmo nome quase ao mesmo tempo: apenas um cadastro é gravado; o
  outro recebe a mesma mensagem de nome duplicado, nunca um erro genérico.
- Quantidades com sinal negativo (`-3`), casas decimais (`2,5`, `2.5`), separador de milhar
  (`1.000`), notação científica (`1e3`) ou texto (`dez`) são recusadas com mensagem junto ao
  campo; campos vazios são recusados como obrigatórios; 2.147.483.647 é aceito e 2.147.483.648 é
  recusado.
- Quantidade Inicial 0 é válida: o produto nasce zerado. Com quantidade 0 e mínimo 0 ele já nasce
  "em alerta", pois a regra é "menor ou igual".
- Clique duplo em "Salvar" ou reenvio do formulário: no máximo um produto é criado; a segunda
  tentativa é recusada como nome duplicado.
- IDs acima de 9999 são exibidos sem truncar (`#10000`); a sequência pode ter lacunas (por
  exemplo, após um cadastro que falhou) e um ID nunca é reutilizado.
- Busca vazia ou só com espaços mostra a lista sem filtro de texto.
- Busca `#0`, `#0000` ou por um ID inexistente não encontra nada e mostra o estado "Nenhum
  produto encontrado"; um número grande demais para ser ID (ex.: 25 dígitos) não causa erro — sem
  `#`, ele ainda é procurado no nome.
- Busca `12` traz o produto `#0012` e também produtos com "12" no nome; para ver só o ID, o
  operador usa `#12`.
- Busca com caracteres especiais (`%`, `_`, `'`, `"`) os trata literalmente, como parte do nome.
- Parâmetros inválidos no endereço (situação, ordenação ou página desconhecidas, página fora do
  intervalo) não causam erro: são ignorados ou ajustados para o valor válido mais próximo.
- Produto cadastrado pelo diálogo enquanto há busca ou filtro ativos que não o incluiriam: a
  lista volta à visão padrão para que o novo produto apareça no topo.
- Renomear um produto para o nome (em qualquer combinação de maiúsculas/minúsculas) de outro é
  recusado; renomear o próprio produto alterando só maiúsculas/minúsculas é aceito.
- Edição concorrente do mesmo produto: prevalece a última gravação de nome/estoque mínimo, e a
  edição nunca sobrescreve a quantidade atual (que pode ter mudado por movimentação no meio-tempo).
- Endereço de detalhe ou edição com ID numérico inexistente (inclusive grande demais) mostra
  "Produto não encontrado"; endereço com ID não numérico mostra a página padrão de "não
  encontrado" do sistema.

## Requirements *(mandatory)*

### Functional Requirements

**Cadastro**

- **FR-001** *(Atividade, item 1)*: O sistema DEVE permitir registrar um produto informando
  **Nome**, **Quantidade Inicial** e **Estoque Mínimo de Segurança**.
- **FR-002** *(Atividade, item 1)*: O sistema DEVE atribuir automaticamente a cada novo produto
  um **ID numérico** único e crescente, que o operador não informa nem altera e que nunca é
  reutilizado; lacunas na sequência são aceitáveis.
- **FR-003**: O ID DEVE ser exibido em toda a interface no formato `#` seguido do número com no
  mínimo 4 dígitos, completado com zeros à esquerda (`#0001`, `#0042`, `#12345`).
- **FR-004**: O Nome DEVE ser obrigatório e normalizado antes de validar e gravar — espaços das
  extremidades removidos e espaços internos consecutivos reduzidos a um só —, com no máximo 120
  caracteres após a normalização; nome formado só por espaços é vazio. Maiúsculas, minúsculas e
  acentos digitados são preservados como informados.
- **FR-005**: O Nome normalizado DEVE ser único sem diferenciar maiúsculas de minúsculas
  ("Caneta Azul" e "caneta azul" são o mesmo nome), inclusive sob cadastros simultâneos; acentos
  são significativos ("Café" e "Cafe" são nomes distintos); a recusa DEVE informar o código do
  produto já existente.
- **FR-006**: Quantidade Inicial e Estoque Mínimo DEVEM ser obrigatórios (sem valor
  pré-preenchido) e números inteiros de 0 a 2.147.483.647; valores vazios, negativos, com casas
  decimais ou separador de milhar, em notação científica, não numéricos ou acima do limite DEVEM
  ser recusados. Não há teto de negócio além desse limite técnico.
- **FR-007**: Erros de validação DEVEM ser exibidos em português, junto ao campo correspondente,
  preservando os valores já digitados; cada mensagem DEVE estar associada ao seu campo de forma
  perceptível a leitores de tela, e nenhum dado DEVE ser gravado enquanto houver erro. Mensagens
  padronizadas: "Informe o nome do produto."; "O nome deve ter no máximo 120 caracteres.";
  "Já existe um produto com este nome (#NNNN)."; "Informe a quantidade inicial." / "Informe o
  estoque mínimo."; "Informe um número inteiro igual ou maior que zero."; "Informe um valor de
  no máximo 2.147.483.647."
- **FR-008**: Um produto recém-cadastrado DEVE ter quantidade atual igual à Quantidade Inicial
  informada.
- **FR-009**: O cadastro DEVE estar disponível em página própria e em diálogo aberto a partir da
  lista, com os mesmos campos, regras e mensagens nas duas formas.
- **FR-010**: Após um cadastro bem-sucedido, o sistema DEVE exibir a lista na visão padrão (sem
  busca nem filtro, primeira página) com o novo produto no topo, com a linha marcada como
  recém-cadastrada (destaque do design system perceptível não apenas por cor) somente nessa
  exibição, e uma notificação "Produto #NNNN cadastrado" anunciada também a leitores de tela;
  quando o cadastro ocorreu no diálogo, ele DEVE fechar e a lista DEVE ser atualizada sem
  recarregar a página inteira.
- **FR-011**: O cadastro DEVE funcionar também com os scripts do navegador desativados (envio
  tradicional do formulário), com as mesmas validações e o mesmo resultado final.

**Listagem e busca**

- **FR-012**: O sistema DEVE oferecer uma lista tabular de produtos, uma linha por produto na
  densidade do design system, com as colunas ID (`#0001`), Nome, Quantidade atual, Estoque mínimo
  e Situação; números alinhados à direita, com largura uniforme dos algarismos e separador de
  milhar "."; ID e nome levam ao detalhe do produto.
- **FR-013** *(Atividade, item 1 — "facilitar a busca")*: A busca DEVE localizar produtos pelo
  ID em qualquer dos formatos `12`, `#12` e `#0012`, e por parte do nome sem diferenciar
  maiúsculas de minúsculas. Um termo `#` + algarismos (`#12`, `#0012`) DEVE buscar somente pelo
  ID; um termo formado apenas por algarismos (`12`) DEVE trazer o produto de ID 12 e também os
  produtos cujo nome contenha "12"; qualquer outro termo busca por parte do nome, tratando
  caracteres especiais literalmente.
- **FR-014**: A busca DEVE ser instantânea: os resultados são atualizados automaticamente,
  sem que o operador precise confirmar e sem recarregar a página, em até 1 segundo depois que ele
  para de digitar (SC-003); com scripts do navegador desativados, a busca funciona por envio do
  formulário.
- **FR-015**: A lista DEVE permitir filtrar por situação — Todos, Em alerta, OK — combinável com
  a busca, em que "em alerta" significa quantidade atual menor ou igual ao estoque mínimo (regra
  fixada no contrato de arquitetura a partir do item 3 da atividade, cuja varredura e relatório
  pertencem à feature 004).
- **FR-016**: A lista DEVE permitir ordenar por qualquer coluna, em sentido crescente ou
  decrescente, alternando ao acionar o cabeçalho; a coluna e o sentido ativos DEVEM ser
  indicados visualmente e para tecnologias assistivas. A ordenação padrão DEVE ser por ID
  decrescente (cadastrados mais recentemente primeiro); a ordenação por nome NÃO DEVE diferenciar
  maiúsculas de minúsculas; empates DEVEM ser desfeitos pelo ID decrescente, para que a ordem
  seja estável entre páginas.
- **FR-017**: A lista DEVE ser paginada com 25 produtos por página, informando o intervalo
  exibido e o total ("1–25 de 60") e preservando busca, filtro e ordenação ao trocar de página.
- **FR-018**: O endereço (URL) da lista DEVE refletir busca, filtro, ordenação e página, de modo
  que recarregar, usar Voltar/Avançar ou abrir o endereço em outra aba reproduza o mesmo
  resultado.
- **FR-019**: A lista DEVE ter estados vazios projetados: sem nenhum produto, "Nenhum produto
  cadastrado" com a ação primária "Cadastrar produto"; com busca ou filtro sem resultado,
  "Nenhum produto encontrado" citando o termo e oferecendo "Limpar busca".
- **FR-020**: A situação DEVE ser exibida com o indicador visual padronizado do design system
  (feature 001): em alerta, ícone de aviso + texto "REPOSIÇÃO NECESSÁRIA" + cor de alerta; ok,
  texto "OK" com aparência neutra; a situação NUNCA DEVE ser comunicada apenas por cor.

**Detalhe**

- **FR-021**: O sistema DEVE oferecer uma página de detalhe por produto, acessível a partir da
  lista e por endereço direto, exibindo código, nome, quantidade atual, estoque mínimo,
  situação e datas de cadastro e de última alteração (`dd/mm/aaaa HH:MM`).
- **FR-022**: A página de detalhe DEVE reservar uma região identificada para as ações de
  Entrada/Saída e o histórico de movimentações (preenchida pela feature 003); enquanto essa
  feature não existir, a região NÃO DEVE exibir controles sem função.
- **FR-023**: O acesso a um produto inexistente (detalhe ou edição) DEVE resultar na página
  "Produto não encontrado", em português, com caminho de volta para a lista.

**Edição**

- **FR-024**: O sistema DEVE permitir editar o Nome e o Estoque Mínimo de um produto, com as
  mesmas regras do cadastro (FR-004 a FR-007), com o formulário já preenchido com os valores
  atuais; a verificação de unicidade desconsidera o próprio produto.
- **FR-025** *(Constituição, princípio I)*: A quantidade atual NÃO DEVE ser editável
  diretamente em nenhuma tela ou formulário; na edição ela aparece apenas para leitura e
  qualquer valor de quantidade enviado DEVE ser ignorado.
- **FR-026**: O sistema NÃO DEVE oferecer exclusão de produtos em nenhuma tela (preserva o
  histórico); o ID do produto nunca muda.
- **FR-027**: Após uma edição bem-sucedida, o sistema DEVE exibir os dados atualizados, com a
  situação recalculada, e a notificação "Produto #NNNN atualizado".

**Acesso rápido**

- **FR-028**: Na lista de produtos, a tecla `/` DEVE levar o foco à busca e a tecla `n` DEVE
  abrir o cadastro de novo produto; os atalhos NÃO DEVEM agir quando o foco estiver em um campo
  editável ou com teclas modificadoras pressionadas, DEVEM ser indicados discretamente na
  interface e são aprimoramento opcional (sem eles nada deixa de funcionar).

**Integração com outras features**

- **FR-029**: O cadastro DEVE ser realizado por uma única operação de domínio reutilizável —
  contrato `produtos.services.cadastrar_produto(*, nome, quantidade_inicial, estoque_minimo) ->
  Produto` — usada pela interface e por qualquer outra feature que crie produtos (ex.: dados de
  demonstração da 004). Nesta feature, ela aplica FR-004 a FR-006, cria o produto e define a
  quantidade atual igual à Quantidade Inicial, de forma atômica (tudo ou nada).
- **FR-030**: Quando a feature 003 existir, a mesma operação DEVE também registrar a Quantidade
  Inicial como primeiro registro do histórico ("Saldo inicial"), na mesma operação atômica, sem
  mudar sua assinatura nem seu resultado observável (produto com quantidade atual igual à
  Quantidade Inicial).
- **FR-031**: Após um cadastro ou uma edição, as regiões da interface que dependem da situação
  dos produtos (ex.: contador de alertas da feature 004) DEVEM ser avisadas para se atualizar,
  sem recarregar a página.

### Key Entities *(include if feature involves data)*

- **Produto**: item controlado no estoque. Atributos: ID numérico automático (exibido como
  `#0001`), nome (normalizado, único sem diferenciar maiúsculas/minúsculas, até 120 caracteres),
  quantidade atual (inteiro de 0 a 2.147.483.647; definida no cadastro e, depois, alterada só por
  movimentação), estoque mínimo de segurança (inteiro de 0 a 2.147.483.647, editável), data/hora
  de cadastro e de última alteração. Não é excluído.
- **Situação do produto** (derivada, não armazenada): "em alerta" quando quantidade atual ≤
  estoque mínimo; "ok" caso contrário. Recalculada sempre a partir dos valores atuais.
- **Movimentação** (feature 003, referência): registro imutável de alteração de saldo. A
  Quantidade Inicial do cadastro passa a ser o primeiro registro ("Saldo inicial") quando a
  feature 003 existir; cada produto terá zero ou mais movimentações.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um operador cadastra um produto válido a partir da lista em até 30 segundos, sem
  sair da página da lista.
- **SC-002**: 100% dos produtos cadastrados recebem um ID único e crescente, e 100% deles são
  localizados pela busca em qualquer dos três formatos de ID (`12`, `#12`, `#0012`).
- **SC-003**: Com 10.000 produtos cadastrados, o resultado de busca, filtro, ordenação ou troca
  de página aparece em até 1 segundo depois que o operador para de digitar ou aciona o controle.
- **SC-004**: 100% das entradas inválidas previstas (nome vazio ou só com espaços, nome com mais
  de 120 caracteres, nome duplicado em qualquer combinação de maiúsculas/minúsculas, quantidades
  negativas, decimais ou não numéricas) são recusadas sem gravar nada, com mensagem em português
  junto ao campo e sem perda dos valores já digitados.
- **SC-005**: Nenhum caminho da interface permite alterar diretamente a quantidade atual de um
  produto existente ou excluí-lo — 0 ocorrências na verificação de todas as telas da feature,
  incluindo envios adulterados.
- **SC-006**: Mesmo com tentativas simultâneas ou com a validação da tela contornada, nunca
  existem dois produtos com o mesmo nome (ignorando maiúsculas/minúsculas) nem produto com
  quantidade negativa — 0 ocorrências.
- **SC-007**: Cadastrar, buscar, filtrar, ordenar, paginar, consultar e editar podem ser
  concluídos usando apenas o teclado e também com os scripts do navegador desativados.
- **SC-008**: Reabrir o endereço de uma lista com busca/filtro/ordenação/página (recarregar,
  Voltar/Avançar, nova aba) reproduz o mesmo resultado em 100% dos casos.
- **SC-009**: Em teste com usuários, pelo menos 90% localizam um produto específico entre 1.000
  itens, por ID ou por nome, na primeira tentativa e em até 10 segundos.

## Assumptions

- **Usuários**: um operador de estoque ou equipe pequena, sem autenticação nem perfis nesta
  versão (o contrato de arquitetura não prevê login); controle de acesso está fora de escopo.
- **Fora de escopo**: exclusão de produtos; edição direta da quantidade; categorias, unidades de
  medida, preço, código de barras e fornecedor; importação/exportação; busca que ignore acentos.
- **Volume de referência**: até 10.000 produtos.
- **Localização**: interface em português do Brasil; números com separador de milhar "." e datas
  `dd/mm/aaaa HH:MM` no horário de Brasília.
- **Situação**: derivada e não armazenada, pela regra "quantidade atual ≤ estoque mínimo" do
  contrato de arquitetura. Esta feature exibe e filtra a situação; varredura, relatório de
  reposição, contador de alertas e painel pertencem à feature 004, que reutiliza a mesma
  derivação.
- **Visão padrão após cadastro pelo diálogo**: a lista volta a não ter busca nem filtro, na
  primeira página, para garantir que o produto recém-criado esteja visível no topo.
- **Dependência da feature 001**: layout base e navegação; componentes do design system (tabela
  densa, campo de formulário com erro, botão, badge, diálogo, notificação, estado vazio);
  exibição de respostas com erro de validação em atualizações parciais; exibição das
  notificações também em navegação sem scripts.
- **Dependência da feature 003**: estende a operação de cadastro para registrar o saldo inicial
  no histórico (FR-030), ocupa a região reservada no detalhe (FR-022) e é a única forma de alterar
  a quantidade atual após o cadastro.
- **Dependência da feature 004**: reutiliza a derivação de situação e o filtro desta feature e
  escuta o aviso de mudança (FR-031) para atualizar o contador de alertas.
- **Edição concorrente**: prevalece a última gravação de nome e estoque mínimo; a edição nunca
  sobrescreve a quantidade atual.
