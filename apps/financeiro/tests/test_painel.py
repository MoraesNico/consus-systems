"""009 — Painel financeiro (Passo 3, item 3) e alerta de caixa negativo."""

import json
from decimal import Decimal

import pytest
from django.core.management import call_command

from apps.core.periodos import resolver_periodo
from apps.financeiro.selectors import resumo_financeiro
from apps.movimentacoes.services import registrar_movimentacao
from apps.produtos.services import cadastrar_produto

pytestmark = pytest.mark.django_db
D = Decimal


def produto(nome="Toner", qtd=10, custo="189.00", venda="279.00"):
    return cadastrar_produto(nome=nome, quantidade_inicial=qtd, estoque_minimo=1,
                             preco_custo=D(custo), preco_venda=D(venda))  # fmt: skip


def test_fr001_indicadores_da_atividade():
    p = produto()
    registrar_movimentacao(produto_id=p.pk, tipo="SAIDA", quantidade=4)
    r = resumo_financeiro(resolver_periodo("tudo"))
    assert r.valor_estoque == D("1134.00")  # 6 × 189
    assert r.receitas == D("1116.00")  # faturamento total
    assert r.lucro_bruto == D("360.00")  # receita − CPV (4 × 189)
    assert r.margem_realizada_percentual == D("32.3")
    assert r.saldo_caixa == D("-774.00") and r.caixa_negativo
    assert [i["valor"] for i in r.top_faturamento] == [D("1116.00")]
    assert r.top_lucro[0]["valor"] == D("360.00")
    assert r.maiores_valores_estoque[0]["valor"] == D("1134.00")
    assert len(r.ultimas_transacoes) == 2 and r.granularidade == "dia"
    assert sum(p.receitas for p in r.serie_fluxo) == D("1116.00")


def test_fr002_caixa_positivo_e_zero_nao_alertam():
    p = produto(qtd=1, custo="1.00", venda="5.00")
    registrar_movimentacao(produto_id=p.pk, tipo="SAIDA", quantidade=1)
    r = resumo_financeiro(resolver_periodo("tudo"))
    assert r.saldo_caixa == D("4.00") and not r.caixa_negativo


def test_fr003_sem_dados():
    r = resumo_financeiro(resolver_periodo("tudo"))
    assert (r.valor_estoque, r.receitas, r.saldo_caixa) == (0, 0, 0)
    assert r.serie_fluxo == [] and r.margem_realizada_percentual is None
    assert not r.caixa_negativo


def test_fr004_pagina_mostra_kpis_e_alerta(client):
    produto()
    html = client.get("/financeiro/").content.decode()
    for texto in (
        "Valor total do estoque",
        "Faturamento",
        "Lucro bruto realizado",
        "Saldo do caixa",
        "CAIXA NEGATIVO",
        "R$ 1.890,00",
        "Fluxo de caixa",
    ):
        assert texto in html, texto  # fmt: skip


def test_fr005_periodo_por_htmx_e_invalido(client):
    produto()
    parcial = client.get("/financeiro/?periodo=7d", HTTP_HX_REQUEST="true",
                         HTTP_HX_TARGET="painel-financeiro").content.decode()  # fmt: skip
    assert parcial.startswith('<section id="painel-financeiro"')
    assert 'aria-current="true">Últimos 7 dias' in parcial
    invalido = client.get("/financeiro/?periodo=personalizado&de=2026-10-09&ate=2026-10-01")
    assert "A data inicial deve ser anterior" in invalido.content.decode()
    assert (
        client.get("/financeiro/?periodo=personalizado&de=2020-01-01&ate=2026-12-31").status_code
        == 200
    )


def test_fr006_painel_principal_tem_faixa_financeira(client):
    produto()
    html = client.get("/").content.decode()
    assert 'id="painel-financeiro-resumo"' in html and "CAIXA NEGATIVO" in html


def test_fr007_comando_resumo_financeiro(capsys):
    produto()
    call_command("resumo_financeiro")
    assert "Saldo do caixa: −R$ 1.890,00" in capsys.readouterr().out
    call_command("resumo_financeiro", "--formato", "json", "--periodo", "mes")
    dados = json.loads(capsys.readouterr().out)
    assert dados["despesas"] == "1890.00" and dados["caixa_negativo"] is True
    with pytest.raises(SystemExit) as saida:
        call_command("resumo_financeiro", "--falhar-se-negativo")
    assert saida.value.code == 1
    with pytest.raises(SystemExit) as saida:
        call_command("resumo_financeiro", "--periodo", "personalizado", "--de", "x")
    assert saida.value.code == 2


def test_fr008_demo_tem_os_dois_estados():
    call_command("popular_demo")
    tudo = resumo_financeiro(resolver_periodo("tudo"))
    assert (tudo.despesas, tudo.receitas, tudo.saldo_caixa) == (
        D("7206.40"), D("3488.40"), D("-3718.00"))  # fmt: skip
    assert tudo.caixa_negativo
    semana = resumo_financeiro(resolver_periodo("7d"))
    assert semana.saldo_caixa > 0
