"""Views do core: Painel, catálogo do design system e saúde (contracts/rotas-core)."""

from collections import OrderedDict

from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.vary import vary_on_headers

from . import design_tokens
from .forms import FormularioExemplo
from .htmx import NIVEIS_TOAST, disparar_evento, disparar_toast, eh_fragmento
from .navegacao import url_se_existir
from .selectors import estado_saude

COMPONENTES_CATALOGO = (
    ("botao", "Botão", "§4.1"),
    ("campo", "Campo", "§4.2"),
    ("tabela", "Tabela densa", "§4.3"),
    ("badge", "Badge", "§4.4"),
    ("cartao", "Cartão", "§4.5"),
    ("kpi", "KPI", "§4.6"),
    ("lista-barras", "BarList", "§4.7"),
    ("barra-categorias", "CategoryBar", "§4.8"),
    ("rastreador", "Tracker", "§4.9"),
    ("barra-progresso", "ProgressBar", "§4.10"),
    ("dialogo", "Diálogo", "§4.11"),
    ("toast", "Toast", "§4.12"),
    ("aviso", "Aviso inline", "§4.13"),
    ("estado-vazio", "Estado vazio", "§4.14"),
    ("paginacao", "Paginação", "§4.15"),
    ("navegacao", "Navegação com badge", "§4.16"),
    ("cabecalho-pagina", "Cabeçalho de página", "§4.17"),
    ("icone", "Ícone", "§4.18"),
)

SECOES_TOKENS = (
    ("cores", "Cores", ("--color-",)),
    ("contraste", "Contraste", ()),
    ("tipografia", "Tipografia", ("--font-", "--text-", "--leading-", "--tracking-", "--measure")),
    ("espacamento", "Espaçamento", ("--space-",)),
    (
        "tamanhos",
        "Tamanhos",
        (
            "--size-",
            "--icon-",
            "--header-h",
            "--container-max",
            "--form-max",
            "--dialog-w-",
            "--toast-w",
            "--grid-",
            "--page-margin",
            "--bp-",
            "--table-",
        ),
    ),
    ("bordas", "Bordas e raios", ("--border-", "--radius-")),
    ("sombras", "Sombras e foco", ("--shadow-", "--focus-")),
    ("camadas", "Camadas", ("--z-",)),
    ("movimento", "Movimento e opacidade", ("--duration-", "--ease-", "--opacity-")),
)

ICONES = (
    "layout-dashboard",
    "package",
    "arrow-left-right",
    "bell",
    "triangle-alert",
    "circle-check",
    "info",
    "octagon-x",
    "circle-alert",
    "arrow-down-to-line",
    "arrow-up-from-line",
    "arrow-up",
    "arrow-down",
    "arrow-right",
    "plus",
    "search",
    "x",
    "chevron-left",
    "chevron-right",
    "chevron-down",
    "inbox",
    "loader-circle",
    "activity",
)


@require_safe
@never_cache
@vary_on_headers("HX-Request", "HX-Target")
def painel(request):
    from apps.alertas.selectors import resumo_painel  # feature 004: KPIs do Painel
    from apps.financeiro.selectors import faixa_financeira  # feature 009: faixa financeira

    resumo = resumo_painel()
    contexto = {
        "resumo": resumo,
        "financeiro": faixa_financeira() if resumo.total_produtos else None,
        "meta_alerta": f"{resumo.total_sem_estoque} sem estoque",
        "url_cadastro_produto": url_se_existir("produtos:novo"),
        "url_lista_produtos": url_se_existir("produtos:lista"),
        "url_relatorio": url_se_existir("alertas:relatorio"),
        "url_movimentacoes": url_se_existir("movimentacoes:lista"),
    }
    if eh_fragmento(request):
        return render(request, "core/partials/painel_kpis.html", contexto)
    return render(request, "core/painel.html", contexto)


def _tokens_por_secao() -> list[dict]:
    tokens = design_tokens.tokens_atuais()
    secoes = []
    for ancora, titulo, prefixos in SECOES_TOKENS:
        itens = OrderedDict()
        for nome, valor in tokens.items():
            if prefixos and nome.startswith(prefixos):
                itens[nome] = {
                    "nome": nome,
                    "valor": valor,
                    "resolvido": design_tokens.resolver(nome, tokens),
                }
        secoes.append({"ancora": ancora, "titulo": titulo, "tokens": list(itens.values())})
    return secoes


