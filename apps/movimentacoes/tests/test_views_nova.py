"""Registrar movimentação pela interface: página, diálogo, prévia e eventos (FR-012–FR-020, 032)."""

import json
import re

import pytest

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def templates(resposta) -> list[str]:
    return [t.name for t in resposta.templates]


def postar(client, produto, tipo="ENTRADA", quantidade="5", origem="pagina", **extra):
    dados = {"produto": produto.pk, "tipo": tipo, "quantidade": quantidade, "origem": origem}
    return client.post("/movimentacoes/nova/", dados, **extra)


# ---------- Variante comum (sem HTMX) ----------


def test_fr012_fr014_get_pagina_com_pre_selecao(client, produto_com_saldo):
    """FR-012/FR-014: ?produto=&tipo= pré-seleciona e mostra o saldo atual."""
    produto = produto_com_saldo(nome="Parafuso", saldo=10)
    resposta = client.get(f"/movimentacoes/nova/?produto={produto.pk}&tipo=SAIDA")
    conteudo = html(resposta)
    assert resposta.status_code == 200 and "movimentacoes/nova.html" in templates(resposta)
    assert re.search(rf'<option value="{produto.pk}" selected>', conteudo)
    assert re.search(r'<input[^>]+value="SAIDA"[^>]+checked', conteudo)
    assert "Saldo atual: 10" in conteudo


def test_fr014_pre_selecao_invalida_ignorada(client, produto_com_saldo):
    """FR-014: produto inexistente e tipo INICIAL na URL são ignorados."""
    conteudo = html(client.get("/movimentacoes/nova/?produto=99999&tipo=INICIAL"))
    assert " selected>" not in conteudo.split('name="produto"', 1)[1].split("</select>", 1)[0]
    assert not re.search(r'name="tipo"[^>]*checked', conteudo)


def test_fr012_fr016_post_valido_redireciona_com_mensagem(client, produto_com_saldo):
    """FR-012/FR-016/FR-019: 302 para nova movimentação do mesmo produto e mensagem."""
    produto = produto_com_saldo(nome="Parafuso", saldo=10)
    resposta = postar(client, produto)
    destino = f"/movimentacoes/nova/?produto={produto.pk}&tipo=ENTRADA"
    assert resposta.status_code == 302 and resposta["Location"] == destino
    seguinte = html(client.get(destino))
    assert f"Entrada registrada: {produto.codigo} Parafuso — saldo 10 → 15" in seguinte


def test_fr004_fr018_saida_acima_do_saldo_422_sem_gravar(client, produto_com_saldo):
    """FR-004/FR-018: saída maior que o saldo → 422, mensagem e nada gravado."""
    produto = produto_com_saldo(saldo=10)
    resposta = postar(client, produto, tipo="SAIDA", quantidade="12")
    conteudo = html(resposta)
    assert resposta.status_code == 422 and "<html" in conteudo
    assert "Saldo insuficiente: disponível 10, solicitado 12" in conteudo
    assert re.search(r'<input[^>]+name="quantidade"[^>]+value="12"', conteudo)
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 10
    assert produto.movimentacoes.count() == 1


@pytest.mark.parametrize("metodo", ["put", "patch", "delete"])
def test_fr021_metodos_de_edicao_405(client, metodo):
    """FR-021: não há edição nem exclusão de movimentação."""
    assert getattr(client, metodo)("/movimentacoes/nova/").status_code == 405
    assert getattr(client, metodo)("/movimentacoes/").status_code == 405


# ---------- Variante HTMX ----------


def test_fr017_vary(client):
    """As views variam por HX-Request e HX-Target."""
    vary = client.get("/movimentacoes/nova/")["Vary"]
    assert "HX-Request" in vary and "HX-Target" in vary


