"""Utilitários HTMX compartilhados por todas as features (contracts/layout-e-htmx.md §3–§4).

Os eventos são acumulados num único cabeçalho `HX-Trigger` por `trigger_client_event`, então
`disparar_toast(fechar_dialogo(resposta), "Salvo.")` envia os dois eventos juntos.
"""

from django.http import HttpRequest, HttpResponse
from django_htmx.http import trigger_client_event

NIVEIS_TOAST = ("sucesso", "info", "alerta", "erro")
TEXTO_MAXIMO_TOAST = 200


def eh_fragmento(request: HttpRequest) -> bool:
    """Responder só o fragmento? Sim para HTMX que não seja boost nem restauração de histórico."""
    htmx = getattr(request, "htmx", None)
    return bool(htmx) and not htmx.boosted and not htmx.history_restore_request


def disparar_evento(response: HttpResponse, nome: str, dados: dict | None = None) -> HttpResponse:
    return trigger_client_event(response, nome, dados if dados is not None else {})


def disparar_toast(response: HttpResponse, texto: str, nivel: str = "sucesso") -> HttpResponse:
    if nivel not in NIVEIS_TOAST:
        raise ValueError(f"Nível de toast inválido: {nivel!r}. Use {', '.join(NIVEIS_TOAST)}.")
    if not texto or len(texto) > TEXTO_MAXIMO_TOAST:
        raise ValueError(f"O texto do toast deve ter de 1 a {TEXTO_MAXIMO_TOAST} caracteres.")
    return disparar_evento(response, "toast", {"nivel": nivel, "texto": texto})


def fechar_dialogo(response: HttpResponse) -> HttpResponse:
    return disparar_evento(response, "fechar-dialogo")
