import datetime
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from analise_ai import AgenteDiagnostico, ErroParecer
from database import engine, obter_banco
from motor_riscos import MotorDeRisco, RiscoEntrada
from motor_viabilidade import STATUS_APROVADO
from servico_projetos import atualizar_exposicao, atualizar_viabilidade

# Cria as tabelas (projetos e riscos) no PostgreSQL caso não existam
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API GRIPS",
    description="Motor de Análise de Riscos Operacionais e Viabilidade de Projetos",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

motor = MotorDeRisco()


@lru_cache(maxsize=1)
def obter_agente() -> AgenteDiagnostico:
    """Cria o agente de IA só na primeira análise: a API sobe mesmo sem chave/base vetorial."""
    return AgenteDiagnostico()


# ─── SCHEMAS PYDANTIC ────────────────────────────────────────────────────────
class ProjetoCreate(BaseModel):
    nome: str
    escopo: str = ""
    prazo_meses: int = Field(gt=0)
    roi_esperado: float
    payback_meses: float = Field(ge=0)
    experiencia_equipe: str  # "Alta", "Média", "Baixa"


class RiscoCreate(BaseModel):
    titulo: str
    responsavel: str = "Equipe Técnica"
    probabilidade: int = Field(ge=1, le=5)
    impacto: int = Field(ge=1, le=5)


# ─── FUNÇÃO AUXILIAR DE RECÁLCULO DO PROJETO ─────────────────────────────────
def recalcular_metricas_projeto(projeto: models.Projeto, db: Session):
    """Atualiza exposição, nível e status de RISCO. A viabilidade não é alterada aqui."""
    atualizar_exposicao(projeto)
    db.commit()
    db.refresh(projeto)


# ─── ROTAS DA API ────────────────────────────────────────────────────────────
@app.post("/projetos")
def criar_projeto(dados: ProjetoCreate, db: Session = Depends(obter_banco)):
    ano_atual = datetime.datetime.now().year
    ultimo = db.query(models.Projeto).order_by(models.Projeto.id.desc()).first()
    seq = (ultimo.id + 1) if ultimo else 1
    codigo = f"PRJ-{ano_atual}-{seq:02d}"

    novo_proj = models.Projeto(
        codigo=codigo,
        nome=dados.nome,
        escopo=dados.escopo
        or f"Projeto {dados.nome} com prazo de {dados.prazo_meses} meses.",
        prazo_meses=dados.prazo_meses,
        roi_esperado=dados.roi_esperado,
        payback_meses=dados.payback_meses,
        experiencia_equipe=dados.experiencia_equipe,
    )
    # Viabilidade (motor_viabilidade) e exposição inicial ("Sem análise", sem riscos)
    atualizar_viabilidade(novo_proj)
    atualizar_exposicao(novo_proj)

    db.add(novo_proj)
    db.commit()
    db.refresh(novo_proj)
    return novo_proj


@app.get("/projetos")
def listar_projetos(db: Session = Depends(obter_banco)):
    projetos = (
        db.query(models.Projeto).order_by(models.Projeto.data_criacao.desc()).all()
    )
    resultado = []
    for p in projetos:
        palavras = [w for w in p.nome.split() if w]
        iniciais = (
            palavras[0][0] + (palavras[1][0] if len(palavras) > 1 else palavras[0][-1])
        ).upper()
        resultado.append(
            {
                "id": p.id,
                "ini": iniciais,
                "nome": p.nome,
                "cod": p.codigo,
                "escopo": p.escopo,
                "prazo_meses": p.prazo_meses,
                "roi_esperado": p.roi_esperado,
                "payback_meses": p.payback_meses,
                "experiencia_equipe": p.experiencia_equipe,
                "nivel": p.nivel_risco,
                "exp": int(round(p.risco_global_score)),
                "viabilidade": round(p.viabilidade_score, 1),
                "status_viabilidade": p.status_viabilidade,
                "status_risco": p.status_risco,
                "rev": p.data_criacao.strftime("%d/%m/%Y"),
                "total_riscos": len(p.riscos),
                "parecer_tecnico": p.parecer_tecnico,
            }
        )
    return resultado


@app.get("/projetos/{projeto_id}")
def detalhar_projeto(projeto_id: int, db: Session = Depends(obter_banco)):
    p = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    riscos_fmt = [
        {
            "id": r.id,
            "titulo": r.titulo,
            "responsavel": r.responsavel,
            "probabilidade": r.probabilidade,
            "impacto": r.impacto,
            "criticidade_score": r.criticidade_score,
            "prioridade": r.prioridade,
        }
        for r in p.riscos
    ]

    return {
        "id": p.id,
        "codigo": p.codigo,
        "nome": p.nome,
        "escopo": p.escopo,
        "prazo_meses": p.prazo_meses,
        "roi_esperado": p.roi_esperado,
        "payback_meses": p.payback_meses,
        "experiencia_equipe": p.experiencia_equipe,
        "viabilidade_score": round(p.viabilidade_score, 1),
        "status_viabilidade": p.status_viabilidade,
        "risco_global_score": round(p.risco_global_score, 1),
        "nivel_risco": p.nivel_risco,
        "status_risco": p.status_risco,
        "parecer_tecnico": p.parecer_tecnico,
        "riscos": riscos_fmt,
    }


