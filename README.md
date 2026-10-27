# Consus

> *Consus*: divindade romana guardiã dos grãos armazenados nos celeiros.

Sistema web de **Controle de Estoque Simples**, porém altamente funcional:

- cadastro de produtos com ID automático;
- entradas e saídas com bloqueio de saldo negativo;
- alerta automático de reposição;
- desde a **2.0**, **módulo financeiro** com preços, margem, transações e fluxo de caixa;
- **login** obrigatório.

Feito em **Django 5.2 + HTMX 2**. Roda com Docker (PostgreSQL) ou **só com Python** (SQLite).

Esse repositório deve conter o conteúdo dos códigos, como optei por HTMX não terá API no
momento então terá somente um repositório.

![Painel financeiro do Consus](docs/capturas/financeiro.png)

## A atividade, item por item

| Item da atividade | Onde está no Consus |
|-------------------|---------------------|
| **1. Cadastro**: nome, quantidade inicial e estoque mínimo de segurança; ID numérico automático | **Produtos** (`/produtos/`) → *Novo produto* (atalho `n`). O ID é gerado pelo banco e exibido como `#0001`; a busca aceita `12`, `#12`, `#0012` ou parte do nome. A quantidade inicial vira o primeiro lançamento do livro-razão (*Saldo inicial*). |
| **2. Movimentação**: entrada soma, saída/venda subtrai, saldo nunca negativo | Botões **+ Entrada / − Saída** em cada linha, no detalhe do produto e em **Movimentações** (`/movimentacoes/`). A prévia mostra o saldo resultante enquanto você digita e bloqueia a saída maior que o disponível. A regra é garantida em três camadas: formulário, serviço transacional com `SELECT … FOR UPDATE` e `CHECK` no banco. Todo lançamento fica no livro-razão, que é imutável. |
| **3. Alerta de baixa**: quantidade ≤ mínimo → **⚠ REPOSIÇÃO NECESSÁRIA** em destaque | Selo em todas as telas, **Relatório de reposição** (`/alertas/`) ordenado por criticidade, com sugestão de compra e exportação CSV. O contador no menu se atualiza sozinho (varredura automática) e o comando `varrer_estoque` faz a varredura pelo terminal. Estoque zerado aparece também como **SEM ESTOQUE**. |

### Passo 3: Módulo Financeiro e Fluxo de Caixa (2.0)

| Item da atividade | Onde está no Consus |
|-------------------|---------------------|
| **1. Cadastro com preços**: Preço de Custo e Preço de Venda obrigatórios; margem calculada automaticamente | O formulário de produto ganhou os dois preços, que aceitam `12,50`, `1.234,56` ou `R$ 12,50`. A **margem prevista** (R$ e %) aparece ao vivo enquanto você digita. A lista mostra as colunas Custo, Venda e Margem, ordenáveis por margem, e o detalhe tem a seção "Preços e margem". Venda abaixo do custo é permitida, com aviso de prejuízo e o selo **MARGEM NEGATIVA**. Produtos anteriores à 2.0 ficam com o selo **PREÇO PENDENTE** até serem editados. |
| **2. Transações**: entrada = despesa (qtd × custo); saída = receita (qtd × venda); histórico com Data/Hora, ID do Produto, Tipo, Quantidade e Valor Total | Toda movimentação grava a **transação financeira** na mesma transação de banco: se uma falhar, nenhuma é gravada. Os preços ficam congelados, e mudar o preço depois não altera o passado. O **Histórico de transações** (`/financeiro/transacoes/`) tem filtros por produto, tipo e datas, além de exportação CSV. O livro-razão ganhou a coluna Valor. |
| **3. Dashboard**: Valor Total do Estoque, Faturamento Total, Lucro Bruto Realizado (Receita − CPV) e Alerta Financeiro com caixa negativo | O **Painel financeiro** (`/financeiro/`) mostra os 4 KPIs, o gráfico de fluxo de caixa (receitas × despesas), os maiores em faturamento, lucro e valor em estoque, e as últimas transações. O período pode ser Todo, Este mês, 30 dias, 7 dias, Hoje ou Personalizado. Com receitas − despesas < 0, aparece o aviso **CAIXA NEGATIVO**, e o KPI de saldo fica em vermelho-tijolo. O Painel `/` tem uma faixa com o resumo financeiro, e o comando `resumo_financeiro` mostra os mesmos números no terminal. |

