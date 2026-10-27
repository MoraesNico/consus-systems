"""Leitura de produtos: lista com busca, filtro e ordenação (contracts/servicos-e-consultas.md)."""

from django.db.models import F, QuerySet
from django.db.models.functions import Lower

from .models import ID_MAXIMO, Produto

ORDEM_PADRAO = "-id"
POR_PAGINA = 25
SITUACOES_VALIDAS = {"alerta", "ok"}
_EXPRESSOES = {
    "id": F("id"),
    "nome": Lower("nome"),
    "quantidade": F("quantidade_atual"),
    "minimo": F("estoque_minimo"),
    "margem": F("margem"),
    "situacao": F("alerta"),  # crescente = em alerta primeiro (ver _expressao)
}
ORDENS_VALIDAS = set(_EXPRESSOES)


def normalizar_ordem(ordem: str | None) -> str:
    ordem = (ordem or "").strip()
    return (
        ordem
        if ordem.removeprefix("-") in ORDENS_VALIDAS and ordem.count("-") <= 1
        else ORDEM_PADRAO
    )


def normalizar_situacao(situacao: str | None) -> str:
    return situacao if situacao in SITUACOES_VALIDAS else ""


def _expressao(ordem: str):
    chave = ordem.removeprefix("-")
    descendente = ordem.startswith("-")
    if chave == "situacao":
        return F("alerta").asc() if descendente else F("alerta").desc()
    expressao = _EXPRESSOES[chave]
    return expressao.desc() if descendente else expressao.asc()


def listar_produtos(
    *, q: str | None = "", situacao: str = "", ordem: str = ""
) -> QuerySet[Produto]:
    qs = Produto.objects.com_situacao().com_financeiro().buscar(q)
    situacao = normalizar_situacao(situacao)
    if situacao == "alerta":
        qs = qs.em_alerta()
    elif situacao == "ok":
        qs = qs.sem_alerta()
    ordem = normalizar_ordem(ordem)
    criterios = [_expressao(ordem)]
    if ordem.removeprefix("-") != "id":
        criterios.append(F("id").desc())
    return qs.order_by(*criterios)


def obter_produto(produto_id: int) -> Produto:
    """Lança Produto.DoesNotExist, inclusive para IDs acima do máximo do BigAutoField."""
    if not 0 < produto_id <= ID_MAXIMO:
        raise Produto.DoesNotExist
    return Produto.objects.com_situacao().com_financeiro().get(pk=produto_id)
