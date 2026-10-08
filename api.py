import datetime
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import Base, engine, obter_banco

app = FastAPI()

# Cria as tabelas no banco de dados assim que a API inicia
Base.metadata.create_all(bind=engine)

# Alias de tipo: substitui "db: Session = Depends(obter_banco)" em cada rota
# (Ruff B008 não permite mais chamar Depends() direto no valor padrão).
SessaoBanco = Annotated[Session, Depends(obter_banco)]


# --- NOVOS MODELOS DE VALIDAÇÃO (Pydantic) ---
class ProjetoEntrada(BaseModel):
    nome: str
    prazo_meses: int
    roi_esperado: float
    payback_meses: float
    experiencia_equipe: str


# --- NOVAS ROTAS ---


@app.post("/projetos")
def cadastrar_projeto(projeto: ProjetoEntrada, db: SessaoBanco):
    """
    Recebe os dados do modal de Novo Projeto, calcula a viabilidade inicial,
    gera o código único e salva no banco de dados.
    """

    # 1. Gerar Código Único (Ex: PRJ-2026-001)
    ano_atual = datetime.datetime.now(datetime.UTC).year
    # Conta quantos projetos já existem para gerar o número sequencial
    total_projetos = db.query(models.Projeto).count()
    codigo_gerado = f"PRJ-{ano_atual}-{total_projetos + 1:03d}"

    # 2. Motor de Cálculo de Viabilidade (Fórmula Inicial Ajustável)
    # Exemplo: Começa em 50%, soma metade do ROI, subtrai o dobro do Payback.
    # Ajusta com base na experiência da equipe.
    viabilidade = 50.0 + (projeto.roi_esperado / 2) - (projeto.payback_meses * 2)

    if projeto.experiencia_equipe.lower() == "alta":
        viabilidade += 20.0
    elif projeto.experiencia_equipe.lower() == "baixa":
        viabilidade -= 20.0

    # Garante que a viabilidade fique entre 0 e 100%
    viabilidade = max(0.0, min(100.0, viabilidade))

    # Define o status inicial baseado na viabilidade
    status_inicial = (
        "Aprovado"
        if viabilidade >= 75
        else "Restrições"
        if viabilidade >= 50
        else "Reprovado"
    )

    # 3. Salvar no Banco de Dados
    novo_projeto = models.Projeto(
        codigo=codigo_gerado,
        nome=projeto.nome,
        prazo_meses=projeto.prazo_meses,
        roi_esperado=projeto.roi_esperado,
        payback_meses=projeto.payback_meses,
        experiencia_equipe=projeto.experiencia_equipe,
        viabilidade_score=viabilidade,
        status=status_inicial,
    )

    db.add(novo_projeto)
    db.commit()
    db.refresh(novo_projeto)

    return novo_projeto


@app.get("/dashboard")
def obter_dados_dashboard(db: SessaoBanco):
    """
    Entrega todas as estatísticas calculadas e os projetos recentes para o front-end.
    """
    projetos = (
        db.query(models.Projeto).order_by(models.Projeto.data_criacao.desc()).all()
    )

    total = len(projetos)
    aprovados = sum(1 for p in projetos if p.status == "Aprovado")

    taxa_aprovacao = (aprovados / total * 100) if total > 0 else 0

    # Por enquanto, como os riscos globais e críticos serão mapeados depois (na matriz 5x5),
    # deixamos valores base calculados a partir dos projetos.

    return {
        "indicadores": {
            "total_projetos": total,
            "taxa_aprovacao": round(taxa_aprovacao, 1),
            "riscos_criticos_ativos": 0,  # Será calculado na rota de matriz depois
            "score_medio_risco": 0.0,  # Será calculado depois
        },
        "analises_recentes": [
            {
                "codigo": p.codigo,
                "projeto": p.nome,
                "risco_global": f"{p.risco_global_score}%",
                "viabilidade": f"{p.viabilidade_score:.1f}%",
                "status": p.status,
            }
            for p in projetos
        ],
    }
