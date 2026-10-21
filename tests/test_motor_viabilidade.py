from backend.motor_viabilidade import (
    LIMIAR_APROVADO,
    LIMIAR_RESSALVAS,
    PESO_EQUIPE,
    PESO_PAYBACK,
    PESO_PRAZO,
    PESO_ROI,
    STATUS_APROVADO,
    STATUS_RESSALVAS,
    STATUS_RESTRICOES,
    calcular_viabilidade,
    classificar_viabilidade,
)


def test_pesos_somam_um():
    assert abs(PESO_ROI + PESO_PAYBACK + PESO_PRAZO + PESO_EQUIPE - 1.0) < 1e-9


def test_experiencia_da_equipe_altera_a_viabilidade():
    assert calcular_viabilidade(25, 4, 6, "Alta") == 72.2
    assert calcular_viabilidade(25, 4, 6, "Média") == 57.2
    assert calcular_viabilidade(25, 4, 6, "Baixa") == 42.2


def test_media_sem_acento_equivale_a_com_acento():
    assert calcular_viabilidade(25, 4, 6, "Media") == calcular_viabilidade(
        25, 4, 6, "Média"
    )


def test_resultado_sempre_entre_0_e_100():
    pior = calcular_viabilidade(0, 120, 120, "Baixa")
    melhor = calcular_viabilidade(1000, 0, 1, "Alta")
    assert 0.0 <= pior <= melhor <= 100.0


def test_classificacao_nos_limiares():
    assert classificar_viabilidade(LIMIAR_APROVADO) == STATUS_APROVADO
    assert classificar_viabilidade(LIMIAR_APROVADO - 0.1) == STATUS_RESSALVAS
    assert classificar_viabilidade(LIMIAR_RESSALVAS) == STATUS_RESSALVAS
    assert classificar_viabilidade(LIMIAR_RESSALVAS - 0.1) == STATUS_RESTRICOES
