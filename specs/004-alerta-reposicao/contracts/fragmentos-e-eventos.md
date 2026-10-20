# Contrato de UI: fragmentos, componentes, eventos e integrações

Todos os estilos usam apenas tokens de `static/css/tokens.css` (001). Esta feature **não cria
componentes nem classes CSS novas**: reutiliza os componentes e classes do design system
entregues pela 001. Ícones vêm do sprite da 001 (`triangle-alert`, `octagon-x`, `circle-check`
— nunca o caractere/emoji ⚠ na web). Nomes de templates, IDs, eventos e funções conforme
`docs/arquitetura.md` v1.1.

## 1. Selo de situação — parcial único `produtos/partials/situacao.html` (002, reutilizado)

A 002 entrega `apps/produtos/templates/produtos/partials/situacao.html` (contexto `produto`),
incluído na linha da lista e no resumo do detalhe, já com as **três** variações do contrato v1.1.
A 004 **não altera** o parcial: apenas o inclui também no relatório e no painel — um único selo
em todas as telas (FR-020).

Ordem de decisão no parcial (espelha `regras.classificar`), delegando o visual a
`components/badge_estoque.html` (001):

| Condição | `situacao` do componente | Visual (design-system §4.4.1) |
|----------|--------------------------|-------------------------------|
| `produto.quantidade_atual == 0` | `sem_estoque` | selo **composto**: segmento "⚠ REPOSIÇÃO NECESSÁRIA" (ícone `triangle-alert`, fundo de alerta) + segmento "SEM ESTOQUE" (ícone `octagon-x`, cor de perigo); nome acessível "Situação: reposição necessária, sem estoque" |
| `produto.em_alerta` | `reposicao` | ícone `triangle-alert` + "REPOSIÇÃO NECESSÁRIA" + cor de alerta |
| senão | `ok` | "OK" discreto, sem cor de alerta |

Funciona com qualquer `Produto` (anotado ou não); nenhuma consulta extra.

## 2. Contador no menu — `{% contador_alertas %}`

- *Inclusion tag* em `apps/alertas/templatetags/alertas_tags.py` (`{% load alertas_tags %}`) que
  renderiza `alertas/partials/contador.html` com `total = selectors.total_em_alerta()` e
  `intervalo = settings.ALERTAS_INTERVALO_SEGUNDOS`. Se a rota `alertas:contador` não existir no
  urlconf corrente (ex.: testes da 001 com urlconf só do core), a tag não renderiza nada.
- A 004 **estende** `templates/components/navegacao.html` (001): dentro do contêiner vazio que a
  001 reserva no item Alertas (mecanismo único do contrato v1.1):

```text
<span id="badge-alertas" class="navegacao__badge">{% load alertas_tags %}{% contador_alertas %}</span>
```

- A região viva `<div id="anuncio-alertas" class="visualmente-oculto" role="status"
  aria-live="polite"></div>` já existe no `templates/base.html` da 001 — a 004 só troca o seu
  conteúdo (OOB `innerHTML`).
