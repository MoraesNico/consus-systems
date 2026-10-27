"""Leitura do financeiro: histórico de transações (008) e resumo do painel (009)."""

import datetime

from django.db.models import QuerySet

from .models import Transacao

ITENS_POR_PAGINA = 25


def listar_transacoes(
    *,
    produto_id: int | None = None,
    tipo: str | None = None,
    de: datetime.date | None = None,
    ate: datetime.date | None = None,
) -> QuerySet[Transacao]:
    consulta = Transacao.objects.recentes()
    if produto_id:
        consulta = consulta.do_produto(produto_id)
    if tipo:
        consulta = consulta.do_tipo(tipo)
    if de or ate:
        consulta = consulta.no_periodo(de, ate)
    return consulta
