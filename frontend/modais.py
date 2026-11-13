"""Janelas (modais) de cadastro, edição e exclusão de projetos e riscos."""

import api_client
import streamlit as st
from componentes import abrir_projeto
from constantes import EXPERIENCIAS, NIVEIS_IMPACTO, NIVEIS_PROBABILIDADE, prioridade


# ── Campos compartilhados entre "novo" e "editar" ────────────────────────────
def _campos_projeto(atual: dict | None = None) -> dict:
    a = atual or {}
    nome = st.text_input("Título do projeto", value=a.get("nome", ""), placeholder="Ex.: Migração Cloud AWS")
    escopo = st.text_area(
        "Escopo técnico", value=a.get("escopo", ""),
        placeholder="Objetivo e arquitetura, para contextualizar a IA...",
    )
    c1, c2, c3 = st.columns(3)
    prazo = c1.number_input(
        "Prazo (meses)", min_value=1, max_value=600, value=int(a.get("prazo_meses", 6)), step=1
    )
    roi = c2.number_input(
        "ROI esperado (%)", min_value=-100.0, max_value=10000.0,
        value=float(a.get("roi_esperado", 25.0)), step=1.0,
    )
    payback = c3.number_input(
        "Payback (meses)", min_value=0.0, max_value=600.0,
        value=float(a.get("payback_meses", 4.0)), step=0.5,
    )
    experiencia_atual = a.get("experiencia_equipe", EXPERIENCIAS[0])
    equipe = st.selectbox(
        "Experiência da equipe", EXPERIENCIAS,
        index=EXPERIENCIAS.index(experiencia_atual) if experiencia_atual in EXPERIENCIAS else 0,
    )
    return {
        "nome": nome.strip(), "escopo": escopo.strip(), "prazo_meses": int(prazo),
        "roi_esperado": float(roi), "payback_meses": float(payback), "experiencia_equipe": equipe,
    }


def _campos_risco(atual: dict | None = None) -> dict:
    a = atual or {}
    titulo = st.text_input(
        "Título do risco", value=a.get("titulo", ""),
        placeholder="Ex.: Falta de conhecimento da equipe em Docker",
    )
    responsavel = st.text_input(
        "Responsável pela mitigação", value=a.get("responsavel", ""), placeholder="Ex.: João Vitor"
    )
    c1, c2 = st.columns(2)
    prob = c1.selectbox(
        "Probabilidade", [1, 2, 3, 4, 5], index=int(a.get("probabilidade", 3)) - 1,
        format_func=lambda v: NIVEIS_PROBABILIDADE[v - 1],
    )
    imp = c2.selectbox(
        "Impacto", [1, 2, 3, 4, 5], index=int(a.get("impacto", 4)) - 1,
        format_func=lambda v: NIVEIS_IMPACTO[v - 1],
    )
    score = prob * imp
    st.info(f"Criticidade resultante: **{score}/25** · prioridade **{prioridade(score)}**", icon="🎯")
    return {
        "titulo": titulo.strip(), "responsavel": responsavel.strip() or "Equipe Técnica",
        "probabilidade": int(prob), "impacto": int(imp),
    }


# ── Projetos ─────────────────────────────────────────────────────────────────
@st.dialog("Novo projeto", width="large")
def modal_novo_projeto() -> None:
    st.caption("Cadastre os parâmetros técnicos e financeiros. A viabilidade é calculada automaticamente.")
    payload = _campos_projeto()
    if st.button("Salvar projeto", type="primary"):
        if not payload["nome"]:
            st.warning("Informe o título do projeto.")
            return
        resposta, erro = api_client.criar_projeto(payload)
        if erro or resposta is None:
            st.error(f"Erro ao salvar projeto: {erro}")
            return
        criado = resposta.json()
        st.toast(f"Projeto {criado['codigo']} salvo!")
        abrir_projeto(criado["id"])


@st.dialog("Editar projeto", width="large")
def modal_editar_projeto(projeto: dict) -> None:
    st.caption(f"{projeto['codigo']} · a viabilidade será recalculada ao salvar.")
    payload = _campos_projeto(projeto)
    if st.button("Salvar alterações", type="primary"):
        if not payload["nome"]:
            st.warning("Informe o título do projeto.")
            return
        _, erro = api_client.editar_projeto(projeto["id"], payload)
        if erro:
            st.error(f"Erro ao salvar: {erro}")
            return
        st.toast("Projeto atualizado!")
        st.rerun()


@st.dialog("Excluir projeto")
def modal_excluir_projeto(projeto: dict) -> None:
    st.warning(
        f"Excluir **{projeto['nome']}** ({projeto['codigo']})? "
        f"Isso apaga também os {len(projeto['riscos'])} risco(s) e o histórico de exposição. "
        "Não dá para desfazer."
    )
    c1, c2 = st.columns(2)
    if c1.button("Cancelar"):
        st.rerun()
    if c2.button("Excluir definitivamente", type="primary"):
        _, erro = api_client.excluir_projeto(projeto["id"])
        if erro:
            st.error(f"Erro ao excluir: {erro}")
            return
        st.session_state.pop("projeto_atual", None)
        st.toast("Projeto excluído.")
        st.rerun()


# ── Riscos ───────────────────────────────────────────────────────────────────
@st.dialog("Novo risco", width="large")
def modal_novo_risco(id_padrao: int | None = None) -> None:
    projetos, _ = api_client.carregar_projetos()
    if not projetos:
        st.info("Cadastre um projeto antes de mapear riscos.")
        return

    rotulos = {p["id"]: f"{p['codigo']} · {p['nome']}" for p in projetos}
    ids = list(rotulos)
    alvo = st.selectbox(
        "Projeto", ids, index=ids.index(id_padrao) if id_padrao in ids else 0,
        format_func=rotulos.get,
    )
    payload = _campos_risco()

    if st.button("Salvar risco", type="primary"):
        if not payload["titulo"]:
            st.warning("Informe o título do risco.")
            return
        _, erro = api_client.criar_risco(alvo, payload)
        if erro:
            st.error(f"Erro ao salvar risco: {erro}")
            return
        st.toast("Risco mapeado e exposição recalculada!")
        st.session_state["projeto_atual"] = int(alvo)
        st.rerun()


@st.dialog("Editar risco", width="large")
def modal_editar_risco(projeto_id: int, risco: dict) -> None:
    payload = _campos_risco(risco)
    if st.button("Salvar alterações", type="primary"):
        if not payload["titulo"]:
            st.warning("Informe o título do risco.")
            return
        _, erro = api_client.editar_risco(projeto_id, risco["id"], payload)
        if erro:
            st.error(f"Erro ao salvar: {erro}")
            return
        st.toast("Risco atualizado e exposição recalculada!")
        st.rerun()


@st.dialog("Excluir risco")
def modal_excluir_risco(projeto_id: int, risco: dict) -> None:
    st.warning(f"Excluir o risco **{risco['titulo']}**? A exposição do projeto será recalculada.")
    c1, c2 = st.columns(2)
    if c1.button("Cancelar"):
        st.rerun()
    if c2.button("Excluir", type="primary"):
        _, erro = api_client.excluir_risco(projeto_id, risco["id"])
        if erro:
            st.error(f"Erro ao excluir: {erro}")
            return
        st.toast("Risco excluído.")
        st.rerun()
