"""007 — Preços de custo e venda e margem automática (Passo 3, item 1)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.produtos.models import Produto
from apps.produtos.services import cadastrar_produto, editar_produto

pytestmark = pytest.mark.django_db
D = Decimal


def novo(custo="10.00", venda="15.00", **extra):
    dados = {"nome": "Caneta", "quantidade_inicial": 4, "estoque_minimo": 1} | extra
    return cadastrar_produto(preco_custo=D(custo), preco_venda=D(venda), **dados)


def test_fr001_cadastro_grava_precos_e_calcula_margem():
    produto = novo()
    produto.refresh_from_db()
    assert (produto.preco_custo, produto.preco_venda) == (D("10.00"), D("15.00"))
    assert produto.margem_prevista == D("5.00")
    assert produto.margem_percentual == D("33.3")
    assert produto.valor_em_estoque == D("40.00")
    assert produto.variante_margem == "positiva"


@pytest.mark.parametrize(
    ("custo", "venda", "campo"),
    [("0", "1", "preco_custo"), ("1", "0", "preco_venda"), ("-1", "1", "preco_custo"),
     ("1000000", "1", "preco_custo"), ("1.001", "2", "preco_custo")],
)  # fmt: skip
def test_fr002_precos_obrigatorios_e_limitados(custo, venda, campo):
    with pytest.raises(ValidationError) as erro:
        novo(custo, venda)
    assert campo in erro.value.error_dict
    assert Produto.objects.count() == 0


def test_fr003_margem_negativa_permitida_e_sinalizada():
    produto = novo("7.20", "6.90")
    assert produto.margem_prevista == D("-0.30")
    assert produto.variante_margem == "negativa"


def test_fr004_edicao_exige_e_altera_precos():
    produto = novo()
    editado = editar_produto(produto_id=produto.pk, nome="Caneta", estoque_minimo=1,
                             preco_custo=D("11.00"), preco_venda=D("11.00"))  # fmt: skip
    assert editado.variante_margem == "zero"
    with pytest.raises(ValidationError):
        editar_produto(produto_id=produto.pk, nome="Caneta", estoque_minimo=1,
                       preco_custo=None, preco_venda=D("1"))  # fmt: skip


def test_fr005_produto_antigo_fica_com_preco_pendente():
    produto = novo()
    Produto.objects.filter(pk=produto.pk).update(preco_custo=0, preco_venda=0)
    produto.refresh_from_db()
    assert produto.precos_pendentes and produto.variante_margem == "pendente"
    assert produto.margem_percentual is None


def test_fr006_queryset_com_financeiro_anota_margem_e_valor():
    novo()
    anotado = Produto.objects.com_financeiro().get()
    assert (anotado.margem, anotado.valor_estoque) == (D("5.00"), D("40.00"))


def test_fr007_lista_mostra_colunas_e_ordena_por_margem(client):
    novo()
    novo("1.00", "9.00", nome="Lápis")
    html = client.get("/produtos/?ordem=-margem").content.decode()
    assert "Custo" in html and "Margem" in html and "R$ 15,00" in html
    assert html.index("Lápis") < html.index("Caneta")


def test_fr008_previa_margem(client):
    html = client.get("/produtos/previa-margem/?preco_custo=10&preco_venda=8,50").content.decode()
    assert "−R$ 1,50" in html and "prejuízo de R$ 1,50" in html
    vazio = client.get("/produtos/previa-margem/?preco_custo=abc").content.decode()
    assert "Informe custo e venda" in vazio


def test_fr009_cadastro_pela_tela_com_precos_brasileiros(client):
    dados = {"nome": "Toner", "quantidade_inicial": "2", "estoque_minimo": "1",
             "preco_custo": "1.189,00", "preco_venda": "R$ 1.279,90"}  # fmt: skip
    assert client.post("/produtos/novo/", dados).status_code == 302
    produto = Produto.objects.get(nome="Toner")
    assert produto.preco_venda == D("1279.90")
    detalhe = client.get(produto.get_absolute_url()).content.decode()
    assert "Preços e margem" in detalhe and "R$ 2.378,00" in detalhe


def test_fr010_cadastro_sem_precos_mostra_erros(client):
    dados = {"nome": "Toner", "quantidade_inicial": "2", "estoque_minimo": "1"}
    resposta = client.post("/produtos/novo/", dados)
    assert resposta.status_code == 422
    assert "Informe o preço de custo." in resposta.content.decode()
