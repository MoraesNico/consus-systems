"""Views do financeiro: histórico de transações (008) e painel (009)."""

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe
from django.views.decorators.vary import vary_on_headers

from apps.core.htmx import eh_fragmento
from apps.core.periodos import ROTULOS, PeriodoInvalidoError, resolver_periodo

from .exportacao import nome_arquivo_csv, para_csv
from .forms import FiltroTransacoesForm
from .selectors import ITENS_POR_PAGINA, listar_transacoes, resumo_financeiro

ATALHOS = ("tudo", "mes", "30d", "7d", "hoje")


def contexto_painel(parametros) -> dict:
    chave = parametros.get("periodo")
    erro = None
    try:
        periodo = resolver_periodo(chave, parametros.get("de"), parametros.get("ate"))
    except PeriodoInvalidoError as excecao:
        erro = str(excecao)
        periodo = resolver_periodo(None)
    return {
        "resumo": resumo_financeiro(periodo),
        "atalhos": [{"chave": c, "rotulo": ROTULOS[c]} for c in ATALHOS],
        "erro_periodo": erro,
        "de": parametros.get("de", ""),
        "ate": parametros.get("ate", ""),
    }


@require_safe
@vary_on_headers("HX-Request", "HX-Target")
def painel(request):
    contexto = contexto_painel(request.GET)
    if eh_fragmento(request) and request.htmx.target == "painel-financeiro":
        return render(request, "financeiro/partials/painel.html", contexto)
    return render(request, "financeiro/painel.html", contexto)


@require_safe
@vary_on_headers("HX-Request", "HX-Target")
def transacoes(request):
    filtros_form = FiltroTransacoesForm(data=request.GET or None)
    filtros, avisos = filtros_form.filtros_validos() if request.GET else ({}, [])
    consulta = listar_transacoes(**filtros)
    if request.GET.get("formato") == "csv":
        resposta = HttpResponse(para_csv(consulta), content_type="text/csv; charset=utf-8")
        resposta["Content-Disposition"] = f'attachment; filename="{nome_arquivo_csv()}"'
        return resposta
    pagina = Paginator(consulta, ITENS_POR_PAGINA).get_page(request.GET.get("pagina"))
    contexto = {
        "filtros_form": filtros_form if request.GET else FiltroTransacoesForm(),
        "page_obj": pagina,
        "avisos": avisos,
        "filtrado": bool(filtros),
        "totais": consulta.totais(),
        "query_csv": request.GET.urlencode(),
    }
    if eh_fragmento(request) and request.htmx.target == "resultados":
        return render(request, "financeiro/partials/tabela_transacoes.html", contexto)
    return render(request, "financeiro/transacoes.html", contexto)
