"""Constantes visuais e textos compartilhados pelo front-end."""

COR_NIVEL = {"Alto": "#d65b48", "Médio": "#e2a13b", "Baixo": "#4c9a87"}
COR_PRIORIDADE = {"Alta": "#d65b48", "Média": "#e2a13b", "Baixa": "#4c9a87"}

BADGE_NIVEL = {"Alto": "red", "Médio": "orange", "Baixo": "green"}
BADGE_VIABILIDADE = {"Aprovado": "green", "Com ressalvas": "orange", "Restrições": "red"}

# O st.dataframe não colore células; a bolinha no texto dá o mesmo recado.
BOLINHA = {
    "Alto": "🔴", "Médio": "🟠", "Baixo": "🟢",
    "Alta": "🔴", "Média": "🟠", "Baixa": "🟢",
}

EXPERIENCIAS = ["Alta", "Média", "Baixa"]
NIVEIS_PROBABILIDADE = ["1 · Muito baixa", "2 · Baixa", "3 · Média", "4 · Alta", "5 · Muito alta"]
NIVEIS_IMPACTO = ["1 · Muito baixo", "2 · Baixo", "3 · Médio", "4 · Alto", "5 · Muito alto"]

PAGINA_PROJETOS = "paginas/projetos.py"


def prioridade(score: int) -> str:
    """Espelha o motor_riscos do back-end (usado só para pré-visualizar na tela)."""
    return "Alta" if score >= 15 else "Média" if score >= 8 else "Baixa"
