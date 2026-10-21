"""
Motor determinístico de viabilidade inicial de um projeto.

Cada variável é normalizada para o intervalo 0..1 (1 = melhor cenário) e
combinada por uma média ponderada. Todos os parâmetros estão em constantes
no topo do arquivo: são heurísticas calibráveis, não verdades absolutas, e
devem ser descritas como tal na documentação do TCC.
"""

from typing import Final

# ── Referências de normalização (valor a partir do qual o ganho/perda satura) ──
ROI_REFERENCIA_PCT: Final[float] = 100.0  # ROI >= 100% => nota máxima em ROI
PAYBACK_MAXIMO_MESES: Final[float] = 36.0  # payback >= 36 meses => nota zero
PRAZO_MAXIMO_MESES: Final[float] = 36.0  # prazo >= 36 meses => nota zero

# ── Pesos (devem somar 1.0) ────────────────────────────────────────────────────
PESO_ROI: Final[float] = 0.30
PESO_PAYBACK: Final[float] = 0.25
PESO_PRAZO: Final[float] = 0.15
PESO_EQUIPE: Final[float] = 0.30

NOTA_EQUIPE: Final[dict[str, float]] = {"alta": 1.0, "média": 0.5, "baixa": 0.0}

# ── Limiares de classificação ──────────────────────────────────────────────────
LIMIAR_APROVADO: Final[float] = 70.0
LIMIAR_RESSALVAS: Final[float] = 45.0

STATUS_APROVADO: Final[str] = "Aprovado"
STATUS_RESSALVAS: Final[str] = "Com ressalvas"
STATUS_RESTRICOES: Final[str] = "Restrições"

assert abs(PESO_ROI + PESO_PAYBACK + PESO_PRAZO + PESO_EQUIPE - 1.0) < 1e-9


def _limitar(valor: float, minimo: float = 0.0, maximo: float = 1.0) -> float:
    return max(minimo, min(maximo, valor))


def _nota_equipe(experiencia: str) -> float:
    """Aceita 'Alta', 'Média' (ou 'Media') e 'Baixa'; valor desconhecido vale 0.5."""
    chave = experiencia.strip().lower().replace("media", "média")
    return NOTA_EQUIPE.get(chave, 0.5)


def calcular_viabilidade(
    roi_pct: float,
    payback_meses: float,
    prazo_meses: int,
    experiencia_equipe: str,
) -> float:
    """Retorna a viabilidade inicial em % (0 a 100, uma casa decimal)."""
    nota_roi = _limitar(roi_pct / ROI_REFERENCIA_PCT)
    nota_payback = 1.0 - _limitar(payback_meses / PAYBACK_MAXIMO_MESES)
    nota_prazo = 1.0 - _limitar(prazo_meses / PRAZO_MAXIMO_MESES)
    nota_equipe = _nota_equipe(experiencia_equipe)

    total = (
        PESO_ROI * nota_roi
        + PESO_PAYBACK * nota_payback
        + PESO_PRAZO * nota_prazo
        + PESO_EQUIPE * nota_equipe
    )
    return round(total * 100.0, 1)


def classificar_viabilidade(viabilidade_pct: float) -> str:
    if viabilidade_pct >= LIMIAR_APROVADO:
        return STATUS_APROVADO
    if viabilidade_pct >= LIMIAR_RESSALVAS:
        return STATUS_RESSALVAS
    return STATUS_RESTRICOES
