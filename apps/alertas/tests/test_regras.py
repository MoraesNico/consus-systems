"""Regra de alerta em Python puro (FR-001–FR-005, FR-019; data-model §3)."""

import pytest

from apps.alertas.regras import (
    Situacao,
    Transicao,
    classificar,
    cobertura_percentual,
    deficit,
    sugestao_reposicao,
    transicao,
)
from apps.produtos.models import QUANTIDADE_MAXIMA

TABELA_VERDADE = [
    # atual, mínimo, situação, déficit, cobertura, sugestão
    (5, 10, Situacao.REPOSICAO_NECESSARIA, 5, 50, 15),
    (9, 10, Situacao.REPOSICAO_NECESSARIA, 1, 90, 11),
    (10, 10, Situacao.REPOSICAO_NECESSARIA, 0, 100, 10),
    (11, 10, Situacao.OK, 0, 110, None),
    (0, 8, Situacao.SEM_ESTOQUE, 8, 0, 16),
    (0, 0, Situacao.SEM_ESTOQUE, 0, 0, 1),
    (3, 0, Situacao.OK, 0, None, None),
    (999, 1000, Situacao.REPOSICAO_NECESSARIA, 1, 99, 1001),
    (QUANTIDADE_MAXIMA, QUANTIDADE_MAXIMA, Situacao.REPOSICAO_NECESSARIA, 0, 100, 0),
]


@pytest.mark.parametrize(("atual", "minimo", "situacao", "falta", "cobertura", "sugestao"),
                         TABELA_VERDADE)  # fmt: skip
def test_fr002_fr005_tabela_verdade(atual, minimo, situacao, falta, cobertura, sugestao):
    """FR-002–FR-005: situação, déficit, cobertura e sugestão conforme a tabela-verdade."""
    assert classificar(atual, minimo) is situacao
    assert deficit(atual, minimo) == falta
    assert cobertura_percentual(atual, minimo) == cobertura
    assert sugestao_reposicao(atual, minimo) == sugestao


def test_fr002_limite_exato_igual_ao_minimo_e_mais_um():
    """FR-002: quantidade = mínimo → alerta; mínimo + 1 → sem alerta (item 3 da atividade)."""
    assert classificar(10, 10) is Situacao.REPOSICAO_NECESSARIA
    assert classificar(11, 10) is Situacao.OK


def test_fr003_sem_estoque_e_forma_mais_grave():
    """FR-003: zero é sempre SEM ESTOQUE, inclusive com mínimo 0."""
    assert classificar(0, 0) is Situacao.SEM_ESTOQUE
    assert Situacao.SEM_ESTOQUE.gravidade > Situacao.REPOSICAO_NECESSARIA.gravidade > 0
    assert Situacao.SEM_ESTOQUE.rotulo == "SEM ESTOQUE"
    assert Situacao.REPOSICAO_NECESSARIA.rotulo == "REPOSIÇÃO NECESSÁRIA"
    assert [s.variante for s in Situacao] == ["ok", "reposicao", "sem_estoque"]


def test_fr005_sugestao_sempre_tira_do_alerta():
    """FR-005/SC-008: atual + sugestão sai do alerta (mínimo abaixo da metade do teto)."""
    for minimo in (0, 1, 2, 7, 10, 100, 1_000_000, 1_073_741_823):
        for atual in {0, min(1, minimo), minimo // 2, minimo}:
            sugestao = sugestao_reposicao(atual, minimo)
            assert sugestao is not None and sugestao >= 1
            assert classificar(atual + sugestao, minimo) is Situacao.OK


@pytest.mark.parametrize(
    ("anterior", "posterior", "minimo", "esperado"),
    [(11, 10, 10, Transicao.PIOROU), (11, 0, 10, Transicao.PIOROU),
     (5, 0, 10, Transicao.PIOROU), (5, 11, 10, Transicao.SAIU_DO_ALERTA),
     (0, 11, 10, Transicao.SAIU_DO_ALERTA), (0, 3, 10, Transicao.NENHUMA),
     (5, 4, 10, Transicao.NENHUMA), (20, 15, 10, Transicao.NENHUMA)],
)  # fmt: skip
def test_fr019_transicoes(anterior, posterior, minimo, esperado):
    """FR-019: compara as gravidades antes e depois da movimentação."""
    assert transicao(anterior, posterior, minimo) is esperado
