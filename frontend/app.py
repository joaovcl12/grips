"""
GRIPS · Ponto de entrada do front-end.

Uso (na raiz do projeto):  streamlit run frontend/app.py

Este arquivo só configura a página e a navegação. Cada página fica em
`paginas/`, e o visual vem do tema em `.streamlit/config.toml`.
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="GRIPS · Gestão de Riscos", page_icon="🛡️", layout="wide")

from api_client import carregar_projetos  # noqa: E402  (precisa vir depois do set_page_config)

LOGO = Path(__file__).parent / "assets" / "logo.png"

# Pouquíssimo CSS: só o espaçamento do topo da página.
st.markdown(
    "<style>.block-container{padding-top:2.2rem;}</style>", unsafe_allow_html=True
)

if LOGO.exists():
    st.logo(str(LOGO), size="large")

with st.sidebar:
    if carregar_projetos()[1] is None:
        st.caption("🟢 API conectada")
    else:
        st.caption("🟠 Modo demonstração")

st.navigation(
    [
        st.Page(
            "paginas/visao_geral.py",
            title="Visão geral",
            icon=":material/dashboard:",
            url_path="visao-geral",
            default=True,
        ),
        st.Page(
            "paginas/projetos.py",
            title="Projetos",
            icon=":material/folder:",
            url_path="projetos",
        ),
        st.Page(
            "paginas/riscos.py",
            title="Riscos",
            icon=":material/warning:",
            url_path="riscos",
        ),
        st.Page(
            "paginas/relatorios.py",
            title="Relatórios",
            icon=":material/description:",
            url_path="relatorios",
        ),
    ]
).run()
