"""
Regras de aplicação sobre os projetos (ORM).

Concentra em um só lugar tudo o que altera os campos calculados, para que a
API e os scripts usem exatamente a mesma regra. Nenhuma função faz commit:
quem chama (rota ou script) decide quando gravar.
"""

import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.motor_riscos import MotorDeRisco
from backend.motor_viabilidade import calcular_viabilidade, classificar_viabilidade

_motor = MotorDeRisco()


# ── Campos calculados ────────────────────────────────────────────────────────
def atualizar_viabilidade(projeto: models.Projeto) -> None:
    """Recalcula viabilidade_score e status_viabilidade a partir dos dados de negócio."""
    projeto.viabilidade_score = calcular_viabilidade(
        roi_pct=projeto.roi_esperado,
        payback_meses=projeto.payback_meses,
        prazo_meses=projeto.prazo_meses,
        experiencia_equipe=projeto.experiencia_equipe,
    )
    projeto.status_viabilidade = classificar_viabilidade(projeto.viabilidade_score)


def atualizar_exposicao(projeto: models.Projeto) -> None:
    """Recalcula risco_global_score, nivel_risco e status_risco a partir dos riscos."""
    resultado = _motor.avaliar_exposicao_projeto(
        scores=[r.criticidade_score for r in projeto.riscos],
        prioridades=[r.prioridade for r in projeto.riscos],
    )
    projeto.risco_global_score = resultado["exposicao_pct"]
    projeto.nivel_risco = resultado["nivel"]
    projeto.status_risco = resultado["status"]


def registrar_historico(projeto: models.Projeto) -> None:
    """Guarda uma foto da exposição atual (a data é preenchida na gravação)."""
    projeto.historico.append(
        models.HistoricoExposicao(
            risco_global_score=projeto.risco_global_score,
            nivel_risco=projeto.nivel_risco,
            total_riscos=len(projeto.riscos),
        )
    )


def recalcular_exposicao(projeto: models.Projeto) -> None:
    """Atualiza a exposição e registra no histórico. Chamar a cada mudança nos riscos."""
    atualizar_exposicao(projeto)
    registrar_historico(projeto)


# ── Projetos ─────────────────────────────────────────────────────────────────
def proximo_codigo(db: Session) -> str:
    ultimo_id = db.scalar(select(func.max(models.Projeto.id))) or 0
    return f"PRJ-{datetime.datetime.now().year}-{ultimo_id + 1:02d}"


def criar_projeto(dados: schemas.ProjetoIn, codigo: str) -> models.Projeto:
    projeto = models.Projeto(
        codigo=codigo,
        nome=dados.nome,
        escopo=dados.escopo
        or f"Projeto {dados.nome} com prazo de {dados.prazo_meses} meses.",
        prazo_meses=dados.prazo_meses,
        roi_esperado=dados.roi_esperado,
        payback_meses=dados.payback_meses,
        experiencia_equipe=dados.experiencia_equipe,
    )
    atualizar_viabilidade(projeto)
    recalcular_exposicao(projeto)  # "Sem análise" + primeiro ponto do histórico
    return projeto


def aplicar_dados_projeto(projeto: models.Projeto, dados: schemas.ProjetoIn) -> None:
    projeto.nome = dados.nome
    projeto.escopo = dados.escopo
    projeto.prazo_meses = dados.prazo_meses
    projeto.roi_esperado = dados.roi_esperado
    projeto.payback_meses = dados.payback_meses
    projeto.experiencia_equipe = dados.experiencia_equipe
    atualizar_viabilidade(projeto)


# ── Riscos ───────────────────────────────────────────────────────────────────
def _criticidade_e_prioridade(dados: schemas.RiscoIn) -> tuple[int, str]:
    # Passa pelo motor (e não por uma conta local) para ter uma regra só.
    saida = _motor.processar_variaveis_escopo(
        [
            {
                "nome": dados.titulo,
                "probabilidade": dados.probabilidade,
                "impacto": dados.impacto,
            }
        ]
    )[0]
    return saida["criticidade_score"], saida["prioridade"]


def criar_risco(dados: schemas.RiscoIn) -> models.Risco:
    score, prioridade = _criticidade_e_prioridade(dados)
    return models.Risco(
        titulo=dados.titulo,
        responsavel=dados.responsavel,
        probabilidade=dados.probabilidade,
        impacto=dados.impacto,
        criticidade_score=score,
        prioridade=prioridade,
    )


def aplicar_dados_risco(risco: models.Risco, dados: schemas.RiscoIn) -> None:
    risco.titulo = dados.titulo
    risco.responsavel = dados.responsavel
    risco.probabilidade = dados.probabilidade
    risco.impacto = dados.impacto
    risco.criticidade_score, risco.prioridade = _criticidade_e_prioridade(dados)


# ── Saída ────────────────────────────────────────────────────────────────────
def serializar_projeto(projeto: models.Projeto) -> dict:
    """Dicionário no formato de schemas.ProjetoOut (riscos do mais ao menos crítico)."""
    riscos = sorted(projeto.riscos, key=lambda r: (-r.criticidade_score, r.id))
    return {
        "id": projeto.id,
        "codigo": projeto.codigo,
        "nome": projeto.nome,
        "escopo": projeto.escopo or "",
        "prazo_meses": projeto.prazo_meses,
        "roi_esperado": projeto.roi_esperado,
        "payback_meses": projeto.payback_meses,
        "experiencia_equipe": projeto.experiencia_equipe,
        "viabilidade_score": round(projeto.viabilidade_score, 1),
        "status_viabilidade": projeto.status_viabilidade,
        "risco_global_score": round(projeto.risco_global_score, 1),
        "nivel_risco": projeto.nivel_risco,
        "status_risco": projeto.status_risco,
        "parecer_tecnico": projeto.parecer_tecnico,
        "rev": projeto.data_criacao.strftime("%d/%m/%Y"),
        "riscos": [
            {
                "id": r.id,
                "titulo": r.titulo,
                "responsavel": r.responsavel,
                "probabilidade": r.probabilidade,
                "impacto": r.impacto,
                "criticidade_score": r.criticidade_score,
                "prioridade": r.prioridade,
            }
            for r in riscos
        ],
    }


def serializar_historico(projeto: models.Projeto) -> list[dict]:
    fotos = sorted(projeto.historico, key=lambda h: (h.data_registro, h.id))
    return [
        {
            "data": h.data_registro,
            "exposicao": h.risco_global_score,
            "nivel": h.nivel_risco,
            "total_riscos": h.total_riscos,
        }
        for h in fotos
    ]
