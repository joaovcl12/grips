"""
Aplica os motores determinísticos a um Projeto (ORM).

Concentra em um só lugar a atualização dos campos calculados, para que a API
e os scripts de migração usem exatamente a mesma regra. Não faz commit.
"""

from models import Projeto
from motor_riscos import MotorDeRisco
from motor_viabilidade import calcular_viabilidade, classificar_viabilidade

_motor = MotorDeRisco()


def atualizar_viabilidade(projeto: Projeto) -> None:
    """Recalcula viabilidade_score e status_viabilidade a partir dos dados de negócio."""
    projeto.viabilidade_score = calcular_viabilidade(
        roi_pct=projeto.roi_esperado,
        payback_meses=projeto.payback_meses,
        prazo_meses=projeto.prazo_meses,
        experiencia_equipe=projeto.experiencia_equipe,
    )
    projeto.status_viabilidade = classificar_viabilidade(projeto.viabilidade_score)


def atualizar_exposicao(projeto: Projeto) -> None:
    """Recalcula risco_global_score, nivel_risco e status_risco a partir dos riscos."""
    resultado = _motor.avaliar_exposicao_projeto(
        scores=[r.criticidade_score for r in projeto.riscos],
        prioridades=[r.prioridade for r in projeto.riscos],
    )
    projeto.risco_global_score = resultado["exposicao_pct"]
    projeto.nivel_risco = resultado["nivel"]
    projeto.status_risco = resultado["status"]
