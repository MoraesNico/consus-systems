"""Views de produtos (contracts/rotas-http.md).

Cada rota atende a navegação comum/boosted (página completa, 302 após POST) e requisições
parciais HTMX identificadas pelo alvo (`resultados` ou `dialogo`). Erros de validação: 422.
"""

from urllib.parse import urlparse

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.vary import vary_on_headers
from django_htmx.http import HttpResponseClientRedirect, push_url, reswap, retarget

from apps.core.htmx import disparar_evento, disparar_toast, eh_fragmento

from .forms import ProdutoEdicaoForm, ProdutoForm
from .models import Produto
from .selectors import (
    ORDEM_PADRAO,
    POR_PAGINA,
    listar_produtos,
    normalizar_ordem,
    normalizar_situacao,
    obter_produto,
)
from .services import cadastrar_produto, editar_produto, normalizar_nome

CHAVE_DESTAQUE = "produtos_destaque"
COLUNAS = (
    ("ID", "id", False),
    ("Nome", "nome", False),
    ("Quantidade atual", "quantidade", True),
    ("Estoque mínimo", "minimo", True),
    ("Situação", "situacao", False),
)


def _alvo(request) -> str | None:
    return request.htmx.target if eh_fragmento(request) else None


def _anexar_erros(form, erro: ValidationError) -> None:
    for campo, erros in erro.error_dict.items():
        for item in erros:
            form.add_error(campo if campo in form.fields else None, item)


def _colunas(ordem: str) -> list[dict]:
    colunas = []
    for rotulo, chave, numerica in COLUNAS:
        if ordem == chave:
            aria, nova = "ascending", f"-{chave}"
        elif ordem == f"-{chave}":
            aria, nova = "descending", chave
        else:
            aria, nova = "none", chave
        colunas.append({"rotulo": rotulo, "aria_sort": aria, "nova_ordem": nova, "num": numerica})
    return colunas


def _contexto_lista(parametros, destaque_id=None) -> dict:
    q = normalizar_nome(parametros.get("q"))
    situacao = normalizar_situacao(parametros.get("situacao"))
    ordem = normalizar_ordem(parametros.get("ordem"))
    pagina = Paginator(listar_produtos(q=q, situacao=situacao, ordem=ordem), POR_PAGINA).get_page(
        parametros.get("pagina")
    )
    filtrado = bool(q or situacao)
    # Só consulta o total quando a busca filtrada não achou nada (distingue os estados vazios).
    total_geral = None if pagina.object_list else (Produto.objects.count() if filtrado else 0)
    canonica = {
        "q": q,
        "situacao": situacao,
        "ordem": ordem if ordem != ORDEM_PADRAO else "",
        "pagina": pagina.number if pagina.number > 1 else "",
    }
    query = urlencode({k: v for k, v in canonica.items() if v})
    return {
        "page_obj": pagina,
        "q": q,
        "situacao": situacao,
        "ordem": ordem,
        "filtrado": filtrado,
        "total_geral": total_geral,
        "destaque_id": destaque_id,
        "colunas": _colunas(ordem),
        "url_canonica": reverse("produtos:lista") + (f"?{query}" if query else ""),
    }


@require_safe
@vary_on_headers("HX-Request", "HX-Target")
def lista(request):
    contexto = _contexto_lista(request.GET, destaque_id=request.session.pop(CHAVE_DESTAQUE, None))
    if _alvo(request) == "resultados":
        resposta = render(request, "produtos/partials/lista_parcial.html", contexto)
        return push_url(resposta, contexto["url_canonica"])
    return render(request, "produtos/lista.html", contexto)


def _render_novo(request, form, no_dialogo: bool, status: int = 200):
    if no_dialogo:
        return render(request, "produtos/partials/dialogo_novo.html", {"form": form}, status=status)
    return render(request, "produtos/novo.html", {"form": form}, status=status)


def _sucesso_cadastro(request, produto: Produto, no_dialogo: bool):
    texto = f"Produto {produto.codigo} cadastrado"
    url_lista = reverse("produtos:lista")
    origem = urlparse(request.htmx.current_url or "").path if no_dialogo else ""
    if no_dialogo and origem == url_lista:
        contexto = _contexto_lista({}, destaque_id=produto.pk)
        resposta = render(request, "produtos/partials/sucesso_cadastro.html", contexto)
        resposta = push_url(reswap(retarget(resposta, "#resultados"), "outerHTML"), url_lista)
        disparar_evento(resposta, "estoque-alterado", {"produto_id": produto.pk})
        disparar_evento(resposta, "fechar-dialogo")
        return disparar_toast(resposta, "sucesso", texto)
    messages.success(request, texto)
    request.session[CHAVE_DESTAQUE] = produto.pk
    if no_dialogo:
        return HttpResponseClientRedirect(url_lista)
    return redirect("produtos:lista")


@require_http_methods(["GET", "HEAD", "POST"])
def novo(request):
    no_dialogo = _alvo(request) == "dialogo"
    if request.method != "POST":
        return _render_novo(request, ProdutoForm(), no_dialogo)
    form = ProdutoForm(request.POST)
    if form.is_valid():
        try:
            produto = cadastrar_produto(**form.cleaned_data)
        except ValidationError as erro:
            _anexar_erros(form, erro)
        else:
            return _sucesso_cadastro(request, produto, no_dialogo)
    form.ajustar_foco()
    return _render_novo(request, form, no_dialogo, status=422)


def _nao_encontrado(request):
    return render(request, "produtos/nao_encontrado.html", status=404)


@require_safe
def detalhe(request, produto_id: int):
    try:
        produto = obter_produto(produto_id)
    except Produto.DoesNotExist:
        return _nao_encontrado(request)
    return render(request, "produtos/detalhe.html", {"produto": produto})


@require_http_methods(["GET", "HEAD", "POST"])
def editar(request, produto_id: int):
    try:
        produto = obter_produto(produto_id)
    except Produto.DoesNotExist:
        return _nao_encontrado(request)
    if request.method != "POST":
        form = ProdutoEdicaoForm(
            initial={"nome": produto.nome, "estoque_minimo": produto.estoque_minimo}
        )
        return render(request, "produtos/editar.html", {"form": form, "produto": produto})
    form = ProdutoEdicaoForm(request.POST)
    if form.is_valid():
        try:
            produto = editar_produto(produto_id=produto.pk, **form.cleaned_data)
        except ValidationError as erro:
            _anexar_erros(form, erro)
        except Produto.DoesNotExist:
            return _nao_encontrado(request)
        else:
            messages.success(request, f"Produto {produto.codigo} atualizado")
            return redirect(produto)
    form.ajustar_foco()
    return render(request, "produtos/editar.html", {"form": form, "produto": produto}, status=422)
