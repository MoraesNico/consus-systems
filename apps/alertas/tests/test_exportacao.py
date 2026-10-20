"""Exportação CSV, texto e JSON (FR-027, FR-028, FR-032, FR-033)."""

import json

import pytest

from apps.alertas.exportacao import nome_arquivo_csv, para_csv, para_json, para_texto
from apps.alertas.selectors import varrer

pytestmark = pytest.mark.django_db

CABECALHO = (
    "ID;Produto;Quantidade atual;Estoque mínimo;Déficit;Cobertura (%);Sugestão de reposição;"
    "Situação"
)


def test_fr032_csv_formato(criar_produto):
    """FR-032: ';', CRLF, BOM opcional, inteiros sem separador e nome íntegro."""
    p = criar_produto('Fita "larga"; 48 mm', 1500, 2000)
    texto = para_csv(varrer(), bom=True)
    assert texto.startswith("﻿" + CABECALHO + "\r\n")
    linha = texto.split("\r\n")[1]
    assert linha == f'{p.codigo};"Fita ""larga""; 48 mm";1500;2000;500;75;2500;REPOSIÇÃO NECESSÁRIA'
    assert not para_csv(varrer(), bom=False).startswith("﻿")


def test_fr032_csv_sem_alertas_so_cabecalho(criar_produto):
    """FR-032: sem alertas, só o cabeçalho."""
    criar_produto("Ok", 10, 1)
    assert para_csv(varrer(), bom=False) == CABECALHO + "\r\n"


@pytest.mark.parametrize("prefixo", ["=", "+", "-", "@"])
def test_fr033_protecao_contra_formula(criar_produto, prefixo):
    """FR-033: nomes com cara de fórmula recebem apóstrofo (TAB/CR são aparados no cadastro)."""
    criar_produto(f"{prefixo}1+1 produto", 0, 5)
    linha = para_csv(varrer(), bom=False).split("\r\n")[1]
    assert f";'{prefixo}1+1 produto;" in linha


def test_fr032_nome_do_arquivo(agora, criar_produto):
    """FR-032: reposicao-AAAAMMDD-HHMM.csv em hora local."""
    assert nome_arquivo_csv(varrer()) == "reposicao-20261020-1432.csv"


def test_fr027_texto(cenario, agora):
    """FR-027: relatório de terminal com cabeçalho, totais e uma linha por item."""
    linhas = [linha for linha, _ in para_texto(varrer())]
    assert linhas[:4] == [
        "CONSUS — VARREDURA DE ESTOQUE",
        "Executada em 20/10/2026 14:32",
        "Produtos analisados: 5",
        "Em alerta: 4 (2 sem estoque)",
    ]
    itens = [linha for linha, alerta in para_texto(varrer()) if alerta]
    assert itens[0].startswith("⚠ REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE")
    assert cenario["E"].codigo in itens[0]
    assert itens[2].startswith("⚠ REPOSIÇÃO NECESSÁRIA ") and "SEM ESTOQUE" not in itens[2]
    marcado = [linha for linha, alerta in para_texto(varrer(), simbolo="(!)") if alerta]
    assert marcado[0].startswith("(!) REPOSIÇÃO NECESSÁRIA")


def test_fr027_texto_numeros_e_nomes_longos(criar_produto):
    """FR-027: milhar com ponto e nomes > 40 encurtados com reticências."""
    criar_produto("N" * 50, 1200, 5000)
    item = [linha for linha, alerta in para_texto(varrer()) if alerta][0]
    assert "1.200" in item and "5.000" in item and "N" * 39 + "…" in item


def test_fr027_texto_estados_vazios(criar_produto):
    """FR-027: mensagens de base vazia e sem alertas."""
    assert para_texto(varrer())[-1][0] == "Nenhum produto cadastrado."
    criar_produto("Ok", 10, 1)
    assert para_texto(varrer())[-1][0] == "Nenhum produto precisa de reposição."


def test_fr028_json(cenario, agora):
    """FR-028: JSON com totais e itens tipados."""
    dados = json.loads(para_json(varrer()))
    assert dados["total_analisado"] == 5 and dados["total_em_alerta"] == 4
    assert dados["total_sem_estoque"] == 2
    assert dados["executada_em"].startswith("2026-10-20T14:32")
    primeiro = dados["itens"][0]
    assert primeiro["codigo"] == cenario["E"].codigo and primeiro["situacao"] == "SEM_ESTOQUE"
    assert primeiro["situacao_rotulo"] == "SEM ESTOQUE" and primeiro["sugestao_reposicao"] == 40