def test_fr016_fr017_htmx_origem_pagina(client, produto_com_saldo, htmx_alvo):
    """FR-016/FR-017: sucesso HTMX na página devolve o formulário limpo + eventos."""
    produto = produto_com_saldo(saldo=10)
    resposta = postar(client, produto, **htmx_alvo("form-movimentacao"))
    conteudo = html(resposta)
    gatilhos = json.loads(resposta["HX-Trigger"])
    assert resposta.status_code == 200 and "<html" not in conteudo
    assert conteudo.lstrip().startswith('<form id="form-movimentacao"')
    assert "Saldo atual: 15" in conteudo
    assert not re.search(r'<input[^>]+name="quantidade"[^>]+value=', conteudo)
    assert gatilhos["estoque-alterado"] == {
        "produto_id": produto.pk,
        "saldo_anterior": 10,
        "saldo_posterior": 15,
    }
    assert gatilhos["toast"]["nivel"] == "sucesso"


def test_fr018_htmx_erro_422_sem_eventos(client, produto_com_saldo, htmx_alvo):
    """FR-018: erro via HTMX → 422 com o formulário, sem HX-Trigger e sem gravar."""
    produto = produto_com_saldo(saldo=3)
    resposta = postar(
        client, produto, tipo="SAIDA", quantidade="5", **htmx_alvo("form-movimentacao")
    )
    conteudo = html(resposta)
    assert resposta.status_code == 422 and "HX-Trigger" not in resposta
    assert "Saldo insuficiente: disponível 3, solicitado 5" in conteudo
    assert re.search(r'role="alert"', conteudo)
    assert produto.movimentacoes.count() == 1


def test_fr020_formulario_desabilita_envio_e_boost_recebe_pagina(client, produto_com_saldo):
    """FR-020: envio desabilita o botão; navegação boostada recebe a página inteira."""
    resposta = client.get("/movimentacoes/nova/", HTTP_HX_REQUEST="true", HTTP_HX_BOOSTED="true")
    conteudo = html(resposta)
    assert "<html" in conteudo
    formulario = re.search(r'<form id="form-movimentacao"[^>]*>', conteudo).group(0)
    assert 'hx-disabled-elt="#confirmar-movimentacao"' in formulario
    assert 'id="confirmar-movimentacao"' in conteudo


def test_fr013_fr014_dialogo(client, produto_com_saldo, htmx_alvo):
    """FR-013/FR-014: diálogo com produto fixo, tipo marcado, saldo e foco na quantidade."""
    produto = produto_com_saldo(nome="Parafuso", saldo=10)
    resposta = client.get(
        f"/movimentacoes/nova/?produto={produto.pk}&tipo=ENTRADA&origem=detalhe",
        **htmx_alvo("dialogo"),
    )
    conteudo = html(resposta)
    assert "movimentacoes/partials/dialogo_movimentacao.html" in templates(resposta)
    assert f"Registrar entrada — {produto.codigo} Parafuso" in conteudo
    assert re.search(rf'<input type="hidden" name="produto" value="{produto.pk}"', conteudo)
    assert re.search(r'<input type="hidden" name="origem" value="detalhe"', conteudo)
    assert re.search(r'<input[^>]+name="quantidade"[^>]+autofocus', conteudo)
    assert "Saldo atual: 10" in conteudo


@pytest.mark.parametrize(("valor", "aceito"), [("16", True), ("1.000", False), ("0", False),
                                               ("2000000", False)])  # fmt: skip
def test_fr012_quantidade_pre_preenchida(client, produto_com_saldo, htmx_alvo, valor, aceito):
    """FR-012: ?quantidade= válida pré-preenche (sugestão de reposição da 004)."""
    produto = produto_com_saldo(saldo=10)
    conteudo = html(
        client.get(
            f"/movimentacoes/nova/?produto={produto.pk}&tipo=ENTRADA&origem=alertas&quantidade={valor}",
            **htmx_alvo("dialogo"),
        )
    )
    campo = re.search(r'<input[^>]+name="quantidade"[^>]*>', conteudo).group(0)
    assert (f'value="{valor}"' in campo) is aceito


