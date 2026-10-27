"""Períodos de consulta (008 cria; 009 usa) — docs/arquitetura.md, "Períodos"."""

import datetime
from dataclasses import dataclass

from django.utils import timezone

ROTULOS = {
    "tudo": "Todo o período",
    "mes": "Este mês",
    "30d": "Últimos 30 dias",
    "7d": "Últimos 7 dias",
    "hoje": "Hoje",
    "personalizado": "Personalizado",
}
PADRAO = "tudo"


class PeriodoInvalidoError(ValueError):
    pass


@dataclass(frozen=True)
class Periodo:
    chave: str
    rotulo: str
    de: datetime.date | None
    ate: datetime.date | None

    @property
    def dias(self) -> int | None:
        if self.de is None or self.ate is None:
            return None
        return (self.ate - self.de).days + 1


def _data(valor) -> datetime.date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime.date):
        return valor
    try:
        return datetime.date.fromisoformat(str(valor))
    except ValueError as erro:
        raise PeriodoInvalidoError("Informe datas válidas (AAAA-MM-DD).") from erro


def resolver_periodo(chave: str | None, de=None, ate=None, *, hoje=None) -> Periodo:
    """Chave desconhecida → `tudo`. `personalizado` exige `de ≤ ate` (PeriodoInvalidoError)."""
    hoje = hoje or timezone.localdate()
    chave = chave if chave in ROTULOS else PADRAO
    rotulo = ROTULOS[chave]
    if chave == "hoje":
        return Periodo(chave, rotulo, hoje, hoje)
    if chave == "7d":
        return Periodo(chave, rotulo, hoje - datetime.timedelta(days=6), hoje)
    if chave == "30d":
        return Periodo(chave, rotulo, hoje - datetime.timedelta(days=29), hoje)
    if chave == "mes":
        return Periodo(chave, rotulo, hoje.replace(day=1), hoje)
    if chave == "personalizado":
        inicio, fim = _data(de), _data(ate)
        if inicio is None or fim is None:
            raise PeriodoInvalidoError("Informe as duas datas do período.")
        if inicio > fim:
            raise PeriodoInvalidoError("A data inicial deve ser anterior ou igual à final.")
        return Periodo(chave, rotulo, inicio, fim)
    return Periodo(chave, rotulo, None, None)
