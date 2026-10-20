# Feature Specification: Fundação do Consus e Design System

**Feature Branch**: `001-fundacao-design-system`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Fundação do Consus: aplicação web com layout base (cabeçalho com a marca "Consus", navegação Painel / Produtos / Movimentações / Alertas com um espaço reservado para o badge de alertas, área de toasts com aria-live, contêiner `<dialog>` para formulários), design system **High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise** aplicado por tokens CSS, catálogo vivo de componentes em `/design/`, verificação de saúde em `/saude/` (JSON com status do banco), página inicial do Painel (placeholder que a feature 004 preencherá com KPIs), páginas de erro 404/500 no mesmo estilo, e execução completa via `docker compose up --build` (app Gunicorn + PostgreSQL 17, migrações e collectstatic automáticos, `.env.example`). Inclui configuração de qualidade (Ruff, pytest-django, cobertura) e assets vendorizados (HTMX 2, IBM Plex Sans/Mono)."

**Fonte de verdade visual**: [`docs/design/design-system.md`](../../docs/design/design-system.md)
(tokens, contrastes, anatomia e estados de componentes). Pesquisa que o fundamenta:
[`docs/design/referencias.md`](../../docs/design/referencias.md). Contrato compartilhado entre
features: [`docs/arquitetura.md`](../../docs/arquitetura.md).

## Contexto

A atividade do SENAI-SP pede um "Controle de Estoque Simples, porém altamente funcional e
eficaz" (Passo 1). Os requisitos de negócio (cadastro, movimentação, alerta — itens 1 a 3 do
Passo 2) são das features 002, 003 e 004. Esta feature entrega o **chão comum** sobre o qual
elas são construídas: a aplicação que sobe com um comando, a casca de navegação com os pontos
de entrada de cada requisito, o sistema visual (inclusive o alerta visual destacado exigido pelo
item 3) e as garantias de qualidade. Sem ela, nenhuma das outras pode ser demonstrada.

### Rastreabilidade com a atividade

| Atividade | Como esta feature atende | Requisitos |
|-----------|--------------------------|------------|
| Passo 1 — "altamente funcional e eficaz" | Sistema sobe com um comando em qualquer máquina; qualidade verificada por gates automáticos | FR-001…FR-010, FR-040…FR-044 |
| Passo 2, item 1 — cadastro de produtos | Ponto de entrada "Produtos" na navegação; componentes de formulário, tabela e paginação | FR-012, FR-027 |
| Passo 2, item 2 — entradas e saídas | Ponto de entrada "Movimentações"; diálogo de formulário; toasts de confirmação/erro | FR-012, FR-015…FR-017 |
| Passo 2, item 3 — alerta visual destacado "⚠ REPOSIÇÃO NECESSÁRIA" | Ponto de entrada "Alertas" com espaço para o contador; componente de alerta visual destacado (ícone + texto + cor) | FR-012, FR-014, FR-028 |

## Clarifications

### Session 2026-10-20

- Q: Como a navegação deve tratar as seções que ainda não existem (Produtos, Movimentações e Alertas antes das features 002–004)? → A: Os itens ficam sempre visíveis na ordem fixa; enquanto a rota da seção não existir, o item é exibido desabilitado (sem link, marcado como indisponível para tecnologias assistivas e com o texto "(em breve)"), e passa a ser link automaticamente quando a rota existir, sem alteração no layout.
- Q: Que resposta `/saude/` deve dar quando o banco estiver indisponível, e quanto tempo esperar por ele? → A: Status 503 com JSON `{"status": "erro", "banco": "indisponivel", "versao": "<versão>"}`; a verificação desiste do banco após 2 segundos. Com sucesso: 200 e `{"status": "ok", "banco": "ok", "versao": "<versão>"}`.
- Q: O catálogo `/design/` deve ficar disponível com a depuração desligada (como no ambiente em contêiner)? → A: Sim, sempre disponível: usa só dados fictícios, serve à avaliação do professor e às outras features; fica fora da navegação principal (link no rodapé) e marcado para não ser indexado.
- Q: O sistema exige autenticação de usuários? → A: Não. Uso local e monousuário, como na atividade; não há login e o painel administrativo do framework não é exposto (evita alteração direta de saldo, Constituição I).
- Q: A interface deve oferecer tema escuro? → A: Não. Apenas o tema claro "tinta sobre papel", inclusive quando o sistema operacional estiver em modo escuro; os tokens têm nomes semânticos para permitir um tema futuro.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir o sistema com um comando e navegar pela casca (Priority: P1)

