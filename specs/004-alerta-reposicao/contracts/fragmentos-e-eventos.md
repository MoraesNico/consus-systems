# Contrato de UI: fragmentos, componentes, eventos e integrações

Todos os estilos usam apenas tokens de `static/css/tokens.css` (001). Classes novas em
`static/css/components.css`. Ícone ⚠ = SVG `alerta` do conjunto de ícones da 001 (nunca o
caractere/emoji na web). Nomes de templates e funções da 002/003 conforme os contratos
publicados por essas features.

## 1. Selo de situação — parcial único `produtos/partials/situacao.html` (002, estendido pela 004)

A 002 já entrega `apps/produtos/templates/produtos/partials/situacao.html` (contexto `produto`),
incluído na linha da lista e no resumo do detalhe, com "REPOSIÇÃO NECESSÁRIA" / "OK". A 004
**estende o mesmo parcial** (não cria outro) com a variação SEM ESTOQUE e passa a incluí-lo no
relatório e no painel — um único selo em todas as telas (FR-020).

Ordem de decisão no parcial (espelha `regras.classificar`):

| Condição | Marcação | Visual |
|----------|----------|--------|
| `produto.quantidade_atual == 0` | `<span class="badge badge--perigo selo-situacao"><svg aria-hidden="true">…alerta…</svg>SEM ESTOQUE</span>` | cor de perigo, borda 2px (variação mais grave) |
| `produto.em_alerta` | `<span class="badge badge--alerta selo-situacao"><svg aria-hidden="true">…alerta…</svg>REPOSIÇÃO NECESSÁRIA</span>` | cor de alerta, caixa alta com tracking |
| senão | `<span class="badge badge--neutro selo-situacao">OK</span>` | texto atenuado, sem ícone e sem cor de alerta |

Funciona com qualquer `Produto` (anotado ou não); nenhuma consulta extra. Os nomes de classe do
badge seguem o componente `badge` da 001; o contrato aqui é **texto + ícone + variante**.

## 2. Contador no menu — `{% contador_alertas %}`

- *Inclusion tag* em `apps/alertas/templatetags/alertas_tags.py` (`{% load alertas_tags %}`) que
  renderiza `alertas/partials/contador.html` com `total = selectors.total_em_alerta()` e
  `intervalo = settings.ALERTAS_INTERVALO_SEGUNDOS`.
- Uso em `templates/base.html` (001):

```text
<nav …>
  …
  <a href="{% url 'alertas:relatorio' %}" class="menu__item">Alertas {% contador_alertas %}</a>
</nav>
…
<div id="anuncio-alertas" class="visualmente-oculto" role="status" aria-live="polite"></div>
```

