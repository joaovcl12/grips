"""Montagem dos DataFrames exibidos nas tabelas e a configuração das colunas."""

import pandas as pd
import streamlit as st
from constantes import BOLINHA

COLUNAS_RISCO = {
    "Score": st.column_config.ProgressColumn("Score (1–25)", min_value=0, max_value=25, format="%d"),
}
COLUNAS_PROJETO = {
    "Exposição (%)": st.column_config.ProgressColumn("Exposição (%)", min_value=0, max_value=100, format="%.0f"),
    "Viabilidade (%)": st.column_config.ProgressColumn("Viabilidade (%)", min_value=0, max_value=100, format="%.1f"),
}


def tabela_projetos(projetos: list[dict]) -> pd.DataFrame:
    """Uma linha por projeto. A coluna `id` serve para localizar a linha clicada; esconda-a ao exibir."""
    return pd.DataFrame([
        {
            "id": p["id"],
            "Projeto": p["nome"],
            "Código": p["codigo"],
            "Nível": f"{BOLINHA.get(p['nivel_risco'], '')} {p['nivel_risco']}",
            "Exposição (%)": p["risco_global_score"],
            "Status do risco": p["status_risco"],
            "Viabilidade (%)": p["viabilidade_score"],
            "Status da viabilidade": p["status_viabilidade"],
            "Riscos": len(p["riscos"]),
            "Criado em": p.get("rev", ""),
        }
        for p in projetos
    ])


def tabela_riscos(riscos: list[dict], com_projeto: bool = False) -> pd.DataFrame:
    """
    Uma linha por risco, do mais ao menos crítico. Colunas `id` (e `projeto_id`, na visão
    global) servem para localizar a linha clicada; esconda-as ao exibir.
    Com `com_projeto`, cada risco precisa trazer `_projeto` (código) e `_projeto_id`.
    """
    linhas = []
    for r in sorted(riscos, key=lambda r: (-r["criticidade_score"], r["id"])):
        linha = {
            "Risco": r["titulo"],
            "Responsável": r["responsavel"],
            "Prob.": r["probabilidade"],
            "Imp.": r["impacto"],
            "Score": r["criticidade_score"],
            "Prioridade": f"{BOLINHA.get(r['prioridade'], '')} {r['prioridade']}",
        }
        if com_projeto:
            linha = {"id": r["id"], "projeto_id": r["_projeto_id"], "Projeto": r["_projeto"], **linha}
        else:
            linha = {"id": r["id"], **linha}
        linhas.append(linha)
    return pd.DataFrame(linhas)