O professor (ou um colega) clona o repositório, copia o arquivo de exemplo de configuração e
executa um único comando de orquestração de contêineres. Em poucos minutos abre o navegador no
endereço local e encontra o Consus: cabeçalho com a marca, navegação com Painel, Produtos,
Movimentações e Alertas, e o Painel inicial explicando o que aparecerá ali. Notificações
temporárias e janelas de formulário já funcionam como infraestrutura para as próximas features.

**Why this priority**: é o requisito de entrega da atividade — se o avaliador não conseguir
rodar o projeto, nenhuma outra funcionalidade é vista. É também a base de que 002–004 dependem.

**Independent Test**: em uma máquina apenas com o motor de contêineres instalado, clonar,
copiar o arquivo de exemplo, executar o comando de subida e abrir a página inicial: o Painel é
exibido com cabeçalho, navegação, região de notificações e contêiner de diálogo presentes.

**Acceptance Scenarios**:

1. **Given** um clone limpo e o arquivo de exemplo copiado sem alterações, **When** o comando
   único de subida é executado, **Then** a aplicação e o banco iniciam, as migrações são
   aplicadas e os arquivos estáticos ficam disponíveis sem nenhum passo manual adicional.
2. **Given** o sistema no ar, **When** o usuário abre a página inicial, **Then** vê o Painel com
   a marca "Consus", a navegação (Painel, Produtos, Movimentações, Alertas, nessa ordem) com
   "Painel" marcado como item ativo, e um estado vazio que explica que os indicadores aparecerão
   quando houver produtos.
3. **Given** o sistema reiniciado, **When** os contêineres sobem de novo, **Then** os dados do
   banco continuam lá e nenhuma migração é reaplicada indevidamente.
4. **Given** qualquer página, **When** o usuário navega apenas com o teclado, **Then** o
   primeiro elemento focável é "Pular para o conteúdo" e todo elemento interativo mostra
   indicador de foco visível.
5. **Given** o JavaScript desativado no navegador, **When** o usuário navega pelos links da
   navegação, **Then** todas as páginas carregam normalmente (navegação comum de página
   inteira).
6. **Given** uma resposta do servidor que dispara uma notificação de sucesso, **When** ela
   chega, **Then** um toast aparece na região de notificações, é anunciado por leitores de tela
   e some sozinho após 5 segundos.
7. **Given** que a seção Produtos ainda não existe, **When** o usuário vê a navegação, **Then**
   "Produtos" aparece desabilitado com "(em breve)" e sem link; **and when** a rota da seção
   passa a existir, **then** o item vira link sem nenhuma mudança no layout.

---

### User Story 2 - Consultar o catálogo vivo do design system (Priority: P2)

Quem implementa as features 002–004 (e o professor, ao avaliar a interface) abre `/design/` e
encontra todos os tokens (cores com contraste calculado, tipografia, espaçamento, bordas,
sombras) e todos os componentes do design system em todos os seus estados, com o trecho de uso
para copiar. Pode abrir um diálogo de exemplo e disparar toasts de cada nível pelo mesmo
mecanismo que as features usarão.

**Why this priority**: garante que as três features paralelas usem a mesma linguagem visual
sem reinventar componentes; materializa o princípio IV da constituição. Depende apenas da casca
(US1) para ser exibido.

**Independent Test**: abrir `/design/` e conferir que o sumário lista cada componente da seção
4 do design system, que cada seção mostra os estados aplicáveis, que as amostras de cor exibem a
razão de contraste e que os botões de demonstração abrem o diálogo e disparam os toasts.

**Acceptance Scenarios**:

1. **Given** o sistema no ar, **When** o usuário abre `/design/`, **Then** vê um sumário com
   âncoras para tokens e para cada componente (botão, campo, tabela densa, badges, cartão, KPI,
   BarList, CategoryBar, Tracker, ProgressBar, diálogo, toast, aviso inline, estado vazio,
   paginação, navegação com badge, cabeçalho de página, ícone).
2. **Given** a seção de cores, **When** o usuário a consulta, **Then** cada par texto/fundo
   permitido aparece com nome do token, valor e razão de contraste, todas ≥ ao mínimo WCAG AA.
