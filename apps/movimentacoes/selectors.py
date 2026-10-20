"""Leituras do livro-razão e auditoria de saldos (contracts/servico-movimentacao.md)."""

import datetime
from collections import defaultdict
from typing import NamedTuple

from django.db.models import QuerySet

from apps.produtos.models import Produto

from .models import HISTORICO_DETALHE, Movimentacao, TipoMovimentacao


def listar_movimentacoes(
    *,
    produto_id: int | None = None,
    tipo: str | None = None,
    de: datetime.date | None = None,
    ate: datetime.date | None = None,
) -> QuerySet[Movimentacao]:
    consulta = Movimentacao.objects.recentes()
    if produto_id:
        consulta = consulta.do_produto(produto_id)
    if tipo:
        consulta = consulta.do_tipo(tipo)
    if de or ate:
        consulta = consulta.no_periodo(de, ate)
    return consulta


def historico_do_produto(produto_id: int, *, limite: int = HISTORICO_DETALHE) -> list[Movimentacao]:
    return list(Movimentacao.objects.recentes().do_produto(produto_id)[:limite])


class DivergenciaSaldo(NamedTuple):
    produto_id: int
    saldo_atual: int
    saldo_calculado: int
    motivo: str  # "soma" | "continuidade" | "inicial"


def auditar_saldos() -> list[DivergenciaSaldo]:
    """Verifica os invariantes do livro-razão; lista vazia = consistente (FR-029)."""
    por_produto: dict[int, list[Movimentacao]] = defaultdict(list)
    for mov in Movimentacao.objects.order_by("produto_id", "criado_em", "id"):
        por_produto[mov.produto_id].append(mov)
    divergencias = []
    for produto in Produto.objects.order_by("id"):
        movs = por_produto.get(produto.pk, [])
        calculado = sum(m.quantidade_assinada for m in movs)
        if calculado != produto.quantidade_atual:
            divergencias.append(
                DivergenciaSaldo(produto.pk, produto.quantidade_atual, calculado, "soma")
            )
            continue
        iniciais = [m for m in movs if m.tipo == TipoMovimentacao.INICIAL]
        if len(iniciais) != 1 or movs[0].tipo != TipoMovimentacao.INICIAL:
            divergencias.append(
                DivergenciaSaldo(produto.pk, produto.quantidade_atual, calculado, "inicial")
            )
            continue
        continuidade = all(
            a.saldo_posterior == b.saldo_anterior for a, b in zip(movs, movs[1:], strict=False)
        )
        if not continuidade or movs[-1].saldo_posterior != produto.quantidade_atual:
            divergencias.append(
                DivergenciaSaldo(produto.pk, produto.quantidade_atual, calculado, "continuidade")
            )
    return divergencias
