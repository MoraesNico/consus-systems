"""Busca, filtro, ordenação e obtenção de produtos (FR-013, FR-015, FR-016, FR-023)."""

import pytest

from apps.produtos.models import Produto
from apps.produtos.selectors import (
    listar_produtos,
    normalizar_ordem,
    normalizar_situacao,
    obter_produto,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogo(produto_factory):
    """Produtos com IDs conhecidos: o 12º é "Caneta Azul" e existe "Bucha 12 mm"."""
    produtos = [produto_factory(nome=f"Item {i:02d}") for i in range(1, 12)]
    caneta = produto_factory(nome="Caneta Azul", quantidade_inicial=3, estoque_minimo=5)
    bucha = produto_factory(nome="Bucha 12 mm", quantidade_inicial=50, estoque_minimo=5)
    especial = produto_factory(nome="Desconto 50% a_b d'água", quantidade_inicial=0)
    assert caneta.pk == produtos[0].pk + 11
    return {"caneta": caneta, "bucha": bucha, "especial": especial}


def ids(qs) -> set[int]:
    return {p.pk for p in qs}


@pytest.mark.parametrize("formato", ["#{}", "#{:04d}", "# {}"])
def test_fr013_hash_busca_somente_id(catalogo, formato):
    """FR-013: "#12", "#0012" e "# 12" encontram só o ID, mesmo havendo "Bucha 12 mm"."""
    caneta = catalogo["caneta"]
    assert ids(listar_produtos(q=formato.format(caneta.pk))) == {caneta.pk}


def test_fr013_numero_puro_id_ou_nome(catalogo, produto_factory):
    """FR-013: número sem # busca o ID e também nomes que contenham o número."""
    caneta, bucha = catalogo["caneta"], catalogo["bucha"]
    resultado = ids(listar_produtos(q=str(caneta.pk)))
    assert caneta.pk in resultado
    if str(caneta.pk) in bucha.nome:
        assert bucha.pk in resultado
    assert bucha.pk in ids(listar_produtos(q="12"))


def test_fr013_nome_parcial_sem_diferenciar_maiusculas(catalogo):
    """FR-013: parte do nome, sem diferenciar maiúsculas."""
    assert ids(listar_produtos(q="cAnEtA")) == {catalogo["caneta"].pk}


@pytest.mark.parametrize("termo", ["50%", "a_b", "d'água", "#abc"])
def test_fr013_caracteres_especiais_literais(catalogo, termo):
    """FR-013: %, _, aspas e "#abc" são tratados literalmente."""
    esperado = {catalogo["especial"].pk} if termo != "#abc" else set()
    assert ids(listar_produtos(q=termo)) == esperado


@pytest.mark.parametrize("termo", ["9" * 25, "#" + "9" * 25])
def test_fr013_numero_gigante_sem_erro(catalogo, termo):
    """FR-013: números maiores que o BigAutoField não geram erro."""
    assert list(listar_produtos(q=termo)) == []


def test_fr013_hash_zero_sem_resultado(catalogo):
    """FR-013: "#0" não corresponde a nenhum produto."""
    assert list(listar_produtos(q="#0")) == []


@pytest.mark.parametrize("termo", ["", "   ", None])
def test_fr013_termo_vazio_ou_espacos_sem_filtro(catalogo, termo):
    """FR-013: busca vazia não filtra."""
    assert listar_produtos(q=termo).count() == Produto.objects.count()


def test_fr015_filtro_situacao(produto_factory):
    """FR-015: filtro por situação; valor inválido = todos."""
    alerta = produto_factory(quantidade_inicial=5, estoque_minimo=5)
    ok = produto_factory(quantidade_inicial=6, estoque_minimo=5)
    assert ids(listar_produtos(situacao="alerta")) == {alerta.pk}
    assert ids(listar_produtos(situacao="ok")) == {ok.pk}
    assert ids(listar_produtos(situacao="qualquer")) == {alerta.pk, ok.pk}
    assert normalizar_situacao("qualquer") == "" and normalizar_situacao("ok") == "ok"


def test_fr016_ordenacoes_validas_e_desempate(produto_factory):
    """FR-016: cada chave asc/desc; nome sem diferenciar maiúsculas; desempate -id."""
    b = produto_factory(nome="banana", quantidade_inicial=1, estoque_minimo=5)
    a = produto_factory(nome="Abacate", quantidade_inicial=9, estoque_minimo=1)
    c = produto_factory(nome="cereja", quantidade_inicial=9, estoque_minimo=9)
    ordem = lambda chave: [p.pk for p in listar_produtos(ordem=chave)]  # noqa: E731
    assert ordem("nome") == [a.pk, b.pk, c.pk]
    assert ordem("-nome") == [c.pk, b.pk, a.pk]
    assert ordem("id") == [b.pk, a.pk, c.pk]
    assert ordem("-id") == [c.pk, a.pk, b.pk]
    assert ordem("quantidade") == [b.pk, c.pk, a.pk]  # empate 9/9 → -id
    assert ordem("-quantidade") == [c.pk, a.pk, b.pk]
    assert ordem("minimo") == [a.pk, b.pk, c.pk]
    assert ordem("-minimo") == [c.pk, b.pk, a.pk]
    assert ordem("situacao")[:2] == [c.pk, b.pk]  # em alerta primeiro, desempate -id
    assert ordem("-situacao")[0] == a.pk


@pytest.mark.parametrize("ordem", [None, "", "preco", "--nome", "-"])
def test_fr016_ordem_invalida_usa_padrao(ordem):
    """FR-016: ordem fora da lista branca → padrão -id."""
    assert normalizar_ordem(ordem) == "-id"


def test_fr023_obter_produto_inexistente_does_not_exist():
    """FR-023: ID inexistente → DoesNotExist."""
    with pytest.raises(Produto.DoesNotExist):
        obter_produto(123)


def test_fr023_obter_produto_id_gigante_does_not_exist(django_assert_num_queries):
    """FR-023: ID acima do BigAutoField → DoesNotExist sem consultar o banco."""
    with django_assert_num_queries(0), pytest.raises(Produto.DoesNotExist):
        obter_produto(10**25)
