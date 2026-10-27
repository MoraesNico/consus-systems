"""Entrar, sair e trocar senha (docs/arquitetura.md v1.2, "Autenticação")."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST
from django_htmx.http import HttpResponseClientRedirect

from .forms import EntrarForm
from .models import TentativaAcesso, minutos_de_bloqueio


def _ip(request) -> str | None:
    return request.META.get("REMOTE_ADDR") or None


def _destino_seguro(request) -> str:
    destino = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return resolve_url(settings.LOGIN_REDIRECT_URL)


def _render(request, form, status=200, bloqueio=0):
    contexto = {
        "form": form,
        "next": request.POST.get("next") or request.GET.get("next") or "",
        "bloqueio": bloqueio,
        "demo": getattr(settings, "CONSUS_DEMO", False),
    }
    modelo = "contas/partials/cartao.html" if request.htmx else "contas/entrar.html"
    return render(request, modelo, contexto, status=status)


@login_not_required
@never_cache
@csrf_protect
@require_http_methods(["GET", "HEAD", "POST"])
def entrar(request):
    if request.method != "POST":
        if request.user.is_authenticated:
            return redirect(_destino_seguro(request))
        return _render(request, EntrarForm(request))
    nome = (request.POST.get("usuario") or "").strip()
    ip = _ip(request)
    minutos = minutos_de_bloqueio(nome, ip)
    form = EntrarForm(request, data=request.POST)
    if minutos:
        form.is_valid()
        form.errors.clear()
        return _render(request, form, status=429, bloqueio=minutos)
    if not form.is_valid():
        if nome and "__all__" in form.errors:
            TentativaAcesso.objects.create(usuario=nome.lower(), ip=ip)
        return _render(request, form, status=422)
    usuario = form.usuario_autenticado
    login(request, usuario)
    TentativaAcesso.objects.filter(usuario=nome.lower()).delete()
    request.session.set_expiry(settings.SESSION_COOKIE_AGE if form.cleaned_data["lembrar"] else 0)
    nome_exibicao = usuario.get_short_name() or usuario.get_username()
    messages.success(request, f"Olá, {nome_exibicao}! Sessão iniciada.")
    destino = _destino_seguro(request)
    if request.htmx:
        return HttpResponseClientRedirect(destino)
    return redirect(destino)


@require_POST
def sair(request):
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@require_http_methods(["GET", "HEAD", "POST"])
def trocar_senha(request):
    form = PasswordChangeForm(request.user, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            update_session_auth_hash(request, form.save())
            messages.success(request, "Senha alterada.")
            return redirect("core:painel")
        return render(request, "contas/trocar_senha.html", {"form": form}, status=422)
    return render(request, "contas/trocar_senha.html", {"form": form})
