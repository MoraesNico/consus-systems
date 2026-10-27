"""Serialização única do resultado da varredura: CSV (web e terminal), texto e JSON."""

import json

from django.utils import timezone
from django.utils.formats import number_format

from apps.core.csv import montar_csv, proteger_celula

from .regras import Situacao
from .selectors import ResultadoVarredura

COLUNAS = (
    "ID",
    "Produto",
    "Quantidade atual",
    "Estoque mínimo",
    "Déficit",
    "Cobertura (%)",
    "Sugestão de reposição",
    "Situação",
)
LARGURA_NOME = 40
_seguro = proteger_celula


def _vazio_se_none(valor) -> str:
    return "" if valor is None else str(valor)


def para_csv(resultado: ResultadoVarredura, *, bom: bool) -> str:
    linhas = (
        [
            p.codigo,
            _seguro(p.nome),
            p.quantidade_atual,
            p.estoque_minimo,
            p.deficit,
            _vazio_se_none(p.cobertura_percentual),
            _vazio_se_none(p.sugestao_reposicao),
            p.situacao_estoque.rotulo,
        ]
        for p in resultado.itens
    )
    return montar_csv(COLUNAS, linhas, bom=bom)


def nome_arquivo_csv(resultado: ResultadoVarredura) -> str:
    return f"reposicao-{timezone.localtime(resultado.executada_em):%Y%m%d-%H%M}.csv"


def para_json(resultado: ResultadoVarredura) -> str:
    dados = {
        "executada_em": timezone.localtime(resultado.executada_em).isoformat(timespec="seconds"),
        "total_analisado": resultado.total_analisado,
        "total_em_alerta": resultado.total_em_alerta,
        "total_sem_estoque": resultado.total_sem_estoque,
        "itens": [
            {
                "id": p.pk,
                "codigo": p.codigo,
                "nome": p.nome,
                "quantidade_atual": p.quantidade_atual,
                "estoque_minimo": p.estoque_minimo,
                "deficit": p.deficit,
                "cobertura_percentual": p.cobertura_percentual,
                "sugestao_reposicao": p.sugestao_reposicao,
                "situacao": p.situacao_estoque.value,
                "situacao_rotulo": p.situacao_estoque.rotulo,
            }
            for p in resultado.itens
        ],
    }
    return json.dumps(dados, ensure_ascii=False, indent=2)


def _n(valor: int) -> str:
    return number_format(valor, force_grouping=True)


def para_texto(resultado: ResultadoVarredura, *, simbolo: str = "⚠") -> list[tuple[str, bool]]:
    """Linhas do relatório de terminal: (texto, é_alerta)."""
    momento = timezone.localtime(resultado.executada_em)
    linhas: list[tuple[str, bool]] = [
        ("CONSUS — VARREDURA DE ESTOQUE", False),
        (f"Executada em {momento:%d/%m/%Y %H:%M}", False),
        (f"Produtos analisados: {_n(resultado.total_analisado)}", False),
        (
            f"Em alerta: {_n(resultado.total_em_alerta)} "
            f"({_n(resultado.total_sem_estoque)} sem estoque)",
            False,
        ),
        ("", False),
    ]
    if resultado.sem_produtos:
        linhas.append(("Nenhum produto cadastrado.", False))
        return linhas
    if resultado.sem_alertas and not resultado.itens:
        linhas.append(("Nenhum produto precisa de reposição.", False))
        return linhas
    largura_rotulo = len(f"{simbolo} REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE")
    for p in resultado.itens:
        situacao = p.situacao_estoque
        if situacao is Situacao.OK:
            rotulo = "OK"
        elif situacao is Situacao.SEM_ESTOQUE:
            rotulo = f"{simbolo} REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE"
        else:
            rotulo = f"{simbolo} REPOSIÇÃO NECESSÁRIA"
        nome = p.nome if len(p.nome) <= LARGURA_NOME else p.nome[: LARGURA_NOME - 1] + "…"
        detalhe = f"atual {_n(p.quantidade_atual)} / mín. {_n(p.estoque_minimo)}"
        linha = f"{rotulo:<{largura_rotulo}}  {p.codigo:<6} {nome:<{LARGURA_NOME}}  {detalhe:<26}"
        if situacao is not Situacao.OK:
            linha += f"  déficit {_n(p.deficit):<6}  repor {_n(p.sugestao_reposicao or 0)}"
        linhas.append((linha.rstrip(), situacao is not Situacao.OK))
    if resultado.sem_alertas:
        linhas.append(("Nenhum produto precisa de reposição.", False))
    return linhas