3. **Given** a seção de badges, **When** o usuário a consulta, **Then** vê os estados OK,
   REPOSIÇÃO NECESSÁRIA e SEM ESTOQUE, este último mantendo o texto "REPOSIÇÃO NECESSÁRIA".
4. **Given** a seção de diálogo, **When** o usuário aciona "Abrir diálogo de exemplo", **Then**
   o conteúdo é buscado no servidor, o diálogo abre com foco no primeiro campo, fecha com Esc e
   o foco volta ao botão que o abriu; enviar o formulário vazio mostra os erros dentro do
   diálogo, e enviá-lo preenchido fecha o diálogo e mostra um toast de sucesso.
5. **Given** a seção de toasts, **When** o usuário dispara um toast de cada nível, **Then** os
   de sucesso e info somem após 5 s e os de alerta e erro permanecem até serem fechados.

---

### User Story 3 - Verificar a saúde do sistema (Priority: P2)

Quem opera o sistema (ou o próprio orquestrador de contêineres) consulta `/saude/` e recebe uma
resposta legível por máquina dizendo se a aplicação está de pé e se o banco responde.

**Why this priority**: permite que o orquestrador só considere a aplicação pronta quando ela
realmente atende, e dá ao avaliador um diagnóstico rápido quando algo falha na subida.

**Independent Test**: com o sistema no ar, requisitar `/saude/` e verificar a resposta de
sucesso; parar o banco e requisitar de novo, verificando a resposta de indisponibilidade.

**Acceptance Scenarios**:

1. **Given** aplicação e banco funcionando, **When** `/saude/` é requisitada, **Then** a resposta
   tem status 200 e JSON `{"status": "ok", "banco": "ok", "versao": …}` e não é armazenada em
   cache.
2. **Given** o banco parado, **When** `/saude/` é requisitada, **Then** a resposta chega em até 3
   segundos com status 503 e JSON `{"status": "erro", "banco": "indisponivel", "versao": …}`,
   sem detalhes internos.
3. **Given** a orquestração de contêineres, **When** a aplicação inicia, **Then** ela só é
   marcada como saudável depois que `/saude/` responde com sucesso.

---

### User Story 4 - Ver páginas de erro no mesmo estilo (Priority: P3)

O usuário que digita um endereço inexistente, ou que encontra uma falha inesperada, vê uma
página clara no mesmo visual do sistema, em português, com caminho de volta ao Painel — e nunca
uma página técnica do servidor.

**Why this priority**: acabamento e confiança; não bloqueia o uso das outras features.

**Independent Test**: requisitar uma URL inexistente e verificar a página 404 estilizada; forçar
um erro interno com depuração desligada e verificar a página 500 estilizada.

**Acceptance Scenarios**:

1. **Given** uma URL que não existe, **When** o usuário a abre, **Then** recebe status 404 e uma
   página com cabeçalho, navegação, o código "404", a explicação em português, o caminho
   solicitado e o botão "Voltar ao Painel".
2. **Given** uma falha interna com o banco indisponível, **When** a página de erro é exibida,
   **Then** recebe status 500 e uma página estilizada que não depende do banco, sem detalhes
   técnicos.
3. **Given** uma requisição parcial (de dentro da página) que falha com 4xx/5xx, **When** a
   resposta chega, **Then** o conteúdo atual não é substituído e um toast de erro informa a
   falha.

---

### User Story 5 - Executar os quality gates do projeto (Priority: P3)

A pessoa desenvolvedora roda, com comandos únicos, o lint, a verificação de formatação, a suíte
de testes com cobertura e a checagem de migrações pendentes — localmente com banco de arquivo e
dentro do contêiner com o banco de produção — antes de integrar uma feature.

**Why this priority**: sustenta os princípios III e V da constituição para todas as features;
o valor aparece ao longo do projeto, não na demonstração inicial.

**Independent Test**: executar cada comando de qualidade em um clone limpo e verificar que todos
terminam com sucesso e que a cobertura é reportada.

**Acceptance Scenarios**:

1. **Given** um clone limpo com as dependências instaladas pelo arquivo de lock, **When** os
   comandos de lint e de verificação de formatação são executados, **Then** terminam sem
   violações.