@app.post("/projetos/{projeto_id}/riscos")
def adicionar_risco_projeto(
    projeto_id: int, risco: RiscoCreate, db: Session = Depends(obter_banco)
):
    p = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Usa o seu MotorDeRisco determinístico para calcular score e prioridade
    processado = motor.processar_variaveis_escopo(
        [
            {
                "nome": risco.titulo,
                "probabilidade": risco.probabilidade,
                "impacto": risco.impacto,
            }
        ]
    )[0]

    novo_risco = models.Risco(
        projeto_id=p.id,
        titulo=risco.titulo,
        responsavel=risco.responsavel,
        probabilidade=risco.probabilidade,
        impacto=risco.impacto,
        criticidade_score=processado["criticidade_score"],
        prioridade=processado["prioridade"],
    )

    db.add(novo_risco)
    db.commit()
    db.refresh(p)  # garante que p.riscos já inclui o risco recém-criado
    recalcular_metricas_projeto(p, db)
    return {"mensagem": "Risco adicionado e métricas recalculadas com sucesso."}


@app.post("/projetos/{projeto_id}/analisar-ia")
def gerar_parecer_ia_projeto(projeto_id: int, db: Session = Depends(obter_banco)):
    p = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    if not p.riscos:
        raise HTTPException(
            status_code=400,
            detail="Cadastre ao menos um risco antes de gerar o parecer da IA.",
        )

    riscos_brutos: list[RiscoEntrada] = [
        {"nome": r.titulo, "probabilidade": r.probabilidade, "impacto": r.impacto}
        for r in p.riscos
    ]
    relatorio_riscos = motor.processar_variaveis_escopo(riscos_brutos)

    escopo_completo = (
        f"Projeto: {p.nome}. Escopo: {p.escopo}. "
        f"Prazo: {p.prazo_meses} meses, ROI Esperado: {p.roi_esperado}%, "
        f"Payback: {p.payback_meses} meses, Experiência da Equipe: {p.experiencia_equipe}."
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

    p.parecer_tecnico = parecer
    db.commit()
    return {"parecer_tecnico": parecer}


@app.get("/dashboard")
def obter_dashboard(db: Session = Depends(obter_banco)):
    projetos = (
        db.query(models.Projeto).order_by(models.Projeto.data_criacao.desc()).all()
    )
    riscos = db.query(models.Risco).all()

    total_projetos = len(projetos)
    aprovados = sum(1 for p in projetos if p.status_viabilidade == STATUS_APROVADO)
    taxa_aprovados = (
        round((aprovados / total_projetos) * 100, 1) if total_projetos > 0 else 0.0
    )

    riscos_criticos = sum(1 for r in riscos if r.prioridade == "Alta")
    viabilidade_media = (
        round(sum(p.viabilidade_score for p in projetos) / total_projetos, 1)
        if total_projetos > 0
        else 0.0
    )

    # Agrupa riscos reais na matriz 5x5 para posicionar os marcadores no Mapa de Exposição
    contagem_celulas: dict[tuple[int, int], int] = {}
    for r in riscos:
        chave = (r.probabilidade, r.impacto)
        contagem_celulas[chave] = contagem_celulas.get(chave, 0) + 1

    marcadores_heatmap = []
    for (prob, imp), qtd in contagem_celulas.items():
        # Converte prob (1..5) para X% e imp (1..5) para Y% (topo = impacto 5)
        x_pct = round((prob - 0.5) * 20, 1)
        y_pct = round((5 - imp + 0.5) * 20, 1)
        score_celula = prob * imp
        cor = (
            "#d65b48"
            if score_celula >= 15
            else "#e2a13b"
            if score_celula >= 8
            else "#4c9a87"
        )
        marcadores_heatmap.append({"qtd": qtd, "x": x_pct, "y": y_pct, "cor": cor})

    # Série de evolução baseada nos projetos cadastrados
    serie_evolucao = []
    eixo_x = []
    projetos_cronologicos = list(reversed(projetos))
    for idx, p in enumerate(projetos_cronologicos):
        serie_evolucao.append({"indice": idx, "valor": round(p.risco_global_score, 1)})
        eixo_x.append(p.codigo)

    # Lista formatada para a tabela de Análises Recentes
    projetos_lista = listar_projetos(db)

    return {
        "kpis": {
            "total_projetos": total_projetos,
            "taxa_aprovados": taxa_aprovados,
            "riscos_criticos": riscos_criticos,
            "viabilidade_media": viabilidade_media,
            "total_riscos": len(riscos),
        },
        "marcadores_mapa": marcadores_heatmap,
        "serie_evolucao": serie_evolucao,
        "eixo_x": eixo_x,
        "projetos": projetos_lista,
    }
