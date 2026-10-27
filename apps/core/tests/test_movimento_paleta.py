"""005 — Movimento, transições e paleta v2 "sóbria"."""

import re
from pathlib import Path

import pytest

from apps.core import design_tokens

RAIZ = Path(__file__).resolve().parents[3]
CSS = RAIZ / "static" / "css"
pytestmark = pytest.mark.django_db


def test_fr001_tokens_de_movimento_e_financeiros():
    tokens = design_tokens.carregar_tokens(CSS / "tokens.css")
    for nome in ("--duration-slow", "--duration-deliberate", "--ease-press", "--motion-distance-sm",
                 "--motion-distance-md", "--color-receita", "--color-despesa",
                 "--color-receita-subtle", "--color-despesa-subtle",
                 *(f"--color-serie-{i}" for i in range(1, 6))):  # fmt: skip
        assert nome in tokens, nome


def test_fr002_movimento_reduzido_zera_duracoes_e_distancias():
    texto = (CSS / "tokens.css").read_text()
    bloco = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\n\}", texto, re.S)
    for nome in ("--duration-slow", "--duration-deliberate", "--motion-distance-md"):
        assert nome in bloco.group(1)
    assert "animation-duration: 0ms !important" in (CSS / "motion.css").read_text()


def test_fr003_keyframes_e_classes():
    texto = (CSS / "motion.css").read_text()
    for nome in ("surgir", "sair", "tremer", "pulsar", "destacar", "crescer-x", "crescer-y",
                 "girar", "carregando"):  # fmt: skip
        assert f"@keyframes consus-{nome}" in texto
    for classe in (".animar-surgir", ".animar-tremer", ".animar-destacar", ".toast--saindo",
                   "@starting-style", "view-transition-name", ".htmx-added"):  # fmt: skip
        assert classe in texto


def test_fr004_casca_carrega_movimento_e_barra(client):
    html = client.get("/").content.decode()
    assert (
        html.index("css/components.css")
        < html.index("css/motion.css")
        < html.index("css/utilities.css")
    )
    assert 'id="barra-carregamento"' in html and 'hx-indicator="#barra-carregamento"' in html
    assert '"globalViewTransitions": true' in html


def test_fr005_toast_sai_animado():
    js = (RAIZ / "static" / "js" / "consus.js").read_text()
    assert "toast--saindo" in js and "animationend" in js


def test_fr006_paleta_sobria_mantem_contraste():
    pares = design_tokens.avaliar_pares()
    assert all(p["aprovado"] for p in pares)
    tokens = design_tokens.tokens_atuais()
    assert tokens["--palette-blue-600"].upper() == "#2F4A78"
