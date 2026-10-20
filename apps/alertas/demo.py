"""Dados de demonstração do Consus (data-model §6 da 004).

Tudo passa pelos serviços oficiais (`cadastrar_produto` e `registrar_movimentacao`): o saldo de
cada produto vem do livro-razão, nunca de escrita direta.
"""

from dataclasses import dataclass

from django.db import transaction

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


def _s(qtd: int, obs: str) -> MovimentoDemo:
    return MovimentoDemo("SAIDA", qtd, obs)


def _e(qtd: int, obs: str) -> MovimentoDemo:
    return MovimentoDemo("ENTRADA", qtd, obs)


PRODUTOS_DEMO: tuple[ProdutoDemo, ...] = (
    ProdutoDemo("Caneta esferográfica azul", 50, 200, (_s(60, "Venda balcão"), _s(45, "Pedido 1042"))),
    ProdutoDemo("Papel sulfite A4 (resma 500 fls)", 20, 30, (_s(18, "Pedido 1043"), _e(40, "NF 88231"))),
    ProdutoDemo("Parafuso sextavado M6 x 20", 100, 150, (_s(90, "Obra Rua 7"),)),
    ProdutoDemo("Fita adesiva transparente 48 mm", 24, 24, (_e(12, "NF 88302"), _s(12, "Venda balcão"))),
    ProdutoDemo("Cola branca 90 g", 15, 15, (_s(10, "Escola Aurora"), _s(5, "Venda balcão"))),
    ProdutoDemo("Grampeador de mesa 26/6", 5, 8, (_s(2, "Venda balcão"),)),
    ProdutoDemo("Luva de nitrilo (caixa c/ 100)", 10, 12, (_s(9, "Clínica Bem-Estar"),)),
    ProdutoDemo("Lâmpada LED 9 W", 30, 80, (_s(20, "Pedido 1044"),)),
    ProdutoDemo("Caderno universitário 96 fls", 40, 100, (_s(35, "Escola Aurora"), _e(20, "NF 88410"))),
    ProdutoDemo("Etiqueta adesiva 100x50 (rolo)", 0, 12),
    ProdutoDemo("Toner HP 85A", 4, 10, (_s(3, "Pedido 1045"),)),
    ProdutoDemo("Pilha alcalina AA (par)", 60, 100, (_s(30, "Venda balcão"),)),
)  # fmt: skip


def popular() -> tuple[int, int, int]:
    """Cria os produtos que faltam. Devolve (criados, já existentes, movimentações)."""
    criados = existentes = movimentacoes = 0
    for item in PRODUTOS_DEMO:
        if Produto.objects.filter(nome__iexact=item.nome).exists():
            existentes += 1
            continue
        with transaction.atomic():
            produto = cadastrar_produto(
                nome=item.nome, quantidade_inicial=item.inicial, estoque_minimo=item.minimo
            )
            for movimento in item.movimentos:
                registrar_movimentacao(
                    produto_id=produto.pk,
                    tipo=movimento.tipo,
                    quantidade=movimento.quantidade,
                    observacao=movimento.observacao,
                )
        criados += 1
        movimentacoes += len(item.movimentos)
    return criados, existentes, movimentacoes
