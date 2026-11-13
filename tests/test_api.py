import pytest

from backend import api
from backend.analise_ai import ErroParecer

PROJETO = {
    "nome": "Migração Cloud AWS",
    "escopo": "Migração dos serviços legados.",
    "prazo_meses": 6,
    "roi_esperado": 25,
    "payback_meses": 4,
    "experiencia_equipe": "Alta",
}


def criar_projeto(client, **mudancas):
    resposta = client.post("/projetos", json={**PROJETO, **mudancas})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_risco(client, projeto_id, titulo="Risco A", prob=4, imp=5, responsavel="Ana"):
    resposta = client.post(
        f"/projetos/{projeto_id}/riscos",
        json={"titulo": titulo, "responsavel": responsavel, "probabilidade": prob, "impacto": imp},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ── Projetos ─────────────────────────────────────────────────────────────────
def test_criar_projeto_calcula_viabilidade_e_comeca_sem_analise(client):
    p = criar_projeto(client)
    assert p["codigo"].startswith("PRJ-") and p["codigo"].endswith("-01")
    assert p["viabilidade_score"] == 72.2
    assert p["status_viabilidade"] == "Aprovado"
    assert p["status_risco"] == "Sem análise"
    assert p["risco_global_score"] == 0
    assert p["riscos"] == []


def test_escopo_vazio_ganha_texto_padrao(client):
    p = criar_projeto(client, escopo="")
    assert "Migração Cloud AWS" in p["escopo"]


def test_listar_projetos_ja_traz_os_riscos(client):
    p = criar_projeto(client)
    criar_risco(client, p["id"])
    lista = client.get("/projetos").json()
    assert len(lista) == 1 and len(lista[0]["riscos"]) == 1
    assert lista[0]["rev"]  # data de criação formatada


def test_editar_projeto_recalcula_viabilidade_sem_mexer_na_exposicao(client):
    p = criar_projeto(client)
    criar_risco(client, p["id"])
    resposta = client.put(f"/projetos/{p['id']}", json={**PROJETO, "experiencia_equipe": "Baixa"})
    assert resposta.status_code == 200
    novo = resposta.json()
    assert novo["viabilidade_score"] == 42.2 and novo["status_viabilidade"] == "Restrições"
    assert novo["risco_global_score"] == 80.0 and novo["status_risco"] == "Em mitigação"


def test_excluir_projeto_apaga_riscos_e_historico(client):
    p = criar_projeto(client)
    criar_risco(client, p["id"])
    assert client.delete(f"/projetos/{p['id']}").status_code == 204
    assert client.get(f"/projetos/{p['id']}").status_code == 404
    assert client.get(f"/projetos/{p['id']}/historico").status_code == 404
    assert client.get("/projetos").json() == []


@pytest.mark.parametrize(
    "mudanca",
    [
        {"nome": "   "},
        {"prazo_meses": 0},
        {"payback_meses": -1},
        {"experiencia_equipe": "Altíssima"},
    ],
)
def test_projeto_invalido_retorna_422(client, mudanca):
    assert client.post("/projetos", json={**PROJETO, **mudanca}).status_code == 422


# ── Riscos ───────────────────────────────────────────────────────────────────
def test_adicionar_risco_recalcula_exposicao_e_preserva_viabilidade(client):
    p = criar_projeto(client)
    p = criar_risco(client, p["id"], prob=4, imp=5)
    assert p["viabilidade_score"] == 72.2 and p["status_viabilidade"] == "Aprovado"
    assert p["risco_global_score"] == 80.0
    assert p["nivel_risco"] == "Alto" and p["status_risco"] == "Em mitigação"
    assert p["riscos"][0]["criticidade_score"] == 20 and p["riscos"][0]["prioridade"] == "Alta"


def test_riscos_vem_ordenados_do_mais_critico_ao_menos(client):
    p = criar_projeto(client)
    criar_risco(client, p["id"], "Baixo", 1, 2)
    p = criar_risco(client, p["id"], "Alto", 5, 5)
    assert [r["titulo"] for r in p["riscos"]] == ["Alto", "Baixo"]


def test_editar_risco_recalcula_score_e_exposicao(client):
    p = criar_projeto(client)
    p = criar_risco(client, p["id"], prob=4, imp=5)
    risco_id = p["riscos"][0]["id"]
    resposta = client.put(
        f"/projetos/{p['id']}/riscos/{risco_id}",
        json={"titulo": "Renomeado", "responsavel": "Bia", "probabilidade": 1, "impacto": 2},
    )
    assert resposta.status_code == 200
    novo = resposta.json()
    assert novo["riscos"][0]["titulo"] == "Renomeado" and novo["riscos"][0]["criticidade_score"] == 2
    assert novo["nivel_risco"] == "Baixo" and novo["status_risco"] == "Controlado"


def test_excluir_risco_volta_para_sem_analise(client):
    p = criar_projeto(client)
    p = criar_risco(client, p["id"])
    risco_id = p["riscos"][0]["id"]
    assert client.delete(f"/projetos/{p['id']}/riscos/{risco_id}").status_code == 204
    atual = client.get(f"/projetos/{p['id']}").json()
    assert atual["riscos"] == [] and atual["status_risco"] == "Sem análise"
    assert atual["risco_global_score"] == 0


def test_risco_de_outro_projeto_retorna_404(client):
    a = criar_projeto(client)
    b = criar_projeto(client, nome="Outro")
    a = criar_risco(client, a["id"])
    risco_id = a["riscos"][0]["id"]
    assert client.delete(f"/projetos/{b['id']}/riscos/{risco_id}").status_code == 404
    resposta = client.put(
        f"/projetos/{b['id']}/riscos/{risco_id}",
        json={"titulo": "x", "probabilidade": 1, "impacto": 1},
    )
    assert resposta.status_code == 404


@pytest.mark.parametrize("campo, valor", [("probabilidade", 6), ("impacto", 0), ("titulo", "  ")])
def test_risco_invalido_retorna_422(client, campo, valor):
    p = criar_projeto(client)
    corpo = {"titulo": "R", "probabilidade": 3, "impacto": 3, campo: valor}
    assert client.post(f"/projetos/{p['id']}/riscos", json=corpo).status_code == 422


def test_responsavel_vazio_vira_padrao(client):
    p = criar_projeto(client)
    p = criar_risco(client, p["id"], responsavel="   ")
    assert p["riscos"][0]["responsavel"] == "Equipe Técnica"


# ── Histórico ────────────────────────────────────────────────────────────────
def test_historico_registra_cada_mudanca_nos_riscos(client):
    p = criar_projeto(client)
    p = criar_risco(client, p["id"], "R1", 4, 5)  # 80%
    p = criar_risco(client, p["id"], "R2", 1, 1)  # média (20+1)/2 = 10.5 -> 42%
    client.delete(f"/projetos/{p['id']}/riscos/{p['riscos'][-1]['id']}")  # volta a 80%
    historico = client.get(f"/projetos/{p['id']}/historico").json()
    assert [h["exposicao"] for h in historico] == [0.0, 80.0, 42.0, 80.0]
    assert [h["total_riscos"] for h in historico] == [0, 1, 2, 1]
    datas = [h["data"] for h in historico]
    assert datas == sorted(datas)


# ── IA ───────────────────────────────────────────────────────────────────────
class AgenteFalso:
    def __init__(self, resultado):
        self.resultado = resultado

    def gerar_parecer_tecnico(self, escopo_projeto, riscos_identificados):
        if isinstance(self.resultado, Exception):
            raise self.resultado
        return self.resultado


def test_parecer_sem_riscos_retorna_400(client):
    p = criar_projeto(client)
    assert client.post(f"/projetos/{p['id']}/analisar-ia").status_code == 400


def test_parecer_gerado_e_salvo(client, monkeypatch):
    monkeypatch.setattr(api, "obter_agente", lambda: AgenteFalso("Parecer [1]"))
    p = criar_projeto(client)
    criar_risco(client, p["id"])
    resposta = client.post(f"/projetos/{p['id']}/analisar-ia")
    assert resposta.status_code == 200 and resposta.json() == {"parecer_tecnico": "Parecer [1]"}
    assert client.get(f"/projetos/{p['id']}").json()["parecer_tecnico"] == "Parecer [1]"


def test_erro_da_ia_retorna_502_e_nao_grava_nada(client, monkeypatch):
    monkeypatch.setattr(api, "obter_agente", lambda: AgenteFalso(ErroParecer("cota esgotada")))
    p = criar_projeto(client)
    criar_risco(client, p["id"])
    resposta = client.post(f"/projetos/{p['id']}/analisar-ia")
    assert resposta.status_code == 502 and "cota esgotada" in resposta.json()["detail"]
    assert client.get(f"/projetos/{p['id']}").json()["parecer_tecnico"] is None


def test_agente_indisponivel_retorna_503(client, monkeypatch):
    def quebrado():
        raise RuntimeError("GEMINI_API_KEY ausente")

    monkeypatch.setattr(api, "obter_agente", quebrado)
    p = criar_projeto(client)
    criar_risco(client, p["id"])
    assert client.post(f"/projetos/{p['id']}/analisar-ia").status_code == 503


def test_projeto_inexistente_retorna_404(client):
    assert client.get("/projetos/999").status_code == 404
    assert client.put("/projetos/999", json=PROJETO).status_code == 404
    assert client.delete("/projetos/999").status_code == 404
    assert client.post("/projetos/999/analisar-ia").status_code == 404
