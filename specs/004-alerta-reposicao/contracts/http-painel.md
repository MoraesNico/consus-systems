# Contrato HTTP: Painel (`GET /` — `core:painel`)

A rota, o nome e a view pertencem à feature 001 (placeholder). A 004 substitui o conteúdo:
`apps/core/views.py::painel` passa a usar `alertas.selectors.resumo_painel()`.

## Requisição

`GET /` — sem parâmetros. Outros métodos → 405. `@never_cache`, `Vary: HX-Request, HX-Target`.
Fragmento quando `apps.core.htmx.eh_fragmento(request)` (001).

## Respostas

| Caso | Status | Template |
|------|-------:|----------|
| Sem HTMX ou `HX-Boosted: true` | 200 | `core/painel.html` (estende `base.html`, inclui o parcial) |
| `HX-Request: true` sem `HX-Boosted` (atualização por evento) | 200 | `core/partials/painel_kpis.html` (nome previsto pela 001) |

Contexto: `resumo` (`ResumoPainel`). Orçamento: ≤ 7 consultas SQL na página completa (5 do
resumo + contador do menu + folga para o layout da 001).

## Estrutura (`core/partials/painel_kpis.html`)

A região estável é a `#painel-kpis` reservada pela 001 (`core/painel.html` passa a incluir este
parcial no lugar do estado vazio provisório).

```text
<section id="painel-kpis" aria-labelledby="painel-kpis-titulo"
         hx-get="/" hx-trigger="estoque-alterado from:body" hx-swap="outerHTML">

  ── Faixa de KPIs (4 × components/kpi.html da 001, grade 12 col → 3 col cada; 6 col em telas estreitas)
     │ PRODUTOS CADASTRADOS │ UNIDADES EM ESTOQUE │ EM ALERTA                │ MOVIMENTAÇÕES · 24 H │
     │ 12                   │ 474                 │ 4  · 1 sem estoque       │ 16 · entradas + saídas│
     O KPI "EM ALERTA" usa ícone ⚠ (SVG) + cor de alerta quando > 0 e é link para alertas:relatorio.

  ── Coluna principal (8 col): "Reposição necessária"
     ├ até 5 itens (selectors: ordem de criticidade): #ID, nome, selo (produtos/partials/situacao.html),
     │ atual/mín., sugestão, ação "+ Entrada" (origem=alertas — mesmo contrato do relatório)
     ├ rodapé: link "Ver relatório completo (7)" → alertas:relatorio
     └ sem alertas: estado vazio positivo "Nenhum produto precisa de reposição."

  ── Coluna lateral (4 col): "Cobertura do mínimo" — {% lista_cobertura resumo.cobertura %} → <ul> de components/barra_progresso.html (001)
     até 8 itens, menor cobertura primeiro (empate: menor ID); barra = min(cobertura, 100)%,
     valor "40%"; cor por situação; itens com cobertura "não se aplica" excluídos;
     sem itens: "Sem produtos com estoque mínimo definido."

  ── Largura total (12 col): "Últimas movimentações" — tabela densa, 5 linhas
     Data/hora (dd/mm/aaaa HH:MM) | Tipo (selo de texto da 003) | Produto (#ID nome) | Quantidade (+/−) | Saldo
     sem movimentações: "Nenhuma movimentação registrada."

  ── Sem produtos (total_produtos == 0): KPIs zerados + estado vazio "Cadastre o primeiro produto"
     com link para produtos:novo (substitui as três listas).
</section>
```

## Eventos

| Evento | Origem | Efeito |
|--------|--------|--------|
| `estoque-alterado` (em `body`) | respostas de fragmento da 003 após movimentação e da 002 após cadastro/edição do mínimo (contrato v1.1) | `GET /` com `HX-Request` → troca `#painel-kpis` |
