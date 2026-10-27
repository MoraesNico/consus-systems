from django import forms

from apps.movimentacoes.forms import FiltroMovimentacoesForm

from .models import TipoTransacao


class FiltroTransacoesForm(FiltroMovimentacoesForm):
    tipo = forms.ChoiceField(
        choices=[("", "Todos os tipos"), *TipoTransacao.choices], required=False, label="Tipo"
    )
    AVISOS = {**FiltroMovimentacoesForm.AVISOS, "tipo": "Tipo de transação inválido."}