2. **Given** o mesmo clone, **When** a suíte de testes é executada sem configuração de banco,
   **Then** roda no banco local de arquivo, passa por completo e mostra a cobertura.
3. **Given** o sistema em contêineres, **When** a suíte é executada contra o banco de produção,
   **Then** também passa por completo.
4. **Given** o código entregue, **When** a checagem de migrações pendentes é executada, **Then**
   não há alterações de modelo sem migração.

---

### Edge Cases

- Banco ainda inicializando quando a aplicação sobe: a aplicação espera o banco ficar pronto em
  vez de falhar (FR-003).
- Banco cai com a aplicação no ar: páginas que não dependem de dados continuam respondendo;
  `/saude/` responde 503 em até 3 segundos (FR-035); páginas que dependem do banco mostram a
  página 500 estilizada.
- Chave secreta ausente com depuração desligada: a aplicação se recusa a iniciar e diz por quê
  (FR-005).
- Variável de conexão com o banco ausente (desenvolvimento local): usa banco local de arquivo
  (FR-006).
- Porta da aplicação já ocupada na máquina: a porta publicada é configurável no arquivo de
  ambiente (FR-004).
- Seções da navegação que ainda não existem (Produtos, Movimentações e Alertas antes das
  features 002–004): itens visíveis, desabilitados, com "(em breve)"; viram links quando a rota
  existir (FR-013).
- Navegador sem JavaScript: navegação e formulários funcionam por página inteira; mensagens
  aparecem como avisos estáticos no topo do conteúdo (FR-015, FR-018).
- Diálogo aberto e uma requisição falha: o erro aparece dentro do próprio diálogo, porque o
  diálogo modal cobre a região global de notificações (FR-017).
- Mais de 3 toasts simultâneos: os mais antigos saem para manter no máximo 3 (FR-016).
- Tela estreita (320 px): nenhuma rolagem horizontal da página; tabelas largas rolam dentro do
  próprio contêiner; navegação continua acessível sem menu que dependa de JavaScript (FR-021).
- Usuário com preferência por movimento reduzido: nenhuma animação ou deslocamento (FR-030).
- Falha de proteção contra falsificação de requisição (sessão expirada em formulário): página
  de erro estilizada orientando a recarregar (FR-039).
- Fontes locais não carregadas: o texto aparece imediatamente na fonte de sistema substituta
  (sem texto invisível) e troca quando a fonte carrega (FR-026).

## Requirements *(mandatory)*

### Functional Requirements

#### Execução, configuração e ambiente

- **FR-001** *(Atividade, Passo 1 — "altamente funcional e eficaz"; Constituição V)*: O sistema
  MUST subir por completo (aplicação + banco de dados) com **um único comando** de orquestração
  de contêineres a partir de um clone limpo, exigindo apenas a cópia do arquivo de exemplo de
  variáveis de ambiente.
- **FR-002**: Na inicialização, o sistema MUST aplicar automaticamente as migrações pendentes do
  banco e disponibilizar os arquivos estáticos, sem passo manual.
- **FR-003**: A aplicação MUST aguardar o banco aceitar conexões antes de iniciar e MUST NOT
  falhar por causa da ordem de inicialização dos serviços.
- **FR-004**: Toda configuração MUST vir de variáveis de ambiente — no mínimo: chave secreta,
  modo de depuração, hosts permitidos, origens confiáveis para proteção contra falsificação de
  requisição, conexão com o banco, credenciais do banco, nível de log, quantidade de processos de
  atendimento e porta publicada. O repositório MUST conter um arquivo de exemplo que documenta
  cada variável e MUST NOT conter segredos reais.
- **FR-005**: A depuração MUST vir desligada por padrão; com depuração desligada e sem chave
  secreta definida, a aplicação MUST recusar-se a iniciar com mensagem explícita.
- **FR-006**: Sem variável de conexão com o banco, o sistema MUST usar um banco local de arquivo
  (desenvolvimento e testes rápidos).
- **FR-007**: Os dados do banco MUST persistir entre reinicializações dos contêineres.
- **FR-008** *(Constituição V)*: Bibliotecas e fontes de terceiros MUST ser servidas pela própria
  aplicação; nenhuma página MUST fazer requisição a domínio externo.
- **FR-009**: A aplicação MUST registrar logs na saída padrão, com nível configurável.
- **FR-010**: O processo da aplicação no contêiner MUST rodar com usuário sem privilégios
  administrativos.

