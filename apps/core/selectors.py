"""Leituras do core (verificação de saúde)."""

from django.db import DatabaseError, connections

import config


def estado_saude() -> dict:
    """Testa o banco numa conexão nova (nunca reaproveitada) e resume o estado (data-model §6)."""
    conexao = None
    try:
        conexao = connections.create_connection("default")
        with conexao.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        banco = "ok"
    except DatabaseError:
        banco = "indisponivel"
    finally:
        if conexao is not None:
            conexao.close()
    return {
        "status": "ok" if banco == "ok" else "erro",
        "banco": banco,
        "versao": config.__version__,
    }
