"""Design tokens: fonte única, contraste, foco, fontes e movimento (FR-023 a FR-026, FR-030)."""

import re
from pathlib import Path

from apps.core import design_tokens

RAIZ = Path(__file__).resolve().parents[3]
CSS = RAIZ / "static" / "css"
TOKENS = CSS / "tokens.css"
OUTROS_CSS = [CSS / "base.css", CSS / "components.css", CSS / "utilities.css"]

TOKENS_SEMANTICOS = [
    "--color-paper", "--color-surface", "--color-surface-hover", "--color-muted",
    "--color-muted-strong", "--color-ink", "--color-ink-muted", "--color-ink-subtle",
    "--color-ink-disabled", "--color-border", "--color-border-subtle", "--color-ring",
    "--color-accent", "--color-accent-hover", "--color-accent-subtle", "--color-accent-ink",
    "--color-on-accent", "--color-success", "--color-success-subtle", "--color-success-ink",
    "--color-on-success", "--color-warning", "--color-warning-strong", "--color-warning-subtle",
    "--color-warning-ink", "--color-on-warning", "--color-danger", "--color-danger-hover",
    "--color-danger-subtle", "--color-danger-ink", "--color-on-danger", "--color-info",
    "--color-info-subtle", "--color-info-ink", "--color-overlay",
    "--font-sans", "--font-mono", "--font-weight-regular", "--font-weight-medium",
    "--font-weight-semibold",
    "--text-xs", "--text-sm", "--text-md", "--text-lg", "--text-xl", "--text-2xl", "--text-3xl",
    "--leading-xs", "--leading-sm", "--leading-md", "--leading-lg", "--leading-xl",
    "--leading-2xl", "--leading-3xl", "--tracking-tight", "--tracking-normal", "--tracking-caps",
    "--measure",
    *[f"--space-{n}" for n in range(14)],
    "--size-xs", "--size-sm", "--size-md", "--size-lg", "--icon-sm", "--icon-md", "--header-h",
    "--container-max", "--form-max", "--dialog-w-sm", "--dialog-w-md", "--toast-w",
    "--border-width", "--border-width-strong", "--border-width-accent", "--border-width-callout",
    "--radius-0", "--radius-sm",
    "--shadow-offset-sm", "--shadow-offset-md", "--shadow-offset-lg", "--shadow-none",
    "--shadow-sm", "--shadow-md", "--shadow-lg",
    "--focus-width", "--focus-offset", "--focus-color",
    "--grid-columns", "--grid-gutter", "--page-margin", "--bp-md", "--bp-lg", "--bp-xl",
    "--bp-max",
    "--table-row-sm", "--table-row-md", "--table-cell-px",
    "--z-base", "--z-raised", "--z-sticky", "--z-dropdown", "--z-toast",
    "--duration-instant", "--duration-fast", "--duration-moderate", "--ease-standard",
    "--ease-entrance", "--ease-exit", "--opacity-busy",
]

COR_LITERAL = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|"
    r":\s*(?:white|black|red|blue|green|yellow|gray|grey|orange|purple)\b"
)
MEDIDA_LITERAL = re.compile(r"(?<![\w-])(?:\d*\.)?\d+(?:px|rem|em)\b")


def sem_comentarios(texto: str) -> str:
    return re.sub(r"/\*.*?\*/", "", texto, flags=re.S)


def linhas_sem_prelud_media(texto: str) -> list[str]:
    """Linhas do CSS sem comentários, ignorando prelúdios de @media (única exceção documentada)."""
    linhas = []
    for linha in texto.splitlines():
        if linha.strip().startswith("@media"):
            assert "/* --bp-" in linha or "prefers-" in linha or "forced-colors" in linha, linha
            continue
        linhas.append(sem_comentarios(linha))
    return linhas


def test_fr023_tokens_semanticos_definidos():
    """FR-023: tokens.css define todos os tokens semânticos do design system §2."""
    tokens = design_tokens.carregar_tokens(TOKENS)
    faltando = [nome for nome in TOKENS_SEMANTICOS if nome not in tokens]
    assert not faltando, faltando
    assert "color-scheme: light" in TOKENS.read_text()


