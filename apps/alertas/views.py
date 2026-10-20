"""Relatório de reposição e contador do menu (contracts/http-alertas.md)."""

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from django.views.decorators.vary import vary_on_headers

from apps.core.htmx import eh_fragmento

from .exportacao import nome_arquivo_csv, para_csv
from .selectors import total_em_alerta, varrer


def _plural(total: int, singular: str, plural: str) -> str:
    return f"{total} {singular if total == 1 else plural}"


def texto_varredura(resultado) -> str:
    alertas = _plural(resultado.total_em_alerta, "produto", "produtos")
    return (
        f"Varredura concluída: {alertas} em alerta ({resultado.total_sem_estoque} sem estoque) "
        f"de {resultado.total_analisado} analisados."
    )


@require_safe
@never_cache
@vary_on_headers("HX-Request", "HX-Target")
def relatorio(request):
    formato = request.GET.get("formato", "html")
    if formato not in ("html", "csv"):
        return HttpResponseBadRequest(
            "Formato não suportado. Use html ou csv.", content_type="text/plain; charset=utf-8"
        )
    resultado = varrer()
    if formato == "csv":
        resposta = HttpResponse(
            para_csv(resultado, bom=True), content_type="text/csv; charset=utf-8"
        )
        resposta["Content-Disposition"] = f'attachment; filename="{nome_arquivo_csv(resultado)}"'
        return resposta
    contexto = {
        "resultado": resultado,
        "intervalo": settings.ALERTAS_INTERVALO_SEGUNDOS,
        "texto_anuncio": texto_varredura(resultado),
    }
    if eh_fragmento(request):
        return render(request, "alertas/partials/relatorio_fragmento.html", contexto)
    return render(request, "alertas/relatorio.html", contexto)


def _inteiro_nao_negativo(valor: str | None) -> int | None:
    return int(valor) if valor and valor.isdigit() and valor.isascii() else None


@require_safe
@never_cache
def contador(request):
    total = total_em_alerta()
    anterior = _inteiro_nao_negativo(request.GET.get("anterior"))
    if anterior is not None and anterior == total:
        return HttpResponse(status=204)
    contexto = {"total": total, "intervalo": settings.ALERTAS_INTERVALO_SEGUNDOS}
    if anterior is not None:
        contexto["texto_anuncio"] = (
            f"Alertas de reposição: {_plural(total, 'produto', 'produtos')} (antes {anterior})."
        )
    return render(request, "alertas/partials/contador_resposta.html", contexto)
