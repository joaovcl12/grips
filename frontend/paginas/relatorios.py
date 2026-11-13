"""Página: Relatórios (pareceres técnicos gerados)."""

import streamlit as st
from api_client import carregar_projetos
from componentes import aviso_de_modo, cabecalho


def render() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)
    cabecalho(
        "Relatórios",
        "Pareceres técnicos gerados pela IA. A exportação em PDF entra na próxima etapa.",
    )

    com_parecer = [p for p in projetos if p.get("parecer_tecnico")]
    if not com_parecer:
        st.info("Nenhum parecer gerado ainda. Gere um na página do projeto.")
        return

    for p in com_parecer:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1], vertical_alignment="center")
            c1.markdown(
                f"**{p['nome']}**  \n`{p['codigo']}` · exposição {p['risco_global_score']}% "
                f"· {p['status_viabilidade']}"
            )
            c2.download_button(
                "Baixar (.md)", data=p["parecer_tecnico"],
                file_name=f"parecer_{p['codigo']}.md", mime="text/markdown", key=f"dl_{p['id']}",
            )


render()