@pytest.mark.parametrize(
    ("parametros", "esperado"),
    [("tipo=ENTRADA&quantidade=5", "Saldo atual: 10 · Saldo após: 15"),
     ("tipo=SAIDA&quantidade=3", "Saldo atual: 10 · Saldo após: 7"),
     ("tipo=SAIDA&quantidade=12", "Saldo insuficiente: disponível 10, solicitado 12"),
     ("tipo=ENTRADA&quantidade=abc", "Saldo atual: 10"),
     ("tipo=ENTRADA&quantidade=", "Saldo atual: 10")],
)  # fmt: skip
def test_fr014_previa_do_saldo(client, produto_com_saldo, htmx_alvo, parametros, esperado):
    """FR-014: prévia do saldo resultante enquanto o operador digita."""
    produto = produto_com_saldo(saldo=10)
    resposta = client.get(f"/movimentacoes/nova/?produto={produto.pk}&{parametros}",
                          **htmx_alvo("previa-saldo"))  # fmt: skip
    assert resposta.status_code == 200 and esperado in html(resposta)


def test_fr014_previa_sem_produto(client, htmx_alvo):
    """FR-014: sem produto a prévia orienta a selecionar um."""
    resposta = client.get("/movimentacoes/nova/?tipo=ENTRADA", **htmx_alvo("previa-saldo"))
    assert "Selecione um produto para ver o saldo." in html(resposta)


def test_fr015_sucesso_no_dialogo_origem_lista(client, produto_com_saldo, htmx_alvo):
    """FR-015: sucesso vindo da lista → linha do produto por OOB e diálogo fechado."""
    produto = produto_com_saldo(saldo=10)
    resposta = postar(client, produto, tipo="SAIDA", quantidade="4", origem="lista",
                      **htmx_alvo("form-movimentacao"))  # fmt: skip
    conteudo = html(resposta)
    gatilhos = json.loads(resposta["HX-Trigger"])
    assert resposta["HX-Reswap"] == "none"
    assert re.search(rf'<tr id="produto-{produto.pk}"[^>]*hx-swap-oob="true"', conteudo)
    linha = conteudo.split(f'id="produto-{produto.pk}"', 1)[1]
    assert ">6<" in linha
    assert {"estoque-alterado", "toast", "fechar-dialogo"} <= set(gatilhos)


def test_fr015_sucesso_no_dialogo_origem_detalhe(client, produto_com_saldo, htmx_alvo):
    """FR-015: sucesso vindo do detalhe → resumo e histórico por OOB."""
    produto = produto_com_saldo(saldo=10)
    resposta = postar(client, produto, origem="detalhe", observacao="NF 7",
                      **htmx_alvo("form-movimentacao"))  # fmt: skip
    conteudo = html(resposta)
    assert re.search(rf'id="produto-{produto.pk}-resumo"[^>]*hx-swap-oob="true"', conteudo)
    assert re.search(rf'id="produto-{produto.pk}-historico"[^>]*hx-swap-oob="true"', conteudo)


def test_fr015_sucesso_no_dialogo_origem_alertas(client, produto_com_saldo, htmx_alvo):
    """FR-015: vindo do relatório de alertas, sem OOB (a 004 atualiza por evento)."""
    produto = produto_com_saldo(saldo=1)
    resposta = postar(client, produto, origem="alertas", **htmx_alvo("form-movimentacao"))
    assert resposta["HX-Reswap"] == "none"
    assert f"produto-{produto.pk}" not in html(resposta)
    assert {"estoque-alterado", "toast", "fechar-dialogo"} <= set(
        json.loads(resposta["HX-Trigger"])
    )


def test_fr018_erro_no_dialogo_mantem_formulario(client, produto_com_saldo, htmx_alvo):
    """FR-018: erro no diálogo → 422 com o formulário, valores preservados e sem OOB."""
    produto = produto_com_saldo(saldo=2)
    resposta = postar(client, produto, tipo="SAIDA", quantidade="9", origem="lista",
                      **htmx_alvo("form-movimentacao"))  # fmt: skip
    conteudo = html(resposta)
    assert resposta.status_code == 422 and "hx-swap-oob" not in conteudo
    assert re.search(r'<input type="hidden" name="origem" value="lista"', conteudo)
    assert "Saldo insuficiente: disponível 2, solicitado 9" in conteudo