def _dados_exemplo() -> dict:
    paginas = Paginator(range(132), 25)
    return {
        "pagina_exemplo": paginas.page(2),
        "itens_barras": [
            {"rotulo": "Parafuso sextavado M8", "valor": 1240},
            {"rotulo": "Arruela lisa 8 mm", "valor": 612},
            {"rotulo": "Porca M8", "valor": 180},
            {"rotulo": "Bucha 6 mm", "valor": 0},
        ],
        "segmentos": [
            {"rotulo": "OK", "valor": 98, "tom": "ok"},
            {"rotulo": "Reposição necessária", "valor": 18, "tom": "reposicao"},
            {"rotulo": "Sem estoque", "valor": 4, "tom": "sem_estoque"},
        ],
        "blocos": [
            {"tom": tom, "rotulo": f"{dia:02d}/10/2026"}
            for dia, tom in enumerate(
                ["acento"] * 6
                + ["vazio"] * 2
                + ["acento"] * 5
                + ["reposicao"] * 2
                + ["acento"] * 8
                + ["vazio"]
                + ["sem_estoque"]
                + ["acento"] * 5,
                start=1,
            )
        ],
        "formulario_vazio": FormularioExemplo(),
        "formulario_erro": FormularioExemplo(data={"nome": "", "quantidade": "0"}),
    }


def _contexto_catalogo() -> dict:
    return {
        "secoes_tokens": _tokens_por_secao(),
        "pares_contraste": design_tokens.avaliar_pares(),
        "componentes": [
            {"ancora": a, "nome": n, "secao_ds": s} for a, n, s in COMPONENTES_CATALOGO
        ],
        "icones": ICONES,
        "niveis_toast": NIVEIS_TOAST,
        **_dados_exemplo(),
    }


def _render_dialogo(request, form, status=200):
    if eh_fragmento(request):
        return render(request, "core/partials/design_dialogo.html", {"form": form}, status=status)
    return render(request, "core/design_dialogo_pagina.html", {"form": form}, status=status)


@require_http_methods(["GET", "HEAD", "POST"])
def design(request):
    if request.method == "POST":
        return _design_post(request)
    exemplo = request.GET.get("exemplo")
    if exemplo is None:
        return render(request, "core/design.html", _contexto_catalogo())
    if exemplo == "dialogo":
        return _render_dialogo(request, FormularioExemplo())
    raise SuspiciousOperation("Exemplo desconhecido.")


def _design_post(request):
    exemplo = request.POST.get("exemplo")
    if exemplo == "toast":
        nivel = request.POST.get("nivel")
        if nivel not in NIVEIS_TOAST:
            raise SuspiciousOperation("Nível de toast inválido.")
        texto = f"Exemplo de toast de {nivel}."
        if eh_fragmento(request):
            return disparar_toast(HttpResponse(status=204), nivel, texto)
        nivel_django = {
            "sucesso": messages.SUCCESS,
            "info": messages.INFO,
            "alerta": messages.WARNING,
            "erro": messages.ERROR,
        }[nivel]
        messages.add_message(request, nivel_django, texto)
        return redirect("/design/#toast")
    if exemplo == "formulario":
        form = FormularioExemplo(request.POST)
        if not form.is_valid():
            return _render_dialogo(request, form, status=422)
        texto = f"Exemplo enviado: {form.cleaned_data['nome']} × {form.cleaned_data['quantidade']}."
        if eh_fragmento(request):
            return disparar_toast(
                disparar_evento(HttpResponse(), "fechar-dialogo"), "sucesso", texto
            )
        messages.success(request, texto)
        return redirect("/design/#dialogo")
    raise SuspiciousOperation("Exemplo desconhecido.")


@require_safe
@never_cache
def saude(request):
    estado = estado_saude()
    return JsonResponse(estado, status=200 if estado["status"] == "ok" else 503)
