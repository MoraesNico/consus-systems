# Contrato de UI: fragmentos, componentes, eventos e integrações

Todos os estilos usam apenas tokens de `static/css/tokens.css` (001). Classes novas em
`static/css/components.css`. Ícone ⚠ = SVG `alerta` do conjunto de ícones da 001 (nunca o
caractere/emoji na web).

## 1. Selo de situação — `{% situacao_produto obj %}`

- Tag: `apps/alertas/templatetags/alertas_tags.py` (`{% load alertas_tags %}`), *inclusion tag*
  que renderiza `alertas/partials/situacao.html`.
- Aceita: `Produto` (anotado ou não — sem anotação, calcula com `regras.classificar`) ou
  `ItemReposicao`. Nenhuma consulta extra.

| Situação | Marcação | Visual |
|----------|----------|--------|
| `REPOSICAO_NECESSARIA` | `<span class="selo selo--alerta"><svg aria-hidden="true">…alerta…</svg>REPOSIÇÃO NECESSÁRIA</span>` | fundo/borda de alerta, texto em caixa alta com tracking, contraste AA |
| `SEM_ESTOQUE` | `<span class="selo selo--perigo"><svg aria-hidden="true">…alerta…</svg>SEM ESTOQUE</span>` | cor de perigo, borda 2px (variação mais grave) |
| `OK` | `<span class="selo selo--neutro">OK</span>` | texto atenuado, sem ícone e sem cor de alerta |

Se a 001 expuser `components/badge.html` com variantes, o parcial o reutiliza; o contrato aqui é
o **texto + ícone + classe de variante**, idênticos em todas as telas (FR-020).

## 2. Contador no menu — `{% contador_alertas %}`

- *Inclusion tag* que renderiza `alertas/partials/contador.html` com `total =
  selectors.total_em_alerta()` e `intervalo = settings.ALERTAS_INTERVALO_SEGUNDOS`.
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

Parâmetros (`{% include … with … %}`): `percentual` (int ou `None`), `situacao` (`Situacao`).

```text
{% if percentual is None %}<span class="texto-atenuado">—</span>{% else %}
<span class="barra-cobertura barra-cobertura--{{ variante }}" aria-hidden="true">
  <span class="barra-cobertura__preenchimento" style="--valor: {{ percentual_limitado }}%"></span>
</span>
<span class="numero">{{ percentual }}%</span>{% endif %}
```

- `percentual_limitado = min(percentual, 100)` — a barra nunca ultrapassa o trilho.
- `variante`: `perigo` (SEM ESTOQUE), `alerta` (REPOSIÇÃO NECESSÁRIA), `sucesso` (OK).
- Trilho: borda 1px, raio 0–2px, altura e largura de token; a barra é decorativa
  (`aria-hidden`) porque o percentual é texto visível.

### `templates/components/bar_list.html` (estilo BarList do Tremor)

Parâmetros: `itens` — iterável de objetos com `rotulo`, `valor_texto`, `percentual` (0–100),
`variante`, `href` (opcional).

```text
<ul class="bar-list">
  <li class="bar-list__item">
    <a class="bar-list__rotulo" href="…">#0007 Cola branca 90 g</a>
    <span class="bar-list__trilho" aria-hidden="true"><span class="bar-list__barra bar-list__barra--perigo" style="--valor: 0%"></span></span>
    <span class="bar-list__valor numero">0%</span>
  </li>
</ul>
```

## 4. Eventos HTMX

| Evento | Emitido por | Ouvido por (004) | Reação |
|--------|-------------|------------------|--------|
| `estoque-alterado` | resposta de movimentação da 003 (`HX-Trigger`); 002 após cadastro/edição (proposta 2) | `#contador-alertas`, `#relatorio`, `#painel-conteudo` (`hx-trigger="… estoque-alterado from:body"`) | GET do respectivo fragmento |
| `toast` `{nivel, texto}` | resposta da 003 (inalterado no formato) | componente de toast da 001 | exibe a confirmação, agora composta por `mensagem_confirmacao` |
| (polling) `every Ns` | o próprio `#contador-alertas` | — | GET `/alertas/contador/?anterior=N` |

A 004 **não emite** eventos novos.

## 5. Integração com a feature 003 (aviso no toast — FR-019)

No ponto em que a view de movimentação da 003 monta o aviso de sucesso:

```python
from apps.alertas.regras import mensagem_confirmacao

aviso = mensagem_confirmacao(texto_base, movimentacao)   # texto_base = FR-016 da 003
# HTMX:     HX-Trigger: {"toast": {"nivel": aviso.nivel, "texto": aviso.texto}, "estoque-alterado": true}
# sem HTMX: messages.add_message(request, WARNING if aviso.nivel == "alerta" else SUCCESS, aviso.texto)
```

| Movimentação | `toast.nivel` | `toast.texto` |
|--------------|---------------|---------------|
| Saída 11 → 10, mínimo 10 | `alerta` | "Saída registrada: #0003 Parafuso M6 — saldo 11 → 10. REPOSIÇÃO NECESSÁRIA: #0003 Parafuso M6 ficou com 10 un. (mínimo 10)." |
| Saída 3 → 0, mínimo 5 | `alerta` | "… — saldo 3 → 0. SEM ESTOQUE: #0003 Parafuso M6 zerou (mínimo 5)." |
| Entrada 4 → 25, mínimo 10 | `sucesso` | "… — saldo 4 → 25. #0003 Parafuso M6 saiu do alerta de reposição." |
| Entrada 2 → 5, mínimo 10 | `sucesso` | texto da 003 sem acréscimo |

## 6. Integração com a feature 002 (lista e detalhe — FR-018)

- Na célula "Situação" da linha da lista e no cabeçalho do detalhe, o indicador da 002 passa a ser
  `{% situacao_produto produto %}` (acrescenta "SEM ESTOQUE" ao "OK"/"REPOSIÇÃO NECESSÁRIA" da 002).
- O filtro `?situacao=alerta` da 002 continua usando `em_alerta()` — inclui os SEM ESTOQUE.
- A lista pode usar `com_situacao()` para evitar cálculo por linha; o selo funciona com ou sem.

## 7. Acessibilidade (FR-017, FR-021)

- Selos: ícone `aria-hidden` + texto visível; nunca só cor; contraste ≥ 4,5:1 (texto) e ≥ 3:1
  (bordas/ícones) contra o fundo.
- Contador: texto acessível "N produto(s) em alerta de reposição"; anúncios só na mudança
  (região viva estável `#anuncio-alertas`, troca `innerHTML`).
- Relatório: `<caption>`, `<th scope="col">`, botão "Executar varredura" com estado ocupado
  (`hx-disabled-elt`) e anúncio do resultado; "+ Entrada" com `aria-label` contendo o nome.
- Foco visível (2px) em todos os controles; ordem de tabulação segue a leitura.
