"""Leitura dos tokens de `static/css/tokens.css` e verificação de contraste WCAG 2.1.

Uma única fonte de cálculo para os testes, o comando `checar_contraste` e o catálogo `/design/`
(research R11): é impossível o catálogo mostrar uma razão diferente da testada.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings

CAMINHO_TOKENS = Path(settings.BASE_DIR) / "static" / "css" / "tokens.css"

_DECLARACAO = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
_VAR = re.compile(r"var\((--[\w-]+)\)")


def _bloco_root_principal(texto: str) -> str:
    """Conteúdo do primeiro `:root { … }` (fora de media queries)."""
    sem_comentarios = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    inicio = sem_comentarios.index(":root")
    abre = sem_comentarios.index("{", inicio)
    fecha = sem_comentarios.index("\n}", abre)
    return sem_comentarios[abre + 1 : fecha]


def carregar_tokens(caminho: Path = CAMINHO_TOKENS) -> dict[str, str]:
    """Custom properties do `:root` principal, na ordem em que aparecem."""
    bloco = _bloco_root_principal(Path(caminho).read_text(encoding="utf-8"))
    return {nome: valor.strip() for nome, valor in _DECLARACAO.findall(bloco)}


def resolver(nome: str, tokens: dict[str, str]) -> str:
    """Valor final de um token, resolvendo `var()` encadeado."""
    valor = tokens[nome]
    for _ in range(10):
        if not _VAR.search(valor):
            return valor
        valor = _VAR.sub(lambda m: tokens[m.group(1)], valor)
    raise ValueError(f"Referência circular ao resolver {nome}")


def _canal(valor: int) -> float:
    c = valor / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(hex_cor: str) -> float:
    """Luminância relativa sRGB (WCAG 2.1)."""
    hex_cor = hex_cor.lstrip("#")
    r, g, b = (int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _canal(r) + 0.7152 * _canal(g) + 0.0722 * _canal(b)


def razao_contraste(a: str, b: str) -> float:
    claro, escuro = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


@dataclass(frozen=True)
class ParContraste:
    primeiro_plano: str
    fundo: str
    minimo: float
    uso: str


# Espelho da tabela §3 de docs/design/design-system.md (31 pares).
PARES_CONTRASTE: tuple[ParContraste, ...] = (
    ParContraste("--color-ink", "--color-paper", 4.5, "Texto principal sobre a página"),
    ParContraste("--color-ink", "--color-surface", 4.5, "Texto principal em cartões, tabelas, campos, diálogos"),
    ParContraste("--color-ink", "--color-muted", 4.5, "Texto sobre camada atenuada (linha hover, código)"),
    ParContraste("--color-ink-muted", "--color-paper", 4.5, "Texto secundário sobre a página"),
    ParContraste("--color-ink-muted", "--color-surface", 4.5, "Texto secundário em superfícies; itens de navegação"),
    ParContraste("--color-ink-muted", "--color-muted", 4.5, "Cabeçalho de tabela (caixa alta)"),
    ParContraste("--color-ink-subtle", "--color-surface", 4.5, "Placeholder, texto de ajuda, rótulo de KPI"),
    ParContraste("--color-ink-subtle", "--color-paper", 4.5, "Rodapé, metadados sobre a página"),
    ParContraste("--color-ink-subtle", "--color-muted", 4.5, "Metadados em camada atenuada"),
    ParContraste("--color-accent", "--color-surface", 4.5, "Links em superfícies"),
    ParContraste("--color-accent", "--color-paper", 4.5, "Links sobre a página"),
    ParContraste("--color-on-accent", "--color-accent", 4.5, "Botão primário"),
    ParContraste("--color-on-accent", "--color-accent-hover", 4.5, "Botão primário (hover)"),
    ParContraste("--color-accent-ink", "--color-accent-subtle", 4.5, "Badge/aviso/toast info; linha selecionada"),
    ParContraste("--color-ink", "--color-accent-subtle", 4.5, "Rótulo dentro da barra do BarList"),
    ParContraste("--color-success-ink", "--color-success-subtle", 4.5, "Badge OK; toast/aviso de sucesso"),
    ParContraste("--color-on-warning", "--color-warning", 4.5, "Badge REPOSIÇÃO NECESSÁRIA; badge da navegação"),
    ParContraste("--color-warning-ink", "--color-warning-subtle", 4.5, "Toast/aviso de alerta"),
    ParContraste("--color-ink", "--color-warning-subtle", 4.5, "Texto de linha de tabela em alerta"),
    ParContraste("--color-on-danger", "--color-danger", 4.5, "Botão perigo; segmento SEM ESTOQUE"),
    ParContraste("--color-on-danger", "--color-danger-hover", 4.5, "Botão perigo (hover)"),
    ParContraste("--color-danger-ink", "--color-danger-subtle", 4.5, "Toast/aviso de erro"),
    ParContraste("--color-danger", "--color-surface", 4.5, "Mensagem de erro de campo"),
    ParContraste("--color-accent", "--color-paper", 3.0, "Indicador de foco sobre a página (não-texto)"),
    ParContraste("--color-accent", "--color-surface", 3.0, "Indicador de foco em superfícies (não-texto)"),
    ParContraste("--color-ink", "--color-surface", 3.0, "Borda de campo/botão (limite de componente)"),
    ParContraste("--color-danger", "--color-surface", 3.0, "Borda de campo com erro"),
    ParContraste("--color-warning-strong", "--color-surface", 3.0, "Borda de destaque de alerta; ícone de alerta sobre superfície"),
    ParContraste("--color-success", "--color-surface", 3.0, "Marcas gráficas e ícones de sucesso"),
    ParContraste("--color-accent", "--color-surface", 3.0, "Barras/marcas do acento"),
    ParContraste("--color-ink-disabled", "--color-muted-strong", 0, "Texto desabilitado (isento — WCAG 1.4.3)"),
)  # fmt: skip


@lru_cache(maxsize=1)
def _tokens_em_cache(mtime: float) -> dict[str, str]:
    return carregar_tokens(CAMINHO_TOKENS)


def tokens_atuais() -> dict[str, str]:
    return _tokens_em_cache(CAMINHO_TOKENS.stat().st_mtime)


def avaliar_pares(pares: tuple[ParContraste, ...] | None = None) -> list[dict]:
    """Calcula a razão de cada par a partir de `tokens.css`."""
    tokens = tokens_atuais()
    resultado = []
    for par in PARES_CONTRASTE if pares is None else pares:
        frente = resolver(par.primeiro_plano, tokens)
        fundo = resolver(par.fundo, tokens)
        razao = razao_contraste(frente, fundo)
        resultado.append(
            {
                "primeiro_plano": par.primeiro_plano,
                "fundo": par.fundo,
                "hex_primeiro_plano": frente.upper(),
                "hex_fundo": fundo.upper(),
                "minimo": par.minimo,
                "uso": par.uso,
                "razao": round(razao, 2),
                "aprovado": par.minimo == 0 or razao >= par.minimo,
                "isento": par.minimo == 0,
            }
        )
    return resultado
