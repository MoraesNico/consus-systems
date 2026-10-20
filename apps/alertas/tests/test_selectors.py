"""Varredura, equivalência SQL × Python e resumo do painel (FR-001–FR-010, FR-022–FR-025)."""

import datetime

import pytest

from apps.alertas import regras
from apps.alertas.selectors import produtos_por_criticidade, resumo_painel, total_em_alerta, varrer
from apps.movimentacoes.models import Movimentacao
from apps.produtos.models import QUANTIDADE_MAXIMA, Produto

pytestmark = pytest.mark.django_db


def test_equivalencia_sql_e_python(criar_produto):
    """I-2: anotações do banco == funções de regras.py produto a produto (grade 0…6 × 0…6)."""
    for quantidade in range(7):
        for minimo in range(7):
            criar_produto(f"G {quantidade}/{minimo}", quantidade, minimo)
    criar_produto("Extremo", QUANTIDADE_MAXIMA, QUANTIDADE_MAXIMA)
    for p in produtos_por_criticidade(incluir_ok=True):
        q, m = p.quantidade_atual, p.estoque_minimo
        situacao = regras.classificar(q, m)
        assert p.alerta == (situacao is not regras.Situacao.OK)
        assert p.deficit == regras.deficit(q, m)
        assert p.cobertura_percentual == regras.cobertura_percentual(q, m)
        assert p.gravidade == situacao.gravidade
        assert p.sugestao_reposicao == regras.sugestao_reposicao(q, m)


def test_fr006_ordem_de_criticidade_e_determinismo(cenario):
    """FR-006: sem estoque primeiro (maior déficit antes), depois maior déficit; empate por ID."""
    ordem = [p.pk for p in varrer().itens]
    esperado = [cenario[k].pk for k in ("E", "D", "A", "B")]
    assert ordem == esperado
    assert [p.pk for p in varrer().itens] == ordem


def test_fr006_empate_resolvido_pelo_menor_id(criar_produto):
    """FR-006: mesmos valores → menor ID primeiro."""
    a = criar_produto("Primeiro", 2, 5)
    b = criar_produto("Segundo", 2, 5)
    assert [p.pk for p in varrer().itens] == [a.pk, b.pk]


def test_fr008_resultado_da_varredura(cenario, agora):
    """FR-008: totais coerentes com os itens; executada_em = agora; itens anotados."""
    resultado = varrer()
    assert resultado.executada_em == agora
    assert (resultado.total_analisado, resultado.total_em_alerta, resultado.total_sem_estoque) == (
        5, 4, 2)  # fmt: skip
    assert resultado.total_em_alerta == Produto.objects.em_alerta().count()
    assert all(isinstance(p.situacao_estoque, regras.Situacao) for p in resultado.itens)
    assert cenario["C"].pk not in {p.pk for p in resultado.itens}


def test_fr030_incluir_ok_no_fim(cenario):
    """FR-030: --todos acrescenta os OK depois dos em alerta."""
    itens = varrer(incluir_ok=True).itens
    assert itens[-1].pk == cenario["C"].pk and len(itens) == 5


def test_fr010_estados_vazios(criar_produto):
    """FR-010: base vazia e base sem alertas."""
    assert varrer().sem_produtos
    criar_produto("Ok", 20, 1)
    resultado = varrer()
    assert not resultado.sem_produtos and resultado.sem_alertas


def test_fr031_varredura_nao_grava(cenario, django_assert_max_num_queries):
    """FR-031/FR-037: a varredura só lê (2 consultas) e não altera saldos."""
    antes = (Produto.objects.count(), Movimentacao.objects.count())
    with django_assert_max_num_queries(2):
        varrer()
    assert (Produto.objects.count(), Movimentacao.objects.count()) == antes
    assert total_em_alerta() == 4


def test_fr022_fr025_resumo_do_painel(criar_produto, movimentar, agora, monkeypatch):
    """FR-022–FR-025: KPIs, críticos, cobertura e últimas movimentações."""
    produtos = [criar_produto(f"Item {i:02d}", 100, 10) for i in range(8)]
    criar_produto("Zerado", 0, 5)
    criar_produto("Baixo", 4, 10)
    criar_produto("Limite", 10, 10)
    criar_produto("Sem mínimo", 50, 0)
    for _ in range(4):
        movimentar(produtos[0], "SAIDA", 1)
    for _ in range(3):
        movimentar(produtos[1], "ENTRADA", 2)
    resumo = resumo_painel()
    assert resumo.total_produtos == 12
    assert resumo.total_unidades == 100 * 8 - 4 + 6 + 0 + 4 + 10 + 50
    assert (resumo.total_em_alerta, resumo.total_sem_estoque) == (3, 1)
    assert resumo.movimentacoes_24h == 7
    assert [p.nome for p in resumo.criticos] == ["Zerado", "Baixo", "Limite"]
    assert len(resumo.cobertura) == 8
    assert resumo.cobertura[0].nome == "Zerado"
    assert "Sem mínimo" not in [p.nome for p in resumo.cobertura]
    assert len(resumo.ultimas_movimentacoes) == 5
    depois = resumo_painel(agora=agora + datetime.timedelta(hours=24, minutes=1))
    assert depois.movimentacoes_24h == 0


def test_fr022_painel_base_vazia(db):
    """FR-022: base vazia → zeros e listas vazias."""
    resumo = resumo_painel()
    assert (resumo.total_produtos, resumo.total_unidades, resumo.total_em_alerta) == (0, 0, 0)
    assert resumo.criticos == () and resumo.cobertura == () and resumo.ultimas_movimentacoes == ()
