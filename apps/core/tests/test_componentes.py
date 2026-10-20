"""Componentes do design system (FR-027, FR-028, FR-029)."""

import re
from pathlib import Path

import pytest
from django import forms
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory

RAIZ = Path(__file__).resolve().parents[3]
COMPONENTES = RAIZ / "templates" / "components"
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")


def render(nome: str, **contexto) -> str:
    return render_to_string(f"components/{nome}.html", contexto)


def test_fr027_templates_renderizam():
    """FR-027: os 16 templates de componentes existem e renderizam sem erro."""
    nomes = [
        "icone", "campo", "formulario", "badge_estoque", "delta", "kpi", "lista_barras",
        "barra_categorias", "rastreador", "barra_progresso", "dialogo", "toast", "aviso",
        "estado_vazio", "paginacao", "navegacao",
    ]  # fmt: skip
    for nome in nomes:
        assert (COMPONENTES / f"{nome}.html").is_file(), nome
    request = RequestFactory().get("/")
    request.htmx = False
    assert "dialogo-titulo" in render_to_string("components/dialogo.html", {}, request=request)


def test_fr027_classes_de_componentes_no_css():
    """FR-027: components.css define a API de classes documentada."""
    css = (RAIZ / "static" / "css" / "components.css").read_text()
    for classe in (
        ".botao--primario", ".botao--secundario", ".botao--fantasma", ".botao--perigo",
        ".tabela", ".tabela--compacta", ".badge", ".badge--info", ".badge--sucesso",
        ".badge--alerta", ".badge--perigo", ".cartao--interativo",
    ):  # fmt: skip
        assert classe in css, classe


class FormularioTeste(forms.Form):
    nome = forms.CharField(label="Nome", help_text="Como aparece na nota fiscal.")
    observacao = forms.CharField(label="Observação", required=False)


def test_fr027_campo_acessivel_com_erro():
    """FR-027: rótulo ligado, aria-describedby com ajuda e erro, aria-invalid, "(opcional)"."""
    form = FormularioTeste(data={"nome": ""})
    html = str(form)
    assert '<label class="campo__rotulo" for="id_nome">' in html
    entrada = re.search(r'<input[^>]+name="nome"[^>]*>', html).group(0)
    assert 'aria-invalid="true"' in entrada
    descrito = re.search(r'aria-describedby="([^"]+)"', entrada).group(1).split()
    assert "id_nome_helptext" in descrito and "id_nome_error" in descrito
    assert 'id="id_nome_error"' in html
    assert "(opcional)" in html.split('for="id_observacao"', 1)[1]
    assert 'class="aviso aviso--erro"' in html


def test_fr027_paginacao():
    """FR-027: "1–25 de 132 produtos", aria-label, preserva busca e some com uma página."""
    request = RequestFactory().get("/produtos/", {"q": "parafuso", "pagina": "1"})
    pagina = Paginator(range(132), 25).page(1)
    html = render_to_string(
        "components/paginacao.html",
        {"pagina": pagina, "rotulo_itens": "produtos", "alvo": "#resultados"},
        request=request,
    )
    texto = re.sub(r"<[^>]+>", "", html)
    assert "1–25 de 132 produtos" in re.sub(r"\s+", " ", texto)
    assert 'aria-label="Paginação"' in html
    assert "q=parafuso" in html and "pagina=2" in html
    assert 'hx-target="#resultados"' in html and 'hx-push-url="true"' in html
    unica = Paginator(range(10), 25).page(1)
    assert render_to_string("components/paginacao.html", {"pagina": unica}).strip() == ""


def test_fr027_delta_kpi_barras():
    """FR-027: delta com "−" tipográfico, KPI sem dado, BarList com mínimo de 2 %."""
    delta = render("delta", valor=-5, sentido="negativo")
    assert "−5" in delta and "redução de 5" in delta and "delta--negativo" in delta
    assert "aumento de 3" in render("delta", valor=3, sentido="positivo")
    assert "—" in render("kpi", rotulo="Produtos", valor=None)
    kpi = render("kpi", rotulo="Em alerta", valor=1240, href="/alertas/", destaque="alerta")
    assert "cartao--interativo" in kpi and "1.240" in kpi and "kpi--alerta" in kpi
    barras = render(
        "lista_barras",
        titulo="Mais movimentados",
        rotulo_valor="Unidades",
        itens=[{"rotulo": "A", "valor": 1000}, {"rotulo": "B", "valor": 1}],
    )
    assert "--valor: 100" in barras and "--valor: 2" in barras


def test_fr027_categorias_rastreador_progresso():
    """FR-027: CategoryBar com legenda, Tracker role=img, ProgressBar role=meter."""
    categorias = render(
        "barra_categorias",
        titulo="Situação",
        total=4,
        unidade="produtos",
        segmentos=[
            {"rotulo": "OK", "valor": 3, "tom": "ok"},
            {"rotulo": "Alerta", "valor": 1, "tom": "reposicao"},
        ],
    )
    assert 'aria-hidden="true"' in categorias and "(75%)" in categorias and "(25%)" in categorias
    rastreador = render(
        "rastreador",
        titulo="30 dias",
        blocos=[{"tom": "acento", "rotulo": "x"}],
        resumo="1 dia com movimentação",
    )
    assert 'role="img" aria-label="1 dia com movimentação"' in rastreador
    progresso = render("barra_progresso", rotulo="Saldo", valor=80, maximo=50, tom="ok")
    assert 'role="meter"' in progresso and 'aria-valuenow="80"' in progresso
    assert "--valor: 100" in progresso


@pytest.mark.parametrize(
    ("situacao", "esperado", "icone"),
    [
        ("ok", "OK", "circle-check"),
        ("reposicao", "REPOSIÇÃO NECESSÁRIA", "triangle-alert"),
    ],
)
def test_fr028_badge_estoque(situacao, esperado, icone):
    """FR-028: badge de situação com texto, ícone e nome acessível."""
    html = render("badge_estoque", situacao=situacao)
    assert esperado in html and f"#{icone}" in html and 'aria-label="Situação:' in html
    assert "⚠" not in html


def test_fr028_badge_sem_estoque_mantem_alerta():
    """FR-028: sem_estoque é composto e mantém "REPOSIÇÃO NECESSÁRIA" + "SEM ESTOQUE"."""
    html = render("badge_estoque", situacao="sem_estoque")
    assert "REPOSIÇÃO NECESSÁRIA" in html and "SEM ESTOQUE" in html
    assert "badge-composto" in html
    assert render("badge_estoque", situacao="desconhecida").strip() == ""


def test_fr029_icone_decorativo_e_rotulado():
    """FR-029: ícone decorativo é aria-hidden; com rótulo vira role=img com <title>."""
    decorativo = render("icone", nome="plus")
    assert 'aria-hidden="true"' in decorativo and "#plus" in decorativo
    rotulado = render("icone", nome="triangle-alert", rotulo="Alerta")
    assert 'role="img"' in rotulado and "<title>Alerta</title>" in rotulado


def test_fr029_nenhum_emoji_nos_templates():
    """FR-029: nenhum emoji usado como ícone nos templates."""
    for arquivo in [*RAIZ.glob("templates/**/*.html"), *RAIZ.glob("apps/**/templates/**/*.html")]:
        assert not EMOJI.search(arquivo.read_text()), arquivo
