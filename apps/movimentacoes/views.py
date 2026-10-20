"""Views de movimentação (contracts/rotas-movimentacoes.md).

Variantes: comum/boosted (página completa; PRG após POST) e HTMX por alvo: `dialogo`
(formulário em diálogo), `previa-saldo` (prévia do saldo) e o próprio formulário.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.vary import vary_on_headers
from django_htmx.http import reswap

from apps.core.htmx import disparar_evento, disparar_toast, eh_fragmento
from apps.produtos.models import Produto

from .forms import FiltroMovimentacoesForm, MovimentacaoForm, quantidade_valida
from .models import ITENS_POR_PAGINA, SALDO_MAXIMO, TipoMovimentacao
from .selectors import listar_movimentacoes
from .services import (
    EstoqueInsuficienteError,
    MovimentacaoError,
    MovimentacaoInvalidaError,
    SaldoMaximoExcedidoError,
    formatar_numero,
    registrar_movimentacao,
)


@require_safe
@vary_on_headers("HX-Request", "HX-Target")
def lista_movimentacoes(request):
    filtros_form = FiltroMovimentacoesForm(data=request.GET or None)
    filtros, avisos = filtros_form.filtros_validos() if request.GET else ({}, [])
    pagina = Paginator(listar_movimentacoes(**filtros), ITENS_POR_PAGINA).get_page(
        request.GET.get("pagina")
    )
    contexto = {
        "filtros_form": filtros_form if request.GET else FiltroMovimentacoesForm(),
        "page_obj": pagina,
        "avisos": avisos,
        "filtrado": bool(filtros),
    }
    if eh_fragmento(request) and request.htmx.target == "resultados":
        return render(request, "movimentacoes/partials/tabela_movimentacoes.html", contexto)
    return render(request, "movimentacoes/lista.html", contexto)


def _produto_da_url(valor) -> Produto | None:
    try:
        return Produto.objects.get(pk=int(valor))
    except (TypeError, ValueError, OverflowError, Produto.DoesNotExist):
        return None


def _previa(produto: Produto | None, tipo: str | None, quantidade: int | None) -> dict:
    if produto is None:
        return {"texto": "Selecione um produto para ver o saldo.", "alerta": False}
    atual = produto.quantidade_atual
    texto_atual = f"Saldo atual: {formatar_numero(atual)}"
    if not quantidade or tipo not in (TipoMovimentacao.ENTRADA, TipoMovimentacao.SAIDA):
        return {"texto": texto_atual, "alerta": False}
    if tipo == TipoMovimentacao.SAIDA:
        if quantidade > atual:
            return {"texto": str(EstoqueInsuficienteError(atual, quantidade)), "alerta": True}
        return {"texto": f"{texto_atual} · Saldo após: {formatar_numero(atual - quantidade)}",
                "alerta": False}  # fmt: skip
    if atual + quantidade > SALDO_MAXIMO:
        return {"texto": str(SaldoMaximoExcedidoError(atual, quantidade)), "alerta": True}
    return {"texto": f"{texto_atual} · Saldo após: {formatar_numero(atual + quantidade)}",
            "alerta": False}  # fmt: skip


def _contexto_form(form: MovimentacaoForm, produto: Produto | None, modo: str) -> dict:
    tipo = form["tipo"].value()
    quantidade = quantidade_valida(form["quantidade"].value())
    return {
        "form": form,
        "produto": produto,
        "modo": modo,  # "pagina" ou "dialogo"
        "em_dialogo": form["origem"].value() not in (None, "", "pagina"),
        "previa": _previa(produto, tipo, quantidade),
        "titulo_dialogo": _titulo_dialogo(produto, tipo),
    }


def _titulo_dialogo(produto: Produto | None, tipo: str | None) -> str:
    acao = "Registrar saída" if tipo == TipoMovimentacao.SAIDA else "Registrar entrada"
    return f"{acao} — {produto.codigo} {produto.nome}" if produto else "Nova movimentação"


def _form_inicial(request) -> tuple[MovimentacaoForm, Produto | None, str]:
    produto = _produto_da_url(request.GET.get("produto"))
    tipo = request.GET.get("tipo")
    tipo = tipo if tipo in (TipoMovimentacao.ENTRADA, TipoMovimentacao.SAIDA) else None
    origem = request.GET.get("origem")
    origem = origem if origem in ("lista", "detalhe", "alertas") else "lista"
    inicial = {"tipo": tipo, "origem": origem if eh_fragmento(request) else "pagina"}
    if produto:
        inicial["produto"] = produto.pk
    if (quantidade := quantidade_valida(request.GET.get("quantidade"))) is not None:
        inicial["quantidade"] = str(quantidade)
    return MovimentacaoForm(initial=inicial), produto, inicial["origem"]


def _render_form(request, contexto: dict, status: int = 200):
    if eh_fragmento(request):
        return render(request, "movimentacoes/partials/form_movimentacao.html", contexto,
                      status=status)  # fmt: skip
    return render(request, "movimentacoes/nova.html", contexto, status=status)


@require_http_methods(["GET", "HEAD", "POST"])
@vary_on_headers("HX-Request", "HX-Target")
def nova_movimentacao(request):
    if request.method == "POST":
        return _registrar(request)
    alvo = request.htmx.target if eh_fragmento(request) else None
    if alvo == "previa-saldo":
        produto = _produto_da_url(request.GET.get("produto"))
        quantidade = quantidade_valida(request.GET.get("quantidade"))
        contexto = {"previa": _previa(produto, request.GET.get("tipo"), quantidade)}
        return render(request, "movimentacoes/partials/previa_saldo.html", contexto)
    form, produto, _origem = _form_inicial(request)
    if alvo == "dialogo":
        modo = "dialogo" if produto else "pagina"
        contexto = _contexto_form(form, produto, modo)
        return render(request, "movimentacoes/partials/dialogo_movimentacao.html", contexto)
    return render(request, "movimentacoes/nova.html", _contexto_form(form, produto, "pagina"))


def _registrar(request):
    form = MovimentacaoForm(request.POST)
    produto = _produto_da_url(request.POST.get("produto"))
    origem = request.POST.get("origem") if request.POST.get("origem") in (
        "lista", "detalhe", "alertas") else "pagina"  # fmt: skip
    modo = "dialogo" if origem != "pagina" and produto else "pagina"
    if form.is_valid():
        dados = form.cleaned_data
        try:
            mov = registrar_movimentacao(
                produto_id=dados["produto"].pk,
                tipo=dados["tipo"],
                quantidade=dados["quantidade"],
                observacao=dados["observacao"],
            )
        except (EstoqueInsuficienteError, SaldoMaximoExcedidoError) as erro:
            form.add_error("quantidade", str(erro))
        except MovimentacaoInvalidaError as erro:
            form.add_error(None, str(erro))
        except MovimentacaoError as erro:  # pragma: no cover — hierarquia completa acima
            form.add_error(None, str(erro))
        else:
            return _sucesso(request, mov, origem)
    form.ajustar_foco()
    produto = _produto_da_url(request.POST.get("produto"))
    return _render_form(request, _contexto_form(form, produto, modo), status=422)


def _sucesso(request, mov, origem: str):
    from apps.alertas.regras import confirmacao_com_alerta

    produto = Produto.objects.com_situacao().get(pk=mov.produto_id)
    # Feature 004: a confirmação ganha o aviso de reposição quando a situação muda.
    aviso = confirmacao_com_alerta(mov)
    if not eh_fragmento(request):
        nivel = messages.WARNING if aviso.nivel == "alerta" else messages.SUCCESS
        messages.add_message(request, nivel, aviso.texto)
        destino = (
            reverse("movimentacoes:nova")
            + "?"
            + urlencode({"produto": produto.pk, "tipo": mov.tipo})
        )
        return redirect(destino)
    carga = {
        "produto_id": produto.pk,
        "saldo_anterior": mov.saldo_anterior,
        "saldo_posterior": mov.saldo_posterior,
    }
    if origem == "pagina":
        form = MovimentacaoForm(initial={"produto": produto.pk, "tipo": mov.tipo,
                                         "origem": "pagina"})  # fmt: skip
        resposta = render(request, "movimentacoes/partials/form_movimentacao.html",
                          _contexto_form(form, produto, "pagina"))  # fmt: skip
    else:
        resposta = render(request, "movimentacoes/partials/sucesso_dialogo.html",
                          {"produto": produto, "origem": origem})  # fmt: skip
        resposta = reswap(resposta, "none")
        disparar_evento(resposta, "fechar-dialogo")
    disparar_evento(resposta, "estoque-alterado", carga)
    return disparar_toast(resposta, aviso.nivel, aviso.texto)
