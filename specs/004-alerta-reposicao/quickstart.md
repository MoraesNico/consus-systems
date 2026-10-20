# Quickstart: validar a feature 004 — Alerta de Reposição

Guia de validação ponta a ponta. Contratos: [contracts/](contracts/) · dados esperados:
[data-model.md §6](data-model.md#6-dados-de-demonstração).

## Pré-requisitos

- Features 001, 002 e 003 integradas em `develop` e esta branch atualizada sobre ela.
- `cp .env.example .env` (opcional: `ALERTAS_INTERVALO_SEGUNDOS=10` para ver o polling mais rápido).
- Docker + Docker Compose; ou Python 3.13 + `uv` para rodar local com SQLite.

## 1. Subir e popular

```bash
docker compose up --build -d
docker compose exec app python manage.py migrate
docker compose exec app python manage.py popular_demo
# esperado: "Dados de demonstração: 12 produto(s) criado(s), 0 já existia(m)."
docker compose exec app python manage.py popular_demo
# esperado: "… 0 produto(s) criado(s), 12 já existia(m)." e "Movimentações registradas: 0."
```

## 2. Terminal (História 4)

```bash
docker compose exec app python manage.py varrer_estoque
# esperado: 12 analisados · "Em alerta: 4 (1 sem estoque)" · 4 linhas "⚠ REPOSIÇÃO NECESSÁRIA",
# na ordem Cola branca → Parafuso M6 → Luva de nitrilo → Fita adesiva 48 mm

docker compose exec app python manage.py varrer_estoque --formato json | python -m json.tool
docker compose exec app python manage.py varrer_estoque --formato csv
docker compose exec app python manage.py varrer_estoque --todos          # +8 linhas "OK" no fim

docker compose exec app python manage.py varrer_estoque --falhar-se-alerta; echo "código=$?"
# esperado: relatório + stderr "Há 4 produto(s) em alerta de reposição." e código=1

docker compose exec app python manage.py varrer_estoque --formato pdf; echo "código=$?"
# esperado: mensagem de uso e código=2
```

## 3. Relatório de Reposição (História 1) — http://localhost:8000/alertas/

1. Conferir o resumo "Varredura em dd/mm/aaaa HH:MM · 12 produtos analisados · 4 em alerta
   (1 sem estoque)" e as 4 linhas na ordem acima; Cola branca com o selo composto
   **⚠ REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE**, as demais com **⚠ REPOSIÇÃO NECESSÁRIA** (ícone +
   texto + cor).
2. Fita adesiva 48 mm (24/24): déficit 0, cobertura 100%, sugestão +24.
3. Aguardar 1 minuto e clicar **Executar varredura**: a hora muda sem recarregar a página; o leitor
   de tela anuncia "Varredura concluída: 4 produtos em alerta (1 sem estoque) de 12 analisados."
4. Na linha do Parafuso M6, **+ Entrada** → diálogo da 003 com produto e tipo Entrada e a
   quantidade já preenchida com a sugestão (140) → confirmar. Esperado: toast "… saiu do alerta de reposição.", o Parafuso some
   do relatório e o contador do menu passa de 4 para 3, sem recarregar.
5. Desativar o JavaScript do navegador e repetir 1 e 3: a varredura funciona por recarregamento.

## 4. Alerta automático (História 2)

1. Em `/produtos/`: Cola branca mostra **⚠ REPOSIÇÃO NECESSÁRIA │ SEM ESTOQUE**, Grampeador
   (6/5) mostra **OK**, Fita adesiva mostra **⚠ REPOSIÇÃO NECESSÁRIA**; o detalhe de cada um
   mostra o mesmo selo.
2. No Grampeador, **− Saída** de 1 (6 → 5, mínimo 5): toast de nível alerta com
   "REPOSIÇÃO NECESSÁRIA: #0006 Grampeador de mesa 26/6 ficou com 5 un. (mínimo 5)." e contador +1.
3. No Grampeador, nova saída de 5 (5 → 0): toast "REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: … zerou (mínimo 5)."; contador
   inalterado (já estava em alerta).
4. Com a página aberta e sem tocar nela, em outro terminal:
   `docker compose exec app python manage.py shell -c "from apps.movimentacoes.services import registrar_movimentacao as r; r(produto_id=7, tipo='ENTRADA', quantidade=50)"`
   → em até `ALERTAS_INTERVALO_SEGUNDOS` o contador diminui sozinho.
5. Com leitor de tela (NVDA/Orca): a mudança do contador é anunciada uma vez; ciclos sem mudança
   não anunciam nada (no DevTools, as requisições `/alertas/contador/?anterior=N` respondem 204).

## 5. Painel (História 3) — http://localhost:8000/

- KPIs logo após `popular_demo` em base vazia: **12** produtos · **474** unidades · **4** em alerta
  (1 sem estoque) · **16** movimentações nas últimas 24 h.
- "Reposição necessária": 4 itens (ordem do relatório) + "Ver relatório completo (4)".
- "Cobertura do mínimo": 8 itens, começando por Cola branca (0%); Etiqueta adesiva (mínimo 0)
  não aparece.
- "Últimas movimentações": 5 linhas, mais recentes primeiro.
- Registrar uma movimentação por um "+ Entrada" do próprio painel: KPIs e listas mudam sem
  recarregar.

## 6. CSV (História 5)

```bash
curl -s -D - "http://localhost:8000/alertas/?formato=csv" -o reposicao.csv | grep -i "content-"
# Content-Type: text/csv; charset=utf-8
# Content-Disposition: attachment; filename="reposicao-AAAAMMDD-HHMM.csv"
head -c 3 reposicao.csv | xxd     # ef bb bf (BOM)
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/alertas/?formato=pdf"   # 400
```

Abrir o arquivo no LibreOffice/Excel em pt-BR: 8 colunas, acentos íntegros, mesma ordem da tela.
Cadastrar um produto chamado `=1+1` com mínimo maior que a quantidade e exportar de novo: a célula
mostra o texto `=1+1`, não o resultado 2.

## 7. Testes automatizados

```bash
docker compose --profile testes run --rm testes pytest apps/alertas \
  apps/produtos/tests/test_queryset_situacao.py apps/core/tests/test_painel_kpis.py -q
docker compose --profile testes run --rm testes pytest --cov=apps.alertas --cov=apps.produtos.models \
  --cov-report=term-missing --cov-fail-under=90 apps/alertas apps/produtos/tests/test_queryset_situacao.py
docker compose --profile testes run --rm testes pytest -q   # suíte completa (PostgreSQL, serviço `testes` da 001)
uv run pytest -q                                            # suíte completa (SQLite: sem DATABASE_URL — FR-006 da 001)
ruff check . && ruff format --check . && python manage.py makemigrations --check --dry-run
# makemigrations --check: "No changes detected" (a 004 não tem migrações)
```

Mapa rápido testes → requisitos: cada teste cita o FR no nome ou docstring (ex.:
`test_fr002_quantidade_igual_ao_minimo_entra_em_alerta`); ver `tasks.md`.
