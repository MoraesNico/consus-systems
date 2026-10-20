"""Integração com 002 e 003: selo, aviso na confirmação e entrada a partir do relatório.

FR-011, FR-012, FR-018–FR-021.
"""

import json
import re

import pytest
from django.template.loader import render_to_string

from apps.alertas.regras import Situacao, aviso_movimentacao, classificar, confirmacao_com_alerta
from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


# ---------- Selo único (002) ----------


@pytest.mark.parametrize(("quantidade", "minimo"), [(0, 0), (0, 5), (5, 5), (6, 5)])
def test_fr018_fr020_selo_igual_em_todas_as_telas(client, criar_produto, quantidade, minimo):
    """FR-018/FR-020/FR-021: lista, detalhe e relatório mostram o mesmo selo com texto."""
    produto = criar_produto(f"Selo {quantidade}/{minimo}", quantidade, minimo)
    situacao = classificar(quantidade, minimo)
    for url in ("/produtos/", f"/produtos/{produto.pk}/"):
        conteudo = html(client.get(url))
        if situacao is Situacao.OK:
            assert "badge--ok" in conteudo
            continue
        assert "REPOSIÇÃO NECESSÁRIA" in conteudo and 'aria-hidden="true"' in conteudo
        assert ("SEM ESTOQUE" in conteudo) is (situacao is Situacao.SEM_ESTOQUE)


@pytest.mark.parametrize(("quantidade", "minimo"), [(0, 0), (0, 5), (5, 5), (6, 5)])
def test_fr021_selo_sem_consultas_extras(criar_produto, django_assert_num_queries, quantidade,
                                         minimo):  # fmt: skip
    """FR-021: o selo da 002 usa a variante da regra, com ou sem anotação, sem consultar o banco."""
    criado = criar_produto(f"Variante {quantidade}/{minimo}", quantidade, minimo)
    variante = classificar(quantidade, minimo).variante
    for produto in (Produto.objects.get(pk=criado.pk),
                    Produto.objects.com_situacao().get(pk=criado.pk)):  # fmt: skip
        with django_assert_num_queries(0):
            selo = render_to_string("produtos/partials/situacao.html", {"produto": produto})
        assert produto.variante_situacao == variante and selo.count('aria-hidden="true"') >= 1


def test_fr018_linha_rerenderizada_mostra_sem_estoque(client, criar_produto):
    """FR-018: após a saída que zera pela lista, a linha OOB da 003 mostra SEM ESTOQUE."""
    produto = criar_produto("Zerar", 3, 5)
    resposta = client.post("/movimentacoes/nova/",
                           {"produto": produto.pk, "tipo": "SAIDA", "quantidade": "3",
                            "origem": "lista"}, HTTP_HX_REQUEST="true")  # fmt: skip
    assert "SEM ESTOQUE" in html(resposta)


# ---------- Aviso na confirmação (003 + 004) ----------


def test_fr019_textos_dos_avisos(criar_produto, movimentar):
    """FR-019: textos exatos dos avisos de transição."""
    p = criar_produto("Parafuso M6", 11, 10)
    piorou = movimentar(p, "SAIDA", 1)
    assert aviso_movimentacao(piorou).texto == (
        f"REPOSIÇÃO NECESSÁRIA: {p.codigo} Parafuso M6 ficou com 10 un. (mínimo 10)."
    )
    zerou = movimentar(p, "SAIDA", 10)
    assert aviso_movimentacao(zerou).texto == (
        f"REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: {p.codigo} Parafuso M6 zerou (mínimo 10)."
    )
    saiu = movimentar(p, "ENTRADA", 25)
    assert aviso_movimentacao(saiu).texto == f"{p.codigo} Parafuso M6 saiu do alerta de reposição."
    assert aviso_movimentacao(p.movimentacoes.get(tipo="INICIAL")) is None


def test_fr019_confirmacao_limitada_a_200(criar_produto, movimentar):
    """FR-019: a confirmação composta cabe no toast (≤ 200 caracteres)."""
    p = criar_produto("N" * 120, 1_000_000_001, 1_000_000_000)
    aviso = confirmacao_com_alerta(movimentar(p, "SAIDA", 1))
    assert aviso.nivel == "alerta" and len(aviso.texto) <= 200 and p.codigo in aviso.texto


@pytest.mark.parametrize(
    ("inicial", "minimo", "tipo", "qtd", "nivel", "trecho"),
    [(11, 10, "SAIDA", 1, "alerta", "REPOSIÇÃO NECESSÁRIA:"),
     (3, 5, "SAIDA", 3, "alerta", "REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE:"),
     (4, 10, "ENTRADA", 21, "sucesso", "saiu do alerta de reposição"),
     (2, 10, "ENTRADA", 3, "sucesso", None)],
)  # fmt: skip
def test_fr019_toast_da_movimentacao(client, criar_produto, inicial, minimo, tipo, qtd, nivel,
                                     trecho):  # fmt: skip
    """FR-019: o toast da 003 ganha o aviso (nível alerta quando piora)."""
    p = criar_produto(f"Toast {inicial}/{minimo}/{tipo}", inicial, minimo)
    resposta = client.post("/movimentacoes/nova/",
                           {"produto": p.pk, "tipo": tipo, "quantidade": str(qtd),
                            "origem": "lista"}, HTTP_HX_REQUEST="true")  # fmt: skip
    gatilhos = json.loads(resposta["HX-Trigger"])
    assert gatilhos["toast"]["nivel"] == nivel and "estoque-alterado" in gatilhos
    if trecho:
        assert trecho in gatilhos["toast"]["texto"]
    else:
        assert gatilhos["toast"]["texto"].endswith(f"saldo {inicial} → {inicial + qtd}")


def test_fr019_sem_htmx_mensagem_de_alerta(client, criar_produto):
    """FR-019: sem HTMX a mensagem vem como aviso de alerta na página seguinte."""
    p = criar_produto("Sem JS", 11, 10)
    dados = {"produto": p.pk, "tipo": "SAIDA", "quantidade": "1"}
    resposta = client.post("/movimentacoes/nova/", dados, follow=True)
    assert re.search(r"aviso--alerta[^>]*>.*REPOSIÇÃO NECESSÁRIA", html(resposta), re.S)


# ---------- Entrada a partir do relatório (003) ----------


def test_fr011_fr012_entrada_pelo_relatorio(client, criar_produto):
    """FR-011/FR-012/SC-008: a sugestão registrada tira o produto do relatório."""
    a = criar_produto("Arruela", 5, 10)
    dialogo = html(client.get(f"/movimentacoes/nova/?produto={a.pk}&tipo=ENTRADA&quantidade=15"
                              "&origem=alertas", HTTP_HX_REQUEST="true",
                              HTTP_HX_TARGET="dialogo"))  # fmt: skip
    assert re.search(r'<input[^>]+name="quantidade"[^>]+value="15"', dialogo)
    resposta = client.post("/movimentacoes/nova/",
                           {"produto": a.pk, "tipo": "ENTRADA", "quantidade": "15",
                            "origem": "alertas"}, HTTP_HX_REQUEST="true")  # fmt: skip
    assert resposta["HX-Reswap"] == "none" and f"produto-{a.pk}" not in html(resposta)
    assert {"estoque-alterado", "toast", "fechar-dialogo"} <= set(
        json.loads(resposta["HX-Trigger"])
    )
    assert Produto.objects.get(pk=a.pk).quantidade_atual == 20
    assert f'id="reposicao-{a.pk}"' not in html(client.get("/alertas/", HTTP_HX_REQUEST="true"))
