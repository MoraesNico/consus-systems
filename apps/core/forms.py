from django import forms


class FormularioExemplo(forms.Form):
    """Formulário fictício do catálogo: demonstra o padrão 422/sucesso usado por 002 e 003."""

    nome = forms.CharField(
        label="Nome",
        max_length=120,
        help_text="Dado fictício — nada é salvo.",
        error_messages={"required": "Informe o nome."},
    )
    quantidade = forms.IntegerField(
        label="Quantidade",
        min_value=1,
        error_messages={
            "required": "Informe um número inteiro maior que zero.",
            "invalid": "Informe um número inteiro maior que zero.",
            "min_value": "Informe um número inteiro maior que zero.",
        },
        widget=forms.TextInput(attrs={"inputmode": "numeric"}),
    )
