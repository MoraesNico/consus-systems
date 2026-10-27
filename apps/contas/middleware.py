"""Login obrigatório em todas as páginas, exceto `contas:entrar` e `core:saude`."""

from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.contrib.auth.views import redirect_to_login
from django_htmx.http import HttpResponseClientRedirect


class LoginObrigatorioMiddleware(LoginRequiredMiddleware):
    def handle_no_permission(self, request, view_func):
        if getattr(request, "htmx", False):
            destino = redirect_to_login(
                request.htmx.current_url_abs_path or request.get_full_path(),
                self.get_login_url(view_func),
                self.get_redirect_field_name(view_func),
            )
            return HttpResponseClientRedirect(destino["Location"])
        return super().handle_no_permission(request, view_func)
