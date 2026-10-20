# Quickstart: validar o Cadastro de Produtos (002)

Guia de validação da feature. Detalhes de rotas, serviços e fragmentos estão em
[contracts/](./contracts/); campos e restrições em [data-model.md](./data-model.md).

## Pré-requisitos

- Feature 001 implementada (projeto Django, Docker Compose, layout base, design system,
  `#dialogo`, toasts e troca do status 422 configurada no HTMX).
- Branch `002-cadastro-produtos` com as tarefas de [tasks.md](./tasks.md) concluídas.
- `.env` criado a partir de `.env.example`.

> Os comandos abaixo usam os serviços do `docker-compose.yml` da 001: `app` (aplicação, imagem de
> produção, sem dependências de desenvolvimento) e `testes` (perfil `testes`, roda o `pytest`
> contra o PostgreSQL).

## 1. Subir e migrar

```bash
docker compose up --build -d
docker compose exec app python manage.py migrate
docker compose exec app python manage.py makemigrations --check --dry-run   # sem migrações pendentes
```

Esperado: migração `produtos.0001_initial` aplicada; nenhuma migração pendente.

## 2. Testes automatizados

```bash
# Rápido (SQLite, ambiente local)
pytest apps/produtos -q

# Cobertura exigida pela constituição (≥ 90% em models/services/selectors)
pytest apps/produtos --cov=apps/produtos --cov-report=term-missing

# PostgreSQL (inclui os testes @pytest.mark.postgres, pulados no SQLite)
docker compose --profile testes run --rm testes pytest apps/produtos -q

# Rastreabilidade: todo FR da spec citado em algum teste
for n in $(seq -w 1 31); do grep -rqi "fr0$n\|FR-0$n" apps/produtos/tests || echo "FR-0$n sem teste"; done

# Qualidade
ruff check . && ruff format --check .
```

Esperado: tudo verde, nenhuma linha "sem teste", cobertura ≥ 90% nos três módulos.

## 3. Verificações rápidas de contrato (HTTP)

Com o servidor em `http://localhost:8000` e alguns produtos cadastrados:

```bash
# Lista completa x fragmento
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/produtos/                    # 200
curl -s -D - -H "HX-Request: true" -H "HX-Target: resultados" \
  "http://localhost:8000/produtos/?q=%230012" | grep -i "hx-push-url"                        # HX-Push-Url: /produtos/?q=%230012

# Produto inexistente e método proibido
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/produtos/999999/             # 404
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE http://localhost:8000/produtos/1/        # 405
```

## 4. Cenários manuais (navegador)

| # | História | Passos | Resultado esperado |
|---|----------|--------|--------------------|
| M1 | US1 | Base vazia → `/produtos/` | Estado vazio "Nenhum produto cadastrado" com "Cadastrar produto" |
| M2 | US1 | "Novo produto" → diálogo → "Caneta Azul", 50, 10 → Salvar (cronometrar) | Foco no Nome ao abrir; diálogo fecha; `#0001` no topo com selo "NOVO"; toast "Produto #0001 cadastrado"; URL `/produtos/`; tudo em ≤ 30 s (SC-001) |
| M3 | US1 | Diálogo → "  caneta   AZUL ", vazio, "2,5" → Salvar | Diálogo permanece; mensagens junto aos campos; nome preservado; foco no primeiro campo inválido |
| M4 | US1 | Diálogo aberto → Esc | Fecha; nada criado |
| M5 | US1 | Desativar JavaScript → "Novo produto" → salvar válido | Página `/produtos/novo/`; após salvar, lista com destaque e notificação; recarregar remove o destaque |
| M6 | US2 | Cadastrar `#0012` "Parafuso Sextavado" e "Bucha 12 mm"; buscar `12`, `#12`, `#0012` | `12` → ambos; `#12`/`#0012` → só o `#0012`; URL acompanha a busca |
| M7 | US2 | Filtrar "Em alerta", ordenar por "Quantidade" (duas vezes), ir à página 2 | Só produtos com quantidade ≤ mínimo, com "⚠ REPOSIÇÃO NECESSÁRIA" (os zerados com o selo composto "… │ SEM ESTOQUE"); sentido indicado no cabeçalho; filtro/ordem mantidos; URL com `pagina=2` |
| M8 | US2 | Copiar a URL de M7 para outra aba; usar Voltar/Avançar | Mesmo resultado em todos os casos |
| M9 | US2 | Buscar "xyz-inexistente" | "Nenhum produto encontrado" citando o termo + "Limpar busca" |
| M10 | US3 | Abrir `#0001` pela lista; abrir `/produtos/999999/` | Dados completos com datas `dd/mm/aaaa HH:MM` e região de movimentações sem botões; página "Produto não encontrado" |
| M11 | US4 | Editar `#0001`: nome "Caneta Azul Fina", mínimo 60 | Toast "Produto #0001 atualizado"; situação vira "REPOSIÇÃO NECESSÁRIA"; quantidade exibida só para leitura |
| M12 | US4 | DevTools: adicionar `quantidade_atual=999` ao formulário de edição e salvar | Quantidade inalterada |
| M13 | US5 | Na lista, sem foco em campo: `/` e depois `n`; dentro da busca digitar "n/" | `/` foca a busca (sem digitar "/"); `n` abre o diálogo; dentro do campo, só digita |
| M14 | Todas | Repetir M2, M6, M10 e M11 apenas com teclado | Todas concluídas; foco sempre visível |

## 5. Desempenho (SC-003) com 10.000 produtos

```bash
docker compose exec app python manage.py shell -c "
from apps.produtos.services import cadastrar_produto
for i in range(1, 10001):
    cadastrar_produto(nome=f'Produto de carga {i:05d}', quantidade_inicial=i % 50, estoque_minimo=10)
"
```

Na lista, buscar "carga 09", filtrar "Em alerta", ordenar por "Nome" e paginar: cada resultado
deve aparecer em até 1 s após parar de digitar/acionar (aba Network do navegador). Use um banco
descartável — os dados de carga não devem ir para a demonstração.

## 6. Integridade no banco (SC-006)

```bash
docker compose --profile testes run --rm testes pytest apps/produtos/tests/test_models.py -k "constraint or unique" -v
```

Esperado: os testes das restrições `produto_quantidade_atual_nao_negativa`,
`produto_estoque_minimo_nao_negativo`, `produto_nome_nao_vazio` e `produto_nome_unico_ci` passam
no PostgreSQL — o banco recusa quantidade negativa e nome duplicado mesmo sem as camadas de
formulário e serviço. A verificação fica nos testes automatizados (banco de teste descartável),
nunca no shell sobre dados reais (constituição, princípio I).
