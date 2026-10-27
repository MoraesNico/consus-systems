"""Comandos de terminal: varrer_estoque e popular_demo (FR-027–FR-031, FR-034, FR-035)."""

import io
import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.db import DatabaseError

from apps.alertas import demo
from apps.alertas.exportacao import para_csv
from apps.alertas.management.commands.varrer_estoque import Command as VarrerEstoque
from apps.alertas.selectors import varrer
from apps.movimentacoes.models import Movimentacao
from apps.movimentacoes.selectors import auditar_saldos
from apps.movimentacoes.services import MovimentacaoInvalidaError
from apps.produtos.models import Produto
from apps.produtos.services import cadastrar_produto
from apps.produtos.tests import PRECOS_TESTE

pytestmark = pytest.mark.django_db


def rodar(*args) -> str:
    saida = StringIO()
    call_command(*args, stdout=saida, no_color=True)
    return saida.getvalue()


def test_fr027_texto(cenario, agora):
    """FR-027/SC-006: texto com a mesma ordem e os mesmos totais da varredura."""
    saida = rodar("varrer_estoque")
    assert "CONSUS — VARREDURA DE ESTOQUE" in saida and "Em alerta: 4 (2 sem estoque)" in saida
    linhas = [linha for linha in saida.splitlines() if "REPOSIÇÃO NECESSÁRIA" in linha]
    ordem = [next(c for c in "EDAB" if cenario[c].codigo in linha) for linha in linhas]
    assert ordem == ["E", "D", "A", "B"]
    assert "\x1b[" not in saida  # --no-color: sem sequências ANSI


def test_fr028_csv_e_json(cenario, agora):
    """FR-028: csv igual ao da web sem BOM; json com os mesmos itens."""
    assert rodar("varrer_estoque", "--formato", "csv") == para_csv(varrer(), bom=False)
    dados = json.loads(rodar("varrer_estoque", "--formato", "json"))
    assert [i["id"] for i in dados["itens"]] == [p.pk for p in varrer().itens]


def test_fr030_todos(cenario):
    """FR-030: --todos acrescenta os OK no fim."""
    saida = rodar("varrer_estoque", "--todos")
    ultima = [linha for linha in saida.splitlines() if linha.strip()][-1]
    assert ultima.startswith("OK") and cenario["C"].codigo in ultima


def test_fr029_falhar_se_alerta(cenario):
    """FR-029: --falhar-se-alerta → código 1 depois de imprimir o relatório."""
    saida = StringIO()
    with pytest.raises(CommandError) as erro:
        call_command("varrer_estoque", "--falhar-se-alerta", stdout=saida)
    assert erro.value.returncode == 1
    assert str(erro.value) == "Há 4 produto(s) em alerta de reposição."
    assert "CONSUS — VARREDURA DE ESTOQUE" in saida.getvalue()


def test_fr029_sem_alerta_sai_com_zero(criar_produto):
    """FR-029: sem alertas, --falhar-se-alerta não falha."""
    criar_produto("Ok", 10, 1)
    assert "Nenhum produto precisa de reposição." in rodar("varrer_estoque", "--falhar-se-alerta")


def test_fr031_varredura_somente_leitura(cenario):
    """FR-031/FR-037: o comando não grava nada."""
    antes = (Produto.objects.count(), Movimentacao.objects.count())
    rodar("varrer_estoque", "--todos")
    assert (Produto.objects.count(), Movimentacao.objects.count()) == antes


def test_fr034_popular_demo(db):
    """FR-034/FR-037: 12 produtos, 4 em alerta, 16 movimentações; saldos só pelo livro-razão."""
    saida = rodar("popular_demo")
    assert "Dados de demonstração: 12 produto(s) criado(s), 0 já existia(m)." in saida
    assert "Movimentações registradas: 16." in saida
    resultado = varrer()
    assert (resultado.total_analisado, resultado.total_em_alerta, resultado.total_sem_estoque) == (
        12, 4, 1)  # fmt: skip
    assert [p.nome for p in resultado.itens] == [
        "Cola branca 90 g",
        "Parafuso sextavado M6 x 20",
        "Luva de nitrilo (caixa c/ 100)",
        "Fita adesiva transparente 48 mm",
    ]
    assert sum(Produto.objects.values_list("quantidade_atual", flat=True)) == 474
    assert Movimentacao.objects.filter(tipo="INICIAL").count() == 12
    assert auditar_saldos() == []


