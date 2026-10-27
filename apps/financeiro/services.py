"""Escrita de transações: chamada só por `registrar_movimentacao`, na mesma transação de banco."""

from apps.movimentacoes.models import Movimentacao, TipoMovimentacao

from .models import TipoTransacao, Transacao


def registrar_transacao(*, movimentacao: Movimentacao, produto) -> Transacao | None:
    """Entrada (e saldo inicial > 0) → despesa a custo; Saída → receita a preço de venda.

    Os preços são congelados no momento da movimentação; INICIAL com 0 não gera transação.
    """
    if movimentacao.quantidade == 0:
        return None
    custo = produto.preco_custo
    if movimentacao.tipo == TipoMovimentacao.SAIDA:
        tipo, preco = TipoTransacao.SAIDA, produto.preco_venda
    else:
        tipo, preco = TipoTransacao.ENTRADA, custo
    quantidade = movimentacao.quantidade
    return Transacao.objects.create(
        movimentacao=movimentacao,
        produto=produto,
        tipo=tipo,
        quantidade=quantidade,
        preco_unitario=preco,
        valor_total=quantidade * preco,
        custo_unitario=custo,
        custo_total=quantidade * custo,
        criado_em=movimentacao.criado_em,
    )
