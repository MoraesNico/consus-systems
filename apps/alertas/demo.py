"""Dados de demonstração do Consus (data-model §6 da 004).

Tudo passa pelos serviços oficiais (`cadastrar_produto` e `registrar_movimentacao`): o saldo de
cada produto vem do livro-razão, nunca de escrita direta.
"""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.movimentacoes.services import registrar_movimentacao
from apps.produtos.models import Produto
from apps.produtos.services import cadastrar_produto


@dataclass(frozen=True)
class MovimentoDemo:
    tipo: str  # "ENTRADA" | "SAIDA"
    quantidade: int
    observacao: str


@dataclass(frozen=True)
class ProdutoDemo:
    nome: str
    minimo: int
    inicial: int
    movimentos: tuple[MovimentoDemo, ...] = ()
    custo: Decimal = Decimal("1.00")
    venda: Decimal = Decimal("2.00")


def _s(qtd: int, obs: str) -> MovimentoDemo:
    return MovimentoDemo("SAIDA", qtd, obs)


def _e(qtd: int, obs: str) -> MovimentoDemo:
    return MovimentoDemo("ENTRADA", qtd, obs)


PRODUTOS_DEMO: tuple[ProdutoDemo, ...] = (
    ProdutoDemo("Caneta esferográfica azul", 50, 200, (_s(60, "Venda balcão"), _s(45, "Pedido 1042")), Decimal("1.20"), Decimal("2.50")),
    ProdutoDemo("Papel sulfite A4 (resma 500 fls)", 20, 30, (_s(18, "Pedido 1043"), _e(40, "NF 88231")), Decimal("24.90"), Decimal("34.90")),
    ProdutoDemo("Parafuso sextavado M6 x 20", 100, 150, (_s(90, "Obra Rua 7"),), Decimal("0.35"), Decimal("0.80")),
    ProdutoDemo("Fita adesiva transparente 48 mm", 24, 24, (_e(12, "NF 88302"), _s(12, "Venda balcão")), Decimal("4.10"), Decimal("7.90")),
    ProdutoDemo("Cola branca 90 g", 15, 15, (_s(10, "Escola Aurora"), _s(5, "Venda balcão")), Decimal("2.30"), Decimal("4.50")),
    ProdutoDemo("Grampeador de mesa 26/6", 5, 8, (_s(2, "Venda balcão"),), Decimal("18.00"), Decimal("32.90")),
    ProdutoDemo("Luva de nitrilo (caixa c/ 100)", 10, 12, (_s(9, "Clínica Bem-Estar"),), Decimal("29.90"), Decimal("44.90")),
    ProdutoDemo("Lâmpada LED 9 W", 30, 80, (_s(20, "Pedido 1044"),), Decimal("6.50"), Decimal("12.90")),
    ProdutoDemo("Caderno universitário 96 fls", 40, 100, (_s(35, "Escola Aurora"), _e(20, "NF 88410")), Decimal("9.80"), Decimal("16.90")),
    ProdutoDemo("Etiqueta adesiva 100x50 (rolo)", 0, 12, (), Decimal("15.00"), Decimal("24.00")),
    ProdutoDemo("Toner HP 85A", 4, 10, (_s(3, "Pedido 1045"),), Decimal("189.00"), Decimal("279.00")),
    ProdutoDemo("Pilha alcalina AA (par)", 60, 100, (_s(30, "Venda balcão"),), Decimal("7.20"), Decimal("6.90")),
)  # fmt: skip

# Dias atrás de cada movimentação (009): compras antigas e vendas recentes, para que "Todo o
# período" mostre caixa negativo (estoque inicial comprado) e "Últimos 7 dias" saldo positivo.
DIAS_INICIAL = 30
DIAS_MOVIMENTOS: tuple[tuple[int, ...], ...] = (
    (18, 3),
    (16, 9),
    (5,),
    (20, 2),
    (14, 1),
    (6,),
    (4,),
    (11,),
    (12, 8),
    (),
    (2,),
    (1,),
)


def _momento(dias: int, ordem: int) -> datetime.datetime:
    """Horário comercial do dia, deslocado pela ordem para manter o livro-razão em sequência."""
    agora = timezone.localtime()
    base = (agora - datetime.timedelta(days=dias)).replace(hour=9, minute=0, second=0,
                                                         microsecond=0)  # fmt: skip
    return min(base + datetime.timedelta(minutes=7 * ordem), agora)


def popular() -> tuple[int, int, int]:
    """Cria os produtos que faltam. Devolve (criados, já existentes, movimentações)."""
    criados = existentes = movimentacoes = 0
    for ordem, (item, dias) in enumerate(zip(PRODUTOS_DEMO, DIAS_MOVIMENTOS, strict=True)):
        if Produto.objects.filter(nome__iexact=item.nome).exists():
            existentes += 1
            continue
        with transaction.atomic():
            produto = cadastrar_produto(
                nome=item.nome,
                quantidade_inicial=item.inicial,
                estoque_minimo=item.minimo,
                preco_custo=item.custo,
                preco_venda=item.venda,
                momento=_momento(DIAS_INICIAL, ordem),
            )
            for movimento, dias_atras in zip(item.movimentos, dias, strict=True):
                registrar_movimentacao(
                    produto_id=produto.pk,
                    tipo=movimento.tipo,
                    quantidade=movimento.quantidade,
                    observacao=movimento.observacao,
                    momento=_momento(dias_atras, ordem),
                )
        criados += 1
        movimentacoes += len(item.movimentos)
    return criados, existentes, movimentacoes
