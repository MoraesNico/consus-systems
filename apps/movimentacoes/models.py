"""Movimentação de estoque: livro-razão imutável (specs/003-movimentacao-estoque/data-model.md)."""

import datetime

from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.formats import number_format

from apps.produtos.models import QUANTIDADE_MAXIMA

QUANTIDADE_MAXIMA_MOVIMENTACAO = 1_000_000
SALDO_MAXIMO = QUANTIDADE_MAXIMA
OBSERVACAO_MAX = 200
HISTORICO_DETALHE = 10
ITENS_POR_PAGINA = 25
MENSAGEM_MAXIMA = 200  # limite do toast (001)


class TipoMovimentacao(models.TextChoices):
    INICIAL = "INICIAL", "Saldo inicial"
    ENTRADA = "ENTRADA", "Entrada"
    SAIDA = "SAIDA", "Saída/Venda"


class MovimentacaoImutavelError(Exception):
    def __init__(self):
        super().__init__(
            "Movimentações são imutáveis; registre uma movimentação de sentido oposto."
        )


class MovimentacaoQuerySet(models.QuerySet):
    def do_produto(self, produto_id: int) -> "MovimentacaoQuerySet":
        return self.filter(produto_id=produto_id)

    def do_tipo(self, tipo: str) -> "MovimentacaoQuerySet":
        return self.filter(tipo=tipo)

    def no_periodo(self, de: datetime.date | None, ate: datetime.date | None):
        """`de`/`ate` inclusivos, no fuso atual: [início(de), início(ate + 1 dia))."""
        fuso = timezone.get_current_timezone()
        consulta = self
        if de:
            consulta = consulta.filter(
                criado_em__gte=datetime.datetime.combine(de, datetime.time.min, tzinfo=fuso)
            )
        if ate:
            fim = datetime.datetime.combine(ate + datetime.timedelta(days=1), datetime.time.min)
            consulta = consulta.filter(criado_em__lt=fim.replace(tzinfo=fuso))
        return consulta

    def recentes(self) -> "MovimentacaoQuerySet":
        return self.select_related("produto", "transacao", "registrado_por").order_by(
            "-criado_em", "-id"
        )

    def update(self, **kwargs):
        raise MovimentacaoImutavelError

    def delete(self):
        raise MovimentacaoImutavelError


class Movimentacao(models.Model):
    id = models.BigAutoField(primary_key=True)
    produto = models.ForeignKey(
        "produtos.Produto", on_delete=models.PROTECT, related_name="movimentacoes"
    )
    tipo = models.CharField(max_length=7, choices=TipoMovimentacao.choices)
    quantidade = models.PositiveIntegerField()
    saldo_anterior = models.PositiveIntegerField()
    saldo_posterior = models.PositiveIntegerField()
    observacao = models.CharField(max_length=OBSERVACAO_MAX, blank=True, default="")
    registrado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimentacoes",
        verbose_name="registrado por",
    )
    criado_em = models.DateTimeField(default=timezone.now, db_index=True, editable=False)

    objects = MovimentacaoQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "movimentação"
        verbose_name_plural = "movimentações"
        indexes = [models.Index(F("produto"), F("criado_em").desc(), name="mov_produto_criado_idx")]
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo__in=TipoMovimentacao.values), name="mov_tipo_valido"
            ),
            models.CheckConstraint(
                condition=Q(quantidade__gt=0) | Q(tipo=TipoMovimentacao.INICIAL),
                name="mov_quantidade_positiva_exceto_inicial",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        tipo__in=[TipoMovimentacao.INICIAL, TipoMovimentacao.ENTRADA],
                        saldo_posterior=F("saldo_anterior") + F("quantidade"),
                    )
                    | Q(
                        tipo=TipoMovimentacao.SAIDA,
                        saldo_posterior=F("saldo_anterior") - F("quantidade"),
                    )
                ),
                name="mov_saldo_posterior_consistente",
            ),  # fmt: skip
            models.CheckConstraint(
                condition=~Q(tipo=TipoMovimentacao.INICIAL) | Q(saldo_anterior=0),
                name="mov_inicial_parte_de_zero",
            ),
            models.UniqueConstraint(
                fields=["produto"],
                condition=Q(tipo=TipoMovimentacao.INICIAL),
                name="mov_inicial_unica_por_produto",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} de {self.quantidade} em {self.produto_id}"

    def save(self, *args, **kwargs):
        if self.pk is not None and not self._state.adding:
            raise MovimentacaoImutavelError
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise MovimentacaoImutavelError

    @property
    def transacao_financeira(self):
        """Transação da 008, ou None (saldo inicial 0 e movimentações anteriores à 2.0)."""
        try:
            return self.transacao
        except models.ObjectDoesNotExist:
            return None

    @property
    def eh_saida(self) -> bool:
        return self.tipo == TipoMovimentacao.SAIDA

    @property
    def sinal(self) -> str:
        return "−" if self.eh_saida else "+"

    @property
    def quantidade_assinada(self) -> int:
        return -self.quantidade if self.eh_saida else self.quantidade

    @property
    def variante_selo(self) -> str:
        return "info" if self.tipo == TipoMovimentacao.ENTRADA else "neutro"

    @property
    def icone_selo(self) -> str:
        return {
            TipoMovimentacao.ENTRADA: "arrow-down-to-line",
            TipoMovimentacao.SAIDA: "arrow-up-from-line",
        }.get(self.tipo, "")

    @property
    def mensagem_confirmacao(self) -> str:
        """Ex.: "Saída registrada: #0001 Parafuso — saldo 10 → 7" (≤ 200 caracteres)."""
        acao = {
            TipoMovimentacao.INICIAL: "Saldo inicial registrado",
            TipoMovimentacao.ENTRADA: "Entrada registrada",
            TipoMovimentacao.SAIDA: "Saída registrada",
        }[self.tipo]
        antes = number_format(self.saldo_anterior, force_grouping=True)
        depois = number_format(self.saldo_posterior, force_grouping=True)
        prefixo = f"{acao}: {self.produto.codigo} "
        sufixo = f" — saldo {antes} → {depois}"
        nome = self.produto.nome
        espaco = MENSAGEM_MAXIMA - len(prefixo) - len(sufixo)
        if len(nome) > espaco:
            nome = nome[: max(espaco - 1, 1)] + "…"
        return f"{prefixo}{nome}{sufixo}"
