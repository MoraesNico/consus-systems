"""Regra de alerta de reposição em Python puro (data-model §3).

Espelha as anotações de `ProdutoQuerySet.com_situacao()`; um teste de equivalência garante que
banco e Python nunca divirjam. Item 3 da atividade: quantidade atual ≤ estoque mínimo ⇒ alerta.
"""

import enum
from dataclasses import dataclass

from apps.produtos.models import QUANTIDADE_MAXIMA

FATOR_ESTOQUE_ALVO = 2
TEXTO_MAXIMO = 200  # limite de disparar_toast (001)


class Situacao(enum.StrEnum):
    OK = "OK"
    REPOSICAO_NECESSARIA = "REPOSICAO_NECESSARIA"
    SEM_ESTOQUE = "SEM_ESTOQUE"

    @property
    def rotulo(self) -> str:
        return {"OK": "OK", "REPOSICAO_NECESSARIA": "REPOSIÇÃO NECESSÁRIA",
                "SEM_ESTOQUE": "SEM ESTOQUE"}[self.value]  # fmt: skip

    @property
    def gravidade(self) -> int:
        return {"OK": 0, "REPOSICAO_NECESSARIA": 1, "SEM_ESTOQUE": 2}[self.value]

    @property
    def variante(self) -> str:
        """Vocabulário de `badge_estoque` e do `tom` de `barra_progresso` (001)."""
        return {"OK": "ok", "REPOSICAO_NECESSARIA": "reposicao",
                "SEM_ESTOQUE": "sem_estoque"}[self.value]  # fmt: skip


class Transicao(enum.StrEnum):
    PIOROU = "PIOROU"
    SAIU_DO_ALERTA = "SAIU_DO_ALERTA"
    NENHUMA = "NENHUMA"


@dataclass(frozen=True)
class Aviso:
    nivel: str  # "sucesso" | "alerta"
    texto: str


def classificar(quantidade: int, minimo: int) -> Situacao:
    if quantidade == 0:
        return Situacao.SEM_ESTOQUE
    if quantidade <= minimo:
        return Situacao.REPOSICAO_NECESSARIA
    return Situacao.OK


def deficit(quantidade: int, minimo: int) -> int:
    return max(minimo - quantidade, 0)


def cobertura_percentual(quantidade: int, minimo: int) -> int | None:
    if quantidade == 0:
        return 0
    if minimo == 0:
        return None  # não se aplica
    return quantidade * 100 // minimo


def sugestao_reposicao(quantidade: int, minimo: int) -> int | None:
    """Repor até o dobro do mínimo (pelo menos 1), sem passar do teto de saldo."""
    if classificar(quantidade, minimo) is Situacao.OK:
        return None
    alvo = max(FATOR_ESTOQUE_ALVO * minimo - quantidade, 1)
    return min(alvo, QUANTIDADE_MAXIMA - quantidade)


def transicao(saldo_anterior: int, saldo_posterior: int, minimo: int) -> Transicao:
    antes = classificar(saldo_anterior, minimo)
    depois = classificar(saldo_posterior, minimo)
    if depois is Situacao.OK and antes is not Situacao.OK:
        return Transicao.SAIU_DO_ALERTA
    if antes is not Situacao.SEM_ESTOQUE and depois.gravidade > antes.gravidade:
        return Transicao.PIOROU
    return Transicao.NENHUMA


def _texto_aviso(movimentacao, nome: str) -> str | None:
    produto = movimentacao.produto
    codigo = f"{produto.codigo} {nome}"
    resultado = transicao(
        movimentacao.saldo_anterior, movimentacao.saldo_posterior, produto.estoque_minimo
    )
    if resultado is Transicao.SAIU_DO_ALERTA:
        return f"{codigo} saiu do alerta de reposição."
    if resultado is Transicao.PIOROU:
        minimo = _numero(produto.estoque_minimo)
        if movimentacao.saldo_posterior == 0:
            return f"REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE: {codigo} zerou (mínimo {minimo})."
        saldo = _numero(movimentacao.saldo_posterior)
        return f"REPOSIÇÃO NECESSÁRIA: {codigo} ficou com {saldo} un. (mínimo {minimo})."
    return None


def _numero(valor: int) -> str:
    from django.utils.formats import number_format

    return number_format(valor, force_grouping=True)


def aviso_movimentacao(movimentacao) -> Aviso | None:
    if movimentacao.tipo == "INICIAL":
        return None
    texto = _texto_aviso(movimentacao, movimentacao.produto.nome)
    if texto is None:
        return None
    nivel = "sucesso" if "saiu do alerta" in texto else "alerta"
    return Aviso(nivel, texto)


def confirmacao_com_alerta(movimentacao) -> Aviso:
    """Mensagem de confirmação da 003 + aviso de reposição (≤ 200 caracteres)."""
    base = movimentacao.mensagem_confirmacao
    aviso = aviso_movimentacao(movimentacao)
    if aviso is None:
        return Aviso("sucesso", base)
    texto = f"{base}. {aviso.texto}"
    nome = movimentacao.produto.nome
    while len(texto) > TEXTO_MAXIMO and len(nome) > 1:
        nome = nome[: max(len(nome) - (len(texto) - TEXTO_MAXIMO) // 2 - 1, 1)]
        curto = nome + "…"
        texto = f"{base.replace(movimentacao.produto.nome, curto)}. " + (
            _texto_aviso(movimentacao, curto) or ""
        )
    return Aviso(aviso.nivel, texto[:TEXTO_MAXIMO])
