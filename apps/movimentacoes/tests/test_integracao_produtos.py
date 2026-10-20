"""Integração com as páginas de produto: ações rápidas e histórico (FR-013, FR-015, FR-025)."""

import re

import pytest
from django.template import Context, Template

from apps.movimentacoes.services import registrar_movimentacao

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def test_fr013_acoes_rapidas(produto_com_saldo):
    """FR-013: "+ Entrada" e "− Saída" com href sem JS e hx-get para o diálogo."""
    produto = produto_com_saldo(nome="Parafuso")
    saida = Template('{% load movimentacoes_tags %}{% acoes_rapidas produto "lista" %}').render(
        Context({"produto": produto})
    )
    pk = produto.pk
    assert f'href="/movimentacoes/nova/?produto={pk}&amp;tipo=ENTRADA"' in saida
    assert f'hx-get="/movimentacoes/nova/?produto={pk}&amp;tipo=SAIDA&amp;origem=lista"' in saida
    assert 'hx-target="#dialogo"' in saida
    assert f'aria-label="Registrar entrada de {produto.codigo} Parafuso"' in saida
    assert "+ Entrada" in saida and "− Saída" in saida


def test_fr013_lista_e_detalhe_exibem_acoes(client, produto_com_saldo):
    """FR-013: lista (com coluna Ações) e detalhe oferecem as ações, inclusive com saldo 0."""
    produto = produto_com_saldo(saldo=0)
    lista = html(client.get("/produtos/"))
    assert re.search(r'<th scope="col"[^>]*>\s*<span class="visualmente-oculto">Ações', lista)
    linha = lista.split(f'id="produto-{produto.pk}"', 1)[1].split("</tr>", 1)[0]
    assert "+ Entrada" in linha and "Saída" in linha
    detalhe = html(client.get(f"/produtos/{produto.pk}/"))
    assert "origem=detalhe" in detalhe


def test_fr025_historico_no_detalhe(client, produto_com_saldo):
    """FR-025: o detalhe mostra as 10 mais recentes, sem coluna produto, e o link completo."""
    produto = produto_com_saldo(saldo=0)
    for i in range(12):
        registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=i + 1)
    conteudo = html(client.get(f"/produtos/{produto.pk}/"))
    historico = conteudo.split(f'id="produto-{produto.pk}-historico"', 1)[1].split("</section>", 1)[
        0
    ]
    assert historico.count('class="linha-movimentacao') == 10
    assert "+12" in historico and "Saldo inicial" not in historico
    assert f'href="/movimentacoes/?produto={produto.pk}"' in historico
    assert "Ver histórico completo" in historico


def test_fr025_historico_vazio_nunca_ocorre_mas_tem_texto(client, produto_com_saldo):
    """FR-025: produto recém-cadastrado já mostra o saldo inicial no histórico."""
    produto = produto_com_saldo(saldo=5)
    conteudo = html(client.get(f"/produtos/{produto.pk}/"))
    assert "Saldo inicial" in conteudo.split(f'id="produto-{produto.pk}-historico"', 1)[1]


def test_fr032_acessibilidade_do_dialogo(client, produto_com_saldo):
    """FR-032: nome acessível com o produto, foco na quantidade e toasts anunciados no diálogo."""
    produto = produto_com_saldo(nome="Parafuso")
    dialogo = client.get(
        f"/movimentacoes/nova/?produto={produto.pk}&tipo=SAIDA&origem=lista",
        HTTP_HX_REQUEST="true",
        HTTP_HX_TARGET="dialogo",
    ).content.decode()
    assert re.search(r'<input[^>]+name="quantidade"[^>]+autofocus', dialogo)
    assert re.search(r'data-toasts aria-live="polite"', dialogo)
    assert 'aria-label="Fechar"' in dialogo
    lista = client.get("/produtos/").content.decode()
    assert f'aria-label="Registrar saída de {produto.codigo} Parafuso"' in lista
