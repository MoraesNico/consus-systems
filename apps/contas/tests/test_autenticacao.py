"""006 — Login interativo, sessão e bloqueio de força bruta."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from apps.contas.models import TentativaAcesso
from apps.movimentacoes.services import registrar_movimentacao
from apps.produtos.services import cadastrar_produto

pytestmark = pytest.mark.django_db
SENHA = "senha-forte-123"


@pytest.fixture
def admin(django_user_model):
    return django_user_model.objects.create_user(username="admin", password=SENHA, first_name="Ana")


def entrar(cliente, usuario="admin", senha=SENHA, **extra):
    return cliente.post("/contas/entrar/", {"usuario": usuario, "senha": senha, **extra})


@pytest.mark.parametrize("url", ["/", "/produtos/", "/financeiro/", "/movimentacoes/", "/design/"])
def test_fr001_paginas_exigem_login(cliente_anonimo, url):
    resposta = cliente_anonimo.get(url)
    assert resposta.status_code == 302
    assert resposta["Location"].startswith("/contas/entrar/?next=")


def test_fr002_htmx_anonimo_recebe_hx_redirect(cliente_anonimo):
    atual = "http://testserver/produtos/?q=x"
    resposta = cliente_anonimo.get("/produtos/", HTTP_HX_REQUEST="true", HTTP_HX_CURRENT_URL=atual)
    assert resposta["HX-Redirect"] == "/contas/entrar/?next=/produtos/%3Fq%3Dx"


def test_fr003_saude_e_login_sao_publicos(cliente_anonimo):
    assert cliente_anonimo.get("/saude/").status_code == 200
    html = cliente_anonimo.get("/contas/entrar/").content.decode()
    assert 'autocomplete="current-password"' in html and "data-alternar-senha" in html
    assert 'aria-label="Principal"' not in html


def test_fr004_credenciais_erradas_mensagem_generica(cliente_anonimo, admin):
    for usuario, senha in [("admin", "errada"), ("ninguem", SENHA)]:
        resposta = entrar(cliente_anonimo, usuario, senha)
        assert resposta.status_code == 422
        assert "Usuário ou senha incorretos." in resposta.content.decode()
    admin.is_active = False
    admin.save()
    assert "Usuário ou senha incorretos." in entrar(cliente_anonimo).content.decode()


def test_fr005_login_com_sucesso_e_next_seguro(cliente_anonimo, admin):
    resposta = entrar(cliente_anonimo, next="/financeiro/")
    assert resposta.status_code == 302 and resposta["Location"] == "/financeiro/"
    assert cliente_anonimo.session.get_expire_at_browser_close()
    cliente_anonimo.post("/contas/sair/")
    externo = entrar(cliente_anonimo, next="https://malicioso.example/", lembrar="on")
    assert externo["Location"] == "/"
    assert not cliente_anonimo.session.get_expire_at_browser_close()
    pagina = cliente_anonimo.get("/").content.decode()
    assert "Olá, Ana! Sessão iniciada." in pagina and "Sair" in pagina


def test_fr006_login_htmx_redireciona_com_cabecalho(cliente_anonimo, admin):
    resposta = cliente_anonimo.post("/contas/entrar/", {"usuario": "admin", "senha": SENHA},
                                    HTTP_HX_REQUEST="true")  # fmt: skip
    assert resposta.status_code == 200 and resposta["HX-Redirect"] == "/"
    erro = cliente_anonimo.post("/contas/entrar/", {"usuario": "x", "senha": "y"},
                                HTTP_HX_REQUEST="true")  # fmt: skip
    html = erro.content.decode()
    assert html.startswith('<section id="cartao-login"') and "animar-tremer" in html


def test_fr007_bloqueio_apos_cinco_falhas(cliente_anonimo, admin):
    for _ in range(5):
        entrar(cliente_anonimo, senha="errada")
    bloqueado = entrar(cliente_anonimo)  # até a senha certa é recusada
    assert bloqueado.status_code == 429
    assert "Muitas tentativas. Tente novamente em 15 min." in bloqueado.content.decode()
    assert TentativaAcesso.objects.count() == 5


def test_fr008_sucesso_limpa_falhas(cliente_anonimo, admin):
    entrar(cliente_anonimo, senha="errada")
    entrar(cliente_anonimo)
    assert not TentativaAcesso.objects.exists()


def test_fr009_sair_exige_post(client):
    assert client.get("/contas/sair/").status_code == 405
    assert client.post("/contas/sair/")["Location"] == "/contas/entrar/"
    assert client.get("/").status_code == 302


def test_fr010_trocar_senha(client, usuario):
    assert client.get("/contas/senha/").status_code == 200
    ruim = client.post("/contas/senha/", {"old_password": "x", "new_password1": "a",
                                          "new_password2": "a"})  # fmt: skip
    assert ruim.status_code == 422
    nova = "Outra-Senha-Forte-987"
    ok = client.post("/contas/senha/", {"old_password": "senha-forte-123",
                                        "new_password1": nova, "new_password2": nova})  # fmt: skip
    assert ok.status_code == 302
    usuario.refresh_from_db()
    assert usuario.check_password(nova)


def test_fr011_garantir_usuario(capsys):
    call_command("garantir_usuario", "--usuario", "admin", "--senha", "consus-2026")
    call_command("garantir_usuario", "--usuario", "admin", "--senha", "outra")
    assert "já existe; senha mantida" in capsys.readouterr().out
    assert get_user_model().objects.get(username="admin").check_password("consus-2026")
    with pytest.raises(CommandError):
        call_command("garantir_usuario", "--usuario", "", "--senha", "")


def test_fr012_movimentacao_registra_usuario(client, usuario):
    produto = cadastrar_produto(nome="Caneta", quantidade_inicial=5, estoque_minimo=1,
                                preco_custo=Decimal("1"), preco_venda=Decimal("2"),
                                usuario=usuario)  # fmt: skip
    mov = registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1,
                                 usuario=usuario)  # fmt: skip
    assert mov.registrado_por == usuario
    assert "operador" in client.get("/financeiro/transacoes/").content.decode()


def test_fr013_modo_demo_mostra_dica(cliente_anonimo, settings):
    settings.CONSUS_DEMO = True
    html = cliente_anonimo.get("/contas/entrar/").content.decode()
    assert "Ambiente de demonstração" in html and "CONSUS_SENHA" in html
