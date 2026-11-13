"""Página: Projetos (detalhe de um projeto, com riscos, matriz, evolução e parecer)."""

import streamlit as st
from api_client import (
    carregar_historico,
    carregar_projetos,
    gerar_parecer,
    versao_tabelas,
)
from componentes import aviso_de_modo, cabecalho, cartao_kpi, selos_projeto
from graficos import grafico_evolucao, grafico_matriz
from modais import (
    modal_editar_projeto,
    modal_editar_risco,
    modal_excluir_projeto,
    modal_excluir_risco,
    modal_novo_projeto,
    modal_novo_risco,
)
from tabelas import COLUNAS_RISCO, tabela_riscos


def _aba_riscos(projeto: dict) -> None:
    if not projeto["riscos"]:
        st.info("Nenhum risco mapeado. Use **Adicionar risco** para iniciar a análise.")
        return

    tabela = tabela_riscos(projeto["riscos"])
    evento = st.dataframe(
        tabela.drop(columns="id"), hide_index=True, on_select="rerun",
        selection_mode="single-row", column_config=COLUNAS_RISCO,
        key=f"tabela_riscos_{projeto['id']}_{versao_tabelas()}",
    )
    if not evento.selection.rows:
        st.caption("Selecione um risco na tabela para editar ou excluir.")
        return

    risco_id = int(tabela.iloc[evento.selection.rows[0]]["id"])
    risco = next(r for r in projeto["riscos"] if r["id"] == risco_id)
    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button("Editar risco", icon=":material/edit:"):
        modal_editar_risco(projeto["id"], risco)
    if b2.button("Excluir risco", icon=":material/delete:"):
        modal_excluir_risco(projeto["id"], risco)


def _aba_matriz(projeto: dict) -> None:
    _, centro, _ = st.columns([1, 2, 1])
    with centro:
        st.altair_chart(grafico_matriz(projeto["riscos"], altura=380))
        st.caption("Verde: prioridade baixa · Laranja: média · Vermelho: alta.")


def _aba_evolucao(projeto: dict) -> None:
    historico = carregar_historico(projeto["id"])
    if not historico:
        st.info(
            "Ainda não há histórico para este projeto. Ele passa a ser registrado a cada "
            "mudança nos riscos (ou rode `python -m scripts.iniciar_historico` para os projetos antigos)."
        )
        return
    st.caption("Exposição ao risco a cada mudança nos riscos do projeto.")
    st.altair_chart(grafico_evolucao(historico))
    if len(historico) < 2:
        st.caption("Só há um ponto por enquanto; o gráfico ganha forma conforme os riscos mudam.")


def _aba_parecer(projeto: dict) -> None:
    parecer = projeto.get("parecer_tecnico")
    if not parecer:
        st.info("Parecer ainda não gerado. Mapeie os riscos e clique em **Gerar parecer IA**.")
        return
    with st.container(border=True):
        st.markdown(parecer)
    st.caption("O parecer não se atualiza sozinho: gere de novo depois de alterar os riscos.")
    st.download_button(
        "Baixar parecer (.md)", data=parecer, file_name=f"parecer_{projeto['codigo']}.md",
        mime="text/markdown", icon=":material/download:",
    )


def _aba_dados(projeto: dict) -> None:
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Parâmetros de entrada**")
        st.write(f"Prazo: {projeto['prazo_meses']} meses")
        st.write(f"ROI esperado: {projeto['roi_esperado']}%")
        st.write(f"Payback: {projeto['payback_meses']} meses")
        st.write(f"Experiência da equipe: {projeto['experiencia_equipe']}")
    with d2:
        st.markdown("**Resultados calculados**")
        st.write(f"Viabilidade: {projeto['viabilidade_score']}% ({projeto['status_viabilidade']})")
        st.write(f"Exposição: {projeto['risco_global_score']}% (nível {projeto['nivel_risco']})")
        st.write(f"Status do risco: {projeto['status_risco']}")
        st.write(f"Criado em: {projeto.get('rev', '—')}")

    st.divider()
    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button("Editar projeto", icon=":material/edit:"):
        modal_editar_projeto(projeto)
    if b2.button("Excluir projeto", icon=":material/delete:"):
        modal_excluir_projeto(projeto)


def render() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)

    if not projetos:
        cabecalho("Projetos", "Nenhum projeto cadastrado ainda.", "Novo projeto", modal_novo_projeto)
        return

    ids = [p["id"] for p in projetos]
    atual = st.session_state.get("projeto_atual", ids[0])
    if atual not in ids:
        atual = ids[0]
    rotulos = {p["id"]: f"{p['codigo']} · {p['nome']}" for p in projetos}

    c_sel, c_novo, c_risco, c_ia = st.columns([3, 1.2, 1.2, 1.5], vertical_alignment="bottom")
    escolhido = c_sel.selectbox("Projeto", ids, index=ids.index(atual), format_func=rotulos.get)
    st.session_state["projeto_atual"] = escolhido
    projeto = next(p for p in projetos if p["id"] == escolhido)

    if c_novo.button("Novo projeto", icon=":material/add:"):
        modal_novo_projeto()
    if c_risco.button("Adicionar risco", type="primary", icon=":material/add_alert:"):
        modal_novo_risco(projeto["id"])
    if c_ia.button("Gerar parecer IA", icon=":material/auto_awesome:"):
        if not projeto["riscos"]:
            st.warning("Cadastre ao menos um risco antes de gerar o parecer.")
        else:
            with st.spinner("Consultando a base de conhecimento e gerando o parecer..."):
                _, erro_ia = gerar_parecer(projeto["id"])
            if erro_ia:
                st.warning(f"Não foi possível gerar o parecer: {erro_ia}")
            else:
                st.toast("Parecer técnico gerado!")
                st.rerun()

    st.markdown(f"### {projeto['nome']}")
    st.markdown(selos_projeto(projeto))
    if projeto.get("escopo"):
        st.caption(projeto["escopo"])

    k1, k2, k3, k4 = st.columns(4)
    cartao_kpi(k1, "Viabilidade", f"{projeto['viabilidade_score']}%", projeto["status_viabilidade"])
    cartao_kpi(
        k2, "Exposição ao risco", f"{projeto['risco_global_score']}%",
        f"nível {projeto['nivel_risco']} · {projeto['status_risco']}",
    )
    cartao_kpi(k3, "ROI esperado", f"{projeto['roi_esperado']}%", f"payback de {projeto['payback_meses']} meses")
    cartao_kpi(k4, "Prazo", f"{projeto['prazo_meses']} meses", f"{len(projeto['riscos'])} riscos mapeados")

    aba_riscos, aba_matriz, aba_evolucao, aba_parecer, aba_dados = st.tabs(
        ["Riscos", "Matriz 5×5", "Evolução", "Parecer IA", "Dados do projeto"]
    )
    with aba_riscos:
        _aba_riscos(projeto)
    with aba_matriz:
        _aba_matriz(projeto)
    with aba_evolucao:
        _aba_evolucao(projeto)
    with aba_parecer:
        _aba_parecer(projeto)
    with aba_dados:
        _aba_dados(projeto)


render()
