from django import forms
from django.contrib.auth import authenticate

ERRO_GENERICO = "Usuário ou senha incorretos."


class EntrarForm(forms.Form):
    usuario = forms.CharField(
        label="Usuário",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autocapitalize": "none",
                "spellcheck": "false",
                "autofocus": True,
            }  # fmt: skip
        ),
        error_messages={"required": "Informe o usuário."},
    )
    senha = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        error_messages={"required": "Informe a senha."},
    )
    lembrar = forms.BooleanField(label="Manter conectado por 14 dias", required=False)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.usuario_autenticado = None
        super().__init__(*args, **kwargs)

    def clean(self):
        dados = super().clean()
        if self.errors:
            return dados
        usuario = authenticate(self.request, username=dados["usuario"], password=dados["senha"])
        if usuario is None or not usuario.is_active:
            raise forms.ValidationError(ERRO_GENERICO, code="credenciais")
        self.usuario_autenticado = usuario
        return dados