def test_fr035_popular_demo_idempotente(db):
    """FR-035: segunda execução não cria nem altera nada."""
    rodar("popular_demo")
    antes = (Produto.objects.count(), Movimentacao.objects.count())
    saida = rodar("popular_demo")
    assert "0 produto(s) criado(s), 12 já existia(m)." in saida
    assert "Movimentações registradas: 0." in saida
    assert (Produto.objects.count(), Movimentacao.objects.count()) == antes


def test_fr029_formato_invalido_sai_com_2(capsys):
    """FR-029: argumento inválido → erro de uso do argparse (código 2)."""
    with pytest.raises(SystemExit) as saida:
        VarrerEstoque().run_from_argv(["manage.py", "varrer_estoque", "--formato", "pdf"])
    assert saida.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_fr029_banco_indisponivel_sai_com_2(monkeypatch):
    """FR-029: falha ao consultar o banco → código 2 e nenhum relatório parcial."""

    def falhar(**_):
        raise DatabaseError("conexão recusada")

    monkeypatch.setattr("apps.alertas.management.commands.varrer_estoque.varrer", falhar)
    saida = StringIO()
    with pytest.raises(CommandError) as erro:
        call_command("varrer_estoque", stdout=saida)
    assert erro.value.returncode == 2 and "conexão recusada" in str(erro.value)
    assert saida.getvalue() == ""


def test_terminal_cp1252_troca_o_simbolo(cenario):
    """Edge Case: terminal sem "⚠" (cp1252) → marcador "(!)" mantendo o texto do alerta."""
    bruto = io.BytesIO()
    saida = io.TextIOWrapper(bruto, encoding="cp1252", newline="")
    call_command("varrer_estoque", stdout=saida, no_color=True)
    saida.flush()
    texto = bruto.getvalue().decode("cp1252")
    assert "(!) REPOSIÇÃO NECESSÁRIA" in texto and "⚠" not in texto


@pytest.mark.parametrize(
    "nome",
    ["PAPEL SULFITE A4 (RESMA 500 FLS)",
     # lower() com acentos só é Unicode no PostgreSQL (002 research R3)
     pytest.param("CANETA ESFEROGRÁFICA AZUL", marks=pytest.mark.postgres)],
)  # fmt: skip
def test_fr035_produto_do_usuario_nao_e_alterado(db, nome):
    """FR-035: nome já cadastrado (em outra caixa) conta como existente e fica intacto."""
    meu = cadastrar_produto(**PRECOS_TESTE, nome=nome, quantidade_inicial=7, estoque_minimo=1)
    saida = rodar("popular_demo")
    assert "11 produto(s) criado(s), 1 já existia(m)." in saida
    meu.refresh_from_db()
    assert (meu.nome, meu.quantidade_atual, meu.estoque_minimo) == (nome, 7, 1)
    assert meu.movimentacoes.count() == 1 and Produto.objects.count() == 12


def test_r14_falha_reverte_so_o_produto_e_nova_execucao_completa(db, monkeypatch):
    """research R14: falha no 3º produto desfaz só ele (código 2); rodar de novo completa."""
    original = demo.registrar_movimentacao
    terceiro = demo.PRODUTOS_DEMO[2].nome

    def falhar_no_terceiro(*, produto_id, **dados):
        if Produto.objects.get(pk=produto_id).nome == terceiro:
            raise MovimentacaoInvalidaError("falha simulada")
        return original(produto_id=produto_id, **dados)

    monkeypatch.setattr(demo, "registrar_movimentacao", falhar_no_terceiro)
    with pytest.raises(CommandError) as erro:
        call_command("popular_demo", stdout=StringIO())
    assert erro.value.returncode == 2
    assert list(Produto.objects.order_by("id").values_list("nome", flat=True)) == [
        p.nome for p in demo.PRODUTOS_DEMO[:2]
    ]
    assert auditar_saldos() == []
    monkeypatch.setattr(demo, "registrar_movimentacao", original)
    assert "10 produto(s) criado(s), 2 já existia(m)." in rodar("popular_demo")
    assert Produto.objects.count() == 12 and auditar_saldos() == []
