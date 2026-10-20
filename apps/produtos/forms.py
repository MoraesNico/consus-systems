"""Formulários de produto: só convertem texto; as regras de domínio estão em services.py."""

import re

from django import forms
from django.core.validators import MaxValueValidator
from django.utils.formats import number_format

from .models import QUANTIDADE_MAXIMA
from .services import MENSAGENS, NOME_MAXIMO, normalizar_nome

_DIGITOS = re.compile(r"^[0-9]+$")


class NomeProdutoField(forms.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("label", "Nome")
        kwargs.setdefault("error_messages", {"required": MENSAGENS["nome_obrigatorio"]})
        super().__init__(strip=False, **kwargs)

    def to_python(self, value):
        return normalizar_nome(super().to_python(value))

    def validate(self, value):
        super().validate(value)
        if len(value) > NOME_MAXIMO:
            raise forms.ValidationError(MENSAGENS["nome_longo"], code="nome_longo")


class InteiroNaoNegativoField(forms.Field):
    """Inteiro ≥ 0 só com dígitos: recusa "1.000", "2,5", "+5", "1e3" (research R2)."""

    widget = forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*",
                                    "autocomplete": "off"})  # fmt: skip

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        maximo = number_format(QUANTIDADE_MAXIMA, force_grouping=True)
        self.validators.append(
            MaxValueValidator(QUANTIDADE_MAXIMA, MENSAGENS["inteiro_maximo"].format(maximo=maximo))
        )

    def to_python(self, value):
        texto = (value or "").strip()
        if not texto:
            return None
        if not _DIGITOS.match(texto):
            raise forms.ValidationError(MENSAGENS["inteiro_invalido"], code="inteiro_invalido")
        return int(texto)


class FocoNoPrimeiroErroMixin:
    """Leva o `autofocus` para o primeiro campo inválido (chamar depois de add_error)."""

    def ajustar_foco(self) -> None:
        if not self.errors:
            return
        primeiro = next((nome for nome in self.fields if nome in self.errors), None)
        for nome, campo in self.fields.items():
            campo.widget.attrs.pop("autofocus", None)
            if nome == primeiro:
                campo.widget.attrs["autofocus"] = True


class ProdutoForm(FocoNoPrimeiroErroMixin, forms.Form):
    nome = NomeProdutoField(help_text="Como aparece na nota fiscal ou no fornecedor.")
    quantidade_inicial = InteiroNaoNegativoField(
        label="Quantidade inicial",
        error_messages={"required": "Informe a quantidade inicial."},
        help_text="Unidades em estoque agora. Depois, o saldo muda só por movimentação.",
    )
    estoque_minimo = InteiroNaoNegativoField(
        label="Estoque mínimo de segurança",
        error_messages={"required": "Informe o estoque mínimo."},
        help_text="Com a quantidade igual ou abaixo deste valor, o produto entra em alerta.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["autofocus"] = True


class ProdutoEdicaoForm(FocoNoPrimeiroErroMixin, forms.Form):
    nome = NomeProdutoField()
    estoque_minimo = InteiroNaoNegativoField(
        label="Estoque mínimo de segurança",
        error_messages={"required": "Informe o estoque mínimo."},
    )
