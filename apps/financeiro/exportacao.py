"""CSV do histórico de transações (contrato v1.2: dinheiro como `1234,56`)."""

from django.utils import timezone

from apps.core.csv import montar_csv, proteger_celula
from apps.core.dinheiro import formatar_csv

COLUNAS = (
    "Data/hora",
    "ID do produto",
    "Produto",
    "Tipo",
    "Natureza",
    "Quantidade",
    "Preço unitário",
    "Valor total",
    "Custo total",
)


def para_csv(transacoes, *, bom: bool = True) -> str:
    linhas = (
        [
            timezone.localtime(t.criado_em).strftime("%d/%m/%Y %H:%M"),
            t.produto.codigo,
            proteger_celula(t.produto.nome),
            t.get_tipo_display(),
            t.natureza,
            t.quantidade,
            formatar_csv(t.preco_unitario),
            formatar_csv(t.valor_total),
            formatar_csv(t.custo_total),
        ]
        for t in transacoes
    )
    return montar_csv(COLUNAS, linhas, bom=bom)


def nome_arquivo_csv(agora=None) -> str:
    return f"transacoes-{timezone.localtime(agora or timezone.now()):%Y%m%d-%H%M}.csv"
