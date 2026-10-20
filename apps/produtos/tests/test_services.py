"""Serviços de escrita: cadastro e edição (FR-001, 004–008, 023–025, 027, 029, 030)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.produtos import services
from apps.produtos.models import QUANTIDADE_MAXIMA, Produto
from apps.produtos.services import cadastrar_produto, editar_produto, normalizar_nome

pytestmark = pytest.mark.django_db


def cadastrar(nome="Caneta Azul", quantidade_inicial=10, estoque_minimo=5):
    return cadastrar_produto(
        nome=nome, quantidade_inicial=quantidade_inicial, estoque_minimo=estoque_minimo
    )


def codigos(erro: ValidationError, campo: str) -> list[str]:
    return [e.code for e in erro.error_dict[campo]]


def mensagens(erro: ValidationError, campo: str) -> list[str]:
    return [m for e in erro.error_dict[campo] for m in e.messages]


# ---------- Cadastro ----------


def test_fr001_cadastrar_produto_com_tres_campos():
    """FR-001: nome, quantidade inicial e estoque mínimo bastam para cadastrar."""
    produto = cadastrar("Caneta Azul", 10, 5)
    assert Produto.objects.get(pk=produto.pk).nome == "Caneta Azul"
    assert produto.estoque_minimo == 5


def test_fr002_ids_consecutivos_via_servico():
    """FR-002: cada cadastro recebe um ID maior que o anterior."""
    a, b = cadastrar("A"), cadastrar("B")
    assert b.pk > a.pk


def test_fr008_quantidade_atual_igual_inicial():
    """FR-008: o saldo nasce igual à quantidade inicial."""
    assert cadastrar(quantidade_inicial=37).quantidade_atual == 37


def test_fr004_nome_aparado_e_espacos_colapsados():
    """FR-004: extremidades aparadas e espaços internos colapsados."""
    assert normalizar_nome("  Caneta   Azul ") == "Caneta Azul"
    assert cadastrar("  Caneta   Azul ").nome == "Caneta Azul"


@pytest.mark.parametrize("nome", ["", "   ", "\t  "])
def test_fr004_nome_vazio_ou_so_espacos_recusado(nome):
    """FR-004: nome vazio ou só espaços → nome_obrigatorio."""
    with pytest.raises(ValidationError) as erro:
        cadastrar(nome)
    assert codigos(erro.value, "nome") == ["nome_obrigatorio"]
    assert mensagens(erro.value, "nome") == ["Informe o nome do produto."]


def test_fr004_limite_120_apos_normalizacao():
    """FR-004: 120 caracteres aceitos; 121 recusados; contagem após normalizar."""
    assert len(cadastrar("x" * 120).nome) == 120
    with pytest.raises(ValidationError) as erro:
        cadastrar("y" * 121)
    assert codigos(erro.value, "nome") == ["nome_longo"]
    assert cadastrar("z" * 60 + "  " + "z" * 59).nome == "z" * 60 + " " + "z" * 59


def test_fr005_nome_duplicado_ignora_maiusculas():
    """FR-005: duplicidade sem diferenciar maiúsculas, citando o código existente."""
    existente = cadastrar("Caneta Azul")
    with pytest.raises(ValidationError) as erro:
        cadastrar("CANETA azul")
    assert mensagens(erro.value, "nome") == [
        f"Já existe um produto com este nome ({existente.codigo})."
    ]


def test_fr005_acentos_significativos():
    """FR-005: "Café" e "Cafe" são nomes diferentes."""
    cadastrar("Café")
    cadastrar("Cafe")
    assert Produto.objects.count() == 2


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Lower() Unicode só no PostgreSQL")
def test_fr005_acentuadas_maiusculas_duplicadas_postgres():
    """FR-005: "ÁGUA" e "água" são o mesmo nome (PostgreSQL)."""
    cadastrar("ÁGUA")
    with pytest.raises(ValidationError):
        cadastrar("água")


def test_fr005_corrida_integrity_error_vira_validation_error(monkeypatch):
    """FR-005: se dois cadastros correm, o IntegrityError vira ValidationError nome_duplicado."""
    cadastrar("Caneta")
    monkeypatch.setattr(services, "_nome_em_uso", lambda nome, excluir_pk=None: False)
    with pytest.raises(ValidationError) as erro:
        cadastrar("caneta")
    assert codigos(erro.value, "nome") == ["nome_duplicado"]


@pytest.mark.parametrize("valor", [0, QUANTIDADE_MAXIMA])
def test_fr006_faixa_aceita(valor):
    """FR-006: 0 e o máximo são aceitos."""
    assert cadastrar(f"P{valor}", valor, valor).quantidade_atual == valor


@pytest.mark.parametrize(
    ("valor", "codigo"),
    [(-1, "inteiro_invalido"), (QUANTIDADE_MAXIMA + 1, "inteiro_maximo"),
     (2.5, "inteiro_invalido"), (True, "inteiro_invalido"), ("3", "inteiro_invalido")],
)  # fmt: skip
def test_fr006_faixa_e_tipo_recusados(valor, codigo):
    """FR-006: negativos, acima do máximo, não inteiros e bool são recusados."""
    with pytest.raises(ValidationError) as erro:
        cadastrar("Produto", valor, 0)
    assert codigos(erro.value, "quantidade_inicial") == [codigo]
    with pytest.raises(ValidationError) as erro:
        cadastrar("Produto", 0, valor)
    assert codigos(erro.value, "estoque_minimo") == [codigo]


def test_fr029_somente_argumentos_nomeados():
    """FR-029: o serviço só aceita argumentos nomeados."""
    with pytest.raises(TypeError):
        cadastrar_produto("Caneta", 1, 1)


def test_fr029_atomico_nada_gravado_em_erro():
    """FR-029: em caso de erro nada é gravado."""
    with pytest.raises(ValidationError):
        cadastrar("", -1, -1)
    assert Produto.objects.count() == 0


def test_fr030_poscondicoes_invariantes():
    """FR-030: pós-condições que a extensão da 003 deve preservar."""
    anterior = cadastrar("Anterior")
    produto = cadastrar("  Novo   Produto ", 12, 3)
    persistido = Produto.objects.get(pk=produto.pk)
    assert persistido.pk > anterior.pk
    assert persistido.quantidade_atual == 12
    assert persistido.nome == normalizar_nome("  Novo   Produto ")
    assert persistido.estoque_minimo == 3


# ---------- Edição ----------


def test_fr024_editar_nome_e_estoque_minimo():
    """FR-024: edição altera nome e estoque mínimo."""
    produto = cadastrar("Caneta", 10, 5)
    editado = editar_produto(produto_id=produto.pk, nome=" Caneta  Preta ", estoque_minimo=8)
    assert (editado.nome, editado.estoque_minimo) == ("Caneta Preta", 8)
    assert Produto.objects.get(pk=produto.pk).estoque_minimo == 8


def test_fr024_unicidade_desconsidera_o_proprio():
    """FR-024: mudar só maiúsculas do próprio nome é permitido."""
    produto = cadastrar("Caneta")
    assert editar_produto(produto_id=produto.pk, nome="CANETA", estoque_minimo=5).nome == "CANETA"


def test_fr024_nome_de_outro_produto_recusado():
    """FR-024: não pode assumir o nome de outro produto."""
    outro = cadastrar("Lápis")
    produto = cadastrar("Caneta")
    with pytest.raises(ValidationError) as erro:
        editar_produto(produto_id=produto.pk, nome="lápis", estoque_minimo=5)
    assert mensagens(erro.value, "nome") == [
        f"Já existe um produto com este nome ({outro.codigo})."
    ]


@pytest.mark.parametrize(
    ("nome", "minimo", "campo"),
    [("", 5, "nome"), ("x" * 121, 5, "nome"), ("Ok", -1, "estoque_minimo"),
     ("Ok", QUANTIDADE_MAXIMA + 1, "estoque_minimo")],
)  # fmt: skip
def test_fr024_mesmas_validacoes_do_cadastro(nome, minimo, campo):
    """FR-024: edição aplica as mesmas validações do cadastro."""
    produto = cadastrar("Caneta")
    with pytest.raises(ValidationError) as erro:
        editar_produto(produto_id=produto.pk, nome=nome, estoque_minimo=minimo)
    assert campo in erro.value.error_dict


def test_fr025_editar_nunca_grava_quantidade_atual():
    """FR-025: o UPDATE da edição não toca em quantidade_atual."""
    produto = cadastrar("Caneta", 10, 5)
    with CaptureQueriesContext(connection) as consultas:
        editar_produto(produto_id=produto.pk, nome="Caneta", estoque_minimo=6)
    updates = [q["sql"] for q in consultas.captured_queries if q["sql"].startswith("UPDATE")]
    assert updates and all("quantidade_atual" not in sql for sql in updates)


def test_fr027_atualizado_em_avanca():
    """FR-027: a edição atualiza atualizado_em."""
    produto = cadastrar("Caneta")
    antes = produto.atualizado_em
    editado = editar_produto(produto_id=produto.pk, nome="Caneta", estoque_minimo=9)
    assert editado.atualizado_em > antes


def test_fr023_editar_produto_inexistente():
    """FR-023: editar um ID inexistente lança DoesNotExist."""
    with pytest.raises(Produto.DoesNotExist):
        editar_produto(produto_id=999, nome="X", estoque_minimo=1)
