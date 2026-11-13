from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend import models, schemas, servico_projetos
from backend.analise_ai import AgenteDiagnostico, ErroParecer
from backend.config import CORS_ORIGINS
from backend.database import engine, obter_banco
from backend.motor_riscos import MotorDeRisco, RiscoEntrada


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI) -> AsyncIterator[None]:
    # Cria as tabelas que ainda não existem (projetos, riscos, historico_exposicao).
    # Fica aqui, e não no import, para os testes poderem importar a API sem o Postgres.
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API GRIPS",
    description="Motor de Análise de Riscos Operacionais e Viabilidade de Projetos",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

motor = MotorDeRisco()


@lru_cache(maxsize=1)
def obter_agente() -> AgenteDiagnostico:
    """Cria o agente de IA só na primeira análise: a API sobe mesmo sem chave/base vetorial."""
    return AgenteDiagnostico()


# ─── Auxiliares ──────────────────────────────────────────────────────────────
def _obter_projeto(db: Session, projeto_id: int) -> models.Projeto:
    projeto = db.get(models.Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto


def _obter_risco(projeto: models.Projeto, risco_id: int) -> models.Risco:
    risco = next((r for r in projeto.riscos if r.id == risco_id), None)
    if risco is None:
        raise HTTPException(status_code=404, detail="Risco não encontrado neste projeto")
    return risco


def _gravar(db: Session, projeto: models.Projeto) -> dict:
    db.commit()
    db.refresh(projeto)
    return servico_projetos.serializar_projeto(projeto)


# ─── Projetos ────────────────────────────────────────────────────────────────
@app.post("/projetos", response_model=schemas.ProjetoOut, status_code=201)
def criar_projeto(dados: schemas.ProjetoIn, db: Session = Depends(obter_banco)):
    codigo = servico_projetos.proximo_codigo(db)
    projeto = servico_projetos.criar_projeto(dados, codigo)
    db.add(projeto)
    return _gravar(db, projeto)


@app.get("/projetos", response_model=list[schemas.ProjetoOut])
def listar_projetos(db: Session = Depends(obter_banco)):
    """Todos os projetos já com seus riscos (uma consulta extra só, sem N+1)."""
    projetos = db.scalars(
        select(models.Projeto)
        .options(selectinload(models.Projeto.riscos))
        .order_by(models.Projeto.data_criacao.desc())
    ).all()
    return [servico_projetos.serializar_projeto(p) for p in projetos]


@app.get("/projetos/{projeto_id}", response_model=schemas.ProjetoOut)
def detalhar_projeto(projeto_id: int, db: Session = Depends(obter_banco)):
    return servico_projetos.serializar_projeto(_obter_projeto(db, projeto_id))


@app.put("/projetos/{projeto_id}", response_model=schemas.ProjetoOut)
def atualizar_projeto(
    projeto_id: int, dados: schemas.ProjetoIn, db: Session = Depends(obter_banco)
):
    """Edita os dados de negócio e recalcula a viabilidade (a exposição não muda)."""
    projeto = _obter_projeto(db, projeto_id)
    servico_projetos.aplicar_dados_projeto(projeto, dados)
    return _gravar(db, projeto)


@app.delete("/projetos/{projeto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_projeto(projeto_id: int, db: Session = Depends(obter_banco)):
    """Apaga o projeto, seus riscos e o histórico de exposição."""
    db.delete(_obter_projeto(db, projeto_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/projetos/{projeto_id}/historico", response_model=list[schemas.HistoricoOut])
def historico_exposicao(projeto_id: int, db: Session = Depends(obter_banco)):
    return servico_projetos.serializar_historico(_obter_projeto(db, projeto_id))


# ─── Riscos ──────────────────────────────────────────────────────────────────
@app.post(
    "/projetos/{projeto_id}/riscos",
    response_model=schemas.ProjetoOut,
    status_code=201,
)
def adicionar_risco(
    projeto_id: int, dados: schemas.RiscoIn, db: Session = Depends(obter_banco)
):
    projeto = _obter_projeto(db, projeto_id)
    projeto.riscos.append(servico_projetos.criar_risco(dados))
    servico_projetos.recalcular_exposicao(projeto)
    return _gravar(db, projeto)


@app.put(
    "/projetos/{projeto_id}/riscos/{risco_id}", response_model=schemas.ProjetoOut
)
def atualizar_risco(
    projeto_id: int,
    risco_id: int,
    dados: schemas.RiscoIn,
    db: Session = Depends(obter_banco),
):
    projeto = _obter_projeto(db, projeto_id)
    servico_projetos.aplicar_dados_risco(_obter_risco(projeto, risco_id), dados)
    servico_projetos.recalcular_exposicao(projeto)
    return _gravar(db, projeto)


@app.delete(
    "/projetos/{projeto_id}/riscos/{risco_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_risco(
    projeto_id: int, risco_id: int, db: Session = Depends(obter_banco)
):
    projeto = _obter_projeto(db, projeto_id)
    projeto.riscos.remove(_obter_risco(projeto, risco_id))  # delete-orphan apaga a linha
    servico_projetos.recalcular_exposicao(projeto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── IA ──────────────────────────────────────────────────────────────────────
@app.post("/projetos/{projeto_id}/analisar-ia", response_model=schemas.ParecerOut)
def gerar_parecer_ia_projeto(projeto_id: int, db: Session = Depends(obter_banco)):
    projeto = _obter_projeto(db, projeto_id)
    if not projeto.riscos:
        raise HTTPException(
            status_code=400,
            detail="Cadastre ao menos um risco antes de gerar o parecer da IA.",
        )

    riscos_brutos: list[RiscoEntrada] = [
        {"nome": r.titulo, "probabilidade": r.probabilidade, "impacto": r.impacto}
        for r in projeto.riscos
    ]
    relatorio_riscos = motor.processar_variaveis_escopo(riscos_brutos)

    escopo_completo = (
        f"Projeto: {projeto.nome}. Escopo: {projeto.escopo}. "
        f"Prazo: {projeto.prazo_meses} meses, ROI Esperado: {projeto.roi_esperado}%, "
        f"Payback: {projeto.payback_meses} meses, "
        f"Experiência da Equipe: {projeto.experiencia_equipe}."
    )

    try:
        agente = obter_agente()
    except Exception as erro:
        raise HTTPException(
            status_code=503, detail=f"Agente de IA indisponível: {erro}"
        ) from erro

    try:
        parecer = agente.gerar_parecer_tecnico(
            escopo_projeto=escopo_completo,
            riscos_identificados=relatorio_riscos,
        )
    except ErroParecer as erro:
        # Nada é gravado no banco: o erro nunca vira "parecer técnico".
        raise HTTPException(status_code=502, detail=str(erro)) from erro

    projeto.parecer_tecnico = parecer
    db.commit()
    return {"parecer_tecnico": parecer}
