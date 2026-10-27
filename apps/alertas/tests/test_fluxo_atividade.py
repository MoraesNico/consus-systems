"""Ponta a ponta da atividade do professor (SENAI-SP, itens 1, 2 e 3) só por HTTP e comandos."""

import json
import re
from io import StringIO

import pytest
from django.core.management import call_command

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


@pytest.mark.parametrize("htmx", [False, True])
def test_atividade_completa(client, htmx):
    """Itens 1–3: cadastrar, buscar por ID, movimentar sem negativar e ver o alerta."""
    extra = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialogo",
             "HTTP_HX_CURRENT_URL": "http://testserver/produtos/"} if htmx else {}  # fmt: skip

    # Item 1 — cadastro com Nome, Quantidade Inicial e Estoque Mínimo; ID automático.
    client.post("/produtos/novo/", {"nome": "Caneta Azul", "quantidade_inicial": "10",
                                    "estoque_minimo": "5",
                                    "preco_custo": "1,00", "preco_venda": "2,00"},
                **extra)  # fmt: skip
    produto = Produto.objects.get(nome="Caneta Azul")
    assert produto.quantidade_atual == 10 and produto.codigo.startswith("#")
    for busca in (str(produto.pk), f"%23{produto.pk}", f"%23{produto.pk:04d}"):
        assert f'id="produto-{produto.pk}"' in html(client.get(f"/produtos/?q={busca}"))

    # Item 2 — entrada soma, saída subtrai e o saldo nunca fica negativo.
    mov = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    dados = {"produto": produto.pk, "origem": "lista" if htmx else "pagina"}
    client.post("/movimentacoes/nova/", {**dados, "tipo": "ENTRADA", "quantidade": "5"}, **mov)
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 15
    client.post("/movimentacoes/nova/", {**dados, "tipo": "SAIDA", "quantidade": "10"}, **mov)
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 5
    recusa = client.post("/movimentacoes/nova/", {**dados, "tipo": "SAIDA", "quantidade": "6"},
                         **mov)  # fmt: skip
    assert recusa.status_code == 422
    assert "Saldo insuficiente: disponível 5, solicitado 6" in html(recusa)
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 5
    assert produto.movimentacoes.count() == 3

    # Item 3 — quantidade (5) ≤ mínimo (5) ⇒ alerta visual destacado em todas as superfícies.
    for url in ("/produtos/", f"/produtos/{produto.pk}/", "/alertas/"):
        assert "REPOSIÇÃO NECESSÁRIA" in html(client.get(url)), url
    assert re.search(r'id="contador-alertas"[^>]*>.*?>1<', html(client.get("/alertas/contador/")),
                     re.S)  # fmt: skip
    saida = StringIO()
    call_command("varrer_estoque", "--formato", "json", stdout=saida)
    dados_json = json.loads(saida.getvalue())
    assert dados_json["total_em_alerta"] == 1 and dados_json["itens"][0]["id"] == produto.pk
    texto = StringIO()
    call_command("varrer_estoque", stdout=texto, no_color=True)
    assert "⚠ REPOSIÇÃO NECESSÁRIA" in texto.getvalue()