#### Layout base e navegação

- **FR-011**: Todas as páginas MUST compartilhar um layout base com: link "Pular para o
  conteúdo" como primeiro elemento focável; cabeçalho com a marca "Consus" que leva ao Painel;
  navegação principal; área de conteúdo principal; rodapé com a versão do sistema e links para o
  catálogo de design e para a verificação de saúde.
- **FR-012** *(Atividade, Passo 2, itens 1–3 — pontos de entrada)*: A navegação principal MUST
  conter, nesta ordem, Painel, Produtos, Movimentações e Alertas; o item da seção atual MUST ser
  destacado visualmente e marcado como página atual para tecnologias assistivas, inclusive em
  subpáginas da seção (ex.: o detalhe de um produto ativa "Produtos").
- **FR-013**: Itens de navegação cuja rota de destino ainda não existe MUST continuar visíveis
  na ordem fixa, exibidos como desabilitados (sem link, marcados como indisponíveis para
  tecnologias assistivas, com o texto "(em breve)"); assim que a rota existir, o item MUST virar
  link automaticamente, sem alteração no layout. A mesma regra vale para ações que apontem para
  essas seções (ex.: a ação do estado vazio do Painel).
- **FR-014** *(Atividade, Passo 2, item 3 — preparação)*: O item "Alertas" MUST reservar um
  espaço para o indicador numérico de produtos em alerta, que sem dados não exibe nada nem é
  anunciado; quando a fonte do contador existir (feature 004), o espaço MUST atualizá-lo ao abrir
  a página, sempre que ocorrer o evento de estoque alterado e periodicamente a cada 60 segundos.
- **FR-015**: O layout MUST incluir uma região de notificações temporárias (toasts) anunciada por
  tecnologias assistivas, com quatro níveis — sucesso, info, alerta, erro — cada um com ícone,
  texto e cor próprios; toasts MUST poder ser disparados tanto por respostas parciais (evento
  `toast` com nível e texto) quanto por mensagens do servidor após um redirecionamento de página
  inteira; sem JavaScript, as mensagens MUST aparecer como avisos estáticos no topo do conteúdo.
- **FR-016**: Toasts de sucesso e info MUST sumir após 5 segundos (pausando enquanto o ponteiro
  ou o foco estiverem sobre eles); toasts de alerta e erro MUST permanecer até serem fechados;
  todo toast MUST ter botão de fechar com nome acessível; no máximo 3 toasts MUST ficar visíveis
  (os mais antigos saem); toasts visíveis MUST NOT desaparecer por causa da navegação entre
  páginas.
- **FR-017**: O layout MUST incluir um único contêiner de diálogo modal que recebe conteúdo sob
  demanda do servidor, abre ao recebê-lo, coloca o foco no primeiro campo (ou no campo marcado),
  mantém o foco dentro do diálogo, fecha por tecla Esc, pelo botão fechar ou por sinal do
  servidor após uma ação concluída, NÃO fecha por clique fora, devolve o foco a quem o abriu e
  exibe dentro de si os toasts gerados enquanto está aberto; sem JavaScript, o mesmo conteúdo
  MUST estar acessível como página própria.
- **FR-018** *(Constituição II)*: Navegação e formulários MUST funcionar sem JavaScript; com
  JavaScript, a navegação MUST trocar o conteúdo sem recarregar a página, preservando histórico,
  título e toasts; requisições parciais MUST enviar a proteção contra falsificação de requisição;
  respostas de erro de validação (status 422) MUST ser exibidas no lugar do formulário; respostas
  de erro 4xx/5xx de requisições parciais MUST gerar toast de erro em vez de substituir conteúdo.
- **FR-019**: O título de cada aba do navegador MUST seguir o formato "<Título da página> —
  Consus".
- **FR-020** *(Constituição IV — Idioma)*: A interface MUST estar em português do Brasil
  (idioma declarado no documento), com datas no formato `dd/mm/aaaa HH:MM` no fuso de São Paulo
  e números inteiros com separador de milhar ".".
- **FR-021**: As páginas MUST ser utilizáveis de 320 px a 1920 px de largura sem rolagem
  horizontal da página; tabelas largas MUST rolar dentro do próprio contêiner; a navegação MUST
  continuar acessível em telas estreitas sem depender de JavaScript.

