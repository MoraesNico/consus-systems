"""Transação financeira: espelho imutável de cada Entrada/Saída (docs/arquitetura.md v1.2)."""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from django.db import models
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce

from apps.core.dinheiro import DinheiroField


class TipoTransacao(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SAIDA = "SAIDA", "Saída/Venda"


class TransacaoImutavelError(Exception):
    def __init__(self):
        super().__init__("Transações são imutáveis; registre uma movimentação de sentido oposto.")


@dataclass(frozen=True)
class Totais:
    receitas: Decimal
    despesas: Decimal
    custo_vendido: Decimal
    quantidade_vendida: int
    quantidade_transacoes: int

    @property
    def saldo(self) -> Decimal:
        return self.receitas - self.despesas

    @property
    def lucro_bruto(self) -> Decimal:
        return self.receitas - self.custo_vendido


def _soma(campo: str, filtro: Q | None = None):
    return Coalesce(Sum(campo, filter=filtro, output_field=DinheiroField()), 0,
                    output_field=DinheiroField())  # fmt: skip


class TransacaoQuerySet(models.QuerySet):
    def receitas(self):
        return self.filter(tipo=TipoTransacao.SAIDA)

    def despesas(self):
        return self.filter(tipo=TipoTransacao.ENTRADA)

    def do_produto(self, produto_id: int):
        return self.filter(produto_id=produto_id)

    def do_tipo(self, tipo: str):
        return self.filter(tipo=tipo)

    def no_periodo(self, de: datetime.date | None, ate: datetime.date | None):
        """Mesma semântica de `Movimentacao.no_periodo` (datas inclusivas, fuso local)."""
        from apps.movimentacoes.models import MovimentacaoQuerySet

        return MovimentacaoQuerySet.no_periodo(self, de, ate)

    def recentes(self):
        return self.select_related("produto", "movimentacao").order_by("-criado_em", "-id")

    def totais(self) -> Totais:
        saida = Q(tipo=TipoTransacao.SAIDA)
        dados = self.aggregate(
            receitas=_soma("valor_total", saida),
            despesas=_soma("valor_total", Q(tipo=TipoTransacao.ENTRADA)),
            custo_vendido=_soma("custo_total", saida),
            quantidade_vendida=Coalesce(Sum("quantidade", filter=saida), 0),
            quantidade_transacoes=Count("id"),
        )
        return Totais(**dados)

    def update(self, **kwargs):
        raise TransacaoImutavelError

    def delete(self):
        raise TransacaoImutavelError


class Transacao(models.Model):
    id = models.BigAutoField(primary_key=True)
    movimentacao = models.OneToOneField(
        "movimentacoes.Movimentacao", on_delete=models.PROTECT, related_name="transacao"
    )
    produto = models.ForeignKey(
        "produtos.Produto", on_delete=models.PROTECT, related_name="transacoes"
    )
    tipo = models.CharField(max_length=7, choices=TipoTransacao.choices)
    quantidade = models.PositiveIntegerField()
    preco_unitario = DinheiroField("preço unitário")
    valor_total = DinheiroField("valor total")
    custo_unitario = DinheiroField("custo unitário")
    custo_total = DinheiroField("custo total")
    criado_em = models.DateTimeField(db_index=True, editable=False)

    objects = TransacaoQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "transação"
        verbose_name_plural = "transações"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo__in=TipoTransacao.values), name="transacao_tipo_valido"
            ),
            models.CheckConstraint(
                condition=Q(quantidade__gt=0), name="transacao_quantidade_positiva"
            ),
            models.CheckConstraint(
                condition=Q(valor_total=F("quantidade") * F("preco_unitario")),
                name="transacao_valor_total_consistente",
            ),
            models.CheckConstraint(
                condition=Q(custo_total=F("quantidade") * F("custo_unitario")),
                name="transacao_custo_total_consistente",
            ),
            models.CheckConstraint(
                condition=~Q(tipo=TipoTransacao.ENTRADA) | Q(custo_unitario=F("preco_unitario")),
                name="transacao_entrada_custo_igual_preco",
            ),
            models.CheckConstraint(
                condition=Q(preco_unitario__gte=0, custo_unitario__gte=0),
                name="transacao_valores_nao_negativos",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.natureza} de {self.valor_total} em {self.produto_id}"

    def save(self, *args, **kwargs):
        if self.pk is not None and not self._state.adding:
            raise TransacaoImutavelError
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TransacaoImutavelError

    @property
    def eh_receita(self) -> bool:
        return self.tipo == TipoTransacao.SAIDA

    @property
    def natureza(self) -> str:
        return "Receita" if self.eh_receita else "Despesa"

    @property
    def valor_assinado(self) -> Decimal:
        return self.valor_total if self.eh_receita else -self.valor_total

    @property
    def lucro_bruto(self) -> Decimal | None:
        return self.valor_total - self.custo_total if self.eh_receita else None
