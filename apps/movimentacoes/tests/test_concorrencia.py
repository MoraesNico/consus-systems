"""Integridade sob concorrência no PostgreSQL (FR-008, SC-003)."""

import threading
import time

import pytest
from django.db import connection

from apps.movimentacoes.services import EstoqueInsuficienteError, registrar_movimentacao
from apps.produtos.models import Produto
from apps.produtos.services import cadastrar_produto
from apps.produtos.tests import PRECOS_TESTE

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.django_db(transaction=True),
]


def disparar_em_paralelo(funcoes):
    barreira = threading.Barrier(len(funcoes))
    resultados = [None] * len(funcoes)

    def executar(indice, funcao):
        try:
            barreira.wait()
            resultados[indice] = funcao()
        except Exception as erro:  # noqa: BLE001 — o teste inspeciona o tipo
            resultados[indice] = erro
        finally:
            connection.close()

    threads = [threading.Thread(target=executar, args=(i, f)) for i, f in enumerate(funcoes)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    return resultados


@pytest.mark.parametrize("rodada", range(20))
def test_sc003_vinte_saidas_simultaneas_nunca_negativam(rodada):
    """SC-003: saldo 10 + 20 saídas simultâneas de 1 → exatamente 10 aceitas, saldo 0."""
    produto = cadastrar_produto(**PRECOS_TESTE, nome=f"Concorrência {rodada}",
                                quantidade_inicial=10, estoque_minimo=1)  # fmt: skip
    saida = lambda: registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1)  # noqa: E731
    resultados = disparar_em_paralelo([saida] * 20)
    aceitas = [r for r in resultados if not isinstance(r, Exception)]
    recusas = [r for r in resultados if isinstance(r, EstoqueInsuficienteError)]
    assert (len(aceitas), len(recusas)) == (10, 10)
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 0
    assert produto.movimentacoes.filter(tipo="SAIDA").count() == 10


def test_fr008_duas_saidas_de_6_com_saldo_10():
    """FR-008: uma saída de 6 passa; a outra recebe "disponível 4, solicitado 6"."""
    produto = cadastrar_produto(
        **PRECOS_TESTE, nome="Duas saídas", quantidade_inicial=10, estoque_minimo=1
    )
    saida = lambda: registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=6)  # noqa: E731
    resultados = disparar_em_paralelo([saida, saida])
    erros = [r for r in resultados if isinstance(r, EstoqueInsuficienteError)]
    assert len(erros) == 1 and str(erros[0]) == "Saldo insuficiente: disponível 4, solicitado 6"


def test_fr008_segunda_transacao_espera_a_primeira():
    """FR-008: select_for_update sem nowait — a segunda chamada aguarda o commit da primeira."""
    from django.db import transaction

    produto = cadastrar_produto(
        **PRECOS_TESTE, nome="Espera", quantidade_inicial=10, estoque_minimo=1
    )
    liberado = threading.Event()
    instantes = {}

    def segurar_bloqueio():
        with transaction.atomic():
            Produto.objects.select_for_update().get(pk=produto.pk)
            liberado.set()
            time.sleep(0.5)
        instantes["a"] = time.monotonic()
        connection.close()

    def sair():
        liberado.wait()
        registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1)
        instantes["b"] = time.monotonic()
        connection.close()

    threads = [threading.Thread(target=segurar_bloqueio), threading.Thread(target=sair)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert instantes["b"] >= instantes["a"]
