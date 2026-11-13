"""Gráficos Altair do painel."""

import datetime

import altair as alt
import pandas as pd
from constantes import COR_NIVEL, COR_PRIORIDADE, prioridade


def grafico_exposicao(projetos: list[dict]):
    """Ranking horizontal da exposição ao risco de cada projeto."""
    dados = pd.DataFrame([
        {"projeto": f"{p['codigo']} · {p['nome']}", "exposicao": p["risco_global_score"], "nivel": p["nivel_risco"]}
        for p in projetos
    ])
    return (
        alt.Chart(dados)
        .mark_bar(cornerRadiusEnd=4, size=18)
        .encode(
            x=alt.X("exposicao:Q", title="Exposição ao risco (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("projeto:N", title=None, sort="-x"),
            color=alt.Color(
                "nivel:N", title=None,
                scale=alt.Scale(domain=list(COR_NIVEL), range=list(COR_NIVEL.values())),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("projeto:N", title="Projeto"),
                alt.Tooltip("exposicao:Q", title="Exposição (%)"),
                alt.Tooltip("nivel:N", title="Nível"),
            ],
        )
        .properties(height=max(150, 48 * len(dados)))
    )


def grafico_matriz(riscos: list[dict], altura: int = 300):
    """Matriz 5×5: fundo colorido por faixa + bolhas com a quantidade de riscos em cada célula."""
    grade = pd.DataFrame([
        {"prob": p, "imp": i, "score": p * i, "faixa": prioridade(p * i)}
        for p in range(1, 6) for i in range(1, 6)
    ])
    ordem = [1, 2, 3, 4, 5]
    x = alt.X("prob:O", title="Probabilidade", sort=ordem, axis=alt.Axis(labelAngle=0))
    y = alt.Y("imp:O", title="Impacto", sort=ordem[::-1])
    escala = alt.Scale(domain=list(COR_PRIORIDADE), range=list(COR_PRIORIDADE.values()))

    fundo = (
        alt.Chart(grade)
        .mark_rect(cornerRadius=4, stroke="white", strokeWidth=3, opacity=0.28)
        .encode(
            x=x, y=y, color=alt.Color("faixa:N", scale=escala, legend=None),
            tooltip=[
                alt.Tooltip("prob:O", title="Probabilidade"),
                alt.Tooltip("imp:O", title="Impacto"),
                alt.Tooltip("score:Q", title="Criticidade"),
                alt.Tooltip("faixa:N", title="Prioridade"),
            ],
        )
    )
    if not riscos:
        return fundo.properties(height=altura)

    contagem = (
        pd.DataFrame(riscos)
        .rename(columns={"probabilidade": "prob", "impacto": "imp"})
        .groupby(["prob", "imp"]).size().reset_index(name="qtd")
    )
    contagem["faixa"] = (contagem["prob"] * contagem["imp"]).map(prioridade)
    base = alt.Chart(contagem).encode(x=x, y=y)
    bolhas = base.mark_circle(size=650, opacity=1).encode(
        color=alt.Color("faixa:N", scale=escala, legend=None)
    )
    numeros = base.mark_text(color="white", fontWeight="bold", fontSize=13).encode(text="qtd:Q")
    return (fundo + bolhas + numeros).properties(height=altura)


def grafico_evolucao(historico: list[dict], altura: int = 320):
    """Exposição do projeto ao longo do tempo. Em degraus: o valor vale até a próxima mudança."""
    dados = pd.DataFrame(historico)
    fuso_local = datetime.datetime.now().astimezone().tzinfo
    dados["data"] = (
        pd.to_datetime(dados["data"], utc=True).dt.tz_convert(fuso_local).dt.tz_localize(None)
    )
    return (
        alt.Chart(dados)
        .mark_line(point=True, strokeWidth=3, color="#1f7a78", interpolate="step-after")
        .encode(
            x=alt.X("data:T", title=None),
            y=alt.Y("exposicao:Q", title="Exposição (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=[
                alt.Tooltip("data:T", title="Data", format="%d/%m/%Y %H:%M"),
                alt.Tooltip("exposicao:Q", title="Exposição (%)"),
                alt.Tooltip("total_riscos:Q", title="Riscos mapeados"),
                alt.Tooltip("nivel:N", title="Nível"),
            ],
        )
        .properties(height=altura)
    )
