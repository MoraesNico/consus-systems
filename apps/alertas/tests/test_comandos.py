"""Comandos de terminal: varrer_estoque e popular_demo (FR-027–FR-031, FR-034, FR-035)."""

import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.alertas.exportacao import para_csv
from apps.alertas.selectors import varrer
from apps.movimentacoes.models import Movimentacao
from apps.movimentacoes.selectors import auditar_saldos
from apps.produtos.models import Produto

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
    assert [next(c for c in ("E", "D", "A", "B") if cenario[c].codigo in linha) for linha in linhas] == [
        "E", "D", "A", "B"]  # fmt: skip


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
    """FR-031: o comando não grava nada."""
    antes = (Produto.objects.count(), Movimentacao.objects.count())
    rodar("varrer_estoque", "--todos")
    assert (Produto.objects.count(), Movimentacao.objects.count()) == antes


def test_fr034_popular_demo(db):
    """FR-034: 12 produtos, 4 em alerta (1 sem estoque), 16 movimentações, livro-razão íntegro."""
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
