"""
Comunicação com a API FastAPI.

Toda leitura é cacheada por poucos segundos; toda escrita termina em
`invalidar_cache()`. Se a API estiver fora do ar, as leituras caem nos dados
de demonstração e `modo_demo()` passa a ser verdadeiro (as escritas são
recusadas com uma mensagem clara).
"""

import os

import requests
import streamlit as st
from dados_demo import historico_demo, projetos_demo
from dotenv import load_dotenv

_ = load_dotenv()

API_URL = os.getenv("GRIPS_API_URL", "http://localhost:8000")

CAMPOS_OBRIGATORIOS = {
    "id",
    "codigo",
    "nome",
    "escopo",
    "prazo_meses",
    "roi_esperado",
    "payback_meses",
    "experiencia_equipe",
    "viabilidade_score",
    "status_viabilidade",
    "risco_global_score",
    "nivel_risco",
    "status_risco",
    "parecer_tecnico",
    "riscos",
    "rev",
}


def _get(caminho: str):
    resposta = requests.get(f"{API_URL}{caminho}", timeout=4)
    resposta.raise_for_status()
    return resposta.json()


# ── Leituras (cacheadas) ─────────────────────────────────────────────────────
@st.cache_data(ttl=15, show_spinner=False)
def carregar_projetos() -> tuple[list[dict], str | None]:
    """Retorna (projetos com riscos, erro). Se a API falhar, cai nos dados de demonstração."""
    try:
        projetos = _get("/projetos")
        for projeto in projetos:
            faltando = CAMPOS_OBRIGATORIOS - set(projeto)
            if faltando:
                raise ValueError(
                    f"a API está desatualizada (faltam {len(faltando)} campos, como "
                    f"'{sorted(faltando)[0]}'); reinicie o `python main.py`"
                )
        return projetos, None
    except (requests.exceptions.RequestException, ValueError, KeyError) as erro:
        return projetos_demo(), str(erro)[:140]


def modo_demo() -> bool:
    return carregar_projetos()[1] is not None


@st.cache_data(ttl=15, show_spinner=False)
def carregar_historico(projeto_id: int) -> list[dict]:
    """Fotos da exposição do projeto ao longo do tempo (mais antiga primeiro)."""
    projetos, erro = carregar_projetos()
    if erro is not None:
        projeto = next((p for p in projetos if p["id"] == projeto_id), None)
        return historico_demo(projeto) if projeto else []
    try:
        return _get(f"/projetos/{projeto_id}/historico")
    except (requests.exceptions.RequestException, ValueError):
        return []


def invalidar_cache() -> None:
    """Chamar depois de qualquer escrita: limpa os caches e zera a seleção das tabelas."""
    carregar_projetos.clear()
    carregar_historico.clear()
    st.session_state["versao_tabelas"] = st.session_state.get("versao_tabelas", 0) + 1


def versao_tabelas() -> int:
    return st.session_state.get("versao_tabelas", 0)


# ── Escritas ─────────────────────────────────────────────────────────────────
def enviar(metodo: str, caminho: str, timeout: int = 15, **kwargs):
    """Retorna (resposta, None) ou (None, mensagem de erro)."""
    if modo_demo():
        return None, "modo demonstração: nada é salvo."
    try:
        resposta = requests.request(
            metodo, f"{API_URL}{caminho}", timeout=timeout, **kwargs
        )
    except requests.exceptions.RequestException as erro:
        return None, f"não foi possível falar com a API ({erro})"
    if resposta.status_code >= 400:
        try:
            detalhe = resposta.json().get("detail", resposta.text)
        except ValueError:
            detalhe = resposta.text
        if isinstance(detalhe, list):  # erro de validação (422) vem como lista
            detalhe = "; ".join(str(item.get("msg", item)) for item in detalhe)
        return None, str(detalhe)
    invalidar_cache()
    return resposta, None


def criar_projeto(payload: dict):
    return enviar("POST", "/projetos", json=payload)


def editar_projeto(projeto_id: int, payload: dict):
    return enviar("PUT", f"/projetos/{projeto_id}", json=payload)


def excluir_projeto(projeto_id: int):
    return enviar("DELETE", f"/projetos/{projeto_id}")


def criar_risco(projeto_id: int, payload: dict):
    return enviar("POST", f"/projetos/{projeto_id}/riscos", json=payload)


def editar_risco(projeto_id: int, risco_id: int, payload: dict):
    return enviar("PUT", f"/projetos/{projeto_id}/riscos/{risco_id}", json=payload)


def excluir_risco(projeto_id: int, risco_id: int):
    return enviar("DELETE", f"/projetos/{projeto_id}/riscos/{risco_id}")


def gerar_parecer(projeto_id: int):
    return enviar("POST", f"/projetos/{projeto_id}/analisar-ia", timeout=120)
