import pytest

from backend.motor_riscos import MotorDeRisco

motor = MotorDeRisco()


def test_criticidade_e_produto_de_probabilidade_e_impacto():
    assert motor.calcular_criticidade(4, 5) == 20
    assert motor.calcular_criticidade(1, 1) == 1


@pytest.mark.parametrize("prob, imp", [(0, 3), (6, 3), (3, 0), (3, 6)])
def test_valores_fora_da_escala_sao_rejeitados(prob, imp):
    with pytest.raises(ValueError):
        motor.calcular_criticidade(prob, imp)


@pytest.mark.parametrize(
    "score, esperado",
    [(25, "Alta"), (15, "Alta"), (14, "Média"), (8, "Média"), (7, "Baixa"), (1, "Baixa")],
)
def test_classificacao_de_prioridade(score, esperado):
    assert motor.classificar_risco(score) == esperado


def test_processamento_ordena_do_mais_critico_ao_menos():
    saida = motor.processar_variaveis_escopo(
        [
            {"nome": "baixo", "probabilidade": 1, "impacto": 2},
            {"nome": "alto", "probabilidade": 5, "impacto": 5},
            {"nome": "medio", "probabilidade": 3, "impacto": 3},
        ]
    )
    assert [r["variavel"] for r in saida] == ["alto", "medio", "baixo"]


def test_projeto_sem_riscos_fica_sem_analise():
    r = motor.avaliar_exposicao_projeto([], [])
    assert r == {"exposicao_pct": 0.0, "nivel": "Baixo", "status": "Sem análise"}


def test_um_risco_alta_eleva_o_projeto_mesmo_com_media_baixa():
    r = motor.avaliar_exposicao_projeto(
        [16, 2, 2, 2, 2], ["Alta", "Baixa", "Baixa", "Baixa", "Baixa"]
    )
    assert r["exposicao_pct"] == 19.2
    assert r["nivel"] == "Alto"
    assert r["status"] == "Em mitigação"


def test_exposicao_media_e_baixa():
    medio = motor.avaliar_exposicao_projeto([10, 10], ["Média", "Média"])
    assert (medio["exposicao_pct"], medio["nivel"], medio["status"]) == (
        40.0,
        "Médio",
        "Monitorando",
    )
    baixo = motor.avaliar_exposicao_projeto([3, 4], ["Baixa", "Baixa"])
    assert (baixo["exposicao_pct"], baixo["nivel"], baixo["status"]) == (
        14.0,
        "Baixo",
        "Controlado",
    )