#### Painel

- **FR-022**: A página inicial MUST exibir o Painel: cabeçalho de página "Painel" com descrição,
  uma região de indicadores com identificador estável para a feature 004 preencher e, enquanto
  não houver indicadores, um estado vazio que explica o que aparecerá ali e oferece a ação de ir
  ao cadastro de produtos (respeitando FR-013 enquanto essa seção não existir).

#### Design system

- **FR-023** *(Constituição IV — Tokens primeiro)*: A aparência MUST seguir
  `docs/design/design-system.md`; todos os valores visuais (cores, tipografia, espaçamentos,
  tamanhos, bordas, raios, sombras, camadas, movimento) MUST ser definidos uma única vez como
  tokens nomeados em um único arquivo de tokens, e os estilos de componentes MUST referenciar
  apenas tokens semânticos — verificação automática: zero cores ou medidas literais fora do
  arquivo de tokens (exceto as condições de breakpoint documentadas). A interface MUST usar
  somente o tema claro, inclusive quando o sistema operacional estiver em modo escuro (controles
  nativos do navegador também claros).
- **FR-024** *(Constituição IV — Acessibilidade)*: Todo par texto/fundo permitido pelo design
  system MUST atingir contraste WCAG 2.1 AA (4,5:1 para texto normal; 3:1 para texto grande,
  limites de componentes, indicador de foco e marcas gráficas) — verificação automática a partir
  do arquivo de tokens.
- **FR-025**: Todo elemento interativo MUST exibir indicador de foco visível de pelo menos 2 px
  com contraste ≥ 3:1; o indicador MUST NOT ser removido sem substituto.
- **FR-026**: As famílias tipográficas (sans e mono) MUST ser servidas localmente e exibir texto
  imediatamente com fonte substituta enquanto carregam; números em tabelas e indicadores MUST
  usar a fonte mono com algarismos de largura fixa, alinhados à direita em tabelas.
- **FR-027**: O design system MUST oferecer, como componentes reutilizáveis com a anatomia e os
  estados definidos em `docs/design/design-system.md` §4: botão (primário, secundário, fantasma,
  perigo; tamanhos e só-ícone), campo de formulário (rótulo, ajuda, erro; texto, número, seleção,
  área de texto), tabela densa (duas densidades), badges (status de estoque, semânticos e delta),
  cartão, KPI card, BarList, CategoryBar, Tracker, ProgressBar, diálogo, toast, aviso inline,
  estado vazio, paginação, navegação com badge, cabeçalho de página e ícone.
- **FR-028** *(Atividade, Passo 2, item 3 — "alerta visual destacado (ex: ⚠ REPOSIÇÃO
  NECESSÁRIA)"; Constituição IV)*: O componente de status de estoque MUST oferecer os estados
  OK, REPOSIÇÃO NECESSÁRIA e SEM ESTOQUE; o estado de reposição MUST combinar ícone de alerta
  desenhado (não emoji), o texto "REPOSIÇÃO NECESSÁRIA" em caixa alta e a cor de alerta — nunca
  apenas cor — e ser o elemento de maior destaque visual da linha ou cartão em que aparece; o
  estado SEM ESTOQUE MUST manter o texto "REPOSIÇÃO NECESSÁRIA" e acrescentar a indicação "SEM
  ESTOQUE".
- **FR-029**: Ícones MUST vir de um único conjunto de ícones vetoriais servido localmente;
  ícones decorativos MUST ser ocultos de tecnologias assistivas e ícones sem texto ao lado MUST
  ter nome acessível; emojis MUST NOT ser usados como ícones.
- **FR-030**: Transições MUST ser curtas (≤ 150 ms) e limitadas a cor, opacidade, sombra e
  deslocamento; com preferência do sistema por movimento reduzido, nenhuma animação ou
  deslocamento MUST ocorrer.

#### Catálogo vivo (`/design/`)

- **FR-031**: `/design/` MUST exibir um sumário com âncoras e seções para: tokens (amostras de
  cor com nome, valor e razão de contraste calculada; escala tipográfica; espaçamentos; tamanhos;
  bordas e raios; sombras; camadas; movimento) e cada componente de FR-027 em todos os estados
  aplicáveis (padrão, hover/foco ilustrados, ativo, desabilitado, erro, carregando), cada um com
  o trecho de uso do template.
