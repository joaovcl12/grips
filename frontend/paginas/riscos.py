"""Página: Riscos (visão global de todos os projetos)."""

import streamlit as st
from api_client import carregar_projetos, versao_tabelas
from componentes import abrir_projeto, aviso_de_modo, cabecalho
from modais import modal_novo_risco
from tabelas import COLUNAS_RISCO, tabela_riscos


def render() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)
    cabecalho(
        "Riscos", "Todos os riscos mapeados, do mais crítico ao menos crítico.",
        "Novo risco", modal_novo_risco,
    )

    todos = [
        {**r, "_projeto": p["codigo"], "_projeto_id": p["id"]}
        for p in projetos for r in p["riscos"]
    ]
    if not todos:
        st.info("Nenhum risco mapeado ainda.")
        return

    f1, f2 = st.columns(2)
    projeto_filtro = f1.selectbox("Projeto", ["Todos"] + [p["codigo"] for p in projetos])
    prioridade_filtro = f2.segmented_control(
        "Prioridade", ["Todas", "Alta", "Média", "Baixa"], default="Todas"
    )

    if projeto_filtro != "Todos":
        todos = [r for r in todos if r["_projeto"] == projeto_filtro]
    if prioridade_filtro and prioridade_filtro != "Todas":
        todos = [r for r in todos if r["prioridade"] == prioridade_filtro]

    if not todos:
        st.info("Nenhum risco corresponde aos filtros.")
        return

    st.caption(f"{len(todos)} risco(s) exibido(s). Clique em uma linha para abrir o projeto.")
    tabela = tabela_riscos(todos, com_projeto=True)
    evento = st.dataframe(
        tabela.drop(columns=["id", "projeto_id"]), hide_index=True, on_select="rerun",
        selection_mode="single-row", column_config=COLUNAS_RISCO,
        key=f"tabela_riscos_global_{versao_tabelas()}",
    )
    if evento.selection.rows:
        abrir_projeto(tabela.iloc[evento.selection.rows[0]]["projeto_id"])


render()
