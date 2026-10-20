# Quickstart — validar a feature 001 (Fundação e Design System)

Guia de validação ponta a ponta. Contratos: [rotas-core](contracts/rotas-core.md),
[layout-e-htmx](contracts/layout-e-htmx.md), [componentes](contracts/componentes.md). Dados e
configuração: [data-model](data-model.md).

## Pré-requisitos

- Docker Engine 24+ com Compose v2 (`docker compose version`).
- Para rodar fora do contêiner: Python 3.13 e [uv](https://docs.astral.sh/uv/) 0.5+.
- Porta 8000 livre (ou defina `CONSUS_PORTA` no `.env`).

## 1. Subir com um comando (US1 · FR-001/002/003/007/010 · SC-001)

```bash
cp .env.example .env
docker compose up --build
```

Esperado:

- logs do `db` até "database system is ready to accept connections";
- logs do `app`: `migrate` aplicando `contenttypes` e `sessions` (na 1ª vez) e o Gunicorn
  "Listening at: http://0.0.0.0:8000";
- `docker compose ps` mostra `app` e `db` como **healthy** em até ~1 min.

Verificações rápidas em outro terminal:

```bash
curl -i http://localhost:8000/saude/          # 200 {"status": "ok", "banco": "ok", "versao": "0.1.0"}
curl -I http://localhost:8000/                 # 200, X-Frame-Options: DENY, Referrer-Policy: same-origin
curl -i http://localhost:8000/nao-existe/      # 404 com página estilizada
curl -i http://localhost:8000/admin/           # 404 (admin não exposto, FR-044)
docker compose exec app id -u                  # ≠ 0 (FR-010)
```

Persistência (FR-007): `docker compose down && docker compose up -d` → `migrate` informa "No
migrations to apply" e o volume `dados_postgres` continua listado em `docker volume ls`.

## 2. Cenários manuais no navegador (http://localhost:8000)

| # | Cenário | Esperado | Requisitos |
|---|---------|----------|-----------|
| M1 | Abrir `/` | Painel com marca "CONSUS", navegação Painel · Produtos (em breve) · Movimentações (em breve) · Alertas (em breve); "Painel" ativo (barra ultramar); estado vazio "Os indicadores aparecem aqui" com ação "Cadastrar produto (em breve)" desabilitada; aba "Painel — Consus" | FR-011/012/013/019/022 |
| M2 | Teclado: `Tab` a partir do topo | 1º foco = "Pular para o conteúdo"; todo foco com contorno ultramar de 2 px | FR-011/025, SC-006 |
| M3 | Rodapé → "Catálogo de design" | `/design/` com sumário (cores, contraste, tipografia, espaçamento, tamanhos, bordas, sombras, camadas, movimento + 18 componentes) | FR-031, SC-004 |
| M4 | Catálogo → Toasts → disparar os 4 níveis | sucesso/info somem em 5 s (param no hover); alerta/erro ficam até fechar; no máx. 3 empilhados; leitor de tela anuncia | FR-015/016 |
| M5 | Catálogo → "Abrir diálogo de exemplo" | diálogo abre com foco em "Nome"; `Esc` fecha e o foco volta ao botão; clique no fundo **não** fecha | FR-017 |
| M6 | No diálogo, enviar vazio; depois preencher e enviar | vazio → erros dentro do diálogo (borda vermelha + mensagem com ícone); válido → diálogo fecha e toast de sucesso | FR-032, FR-018 |
| M7 | Com o diálogo aberto, `docker compose stop app` e reenviar | toast de erro **dentro** do diálogo ("Sem conexão com o servidor.") | FR-017/018 |
| M8 | Desativar JavaScript e repetir M1, M3, M5, M6 | navegação por página inteira; diálogo vira página; toasts viram avisos inline no topo | FR-018/032 |
| M9 | Navegar Painel → Catálogo → Painel com toast visível | toast continua visível (não some na troca de página) | FR-016 |
| M10 | Largura 320 px (DevTools) | sem rolagem horizontal da página; navegação rola horizontalmente; tabela do catálogo rola dentro do contêiner | FR-021, SC-008 |
| M11 | SO em modo escuro | interface continua clara (controles nativos claros) | FR-023 |
| M12 | `prefers-reduced-motion: reduce` (DevTools → Rendering) | nenhuma animação; botões não "afundam" | FR-030 |
| M13 | DevTools → Network, recarregar `/` com cache limpo | 0 requisições a domínios externos; total ≤ 300 KB; 2ª visita servida do cache | FR-008, SC-007, SC-010 |
| M14 | `docker compose stop db` e `curl -i http://localhost:8000/saude/` | 503 `{"status": "erro", "banco": "indisponivel", …}` em ≤ 3 s; `/` continua respondendo | FR-035, SC-005 |
| M15 | Com `db` parado, abrir uma URL que consulta o banco (a partir da 002) ou forçar erro | página 500 estilizada, sem detalhes técnicos | FR-038 |

Restaurar: `docker compose start db`.

## 3. Quality gates locais (US5 · FR-040/041/042)

```bash
uv sync                                         # instala pelo uv.lock (inclui grupo dev)
uv run ruff check .                             # 0 violações
uv run ruff format --check .                    # 0 arquivos a reformatar
uv run python manage.py makemigrations --check --dry-run   # "No changes detected"
uv run pytest                                   # SQLite; cobertura ≥ 90 % (fail_under)
uv run python manage.py checar_contraste        # tabela de contraste; código de saída 0
```

Suíte no PostgreSQL em contêiner (FR-041):

```bash
docker compose --profile testes run --rm testes
```

Teste de integração do Docker (opt-in, sobe e derruba o Compose; ~2–3 min):

```bash
uv run pytest -m docker
```

## 4. Critérios de aceite da feature

- Todos os comandos da seção 3 terminam com sucesso.
- Cenários M1–M14 conferidos (M15 a partir da feature 002).
- `docs/design/design-system.md` e `/design/` mostram os mesmos tokens e contrastes (o catálogo
  calcula a partir de `tokens.css`).
