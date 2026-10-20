"""Leituras da feature 004: varredura por criticidade, contador e resumo do painel.

Nada aqui grava no banco: a varredura é calculada na hora (FR-031, research R6).
"""

import datetime
from dataclasses import dataclass

from django.db.models import BigIntegerField, Case, Count, F, Q, QuerySet, Sum, Value, When
from django.db.models.functions import Cast, Coalesce, Greatest, Least
from django.utils import timezone

from apps.movimentacoes.models import Movimentacao, TipoMovimentacao
from apps.produtos.models import QUANTIDADE_MAXIMA, Produto

from . import regras

LIMITE_CRITICOS = 5
LIMITE_COBERTURA = 8
LIMITE_MOVIMENTACOES = 5


def produtos_por_criticidade(*, incluir_ok: bool = False) -> QuerySet[Produto]:
    """Sem estoque primeiro, depois maior déficit, menor cobertura e menor ID (FR-006)."""
    q = Cast("quantidade_atual", BigIntegerField())
    m = Cast("estoque_minimo", BigIntegerField())
    consulta = Produto.objects.com_situacao().annotate(
        gravidade=Case(
            When(quantidade_atual=0, then=Value(2)),
            When(quantidade_atual__lte=F("estoque_minimo"), then=Value(1)),
            default=Value(0),
        ),
        sugestao_reposicao=Case(
            When(
                quantidade_atual__lte=F("estoque_minimo"),
                then=Least(
                    Greatest(Value(regras.FATOR_ESTOQUE_ALVO) * m - q, Value(1)),
                    Value(QUANTIDADE_MAXIMA) - q,
                ),
            ),
            default=Value(None),
            output_field=BigIntegerField(),
        ),
    )
    if not incluir_ok:
        consulta = consulta.em_alerta()
    return consulta.order_by(
        F("gravidade").desc(),
        F("deficit").desc(),
        F("cobertura_percentual").asc(nulls_last=True),
        F("id").asc(),
    )


def _com_situacao_estoque(produtos) -> tuple[Produto, ...]:
    itens = tuple(produtos)
    for produto in itens:
        produto.situacao_estoque = regras.classificar(
            produto.quantidade_atual, produto.estoque_minimo
        )
    return itens


@dataclass(frozen=True)
class ResultadoVarredura:
    executada_em: datetime.datetime
    total_analisado: int
    total_em_alerta: int
    total_sem_estoque: int
    itens: tuple[Produto, ...]

    @property
    def sem_produtos(self) -> bool:
        return self.total_analisado == 0

    @property
    def sem_alertas(self) -> bool:
        return self.total_em_alerta == 0


def varrer(
    *, incluir_ok: bool = False, agora: datetime.datetime | None = None
) -> ResultadoVarredura:
    """Executa a varredura de reposição (2 consultas; totais coerentes com os itens)."""
    executada_em = agora or timezone.now()
    itens = _com_situacao_estoque(produtos_por_criticidade(incluir_ok=incluir_ok))
    em_alerta = [p for p in itens if p.situacao_estoque is not regras.Situacao.OK]
    return ResultadoVarredura(
        executada_em=executada_em,
        total_analisado=Produto.objects.count(),
        total_em_alerta=len(em_alerta),
        total_sem_estoque=sum(p.situacao_estoque is regras.Situacao.SEM_ESTOQUE for p in em_alerta),
        itens=itens,
    )


def total_em_alerta() -> int:
    return Produto.objects.em_alerta().count()


@dataclass(frozen=True)
class ResumoPainel:
    total_produtos: int
    total_unidades: int
    total_em_alerta: int
    total_sem_estoque: int
    movimentacoes_24h: int
    criticos: tuple[Produto, ...]
    cobertura: tuple[Produto, ...]
    ultimas_movimentacoes: tuple[Movimentacao, ...]


def resumo_painel(*, agora: datetime.datetime | None = None) -> ResumoPainel:
    """KPIs e listas do Painel (≤ 5 consultas)."""
    agora = agora or timezone.now()
    kpis = Produto.objects.aggregate(
        total_produtos=Count("id"),
        total_unidades=Coalesce(Sum("quantidade_atual"), 0),
        total_em_alerta=Count("id", filter=Q(quantidade_atual__lte=F("estoque_minimo"))),
        total_sem_estoque=Count("id", filter=Q(quantidade_atual=0)),
    )
    movimentacoes_24h = Movimentacao.objects.filter(
        tipo__in=[TipoMovimentacao.ENTRADA, TipoMovimentacao.SAIDA],
        criado_em__gte=agora - datetime.timedelta(hours=24),
    ).count()
    criticos = _com_situacao_estoque(produtos_por_criticidade()[:LIMITE_CRITICOS])
    cobertura = _com_situacao_estoque(
        Produto.objects.com_situacao()
        .filter(cobertura_percentual__isnull=False)
        .order_by("cobertura_percentual", "id")[:LIMITE_COBERTURA]
    )
    ultimas = tuple(Movimentacao.objects.recentes()[:LIMITE_MOVIMENTACOES])
    return ResumoPainel(
        movimentacoes_24h=movimentacoes_24h,
        criticos=criticos,
        cobertura=cobertura,
        ultimas_movimentacoes=ultimas,
        **kpis,
    )