def test_fr023_nenhum_valor_magico_fora_de_tokens():
    """FR-023: base/components/utilities não têm cor nem medida literal (só tokens)."""
    for arquivo in OUTROS_CSS:
        for numero, linha in enumerate(linhas_sem_prelud_media(arquivo.read_text()), start=1):
            assert not COR_LITERAL.search(linha), f"{arquivo.name}:{numero}: {linha}"
            assert not MEDIDA_LITERAL.search(linha), f"{arquivo.name}:{numero}: {linha}"
            assert "--palette-" not in linha, f"{arquivo.name}:{numero}: {linha}"


def test_fr024_pares_de_contraste_atingem_o_minimo():
    """FR-024: todos os 31 pares do design system §3 atingem o mínimo WCAG calculado."""
    pares = design_tokens.avaliar_pares()
    assert len(pares) == 31
    reprovados = [p for p in pares if not p["aprovado"]]
    assert not reprovados, reprovados


def test_fr024_calculo_wcag_conhecido():
    """FR-024: razão de contraste confere com valores de referência do WCAG."""
    assert round(design_tokens.razao_contraste("#000000", "#FFFFFF"), 2) == 21.0
    assert round(design_tokens.razao_contraste("#1A1814", "#F6F4EF"), 2) == 16.13
    assert design_tokens.razao_contraste("#FFFFFF", "#FFFFFF") == 1.0


def test_fr025_foco_visivel_e_cores_forcadas():
    """FR-025: foco global por outline com tokens; sem outline: none; modo de cores forçadas."""
    base = sem_comentarios((CSS / "base.css").read_text())
    regra_foco = re.search(r":focus-visible\s*\{[^}]*\}", base)
    assert regra_foco
    for token in ("--focus-width", "--focus-color", "--focus-offset"):
        assert token in regra_foco.group(0)
    for arquivo in [TOKENS, *OUTROS_CSS]:
        assert not re.search(r"outline:\s*(none|0)\b", arquivo.read_text()), arquivo.name
    tokens = TOKENS.read_text()
    bloco = re.search(r"@media \(forced-colors: active\)\s*\{(.*?)\n\}", tokens, re.S)
    assert bloco and "--color-border" in bloco.group(1) and "--focus-color" in bloco.group(1)


def test_fr026_fontes_declaradas_com_swap():
    """FR-026: cinco @font-face com font-display: swap; .num em mono tabular."""
    base = (CSS / "base.css").read_text()
    assert base.count("@font-face") == 5
    assert base.count("font-display: swap") == 5
    utilitarios = sem_comentarios((CSS / "utilities.css").read_text())
    regra_num = re.search(r"\.num\s*\{[^}]*\}", utilitarios).group(0)
    assert "var(--font-mono)" in regra_num and "tabular-nums" in regra_num


def test_fr030_movimento_minimo():
    """FR-030: durações ≤ 150 ms, movimento reduzido zera, transições só em propriedades leves."""
    tokens = design_tokens.carregar_tokens(TOKENS)
    for nome, valor in tokens.items():
        if nome.startswith("--duration-"):
            assert int(valor.removesuffix("ms")) <= 150, (nome, valor)
    texto_tokens = TOKENS.read_text()
    reduzido = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\n\}", texto_tokens,
                         re.S)
    assert reduzido and "--duration-instant" in reduzido.group(1)
    permitidas = {"background-color", "color", "border-color", "box-shadow", "transform",
                  "opacity"}
    for arquivo in OUTROS_CSS:
        texto = sem_comentarios(arquivo.read_text())
        assert "transition: all" not in texto
        for declaracao in re.findall(r"transition(?:-property)?:\s*([^;]+);", texto):
            for parte in declaracao.split(","):
                propriedade = parte.strip().split()[0]
                assert propriedade in permitidas, (arquivo.name, declaracao)
