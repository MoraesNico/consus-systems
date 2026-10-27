"""Falhas de login para o bloqueio por força bruta (docs/arquitetura.md v1.2, "Autenticação")."""

import datetime

from django.db import models
from django.utils import timezone

JANELA = datetime.timedelta(minutes=15)
LIMITE_USUARIO = 5
LIMITE_IP = 20


class TentativaAcessoQuerySet(models.QuerySet):
    def recentes(self, agora=None):
        return self.filter(criado_em__gte=(agora or timezone.now()) - JANELA)


class TentativaAcesso(models.Model):
    usuario = models.CharField(max_length=150, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    criado_em = models.DateTimeField(default=timezone.now, db_index=True)

    objects = TentativaAcessoQuerySet.as_manager()

    class Meta:
        verbose_name = "tentativa de acesso"
        verbose_name_plural = "tentativas de acesso"

    def __str__(self) -> str:
        return f"{self.usuario} @ {self.ip}"


def minutos_de_bloqueio(usuario: str, ip: str | None, agora=None) -> int:
    """0 se liberado; senão, minutos até a falha mais antiga da janela expirar."""
    agora = agora or timezone.now()
    recentes = TentativaAcesso.objects.recentes(agora)
    for consulta, limite in (
        (recentes.filter(usuario=usuario.lower()), LIMITE_USUARIO),
        (recentes.filter(ip=ip) if ip else recentes.none(), LIMITE_IP),
    ):
        datas = list(consulta.order_by("-criado_em").values_list("criado_em", flat=True)[:limite])
        if len(datas) >= limite:
            restante = datas[-1] + JANELA - agora
            return max(1, -(-int(restante.total_seconds()) // 60))
    return 0
