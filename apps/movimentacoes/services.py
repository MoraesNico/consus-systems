"""Escrita do livro-razão (contracts/servico-movimentacao.md).

`registrar_movimentacao` é o ÚNICO ponto do sistema que altera `Produto.quantidade_atual`
(constituição, princípio I): transação + `select_for_update` + CheckConstraint no banco.
"""

from django.db import transaction
from django.utils import timezone
from django.utils.formats import number_format

from apps.produtos.models import Produto

from .models import (
    OBSERVACAO_MAX,
    QUANTIDADE_MAXIMA_MOVIMENTACAO,
    SALDO_MAXIMO,
    Movimentacao,
    TipoMovimentacao,
)


def formatar_numero(valor: int) -> str:
    return number_format(valor, force_grouping=True)


class MovimentacaoError(Exception):
    """Base de toda recusa de movimentação."""


class MovimentacaoInvalidaError(MovimentacaoError):
    pass


class EstoqueInsuficienteError(MovimentacaoError):
    def __init__(self, disponivel: int, solicitado: int):
        self.disponivel = disponivel
        self.solicitado = solicitado
        super().__init__(
            f"Saldo insuficiente: disponível {formatar_numero(disponivel)}, "
            f"solicitado {formatar_numero(solicitado)}"
        )


class SaldoMaximoExcedidoError(MovimentacaoError):
    def __init__(self, atual: int, entrada: int):
        self.atual = atual
        self.entrada = entrada
        super().__init__(
            f"Saldo máximo excedido: atual {formatar_numero(atual)}, entrada "
            f"{formatar_numero(entrada)}, máximo {formatar_numero(SALDO_MAXIMO)}"
        )


def _validar_quantidade(tipo: str, quantidade) -> None:
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise MovimentacaoInvalidaError("Informe uma quantidade inteira.")
    minimo = 0 if tipo == TipoMovimentacao.INICIAL else 1
    maximo = SALDO_MAXIMO if tipo == TipoMovimentacao.INICIAL else QUANTIDADE_MAXIMA_MOVIMENTACAO
    if quantidade < minimo:
        raise MovimentacaoInvalidaError("Informe uma quantidade maior que zero.")
    if quantidade > maximo:
        raise MovimentacaoInvalidaError(f"Informe no máximo {formatar_numero(maximo)}.")


def registrar_movimentacao(
    *,
    produto_id: int,
    tipo: str,
    quantidade: int,
    observacao: str = "",
    usuario=None,
    momento=None,
) -> Movimentacao:
    """Registra Entrada, Saída/Venda ou Saldo inicial e atualiza o saldo atomicamente.

    Na mesma transação de banco grava a transação financeira (008): despesa ou receita.
    `momento` (009) serve só a demonstração/importação: ≤ agora e ≥ a última movimentação.
    """
    if tipo not in TipoMovimentacao.values:
        raise MovimentacaoInvalidaError("Tipo de movimentação inválido.")
    _validar_quantidade(tipo, quantidade)
    observacao = (observacao or "").strip()
    if len(observacao) > OBSERVACAO_MAX:
        raise MovimentacaoInvalidaError(f"Use no máximo {OBSERVACAO_MAX} caracteres.")

    with transaction.atomic():
        try:
            # Bloqueia a linha: uma segunda chamada concorrente aguarda o commit desta.
            produto = Produto.objects.select_for_update().get(pk=produto_id)
        except Produto.DoesNotExist:
            raise MovimentacaoInvalidaError(
                f"Produto {Produto(pk=produto_id).codigo} não encontrado."
            ) from None
        saldo_anterior = produto.quantidade_atual
        if tipo == TipoMovimentacao.INICIAL and (
            saldo_anterior != 0 or produto.movimentacoes.exists()
        ):
            raise MovimentacaoInvalidaError(f"Saldo inicial já registrado para {produto.codigo}.")
        if tipo == TipoMovimentacao.SAIDA:
            if quantidade > saldo_anterior:
                raise EstoqueInsuficienteError(disponivel=saldo_anterior, solicitado=quantidade)
            saldo_posterior = saldo_anterior - quantidade
        else:
            saldo_posterior = saldo_anterior + quantidade
            if saldo_posterior > SALDO_MAXIMO:
                raise SaldoMaximoExcedidoError(atual=saldo_anterior, entrada=quantidade)

        agora = timezone.now()
        if momento is not None:
            ultima = (
                produto.movimentacoes.order_by("-criado_em")
                .values_list("criado_em", flat=True)
                .first()
            )
            if momento > agora or (ultima is not None and momento < ultima):
                raise MovimentacaoInvalidaError("Momento fora da ordem do livro-razão.")
            agora = momento

        produto.quantidade_atual = saldo_posterior
        produto.save(update_fields=["quantidade_atual", "atualizado_em"])
        movimentacao = Movimentacao.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            observacao=observacao,
            criado_em=agora,
        )
        # Importação tardia: financeiro depende de movimentacoes (evita ciclo no carregamento).
        from apps.financeiro.services import registrar_transacao

        registrar_transacao(movimentacao=movimentacao, produto=produto)
    return movimentacao