- Marcação, polling e respostas: [http-alertas.md](http-alertas.md#get-alertascontador--alertascontador).

## 3. Componentes novos do design system

### `templates/components/barra_cobertura.html` (estilo ProgressBar/CategoryBar do Tremor)

Parâmetros (`{% include … with … %}`): `percentual` (int ou `None`), `variante`
(`perigo` | `alerta` | `sucesso`).

```text
{% if percentual is None %}<span class="texto-atenuado">—</span>{% else %}
<span class="barra-cobertura barra-cobertura--{{ variante }}" aria-hidden="true">
  <span class="barra-cobertura__preenchimento" style="--valor: {{ percentual_limitado }}%"></span>
</span>
<span class="numero">{{ percentual }}%</span>{% endif %}
```

- `percentual_limitado = min(percentual, 100)` (filtro `limitar_100` em `alertas_tags`) — a barra
  nunca ultrapassa o trilho.
- `variante` vem de `produto.situacao_estoque.variante_barra` (SEM ESTOQUE → `perigo`,
  REPOSIÇÃO NECESSÁRIA → `alerta`, OK → `sucesso`).
- Trilho: borda 1px, raio 0–2px, altura e largura de token; a barra é decorativa
  (`aria-hidden`) porque o percentual é texto visível.

### `templates/components/bar_list.html` (estilo BarList do Tremor)

Parâmetros: `itens` — iterável de dicionários com `rotulo`, `valor_texto`, `percentual` (0–100),
`variante`, `href` (opcional). Como templates Django não montam dicionários, o painel usa a
*inclusion tag* `{% cobertura_bar_list resumo.cobertura %}` (`apps/alertas/templatetags/alertas_tags.py`),
que converte cada `Produto` anotado em `{rotulo: "#0005 Cola branca 90 g", valor_texto: "0%",
percentual: min(cobertura, 100), variante: situacao_estoque.variante_barra, href:
produto.get_absolute_url()}` e renderiza o componente genérico.

```text
<ul class="bar-list">
  <li class="bar-list__item">
    <a class="bar-list__rotulo" href="…">#0005 Cola branca 90 g</a>
    <span class="bar-list__trilho" aria-hidden="true"><span class="bar-list__barra bar-list__barra--perigo" style="--valor: 0%"></span></span>
    <span class="bar-list__valor numero">0%</span>
  </li>
</ul>
```

## 4. Ação "+ Entrada" do relatório e do painel

```text
<a href="/movimentacoes/nova/?produto=3&tipo=ENTRADA"
   hx-get="/movimentacoes/nova/?produto=3&tipo=ENTRADA&origem=alertas"
   hx-target="#dialogo"
   class="botao botao--compacto"
   aria-label="Registrar entrada de #0003 Parafuso sextavado M6 x 20">+ Entrada</a>
```

- Sem JS: navega para a página de nova movimentação da 003 (produto e tipo pré-selecionados).
- Com HTMX: diálogo da 003. A 004 acrescenta à 003 o valor `origem=alertas` (ver §6): no sucesso,
  a resposta não traz fragmentos OOB de produto (o relatório/painel não têm linha
  `#produto-<id>`), só `HX-Reswap: none` + `HX-Trigger` (`estoque-alterado`, `toast`,
  `fechar-dialogo`). O relatório e o painel se atualizam pelo evento.
- As linhas do relatório usam `id="reposicao-<id>"` (nunca `produto-<id>`, reservado à lista da
  002/003, para não receber OOB alheio).

## 5. Eventos HTMX

| Evento | Emitido por | Ouvido por (004) | Reação |
|--------|-------------|------------------|--------|
| `estoque-alterado` `{produto_id, saldo_anterior, saldo_posterior}` | resposta HTMX de movimentação da 003; cadastro parcial da 002 | `#contador-alertas`, `#relatorio`, `#painel-conteudo` (`hx-trigger="… estoque-alterado from:body"`) | GET do respectivo fragmento (a carga útil é ignorada) |
| `toast` `{nivel, texto}` | resposta da 003 (formato inalterado) | componente de toast da 001 | exibe a confirmação, agora composta por `confirmacao_com_alerta` |
| `fechar-dialogo` | resposta da 003 | 001 | fecha o `<dialog>` |
| (polling) `every Ns` | o próprio `#contador-alertas` | — | GET `/alertas/contador/?anterior=N` |

A 004 **não emite** eventos novos.

## 6. Integração com a feature 003 (aviso na confirmação — FR-019)

Pontos alterados pela 004 (após a 003 estar em `develop`):

| Arquivo (003) | Alteração |
|---------------|-----------|
| `apps/movimentacoes/views.py` (`nova_movimentacao`) | onde hoje usa `mov.mensagem_confirmacao`, passa a usar `aviso = confirmacao_com_alerta(mov)`: HTMX → `toast` `{"nivel": aviso.nivel, "texto": aviso.texto}`; sem HTMX → `messages.add_message(request, messages.WARNING if aviso.nivel == "alerta" else messages.SUCCESS, aviso.texto)` |
| `apps/movimentacoes/forms.py` | campo oculto `origem` aceita também `alertas` |
| `apps/movimentacoes/templates/movimentacoes/partials/sucesso_dialogo.html` | `origem=alertas` → nenhum fragmento OOB (corpo vazio) |
| `apps/movimentacoes/management/commands/movimentar.py` | após a linha de sucesso, imprime o aviso (estilo `WARNING`) quando `aviso.nivel == "alerta"` — paridade de terminal |

| Movimentação | `toast.nivel` | `toast.texto` |
|--------------|---------------|---------------|
| Saída 11 → 10, mínimo 10 | `alerta` | "Saída registrada: #0003 Parafuso M6 — saldo 11 → 10. REPOSIÇÃO NECESSÁRIA: #0003 Parafuso M6 ficou com 10 un. (mínimo 10)." |
| Saída 3 → 0, mínimo 5 | `alerta` | "Saída registrada: #0003 Parafuso M6 — saldo 3 → 0. SEM ESTOQUE: #0003 Parafuso M6 zerou (mínimo 5)." |
| Entrada 4 → 25, mínimo 10 | `sucesso` | "Entrada registrada: #0003 Parafuso M6 — saldo 4 → 25. #0003 Parafuso M6 saiu do alerta de reposição." |
| Entrada 2 → 5, mínimo 10 | `sucesso` | "Entrada registrada: #0003 Parafuso M6 — saldo 2 → 5" (texto da 003 sem acréscimo) |

## 7. Integração com a feature 002 (lista e detalhe — FR-018)

| Arquivo (002) | Alteração |
|---------------|-----------|
| `apps/produtos/templates/produtos/partials/situacao.html` | acrescenta o ramo SEM ESTOQUE (§1) antes do ramo REPOSIÇÃO NECESSÁRIA |
| `apps/produtos/models.py` | `ProdutoQuerySet.com_situacao()` acrescenta `deficit` e `cobertura_percentual` (mantém `alerta`) |

Lista, detalhe e a linha re-renderizada pela 003 já incluem o parcial — passam a exibir SEM
ESTOQUE sem outra mudança. O filtro `?situacao=alerta` da 002 continua usando `em_alerta()`
(inclui os SEM ESTOQUE).

## 8. Acessibilidade (FR-017, FR-021)

- Selos: ícone `aria-hidden` + texto visível; nunca só cor; contraste ≥ 4,5:1 (texto) e ≥ 3:1
  (bordas/ícones) contra o fundo.
- Contador: texto acessível "N produto(s) em alerta de reposição"; anúncios só na mudança
  (região viva estável `#anuncio-alertas`, troca `innerHTML`).
- Relatório: `<caption>`, `<th scope="col">`, botão "Executar varredura" com estado ocupado
  (`hx-disabled-elt`) e anúncio do resultado; "+ Entrada" com `aria-label` contendo o nome.
- Foco visível (2px) em todos os controles; ordem de tabulação segue a leitura.