- **FR-032**: `/design/` MUST oferecer demonstrações vivas, usando o mesmo mecanismo que as
  features usarão: (a) abrir um diálogo de exemplo com conteúdo vindo do servidor contendo um
  formulário fictício validado no servidor — dados inválidos re-exibem o formulário com os erros
  no próprio diálogo (status 422), dados válidos fecham o diálogo e exibem um toast de sucesso —
  e (b) disparar um toast de cada nível; sem JavaScript, as demonstrações MUST degradar para
  navegação de página inteira (diálogo como página; toast como mensagem após redirecionamento).
- **FR-033**: `/design/` MUST usar apenas dados fictícios rotulados como exemplo, MUST estar
  disponível em qualquer ambiente (inclusive com depuração desligada), MUST NOT aparecer na
  navegação principal (acesso pelo rodapé) e MUST pedir a mecanismos de busca que não a indexem.

#### Verificação de saúde (`/saude/`)

- **FR-034**: `/saude/` MUST responder a leitura (inclusive requisição só de cabeçalhos) em
  formato JSON informando o estado geral e o estado do banco, sem exigir sessão nem proteção
  contra falsificação de requisição, sem permitir cache e sem expor detalhes internos (mensagens
  de exceção, credenciais, endereços); outros métodos MUST ser recusados com 405.
- **FR-035**: Com o banco respondendo, `/saude/` MUST retornar 200 e
  `{"status": "ok", "banco": "ok", "versao": "<versão>"}`; se o banco não responder em até 2
  segundos (ou recusar a conexão), MUST retornar 503 e
  `{"status": "erro", "banco": "indisponivel", "versao": "<versão>"}`.
- **FR-036**: A orquestração de contêineres MUST usar `/saude/` como verificação de prontidão da
  aplicação, e o banco MUST ter verificação de prontidão própria da qual a aplicação depende.

#### Páginas de erro

- **FR-037**: URLs inexistentes MUST receber status 404 e uma página no mesmo visual, com o
  layout completo (cabeçalho e navegação), o código "404", explicação em português, o caminho
  solicitado e ação "Voltar ao Painel".
- **FR-038**: Falhas internas MUST receber status 500 e uma página autônoma no mesmo visual, que
  não depende do banco, da sessão nem de dados de contexto, sem detalhes técnicos e com ação
  "Voltar ao Painel".
- **FR-039**: Requisições malformadas (400) e acessos negados (403, inclusive falha da proteção
  contra falsificação de requisição) MUST receber páginas no mesmo visual das páginas de erro
  (marca, código, mensagem em português e ação "Voltar ao Painel"), com mensagem própria (a de
  403 por falha de proteção orienta a recarregar a página); as que o framework gera sem contexto
  de requisição (400 e falha de proteção) MAY omitir a navegação, como a 500.

#### Qualidade e segurança

- **FR-040** *(Constituição — Quality gates)*: O código MUST passar no lint e na verificação de
  formatação com zero violações, cada um executável por um único comando.
- **FR-041** *(Constituição III)*: A suíte de testes MUST ser executável por um único comando,
  reportar cobertura, passar tanto no banco local de arquivo quanto no banco de produção em
  contêiner e atingir cobertura de linhas ≥ 90 % no código desta feature.
- **FR-042**: As dependências MUST ser declaradas com versões travadas em arquivo de lock que
  torna a instalação reprodutível; a checagem de migrações pendentes MUST passar.
- **FR-043**: As respostas MUST incluir proteções padrão de navegador — bloqueio de exibição em
  quadros de outros sites, bloqueio de detecção de tipo de conteúdo e política de referência
  restrita à mesma origem; cookies de sessão e de proteção contra falsificação MUST poder ser
  marcados como seguros por variável de ambiente.
- **FR-044** *(Constituição I — saldo só muda por movimentação)*: O sistema MUST NOT exigir
  autenticação nesta versão e MUST NOT expor o painel administrativo do framework (nenhuma rota
  de administração responde; acessá-la resulta em 404).

### Key Entities *(include if feature involves data)*

Esta feature **não cria tabelas de negócio**. As entidades abaixo são conceituais (configuração
e contratos de interface), detalhadas em `data-model.md`:

