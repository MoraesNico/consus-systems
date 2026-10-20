"""Produto do estoque (docs/arquitetura.md; specs/002-cadastro-produtos/data-model.md)."""

import re

from django.db import models
from django.db.models import (
    BigIntegerField,
    BooleanField,
    Case,
    ExpressionWrapper,
    F,
    Q,
    Value,
    When,
)
from django.db.models.functions import Cast, Greatest, Lower
from django.urls import reverse

# Teto do `integer` do PostgreSQL: limite de saldo, quantidade inicial e estoque mínimo.
QUANTIDADE_MAXIMA = 2_147_483_647
# Maior valor de um BigAutoField; IDs acima disso nunca existem.
ID_MAXIMO = 9_223_372_036_854_775_807

_SO_ID = re.compile(r"^#\s*([0-9]+)$")
_SO_DIGITOS = re.compile(r"^[0-9]+$")


class ProdutoQuerySet(models.QuerySet):
    def buscar(self, q: str | None) -> "ProdutoQuerySet":
        """Busca por ID (`12`, `#12`, `#0012`) ou parte do nome (contracts/servicos-e-consultas)."""
        termo = " ".join((q or "").split())
        if not termo:
            return self
        if casou := _SO_ID.match(termo):
            numero = int(casou.group(1))
            return self.filter(pk=numero) if 0 < numero <= ID_MAXIMO else self.none()
        if _SO_DIGITOS.match(termo):
            numero = int(termo)
            filtro = Q(nome__icontains=termo)
            if 0 < numero <= ID_MAXIMO:
                filtro |= Q(pk=numero)
            return self.filter(filtro)
        return self.filter(nome__icontains=termo)

    def em_alerta(self) -> "ProdutoQuerySet":
        """Regra do item 3 da atividade: quantidade atual ≤ estoque mínimo."""
        return self.filter(quantidade_atual__lte=F("estoque_minimo"))

    def sem_alerta(self) -> "ProdutoQuerySet":
        return self.filter(quantidade_atual__gt=F("estoque_minimo"))

    def com_situacao(self) -> "ProdutoQuerySet":
        """Anota `alerta` (002), `deficit` e `cobertura_percentual` (004).

        A aritmética usa bigint: `quantidade × 100` estouraria o `integer` do PostgreSQL.
        """
        q = Cast("quantidade_atual", BigIntegerField())
        m = Cast("estoque_minimo", BigIntegerField())
        return self.annotate(
            alerta=ExpressionWrapper(
                Q(quantidade_atual__lte=F("estoque_minimo")), output_field=BooleanField()
            ),
            deficit=Greatest(m - q, Value(0), output_field=BigIntegerField()),
            cobertura_percentual=Case(
                When(quantidade_atual=0, then=Value(0)),
                When(estoque_minimo=0, then=Value(None)),
                default=(q * Value(100)) / m,
                output_field=BigIntegerField(),
            ),
        )


class Produto(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField("nome", max_length=120)
    quantidade_atual = models.PositiveIntegerField("quantidade atual")
    estoque_minimo = models.PositiveIntegerField("estoque mínimo de segurança")
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    objects = ProdutoQuerySet.as_manager()

    class Meta:
        ordering = ["-id"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade_atual__gte=0),
                name="produto_quantidade_atual_nao_negativa",
            ),
            models.CheckConstraint(
                condition=Q(estoque_minimo__gte=0), name="produto_estoque_minimo_nao_negativo"
            ),
            models.CheckConstraint(condition=~Q(nome=""), name="produto_nome_nao_vazio"),
            models.UniqueConstraint(Lower("nome"), name="produto_nome_unico_ci"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} — {self.nome}"

    def get_absolute_url(self) -> str:
        return reverse("produtos:detalhe", args=[self.pk])

    @property
    def codigo(self) -> str:
        return f"#{self.pk:04d}"

    @property
    def em_alerta(self) -> bool:
        return self.quantidade_atual <= self.estoque_minimo

    @property
    def situacao(self) -> str:
        return "alerta" if self.em_alerta else "ok"

    @property
    def variante_situacao(self) -> str:
        """Variação do selo único: `ok`, `reposicao` ou `sem_estoque` (quantidade 0).

        Mesmo vocabulário de `alertas.regras.Situacao.variante` (004).
        """
        if self.quantidade_atual == 0:
            return "sem_estoque"
        return "reposicao" if self.em_alerta else "ok"
