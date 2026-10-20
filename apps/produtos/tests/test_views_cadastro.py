"""Cadastro pela interface: página, diálogo HTMX, 422 e eventos (FR-005–FR-011, FR-031)."""

import json
import re

import pytest

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db

VALIDO = {"nome": "Caneta Azul", "quantidade_inicial": "10", "estoque_minimo": "5"}


def html(resposta) -> str:
    return resposta.content.decode()


def campo(conteudo: str, nome: str) -> str:
    return re.search(rf'<input[^>]+name="{nome}"[^>]*>', conteudo).group(0)


@pytest.mark.parametrize("boost", [False, True])
def test_fr009_get_novo_pagina_completa_comum_e_boosted(client, hx_boosted, boost):
    """FR-009: GET /produtos/novo/ devolve a página completa, campos numéricos vazios."""
    resposta = client.get("/produtos/novo/", **(hx_boosted if boost else {}))
    conteudo = html(resposta)
    assert resposta.status_code == 200
    assert "produtos/novo.html" in [t.name for t in resposta.templates]
    assert "<html" in conteudo
    assert "value=" not in campo(conteudo, "quantidade_inicial")
    assert "value=" not in campo(conteudo, "estoque_minimo")


def test_fr009_get_novo_dialogo_parcial(client, hx_parcial):
    """FR-009: com HX-Target dialogo devolve só o fragmento do diálogo com foco no nome."""
    resposta = client.get("/produtos/novo/", **hx_parcial("dialogo"))
    conteudo = html(resposta)
    assert "produtos/partials/dialogo_novo.html" in [t.name for t in resposta.templates]
    assert "<html" not in conteudo
    assert "autofocus" in campo(conteudo, "nome")
    assert 'id="dialogo-titulo"' in conteudo


def test_fr009_salvar_indisponivel_durante_envio(client, hx_parcial):
    """FR-009: o botão Salvar fica desabilitado durante o envio (hx-disabled-elt)."""
    conteudo = html(client.get("/produtos/novo/", **hx_parcial("dialogo")))
    botao = re.search(r"<button[^>]*>[^<]*(?:<[^>]+>[^<]*)*Salvar", conteudo).group(0)
    assert 'hx-disabled-elt="this"' in botao


def test_fr009_mesmas_mensagens_pagina_e_dialogo(client, hx_parcial):
    """FR-009: página e diálogo exibem as mesmas mensagens de validação."""
    invalido = {"nome": "", "quantidade_inicial": "x", "estoque_minimo": ""}
    pagina = html(client.post("/produtos/novo/", invalido))
    dialogo = html(client.post("/produtos/novo/", invalido, **hx_parcial("dialogo")))
    for mensagem in (
        "Informe o nome do produto.",
        "Informe um número inteiro igual ou maior que zero.",
        "Informe o estoque mínimo.",
    ):
        assert mensagem in pagina and mensagem in dialogo


@pytest.mark.parametrize("boost", [False, True])
def test_fr010_fr011_post_valido_comum_e_boosted_302_com_destaque(client, hx_boosted, boost):
    """FR-010/FR-011: 302 para a lista; linha nova no topo com selo NOVO e mensagem."""
    extra = hx_boosted if boost else {}
    resposta = client.post("/produtos/novo/", VALIDO, **extra)
    assert resposta.status_code == 302 and resposta["Location"] == "/produtos/"
    produto = Produto.objects.get()
    lista = html(client.get("/produtos/", **extra))
    primeira = re.search(r'<tr id="produto-\d+"[^>]*>', lista).group(0)
    assert f'id="produto-{produto.pk}"' in primeira and "tabela__linha--destaque" in primeira
    assert "NOVO" in lista
    assert f"Produto {produto.codigo} cadastrado" in lista
    assert "NOVO" not in html(client.get("/produtos/"))


def test_fr007_post_invalido_comum_422_preserva_valores(client):
    """FR-007: inválido → 422 na página, erros acessíveis e valores preservados."""
    resposta = client.post(
        "/produtos/novo/", {"nome": "Caneta", "quantidade_inicial": "-3", "estoque_minimo": "2"}
    )
    conteudo = html(resposta)
    assert resposta.status_code == 422
    entrada = campo(conteudo, "quantidade_inicial")
    assert 'aria-invalid="true"' in entrada and "aria-describedby=" in entrada
    assert 'value="Caneta"' in campo(conteudo, "nome") and 'value="-3"' in entrada
    assert Produto.objects.count() == 0