- Marcação, polling e respostas: [http-alertas.md](http-alertas.md#get-alertascontador--alertascontador).
  O visual é a classe `.contador-alertas` da 001 (design-system §4.16); com total 0 o elemento
  recebe o atributo `hidden`.

## 3. Componentes do design system reutilizados (001)

### Cobertura — `components/barra_progresso.html`

`{% include "components/barra_progresso.html" with rotulo="Cobertura" valor=produto.cobertura_percentual maximo=100 sufixo="%" tom=produto.situacao_estoque.variante %}`

- `cobertura_percentual is None` ("não se aplica") → no lugar do componente, `<span
  class="texto-atenuado">—</span>`.
- Acima de 100% o componente desenha a barra cheia e mostra o texto real ("150%") — a barra nunca
  ultrapassa o trilho.
- `tom` = `Situacao.variante` (`sem_estoque` → perigo, `reposicao` → alerta, `ok` → sucesso),
  os mesmos tons do componente da 001.
- `role="meter"` com `aria-valuenow`/`aria-valuetext` vem do componente.

### Lista de cobertura do painel — `{% lista_cobertura resumo.cobertura %}`

*Inclusion tag* em `apps/alertas/templatetags/alertas_tags.py` que renderiza
`alertas/partials/lista_cobertura.html`: `<ul class="pilha">` com um `<li>` por `Produto` anotado
contendo o link `#0005 Cola branca 90 g` (`produto.get_absolute_url()`) e o
`components/barra_progresso.html` acima. Sem itens elegíveis: "Sem produtos com estoque mínimo
definido.".

### Demais

`components/kpi.html` (KPIs do painel), `components/estado_vazio.html` (estados vazios),
classes `.tabela`, `.num`, `.botao` (API de classes da 001).

## 4. Ação "+ Entrada" do relatório e do painel

```text
<a href="/movimentacoes/nova/?produto=3&tipo=ENTRADA&quantidade=140"
   hx-get="/movimentacoes/nova/?produto=3&tipo=ENTRADA&quantidade=140&origem=alertas"
   hx-target="#dialogo"
   class="botao botao--secundario botao--sm"
   aria-label="Registrar entrada de #0003 Parafuso sextavado M6 x 20">+ Entrada</a>
```

- IDs e números em atributos com `|unlocalize` (contrato v1.1). `quantidade` =
  `min(sugestao_reposicao, 1.000.000)` (máximo por movimentação da 003); omitida quando a
  sugestão é 0 ou `None`.
- Sem JS: navega para a página de nova movimentação da 003 (produto, tipo e quantidade
  pré-preenchidos).
- Com HTMX: diálogo da 003 com `origem=alertas` — valor e parâmetro `quantidade` **entregues
  pela 003** (contrato v1.1): no sucesso, a resposta não traz fragmentos OOB de produto (o
  relatório/painel não têm linha `#produto-<id>`), só `HX-Reswap: none` + `HX-Trigger`
  (`estoque-alterado`, `toast`, `fechar-dialogo`). O relatório e o painel se atualizam pelo
  evento.
- As linhas do relatório usam `id="reposicao-<id>"` (nunca `produto-<id>`, reservado à lista da
  002/003, para não receber OOB alheio).

## 5. Eventos HTMX

| Evento | Emitido por | Ouvido por (004) | Reação |
|--------|-------------|------------------|--------|
| `estoque-alterado` `{produto_id, saldo_anterior, saldo_posterior}` (carga opcional) | respostas de fragmento após qualquer operação que altere saldo ou situação: movimentação (003), cadastro e edição do estoque mínimo (002) — contrato v1.1 | `#contador-alertas`, `#relatorio`, `#painel-kpis` (`hx-trigger="… estoque-alterado from:body"`) | GET do respectivo fragmento (a carga útil é ignorada) |
| `toast` `{nivel, texto}` (`nivel ∈ {sucesso, info, alerta, erro}`) | resposta da 003 (formato inalterado) | componente de toast da 001 | exibe a confirmação, agora composta por `confirmacao_com_alerta` |
| `fechar-dialogo` | resposta da 003 | 001 | fecha o `<dialog>` |
| (polling) `every Ns` | o próprio `#contador-alertas` | — | GET `/alertas/contador/?anterior=N` |

A 004 **não emite** eventos novos. Respostas de página inteira (comum/*boosted*) já trazem o
contador re-renderizado com o total atual.

## 6. Integração com a feature 003 (aviso na confirmação — FR-019)

Pontos **estendidos** pela 004 (após a 003 estar em `develop`):

| Arquivo (003) | Extensão |
|---------------|----------|
| `apps/movimentacoes/views.py` (`nova_movimentacao`) | onde hoje usa `mov.mensagem_confirmacao`, passa a usar `aviso = confirmacao_com_alerta(mov)`: HTMX → `disparar_toast(response, aviso.nivel, aviso.texto)` (001); sem HTMX → `messages.add_message(request, messages.WARNING if aviso.nivel == "alerta" else messages.SUCCESS, aviso.texto)` |
| `apps/movimentacoes/management/commands/movimentar.py` | após a linha de sucesso, imprime o aviso (estilo `WARNING`) quando `aviso.nivel == "alerta"` — paridade de terminal |

`origem=alertas` (campo oculto e ramo sem OOB em `partials/sucesso_dialogo.html`) e o
parâmetro `quantidade` já são da 003 — a 004 apenas os usa (ver §4).

| Movimentação | `toast.nivel` | `toast.texto` |
|--------------|---------------|---------------|
| Saída 11 → 10, mínimo 10 | `alerta` | "Saída registrada: #0003 Parafuso M6 — saldo 11 → 10. REPOSIÇÃO NECESSÁRIA: #0003 Parafuso M6 ficou com 10 un. (mínimo 10)." |
| Saída 3 → 0, mínimo 5 | `alerta` | "Saída registrada: #0003 Parafuso M6 — saldo 3 → 0. REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: #0003 Parafuso M6 zerou (mínimo 5)." |
| Entrada 4 → 25, mínimo 10 | `sucesso` | "Entrada registrada: #0003 Parafuso M6 — saldo 4 → 25. #0003 Parafuso M6 saiu do alerta de reposição." |
| Entrada 2 → 5, mínimo 10 | `sucesso` | "Entrada registrada: #0003 Parafuso M6 — saldo 2 → 5" (texto da 003 sem acréscimo) |

O texto final tem no máximo 200 caracteres (limite de `disparar_toast` da 001): se a composição
ultrapassar, o nome do produto é encurtado com "…" nas duas ocorrências (o `#ID` permanece).

## 7. Integração com a feature 002 (lista e detalhe — FR-018)

| Arquivo (002) | Extensão |
|---------------|----------|
| `apps/produtos/models.py` | `ProdutoQuerySet.com_situacao()` acrescenta `deficit` e `cobertura_percentual` com `Cast(..., BigIntegerField())` (mantém `alerta`); nenhuma propriedade nova no modelo |

`produtos/partials/situacao.html` é usado sem alteração (§1). Lista, detalhe e a linha
re-renderizada pela 003 já incluem o parcial. O filtro `?situacao=alerta` da 002 continua usando
`em_alerta()` (inclui os SEM ESTOQUE).

## 8. Acessibilidade (FR-017, FR-021)

- Selos: ícone `aria-hidden` + texto visível; nunca só cor; contraste ≥ 4,5:1 (texto) e ≥ 3:1
  (bordas/ícones) contra o fundo (garantido pelo componente da 001).
- Contador: texto acessível "N produto(s) em alerta de reposição"; anúncios só na mudança
  (região viva estável `#anuncio-alertas`, troca `innerHTML`).
- Relatório: `<caption>`, `<th scope="col">`, botão "Executar varredura" com estado ocupado
  (`hx-disabled-elt`) e anúncio do resultado; "+ Entrada" com `aria-label` contendo o nome.
- Foco visível (2px) em todos os controles; ordem de tabulação segue a leitura.
