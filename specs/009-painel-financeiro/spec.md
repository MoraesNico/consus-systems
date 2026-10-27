# Feature 009 — Painel financeiro e alerta de caixa

**Origem**: Passo 3, item 3 · **Contrato**: `docs/arquitetura.md` v1.2, "Painel financeiro".

## História
Como gestor, quero ver em uma tela o valor do estoque, o faturamento, o lucro bruto e o saldo do
caixa, com um alerta quando o caixa ficar negativo no período.

## Requisitos
- **FR-001** KPIs:
  - Valor total do estoque (Σ quantidade × custo, foto do momento);
  - Faturamento (Σ receitas);
  - Lucro bruto realizado (receitas − CPV, com a margem realizada %);
  - Saldo do caixa (receitas − despesas).
- **FR-002** Com saldo < 0, o KPI fica na variante de perigo e aparece o aviso **CAIXA NEGATIVO** ("As despesas superam as receitas em R$ X no período."): ícone + texto + cor. Saldo zero ou positivo não alerta.
- **FR-003** Sem dados, aparecem zeros e estados vazios, sem erro.
- **FR-004** `/financeiro/` mostra os KPIs, o gráfico de fluxo de caixa (receitas × despesas por dia, ou por mês quando o intervalo passa de 62 dias, com tabela acessível), os 5 maiores em faturamento, lucro e valor em estoque, e as últimas 5 transações.
- **FR-005** Períodos: Todo o período (padrão) · Este mês · 30 dias · 7 dias · Hoje · Personalizado, via HTMX com `hx-push-url`. Um intervalo inválido gera aviso e cai em "Todo o período".
- **FR-006** O Painel `/` ganha a faixa financeira (valor em estoque, faturamento total e saldo + alerta) com link para `/financeiro/`.
- **FR-007** `manage.py resumo_financeiro [--periodo] [--de --ate] [--formato texto|json] [--falhar-se-negativo]` sai com 0, 1 (caixa negativo com a opção) ou 2 (erro).
- **FR-008** A demonstração espalha as movimentações em 30 dias: "Todo o período" com caixa negativo (−R$ 3.718,00) e "Últimos 7 dias" com saldo positivo.

Navegação: Painel · Produtos · Movimentações · **Financeiro** · Alertas.