- **Token de design**: nome, categoria (cor, tipografia, espaço, tamanho, borda, sombra,
  camada, movimento), valor; tokens semânticos podem referenciar primitivas.
- **Par de contraste**: token de primeiro plano, token de fundo, mínimo exigido, uso.
- **Item de navegação**: rótulo, rota de destino, ícone, seção a que pertence, disponibilidade.
- **Notificação (toast)**: nível (sucesso, info, alerta, erro) e texto.
- **Estado de saúde**: estado geral, estado do banco, versão do sistema.
- **Variável de ambiente**: nome, obrigatoriedade, valor padrão, descrição.
- **Componente do catálogo**: identificador/âncora, nome, estados demonstrados, trecho de uso.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa que nunca viu o projeto coloca o sistema no ar e vê o Painel em até 10
  minutos (excluindo o download inicial de imagens), executando no máximo 2 comandos (copiar o
  arquivo de exemplo e subir).
- **SC-002**: 100 % dos pares texto/fundo do design system atingem o contraste mínimo WCAG 2.1
  AA, comprovado por verificação automática.
- **SC-003**: 0 cores ou medidas literais nos estilos de componentes fora do arquivo de tokens,
  comprovado por verificação automática.
- **SC-004**: O catálogo exibe 100 % dos 18 componentes listados no design system, cada um com
  todos os estados aplicáveis.
- **SC-005**: A verificação de saúde responde em menos de 1 segundo em 95 % das chamadas com o
  banco no ar, e informa a indisponibilidade do banco em no máximo 3 segundos quando ele cai.
- **SC-006**: Todas as páginas desta feature são operáveis apenas pelo teclado, com foco sempre
  visível (0 ocorrências de foco invisível em revisão manual).
- **SC-007**: 0 requisições a domínios externos ao carregar qualquer página do sistema.
- **SC-008**: 0 páginas desta feature com rolagem horizontal da página entre 320 px e 1920 px.
- **SC-009**: Os quality gates (lint, formatação, testes nos dois bancos, migrações) terminam com
  sucesso em um clone limpo; cobertura de linhas do código desta feature ≥ 90 %.
- **SC-010**: A primeira visita ao Painel transfere no máximo 300 KB de recursos próprios e de
  terceiros (estilos, script, fontes e ícones) e as visitas seguintes reutilizam esses recursos
  do cache do navegador.

## Assumptions

- **Restrições herdadas da constituição** (não são escolhas desta spec): Python 3.13, Django 5.2
  LTS + django-htmx, HTMX 2.x vendorizado, PostgreSQL 17 em contêiner (SQLite para
  desenvolvimento/testes), Gunicorn + WhiteNoise, Docker Compose, pytest + pytest-django +
  pytest-cov, Ruff, dependências em `pyproject.toml` com `uv.lock`, estrutura `config/` +
  `apps/core`, design system em `static/css/`. Os detalhes de implementação ficam no `plan.md`.
- Público: professor e colegas do SENAI-SP rodando o projeto em máquina própria (Linux, macOS ou
  Windows com o motor de contêineres instalado); uso local, em rede confiável.
- Navegadores suportados: as duas últimas versões de Chrome, Edge, Firefox e Safari (necessário
  para diálogo nativo e seletores modernos de CSS).
- O Painel desta feature é provisório: os indicadores (KPIs, BarList, CategoryBar) são
  preenchidos pela feature 004; a feature 001 garante a região, o estado vazio e os componentes.
- A situação de estoque (OK / reposição / sem estoque) é calculada pela feature 004 a partir de
  `quantidade_atual` e `estoque_minimo`; esta feature só fornece o componente visual.
- Rotas, nomes, eventos e convenções HTMX seguem `docs/arquitetura.md`; o detalhamento do que esta
  feature acrescenta está em `contracts/`.
- Não há modelos de negócio nesta feature; as migrações aplicadas na subida são as dos
  aplicativos padrão do framework (tipos de conteúdo e sessões) e as que as features seguintes
  criarem.
- Fora de escopo desta feature: entidades e regras de estoque (002–004), gráficos com biblioteca
  de visualização, idiomas além do português do Brasil, terminação HTTPS (o uso previsto é local;
  cookies seguros ficam disponíveis por variável de ambiente para um eventual proxy),
  autenticação/usuários e painel administrativo (FR-044), tema escuro (FR-023).
