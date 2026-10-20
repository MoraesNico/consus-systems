"""Escrita de produtos: cadastro e edição (contracts/servicos-e-consultas.md).

Toda validação de domínio vive aqui; formulários apenas convertem texto em valores.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Value
from django.db.models.functions import Lower
from django.utils.formats import number_format

from .models import QUANTIDADE_MAXIMA, Produto

NOME_MAXIMO = 120

MENSAGENS = {
    "nome_obrigatorio": "Informe o nome do produto.",
    "nome_longo": f"O nome deve ter no máximo {NOME_MAXIMO} caracteres.",
    "nome_duplicado": "Já existe um produto com este nome ({codigo}).",
    "inteiro_invalido": "Informe um número inteiro igual ou maior que zero.",
    "inteiro_maximo": "Informe um valor de no máximo {maximo}.",
}


def normalizar_nome(valor: str | None) -> str:
    """Remove espaços das extremidades e colapsa espaços internos (FR-004)."""
    return " ".join((valor or "").split())


def _produto_com_nome(nome: str, excluir_pk: int | None = None) -> Produto | None:
    consulta = Produto.objects.annotate(nome_ci=Lower("nome")).filter(nome_ci=Lower(Value(nome)))
    if excluir_pk is not None:
        consulta = consulta.exclude(pk=excluir_pk)
    return consulta.first()


def _nome_em_uso(nome: str, excluir_pk: int | None = None) -> bool:
    return _produto_com_nome(nome, excluir_pk) is not None


def _erro_nome_duplicado(nome: str, excluir_pk: int | None = None) -> ValidationError:
    existente = _produto_com_nome(nome, excluir_pk)
    codigo = existente.codigo if existente else "?"
    return ValidationError(
        {"nome": ValidationError(MENSAGENS["nome_duplicado"].format(codigo=codigo),
                                 code="nome_duplicado")}
    )  # fmt: skip


def _validar_nome(nome: str, erros: dict) -> None:
    if not nome:
        erros["nome"] = ValidationError(MENSAGENS["nome_obrigatorio"], code="nome_obrigatorio")
    elif len(nome) > NOME_MAXIMO:
        erros["nome"] = ValidationError(MENSAGENS["nome_longo"], code="nome_longo")


def _validar_inteiro(campo: str, valor, erros: dict) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        erros[campo] = ValidationError(MENSAGENS["inteiro_invalido"], code="inteiro_invalido")
    elif valor > QUANTIDADE_MAXIMA:
        maximo = number_format(QUANTIDADE_MAXIMA, force_grouping=True)
        erros[campo] = ValidationError(
            MENSAGENS["inteiro_maximo"].format(maximo=maximo), code="inteiro_maximo"
        )


def cadastrar_produto(*, nome: str, quantidade_inicial: int, estoque_minimo: int) -> Produto:
    """Cadastra um produto (FR-001, FR-029).

    Com a feature 003, a Quantidade Inicial é registrada como a movimentação `INICIAL`, na mesma
    transação (FR-027 da 003; FR-030 da 002): assinatura e pós-condições preservadas.
    """
    nome = normalizar_nome(nome)
    erros: dict = {}
    _validar_nome(nome, erros)
    _validar_inteiro("quantidade_inicial", quantidade_inicial, erros)
    _validar_inteiro("estoque_minimo", estoque_minimo, erros)
    if "nome" not in erros and _nome_em_uso(nome):
        raise _erro_nome_duplicado(nome)
    if erros:
        raise ValidationError(erros)
    # Importação tardia: movimentacoes depende de produtos (evita ciclo no carregamento).
    from apps.movimentacoes import services as servicos_mov
    from apps.movimentacoes.models import TipoMovimentacao

    try:
        with transaction.atomic():
            # O produto nasce com saldo 0; a Quantidade Inicial entra como movimentação INICIAL.
            produto = Produto.objects.create(
                nome=nome, quantidade_atual=0, estoque_minimo=estoque_minimo
            )
            servicos_mov.registrar_movimentacao(
                produto_id=produto.pk, tipo=TipoMovimentacao.INICIAL, quantidade=quantidade_inicial
            )
            produto.refresh_from_db()
            return produto
    except IntegrityError as erro:
        if "produto_nome_unico_ci" in str(erro) or "UNIQUE" in str(erro).upper():
            raise _erro_nome_duplicado(nome) from erro
        raise


def editar_produto(*, produto_id: int, nome: str, estoque_minimo: int) -> Produto:
    """Altera nome e estoque mínimo; nunca a quantidade (FR-024, FR-025)."""
    nome = normalizar_nome(nome)
    erros: dict = {}
    _validar_nome(nome, erros)
    _validar_inteiro("estoque_minimo", estoque_minimo, erros)
    with transaction.atomic():
        produto = Produto.objects.select_for_update().get(pk=produto_id)
        if "nome" not in erros and _nome_em_uso(nome, excluir_pk=produto.pk):
            raise _erro_nome_duplicado(nome, excluir_pk=produto.pk)
        if erros:
            raise ValidationError(erros)
        produto.nome = nome
        produto.estoque_minimo = estoque_minimo
        try:
            with transaction.atomic():
                produto.save(update_fields=["nome", "estoque_minimo", "atualizado_em"])
        except IntegrityError as erro:
            raise _erro_nome_duplicado(nome, excluir_pk=produto.pk) from erro
    return produto
