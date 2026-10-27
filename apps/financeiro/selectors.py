"""Leitura do financeiro: histórico de transações (008) e resumo do painel (009)."""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Count, F, Q, QuerySet, Sum
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.urls import reverse
from django.utils import timezone

from apps.core.dinheiro import ZERO, DinheiroField
from apps.core.periodos import Periodo
from apps.produtos.models import Produto

from .models import TipoTransacao, Totais, Transacao, _soma


def _soma_expr(expressao):
    return Coalesce(Sum(expressao, output_field=DinheiroField()), 0,
                    output_field=DinheiroField())  # fmt: skip


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


@dataclass(frozen=True)
class PontoFluxo:
    rotulo: str
    receitas: Decimal
    despesas: Decimal

    @property
    def saldo(self) -> Decimal:
        return self.receitas - self.despesas


@dataclass(frozen=True)
class ResumoFinanceiro:
    periodo: Periodo
    valor_estoque: Decimal
    produtos_preco_pendente: int
    totais: Totais
    serie_fluxo: list[PontoFluxo]
    granularidade: str
    top_faturamento: list[dict]
    top_lucro: list[dict]
    maiores_valores_estoque: list[dict]
    ultimas_transacoes: list[Transacao]

    receitas = property(lambda self: self.totais.receitas)
    despesas = property(lambda self: self.totais.despesas)
    saldo_caixa = property(lambda self: self.totais.saldo)
    custo_vendido = property(lambda self: self.totais.custo_vendido)
    lucro_bruto = property(lambda self: self.totais.lucro_bruto)

    @property
    def margem_realizada_percentual(self) -> Decimal | None:
        if not self.receitas:
            return None
        return (self.lucro_bruto * 100 / self.receitas).quantize(Decimal("0.1"))

    @property
    def caixa_negativo(self) -> bool:
        return self.saldo_caixa < 0

    @property
    def maior_valor_serie(self) -> Decimal:
        return max([max(p.receitas, p.despesas) for p in self.serie_fluxo] or [ZERO])


def _serie(consulta, periodo: Periodo, hoje: datetime.date) -> tuple[list[PontoFluxo], str]:
    de = periodo.de
    if de is None:
        primeira = consulta.order_by("criado_em").values_list("criado_em", flat=True).first()
        if primeira is None:
            return [], "dia"
        de = timezone.localtime(primeira).date()
    ate = periodo.ate or hoje
    por_dia = (ate - de).days < 62
    trunc = TruncDate if por_dia else TruncMonth
    linhas = (
        consulta.order_by()
        .annotate(chave=trunc("criado_em", tzinfo=timezone.get_current_timezone()))
        .values("chave")
        .annotate(
            receitas=_soma("valor_total", Q(tipo=TipoTransacao.SAIDA)),
            despesas=_soma("valor_total", Q(tipo=TipoTransacao.ENTRADA)),
        )
    )
    dados = {}
    for linha in linhas:
        chave = linha["chave"]
        chave = chave.date() if isinstance(chave, datetime.datetime) else chave
        dados[chave] = (linha["receitas"], linha["despesas"])
    pontos = []
    if por_dia:
        dia = de
        while dia <= ate:
            r, d = dados.get(dia, (ZERO, ZERO))
            pontos.append(PontoFluxo(dia.strftime("%d/%m"), r, d))
            dia += datetime.timedelta(days=1)
        return pontos, "dia"
    mes = de.replace(day=1)
    while mes <= ate:
        r, d = dados.get(mes, (ZERO, ZERO))
        pontos.append(PontoFluxo(mes.strftime("%m/%Y"), r, d))
        mes = (mes + datetime.timedelta(days=32)).replace(day=1)
    return pontos, "mes"


def _top(consulta, expressao, limite: int = 5) -> list[dict]:
    linhas = (
        consulta.order_by()
        .values("produto_id", "produto__nome")
        .annotate(valor=expressao)
        .filter(valor__gt=0)
        .order_by("-valor", "produto_id")[:limite]
    )
    return [
        {
            "rotulo": f"{Produto(pk=linha['produto_id']).codigo} {linha['produto__nome']}",
            "valor": linha["valor"],
            "href": reverse("produtos:detalhe", args=[linha["produto_id"]]),
        }
        for linha in linhas
    ]


def resumo_financeiro(periodo: Periodo, *, hoje: datetime.date | None = None) -> ResumoFinanceiro:
    """Indicadores do painel financeiro (Passo 3, item 3). Valor do estoque é foto do momento."""
    hoje = hoje or timezone.localdate()
    consulta = Transacao.objects.no_periodo(periodo.de, periodo.ate)
    estoque = Produto.objects.aggregate(
        valor=_soma_expr(F("quantidade_atual") * F("preco_custo")),
        pendentes=Count("id", filter=Q(preco_custo=0) | Q(preco_venda=0)),
    )
    serie, granularidade = _serie(consulta, periodo, hoje)
    vendas = consulta.filter(tipo=TipoTransacao.SAIDA)
    maiores = (
        Produto.objects.com_financeiro()
        .filter(valor_estoque__gt=0)
        .order_by("-valor_estoque", "id")
    )[:5]
    return ResumoFinanceiro(
        periodo=periodo,
        valor_estoque=estoque["valor"],
        produtos_preco_pendente=estoque["pendentes"],
        totais=consulta.totais(),
        serie_fluxo=serie,
        granularidade=granularidade,
        top_faturamento=_top(vendas, _soma("valor_total")),
        top_lucro=_top(vendas, _soma_expr(F("valor_total") - F("custo_total"))),
        maiores_valores_estoque=[
            {
                "rotulo": f"{p.codigo} {p.nome}",
                "valor": p.valor_estoque,
                "href": p.get_absolute_url(),
            }
            for p in maiores
        ],  # fmt: skip
        ultimas_transacoes=list(consulta.recentes()[:5]),
    )


@dataclass(frozen=True)
class FaixaFinanceira:
    """Resumo enxuto da faixa do Painel `/` (2 consultas): todo o período."""

    valor_estoque: Decimal
    receitas: Decimal
    saldo_caixa: Decimal

    @property
    def caixa_negativo(self) -> bool:
        return self.saldo_caixa < 0


def faixa_financeira() -> FaixaFinanceira:
    valor = Produto.objects.aggregate(v=_soma_expr(F("quantidade_atual") * F("preco_custo")))["v"]
    totais = Transacao.objects.totais()
    return FaixaFinanceira(valor, totais.receitas, totais.saldo)
