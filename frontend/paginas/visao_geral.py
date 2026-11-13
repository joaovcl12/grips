"""Página: Visão geral (portfólio)."""

from statistics import mean

import streamlit as st
from api_client import carregar_projetos, versao_tabelas
from componentes import abrir_projeto, aviso_de_modo, cabecalho, cartao_kpi
from graficos import grafico_exposicao, grafico_matriz
from modais import modal_novo_projeto
from tabelas import COLUNAS_PROJETO, tabela_projetos


def render() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)
    cabecalho(
        "Visão geral", "Pontos de atenção do portfólio, calculados em tempo real.",
        "Novo projeto", modal_novo_projeto,
    )

    if not projetos:
        st.info("Nenhum projeto cadastrado ainda. Use **Novo projeto** para começar.")
        return

    riscos = [r for p in projetos for r in p["riscos"]]
    aprovados = sum(p["status_viabilidade"] == "Aprovado" for p in projetos)
    criticos = sum(r["prioridade"] == "Alta" for r in riscos)
    viab_media = round(mean(p["viabilidade_score"] for p in projetos), 1)
    exposicao_media = round(mean(p["risco_global_score"] for p in projetos), 1)

    k1, k2, k3, k4 = st.columns(4)
    cartao_kpi(k1, "Projetos", str(len(projetos)), f"{aprovados} com viabilidade aprovada")
    cartao_kpi(k2, "Riscos críticos", str(criticos), f"de {len(riscos)} riscos mapeados")
    cartao_kpi(k3, "Viabilidade média", f"{viab_media}%", "média do portfólio")
    cartao_kpi(k4, "Exposição média", f"{exposicao_media}%", "média do portfólio")

    g1, g2 = st.columns([1.7, 1])
    with g1, st.container(border=True):
        st.markdown("**Exposição por projeto**")
        st.caption("Ranking: quanto mais à direita, maior a exposição ao risco.")
        st.altair_chart(grafico_exposicao(projetos))
    with g2, st.container(border=True):
        st.markdown("**Mapa de exposição**")
        st.caption("Probabilidade × impacto; o número é a quantidade de riscos.")
        st.altair_chart(grafico_matriz(riscos))

    st.markdown("#### Projetos em atenção")
    f1, f2 = st.columns([3, 2])
    busca = f1.text_input(
        "Buscar", placeholder="Buscar por nome ou código...",
        label_visibility="collapsed", icon=":material/search:",
    )
    nivel = f2.segmented_control(
        "Nível", ["Todos", "Alto", "Médio", "Baixo"], default="Todos", label_visibility="collapsed"
    )

    tabela = tabela_projetos(projetos)
    if busca:
        termo = busca.lower()
        tabela = tabela[
            tabela["Projeto"].str.lower().str.contains(termo, regex=False)
            | tabela["Código"].str.lower().str.contains(termo, regex=False)
        ]
    if nivel and nivel != "Todos":
        tabela = tabela[tabela["Nível"].str.contains(nivel, regex=False)]
    tabela = tabela.sort_values("Exposição (%)", ascending=False).reset_index(drop=True)

    if tabela.empty:
        st.info("Nenhum projeto corresponde aos filtros.")
        return

    st.caption("Clique em uma linha para abrir o projeto.")
    evento = st.dataframe(
        tabela.drop(columns="id"), hide_index=True, on_select="rerun",
        selection_mode="single-row", key=f"tabela_projetos_{versao_tabelas()}",
        column_config=COLUNAS_PROJETO,
    )
    if evento.selection.rows:
        abrir_projeto(tabela.iloc[evento.selection.rows[0]]["id"])


render()