def test_fr010_post_valido_dialogo_cabecalhos(client, hx_parcial):
    """FR-010: sucesso no diálogo atualiza a lista, fecha o diálogo e mostra toast."""
    resposta = client.post("/produtos/novo/", VALIDO, **hx_parcial("dialogo"))
    produto = Produto.objects.get()
    gatilhos = json.loads(resposta["HX-Trigger"])
    assert resposta.status_code == 200
    assert resposta["HX-Retarget"] == "#resultados"
    assert resposta["HX-Reswap"] == "outerHTML"
    assert resposta["HX-Push-Url"] == "/produtos/"
    assert gatilhos["toast"] == {
        "nivel": "sucesso",
        "texto": f"Produto {produto.codigo} cadastrado",
    }
    assert "fechar-dialogo" in gatilhos
    conteudo = html(resposta)
    assert 'id="resultados"' in conteudo and "tabela__linha--destaque" in conteudo


def test_fr010_dialogo_fora_da_lista_redireciona(client, hx_parcial):
    """FR-010: aberto fora da lista (ex.: Painel), o sucesso leva à lista com destaque."""
    resposta = client.post("/produtos/novo/", VALIDO, **hx_parcial("dialogo", "http://testserver/"))
    assert resposta["HX-Redirect"] == "/produtos/"
    assert "NOVO" in html(client.get("/produtos/"))


def test_fr031_post_valido_dialogo_emite_estoque_alterado(client, hx_parcial):
    """FR-031: o cadastro emite estoque-alterado (o produto pode nascer em alerta)."""
    resposta = client.post("/produtos/novo/", VALIDO, **hx_parcial("dialogo"))
    assert "estoque-alterado" in json.loads(resposta["HX-Trigger"])


def test_fr010_sucesso_no_dialogo_reseta_filtros(client, hx_parcial):
    """FR-010: a resposta traz filtros limpos e contagem por OOB."""
    conteudo = html(client.post("/produtos/novo/", VALIDO, **hx_parcial("dialogo")))
    filtros = re.search(r'<form id="filtros-produtos"[^>]*>', conteudo).group(0)
    assert 'hx-swap-oob="true"' in filtros
    assert 'value=""' in campo(conteudo, "q") or "value=" not in campo(conteudo, "q")
    assert re.search(r'id="contagem-produtos"[^>]*hx-swap-oob="true"', conteudo)


def test_fr007_post_invalido_dialogo_422_com_autofocus(client, hx_parcial):
    """FR-007: inválido no diálogo → 422 com o fragmento e foco no primeiro campo inválido."""
    dados = {"nome": "Caneta", "quantidade_inicial": "", "estoque_minimo": "1"}
    resposta = client.post("/produtos/novo/", dados, **hx_parcial("dialogo"))
    conteudo = html(resposta)
    assert resposta.status_code == 422 and "<html" not in conteudo
    assert "autofocus" in campo(conteudo, "quantidade_inicial")
    assert "autofocus" not in campo(conteudo, "nome")


def test_fr005_post_duplicado_mensagem_com_codigo(client, produto_factory):
    """FR-005: nome duplicado → 422 citando o código do produto existente."""
    existente = produto_factory(nome="Caneta Azul")
    resposta = client.post("/produtos/novo/", {**VALIDO, "nome": "caneta AZUL"})
    assert resposta.status_code == 422
    assert f"Já existe um produto com este nome ({existente.codigo})." in html(resposta)


@pytest.mark.parametrize("valor", ["2,5", "1.000", "-1", "abc"])
def test_fr006_post_quantidade_invalida_422(client, valor):
    """FR-006: quantidade inválida → 422 e nada gravado."""
    resposta = client.post("/produtos/novo/", {**VALIDO, "quantidade_inicial": valor})
    assert resposta.status_code == 422 and Produto.objects.count() == 0


@pytest.mark.parametrize("metodo", ["put", "delete", "patch"])
def test_novo_metodos_nao_permitidos_405(client, metodo):
    """PUT/DELETE/PATCH em /produtos/novo/ → 405."""
    assert getattr(client, metodo)("/produtos/novo/").status_code == 405