Pedidos extras da 2.0:
- **Login interativo** com bloqueio após tentativas erradas;
- **animações e transições**;
- **paleta de cores** mais sóbria e documentada;
- execução **só com Python**.

| Login | Produtos com preços e margem |
|-------|------------------------------|
| ![Tela de login](docs/capturas/login.png) | ![Lista de produtos](docs/capturas/produtos.png) |

| Painel | Saída bloqueada (saldo insuficiente) |
|----------|--------------------------------------|
| ![Painel](docs/capturas/painel.png) | ![Diálogo de saída](docs/capturas/saida-bloqueada.png) |

| Relatório de reposição | Livro-razão |
|------------------------|-------------|
| ![Relatório de reposição](docs/capturas/alertas.png) | ![Livro-razão](docs/capturas/livro-razao.png) |

## Como executar

Pré-requisitos: [Docker](https://docs.docker.com/get-docker/) com o plugin Compose.

```bash
cp .env.example .env          # revise os valores se quiser
docker compose up --build     # app + PostgreSQL 17, migrações automáticas
```

Abra <http://localhost:8000> e entre com o usuário **`admin`** e a senha de `CONSUS_SENHA` no `.env`
(o `.env.example` traz `troque-esta-senha`). O usuário é criado na primeira subida, e a senha
de um usuário existente nunca é trocada.

Com `CONSUS_POPULAR_DEMO=1` (padrão do `.env.example`), o banco começa com 12 produtos de demonstração:

- 4 deles estão em alerta;
- as movimentações estão espalhadas pelos últimos 30 dias;
- em "Todo o período", o caixa aparece **negativo** (a compra do estoque inicial custou R$ 7.206,40 e as vendas somam R$ 3.488,40);
- em "Últimos 7 dias", o saldo é positivo.

| Endereço | O que é |
|----------|---------|
| `/contas/entrar/` | Login (única página pública, junto com `/saude/`) |
| `/` | Painel: KPIs, resumo financeiro, produtos críticos, cobertura do mínimo e últimas movimentações |
| `/produtos/` | Cadastro, busca por ID/nome, filtro por situação |
| `/movimentacoes/` | Livro-razão com filtros e nova movimentação |
| `/alertas/` | Relatório de reposição (`?formato=csv` exporta) |
| `/financeiro/` | Painel financeiro: valor do estoque, faturamento, lucro bruto, saldo do caixa, fluxo |
| `/financeiro/transacoes/` | Histórico de transações (`?formato=csv` exporta) |
| `/design/` | Catálogo vivo do design system |
| `/saude/` | Verificação de saúde (JSON) |

O contador de alertas do menu consulta o servidor a cada `ALERTAS_INTERVALO_SEGUNDOS`
(padrão 30, mínimo 5) e também logo após qualquer movimentação. Mudanças são anunciadas a
leitores de tela.

### Pelo terminal

```bash
docker compose exec app python manage.py varrer_estoque                 # relatório em texto
docker compose exec app python manage.py varrer_estoque --formato csv   # ou json
docker compose exec app python manage.py varrer_estoque --todos         # inclui os produtos OK
docker compose exec app python manage.py varrer_estoque --falhar-se-alerta
docker compose exec app python manage.py movimentar 12 saida 3 --obs "Pedido 1045"
docker compose exec app python manage.py popular_demo                   # idempotente
docker compose exec app python manage.py resumo_financeiro              # KPIs financeiros
docker compose exec app python manage.py resumo_financeiro --periodo 7d --formato json
docker compose exec app python manage.py garantir_usuario --usuario ana --senha "S3nha-forte"
docker compose exec app python manage.py createsuperuser                # também funciona
```

`resumo_financeiro --falhar-se-negativo` sai com código `1` quando o caixa do período está
negativo. Isso é útil em cron, como no exemplo do `varrer_estoque` abaixo.

`varrer_estoque` só lê o banco. Códigos de saída: `0` sem problemas, `1` há produto em alerta
(apenas com `--falhar-se-alerta`), `2` o banco não pôde ser consultado. Exemplo de cron que
avisa toda manhã:

```cron
0 7 * * 1-5  cd /srv/consus && docker compose exec -T app python manage.py varrer_estoque --falhar-se-alerta || mail -s "Consus: reposição" compras@exemplo.com
```

## Rodar só com Python

Não precisa de Docker. Basta ter **Python 3.11 ou mais novo** ([python.org](https://www.python.org/downloads/);
no Windows, marque *Add python.exe to PATH*). O banco é um arquivo SQLite (`db.sqlite3`) na
pasta do projeto.

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1          # se bloquear: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
python iniciar.py
```

**Linux / macOS (bash)**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python iniciar.py
```

O `iniciar.py`, que só usa a biblioteca padrão:

1. confere a versão do Python e as dependências;
2. aplica as migrações;
3. cria os dados de demonstração na primeira vez (`--sem-demo` pula essa etapa);
4. garante o usuário `admin` (senha `consus`, ou a de `CONSUS_SENHA`, mostrada no terminal);
5. abre o servidor em <http://127.0.0.1:8000>.

Ele aceita `--porta 8080` e `--host 0.0.0.0` para acesso pela rede local. Ctrl+C encerra.

### Levar para outra máquina

1. Copie a pasta do projeto, sem `.venv/`, que é específica de cada máquina. Por exemplo: `git clone`, ZIP ou pendrive.
2. Na máquina nova, repita os 4 comandos acima.
3. Para levar **os dados** junto, copie também o arquivo `db.sqlite3`. Ele contém produtos, movimentações, transações e usuários.

### Usar PostgreSQL sem Docker

```bash
export DATABASE_URL=postgres://usuario:senha@localhost:5432/consus   # PowerShell: $env:DATABASE_URL="..."
python iniciar.py
```

### Desenvolvimento (uv)

```bash
uv sync                                   # Python + dependências travadas no uv.lock
DJANGO_DEBUG=true uv run python manage.py migrate
DJANGO_DEBUG=true uv run python manage.py runserver
```

`requirements.txt` e `requirements-dev.txt` são exportados do `uv.lock`
(`uv export --no-dev --no-hashes --format requirements-txt`), e um teste garante que as versões
batem. A suíte passa em Python 3.11, 3.12 e 3.13. A imagem Docker usa 3.13.

## Design

Estratégia **High-Density Neo-Brutalism Sóbrio / Swiss Grid Enterprise**:

- grade de 12 colunas;
- bordas de 1 px e sombras sólidas deslocadas;
- IBM Plex Sans/Mono, com números tabulares;
- cor só onde há significado;
- contraste WCAG AA verificado por teste.

Os tokens ficam em [`static/css/tokens.css`](static/css/tokens.css), e o restante do CSS só os referencia. Tudo funciona sem JavaScript; o HTMX apenas melhora a experiência.

### Paleta de cores

A 2.0 trocou a paleta saturada da 1.0 por uma **paleta "sóbria"**. Em telas cheias de números, cor forte cansa e compete com os dados. Os nomes semânticos não mudaram, só as cores por trás:

| Papel | Cor | Por quê |
|-------|-----|---------|
| Papel / tinta | `#F6F4EF` / `#1A1814` | creme quente e quase-preto: leitura longa sem o branco puro ofuscar |
| Acento (ações, foco, links) | **azul-tinta** `#2F4A78` | cor de caneta-tinteiro: marca a ação sem gritar (contraste ≥ 8:1 com branco) |
| Sucesso / **receita** | **musgo** `#3B6A3E` | verde de livro-caixa, não de semáforo |
| Atenção / reposição | **ocre** `#C99A3E` (selo: fundo `#F6EEDB`, borda `#8A6420`, texto `#553C0E`) | o alerta continua evidente (ícone + texto + borda), mas sem amarelo-sinal |
| Perigo / **despesa** / caixa negativo | **tijolo** `#A3402F` | vermelho terroso: "saída de dinheiro" sem parecer erro do sistema |
| Séries de gráfico | azul-tinta, musgo, ocre, ardósia `#7D8BA3`, areia `#B9A57E` | mesma luminosidade média; ordem fixa |

Cor nunca é o único sinal: todo estado tem ícone e texto. Os detalhes estão em
[`docs/design/design-system.md`](docs/design/design-system.md) §2.1 (v2.0.0).

### Movimento

As animações são curtas (até 400 ms) e mecânicas, e nunca bloqueiam clique nem digitação:

- linhas novas piscam em azul suave;
- KPIs e cartões surgem em sequência;
- as barras crescem ao entrar;
- diálogos e toasts entram e saem;
- os botões "afundam" ao clicar;
- uma barra de carregamento aparece no topo;
- as páginas trocam com View Transitions;
- o cartão de login treme quando a senha está errada.

Com "reduzir movimento" ligado no sistema operacional, tudo isso desliga.

<img src="docs/capturas/mobile.png" alt="Consus no celular" width="260">

## Qualidade

| Comando | Verifica |
|---------|----------|
| `uv run ruff check .` | lint |
| `uv run ruff format --check .` | formatação |
| `uv run pytest` | testes + cobertura (mínimo 90 %) em SQLite |
| `uv run python manage.py makemigrations --check --dry-run` | migrações em dia |
| `uv run python manage.py checar_contraste` | contraste WCAG AA dos tokens |
| `docker compose --profile testes run --rm testes` | suíte completa no PostgreSQL (concorrência e desempenho incluídos) |
| `uv run pytest -m docker` | integração com Docker Compose (sobe e derruba um ambiente isolado) |

## Como o projeto foi especificado

Desenvolvimento orientado por especificação com o [GitHub Spec Kit](https://github.com/github/spec-kit):

- [`.specify/memory/constitution.md`](.specify/memory/constitution.md): princípios do projeto;
- [`docs/arquitetura.md`](docs/arquitetura.md): contrato compartilhado entre as features;
- [`docs/design/`](docs/design/): design system e as referências estudadas (shadcn/ui, Tremor,
  Carbon, design-resources-for-developers, Refactoring UI);
- [`specs/`](specs/): uma pasta por atividade, cada uma com `spec.md`, `plan.md`, `tasks.md`,
  contratos e checklists:
  1. [`001-fundacao-design-system`](specs/001-fundacao-design-system/): layout, design system, Docker;
  2. [`002-cadastro-produtos`](specs/002-cadastro-produtos/): item 1 da atividade;
  3. [`003-movimentacao-estoque`](specs/003-movimentacao-estoque/): item 2;
  4. [`004-alerta-reposicao`](specs/004-alerta-reposicao/): item 3;
  5. Parte 2 (2.0):
     - [`005-movimento-e-paleta`](specs/005-movimento-e-paleta/);
     - [`006-autenticacao`](specs/006-autenticacao/);
     - [`007-precos-margem`](specs/007-precos-margem/): item 1 do Passo 3;
     - [`008-transacoes-financeiras`](specs/008-transacoes-financeiras/): item 2;
     - [`009-painel-financeiro`](specs/009-painel-financeiro/): item 3;
     - [`010-execucao-local`](specs/010-execucao-local/);
- [`docs/rastreabilidade.md`](docs/rastreabilidade.md) e
  [`docs/auditoria-especificacoes.md`](docs/auditoria-especificacoes.md): auditoria das specs
  contra o enunciado.

Branches: cada feature nasce de `develop` (`NNN-slug`) e volta por merge `--no-ff`;
`main` recebe apenas releases vindas de `develop`.
