"""Formulários de movimentação e de filtros do livro-razão."""

import re

from django import forms

from apps.produtos.models import Produto

from .models import OBSERVACAO_MAX, QUANTIDADE_MAXIMA_MOVIMENTACAO, TipoMovimentacao
from .services import EstoqueInsuficienteError, SaldoMaximoExcedidoError, formatar_numero

_DIGITOS = re.compile(r"^[0-9]+$")
_NEGATIVO = re.compile(r"^-[0-9]+$")
ORIGENS = ("pagina", "lista", "detalhe", "alertas")


def quantidade_valida(texto: str | None) -> int | None:
    """Converte `?quantidade=` da URL: só dígitos, 1..1.000.000; senão None."""
    texto = (texto or "").strip()
    if _DIGITOS.match(texto) and 1 <= int(texto) <= QUANTIDADE_MAXIMA_MOVIMENTACAO:
        return int(texto)
    return None


class QuantidadeField(forms.Field):
    """Inteiro só com dígitos entre 1 e 1.000.000 (recusa "1.000", "2,5", "+5")."""

    widget = forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*",
                                    "autocomplete": "off"})  # fmt: skip
    default_error_messages = {"required": "Informe a quantidade."}

    def to_python(self, value):
        texto = (value or "").strip()
        if not texto:
            return None
        if _NEGATIVO.match(texto):
            raise forms.ValidationError("Informe uma quantidade maior que zero.", code="minimo")
        if not _DIGITOS.match(texto):
            raise forms.ValidationError(
                "Informe um número inteiro, sem casas decimais nem separadores.", code="inteiro"
            )
        return int(texto)

    def validate(self, value):
        super().validate(value)
        if value is None:
            return
        if value < 1:
            raise forms.ValidationError("Informe uma quantidade maior que zero.", code="minimo")
        if value > QUANTIDADE_MAXIMA_MOVIMENTACAO:
            raise forms.ValidationError(
                f"Informe no máximo {formatar_numero(QUANTIDADE_MAXIMA_MOVIMENTACAO)}.",
                code="maximo",
            )


class ProdutoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Produto) -> str:
        return f"{obj.codigo} — {obj.nome}"


class MovimentacaoForm(forms.Form):
    produto = ProdutoChoiceField(
        label="Produto",
        queryset=Produto.objects.order_by("nome", "id"),
        empty_label="Selecione o produto",
        error_messages={
            "required": "Selecione um produto.",
            "invalid_choice": "Selecione um produto válido.",
        },
    )
    tipo = forms.ChoiceField(
        label="Tipo",
        choices=[
            (TipoMovimentacao.ENTRADA, TipoMovimentacao.ENTRADA.label),
            (TipoMovimentacao.SAIDA, TipoMovimentacao.SAIDA.label),
        ],
        widget=forms.RadioSelect,
        error_messages={
            "required": "Escolha Entrada ou Saída/Venda.",
            "invalid_choice": "Escolha Entrada ou Saída/Venda.",
        },
    )
    quantidade = QuantidadeField(label="Quantidade")
    observacao = forms.CharField(
        label="Observação",
        required=False,
        max_length=OBSERVACAO_MAX,
        strip=True,
        help_text="Ex.: nº da nota, cliente.",
        error_messages={"max_length": f"Use no máximo {OBSERVACAO_MAX} caracteres."},
    )
    origem = forms.ChoiceField(
        choices=[(o, o) for o in ORIGENS], required=False, widget=forms.HiddenInput
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantidade"].widget.attrs["autofocus"] = True

    def clean_origem(self):
        return self.cleaned_data.get("origem") or "pagina"

    def clean(self):
        dados = super().clean()
        produto, tipo, quantidade = (dados.get(c) for c in ("produto", "tipo", "quantidade"))
        if produto and tipo and quantidade:
            # Aviso antecipado com o saldo lido sem bloqueio; o serviço decide sob bloqueio.
            if tipo == TipoMovimentacao.SAIDA and quantidade > produto.quantidade_atual:
                self.add_error(
                    "quantidade",
                    str(EstoqueInsuficienteError(produto.quantidade_atual, quantidade)),
                )
            elif tipo == TipoMovimentacao.ENTRADA:
                try:
                    _verificar_teto(produto.quantidade_atual, quantidade)
                except SaldoMaximoExcedidoError as erro:
                    self.add_error("quantidade", str(erro))
        return dados

    def ajustar_foco(self) -> None:
        primeiro = next((nome for nome in self.fields if nome in self.errors), None)
        if primeiro:
            for nome, campo in self.fields.items():
                campo.widget.attrs.pop("autofocus", None)
                if nome == primeiro:
                    campo.widget.attrs["autofocus"] = True


def _verificar_teto(atual: int, entrada: int) -> None:
    from .models import SALDO_MAXIMO

    if atual + entrada > SALDO_MAXIMO:
        raise SaldoMaximoExcedidoError(atual=atual, entrada=entrada)


class FiltroMovimentacoesForm(forms.Form):
    produto = ProdutoChoiceField(
        queryset=Produto.objects.order_by("nome", "id"),
        required=False,
        empty_label="Todos os produtos",
        label="Produto",
    )
    tipo = forms.ChoiceField(
        choices=[("", "Todos os tipos"), *TipoMovimentacao.choices], required=False, label="Tipo"
    )
    de = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="De",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    ate = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        label="Até",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    AVISOS = {
        "produto": "Produto não encontrado.",
        "tipo": "Tipo de movimentação inválido.",
        "de": "Data inicial inválida.",
        "ate": "Data final inválida.",
    }

    def filtros_validos(self) -> tuple[dict, list[str]]:
        """Filtros aplicáveis e avisos dos inválidos (que são ignorados)."""
        self.is_valid()
        filtros: dict = {}
        avisos: list[str] = []
        dados = self.cleaned_data
        for campo, aviso in self.AVISOS.items():
            if campo in self.errors:
                avisos.append(aviso)
        if dados.get("produto"):
            filtros["produto_id"] = dados["produto"].pk
        if dados.get("tipo"):
            filtros["tipo"] = dados["tipo"]
        de, ate = dados.get("de"), dados.get("ate")
        if de and ate and de > ate:
            avisos.append("A data final deve ser igual ou posterior à inicial.")
        else:
            if de:
                filtros["de"] = de
            if ate:
                filtros["ate"] = ate
        return filtros, avisos
