"""Cria o saldo INICIAL para produtos cadastrados antes da feature 003 (FR-030).

Usa os modelos históricos (`apps.get_model`), sem as guardas de imutabilidade do modelo atual.
"""

from django.db import migrations


def criar_saldos_iniciais(apps, schema_editor):
    Produto = apps.get_model("produtos", "Produto")
    Movimentacao = apps.get_model("movimentacoes", "Movimentacao")
    sem_historico = Produto.objects.filter(movimentacoes__isnull=True)
    Movimentacao.objects.bulk_create(
        Movimentacao(
            produto=produto,
            tipo="INICIAL",
            quantidade=produto.quantidade_atual,
            saldo_anterior=0,
            saldo_posterior=produto.quantidade_atual,
            observacao="",
            criado_em=produto.criado_em,
        )
        for produto in sem_historico.iterator()
    )


class Migration(migrations.Migration):
    dependencies = [("movimentacoes", "0001_initial"), ("produtos", "0001_initial")]

    operations = [migrations.RunPython(criar_saldos_iniciais, migrations.RunPython.noop)]
