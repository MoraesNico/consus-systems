"""008 — Registro de transações financeiras (Passo 3, item 2)."""

import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.core.periodos import PeriodoInvalidoError, resolver_periodo
from apps.financeiro.models import Transacao, TransacaoImutavelError
from apps.movimentacoes.services import (
    EstoqueInsuficienteError,
    MovimentacaoInvalidaError,
    registrar_movimentacao,
)
from apps.produtos.services import cadastrar_produto, editar_produto

pytestmark = pytest.mark.django_db
D = Decimal


@pytest.fixture
def produto():
    return cadastrar_produto(nome="Toner", quantidade_inicial=10, estoque_minimo=1,
                             preco_custo=D("189.00"), preco_venda=D("279.00"))  # fmt: skip


def test_fr001_saldo_inicial_vira_despesa_a_custo(produto):
    t = Transacao.objects.get()
    assert (t.tipo, t.quantidade, t.preco_unitario, t.valor_total) == (
        "ENTRADA", 10, D("189.00"), D("1890.00"))  # fmt: skip
    assert t.natureza == "Despesa" and t.valor_assinado == D("-1890.00") and t.lucro_bruto is None


def test_fr002_entrada_registra_despesa(produto):
    mov = registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=3)
    assert mov.transacao.valor_total == D("567.00")
    assert mov.transacao.criado_em == mov.criado_em


def test_fr003_saida_registra_receita_com_cpv_congelado(produto):
    mov = registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=2)
    t = mov.transacao
    assert (t.tipo, t.valor_total, t.custo_total, t.lucro_bruto) == (
        "SAIDA", D("558.00"), D("378.00"), D("180.00"))  # fmt: skip
    editar_produto(produto_id=produto.pk, nome="Toner", estoque_minimo=1,
                   preco_custo=D("1.00"), preco_venda=D("2.00"))  # fmt: skip
    t.refresh_from_db()
    assert t.valor_total == D("558.00")


def test_fr004_inicial_zero_nao_gera_transacao():
    cadastrar_produto(nome="Vazio", quantidade_inicial=0, estoque_minimo=1,
                      preco_custo=D("1"), preco_venda=D("2"))  # fmt: skip
    assert not Transacao.objects.exists()


def test_fr005_saida_recusada_nao_gera_transacao(produto):
    with pytest.raises(EstoqueInsuficienteError):
        registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=99)
    assert Transacao.objects.count() == 1


def test_fr006_transacao_imutavel(produto):
    t = Transacao.objects.get()
    with pytest.raises(TransacaoImutavelError):
        t.save()
    with pytest.raises(TransacaoImutavelError):
        t.delete()
    with pytest.raises(TransacaoImutavelError):
        Transacao.objects.update(quantidade=1)
    with pytest.raises(TransacaoImutavelError):
        Transacao.objects.all().delete()


def test_fr007_totais(produto):
    registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=4)
    totais = Transacao.objects.totais()
    assert (totais.receitas, totais.despesas, totais.custo_vendido) == (
        D("1116.00"), D("1890.00"), D("756.00"))  # fmt: skip
    assert totais.saldo == D("-774.00") and totais.lucro_bruto == D("360.00")
    assert (totais.quantidade_vendida, totais.quantidade_transacoes) == (4, 2)


def test_fr008_momento_respeita_ordem_do_livro_razao(produto):
    passado = timezone.now() - datetime.timedelta(days=3)
    with pytest.raises(MovimentacaoInvalidaError):
        registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1, momento=passado)
    futuro = timezone.now() + datetime.timedelta(days=1)
    with pytest.raises(MovimentacaoInvalidaError):
        registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1, momento=futuro)


def test_fr009_historico_lista_filtra_e_exporta(client, produto):
    registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1)
    html = client.get("/financeiro/transacoes/").content.decode()
    assert "Histórico de transações" in html and "+R$ 279,00" in html and "−R$ 1.890,00" in html
    so_receitas = client.get("/financeiro/transacoes/?tipo=SAIDA").content.decode()
    assert "−R$ 1.890,00" not in so_receitas
    parcial = client.get("/financeiro/transacoes/?tipo=ENTRADA", HTTP_HX_REQUEST="true",
                         HTTP_HX_TARGET="resultados")  # fmt: skip
    assert parcial.content.decode().startswith('<div id="resultados"')
    csv = client.get("/financeiro/transacoes/?formato=csv")
    assert csv["Content-Disposition"].startswith('attachment; filename="transacoes-')
    texto = csv.content.decode("utf-8-sig")
    assert texto.splitlines()[0].startswith("Data/hora;ID do produto;Produto;Tipo")
    assert ";279,00;279,00;189,00" in texto


def test_fr010_livro_razao_mostra_valor(client, produto):
    html = client.get("/movimentacoes/").content.decode()
    assert "Valor" in html and "−R$ 1.890,00" in html


def test_fr011_vazio_e_filtro_sem_resultado(client):
    assert "Nenhuma transação ainda" in client.get("/financeiro/transacoes/").content.decode()
    filtrado = client.get("/financeiro/transacoes/?tipo=SAIDA").content.decode()
    assert "Nenhuma transação encontrada." in filtrado


def test_periodos():
    hoje = datetime.date(2026, 10, 27)
    assert resolver_periodo("7d", hoje=hoje).de == datetime.date(2026, 10, 21)
    assert resolver_periodo("30d", hoje=hoje).dias == 30
    assert resolver_periodo("mes", hoje=hoje).de == datetime.date(2026, 10, 1)
    assert resolver_periodo("hoje", hoje=hoje).ate == hoje
    assert resolver_periodo("xyz", hoje=hoje).chave == "tudo"
    assert resolver_periodo(None).dias is None
    p = resolver_periodo("personalizado", "2026-10-01", "2026-10-05", hoje=hoje)
    assert (p.dias, p.rotulo) == (5, "Personalizado")
    for de, ate in [("2026-10-05", "2026-10-01"), ("", "2026-10-01"), ("31/02", "2026-10-01")]:
        with pytest.raises(PeriodoInvalidoError):
            resolver_periodo("personalizado", de, ate, hoje=hoje)
