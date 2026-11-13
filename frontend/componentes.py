"""Peças visuais reutilizadas pelas páginas."""

import streamlit as st
from constantes import BADGE_NIVEL, BADGE_VIABILIDADE, PAGINA_PROJETOS


def aviso_de_modo(erro: str | None) -> None:
    if erro is not None:
        st.warning(
            f"Modo demonstração: não consegui ler a API ({erro}). "
            "Os dados abaixo são fictícios e nada é salvo.",
            icon="🧪",
        )


def cabecalho(
    titulo: str, subtitulo: str, rotulo_botao: str | None = None, acao=None
) -> None:
    col_titulo, col_botao = st.columns([4, 1], vertical_alignment="center")
    with col_titulo:
        st.markdown(f"## {titulo}")
        st.caption(subtitulo)
    if rotulo_botao and acao:
        with col_botao:
            if st.button(rotulo_botao, type="primary", icon=":material/add:"):
                acao()


def cartao_kpi(coluna, rotulo: str, valor: str, legenda: str) -> None:
    with coluna, st.container(border=True):
        st.metric(rotulo, valor)
        st.caption(legenda)


def selos_projeto(projeto: dict) -> str:
    """Linha de selos coloridos (markdown) com código, nível de risco e status."""
    cor_nivel = BADGE_NIVEL.get(projeto["nivel_risco"], "gray")
    cor_viab = BADGE_VIABILIDADE.get(projeto["status_viabilidade"], "gray")
    return (
        f"`{projeto['codigo']}` &nbsp; :{cor_nivel}-badge[Risco {projeto['nivel_risco']}] "
        f":{cor_viab}-badge[{projeto['status_viabilidade']}] :gray-badge[{projeto['status_risco']}]"
    )


def abrir_projeto(projeto_id: int) -> None:
    """Seleciona o projeto e vai para a página de detalhes."""
    st.session_state["projeto_atual"] = int(projeto_id)
    st.switch_page(PAGINA_PROJETOS)
