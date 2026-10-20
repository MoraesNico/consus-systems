"""Assets vendorizados e ausência de CDN (FR-008, FR-026, FR-029, SC-010)."""

import re
from pathlib import Path

from django.conf import settings

RAIZ = Path(__file__).resolve().parents[3]
ESTATICOS = RAIZ / "static"
FONTES = [
    "IBMPlexSans-Regular-Latin1.woff2",
    "IBMPlexSans-Medium-Latin1.woff2",
    "IBMPlexSans-SemiBold-Latin1.woff2",
    "IBMPlexMono-Regular-Latin1.woff2",
    "IBMPlexMono-SemiBold-Latin1.woff2",
]
ICONES = [
    "layout-dashboard", "package", "arrow-left-right", "bell", "triangle-alert", "circle-check",
    "info", "octagon-x", "circle-alert", "arrow-down-to-line", "arrow-up-from-line", "arrow-up",
    "arrow-down", "arrow-right", "plus", "search", "x", "chevron-left", "chevron-right",
    "chevron-down", "inbox", "loader-circle", "activity",
]
URL_EXTERNA = re.compile(r"""(?:src|href)=["'](?:https?:)?//|url\(\s*["']?(?:https?:)?//""")


def arquivos_de_interface():
    padroes = [
        RAIZ.glob("templates/**/*.html"),
        RAIZ.glob("apps/**/templates/**/*.html"),
        ESTATICOS.glob("css/**/*.css"),
        ESTATICOS.glob("js/**/*.js"),
    ]
    for padrao in padroes:
        yield from padrao


def test_fr008_assets_locais_presentes():
    """FR-008: HTMX 2.x, fontes, licenças e sprite existem localmente."""
    htmx = (ESTATICOS / "vendor" / "htmx.min.js").read_text()
    assert re.search(r'version:"2\.\d+\.\d+"', htmx)
    for nome in FONTES:
        assert (ESTATICOS / "fonts" / nome).is_file(), nome
    assert (ESTATICOS / "fonts" / "OFL.txt").is_file()
    assert (ESTATICOS / "vendor" / "lucide" / "sprite.svg").is_file()
    assert (ESTATICOS / "vendor" / "lucide" / "LICENSE").is_file()


def test_fr008_nenhuma_url_externa_em_templates_css_js():
    """FR-008: nada é carregado de CDN em tempo de execução."""
    for arquivo in arquivos_de_interface():
        texto = arquivo.read_text()
        assert not URL_EXTERNA.search(texto), arquivo


def test_fr026_fontes_nao_vazias():
    """FR-026: os arquivos de fonte têm conteúdo."""
    for nome in FONTES:
        assert (ESTATICOS / "fonts" / nome).stat().st_size > 1000, nome


def test_fr029_sprite_contem_todos_os_icones():
    """FR-029: o sprite tem um <symbol> para cada ícone do design system §2.13."""
    sprite = (ESTATICOS / "vendor" / "lucide" / "sprite.svg").read_text()
    for nome in ICONES:
        assert f'<symbol id="{nome}" viewBox="0 0 24 24">' in sprite, nome
    assert "stroke=" not in sprite and "fill=" not in sprite


def test_sc010_orcamento_de_peso_e_manifesto():
    """SC-010: CSS + JS + HTMX + sprite + fontes ≤ 300 KB; estáticos com manifesto (hash)."""
    arquivos = [
        *ESTATICOS.glob("css/*.css"),
        ESTATICOS / "js" / "consus.js",
        ESTATICOS / "vendor" / "htmx.min.js",
        ESTATICOS / "vendor" / "lucide" / "sprite.svg",
        *(ESTATICOS / "fonts" / nome for nome in FONTES),
    ]
    total = sum(arquivo.stat().st_size for arquivo in arquivos)
    assert total <= 300 * 1024, total
    texto_settings = (RAIZ / "config" / "settings.py").read_text()
    assert "CompressedManifestStaticFilesStorage" in texto_settings
    assert settings.STATIC_URL == "/static/"
