import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Projeto(Base):
    __tablename__ = "projetos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)  # Ex: PRJ-2026-001
    nome = Column(String, nullable=False)
    escopo = Column(Text, default="")
    prazo_meses = Column(Integer, nullable=False)
    roi_esperado = Column(Float, nullable=False)
    payback_meses = Column(Float, nullable=False)
    experiencia_equipe = Column(String, nullable=False)  # Alta, Média, Baixa

    # Dados calculados pelo sistema
    viabilidade_score = Column(Float, default=0.0)
    # Aprovado / Com ressalvas / Restrições  (derivado de viabilidade_score)
    status_viabilidade = Column(String, default="Restrições")
    risco_global_score = Column(Float, default=0.0)
    nivel_risco = Column(String, default="Baixo")  # Baixo, Médio, Alto
    # Sem análise / Controlado / Monitorando / Em mitigação  (derivado dos riscos)
    status_risco = Column(String, default="Sem análise")
    parecer_tecnico = Column(Text, nullable=True)

    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)

    # Relacionamento 1-para-Muitos com Riscos
    riscos = relationship(
        "Risco", back_populates="projeto", cascade="all, delete-orphan"
    )


class Risco(Base):
    __tablename__ = "riscos"

    id = Column(Integer, primary_key=True, index=True)
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    titulo = Column(String, nullable=False)
    responsavel = Column(String, default="Não atribuído")
    probabilidade = Column(Integer, nullable=False)  # 1 a 5
    impacto = Column(Integer, nullable=False)  # 1 a 5
    criticidade_score = Column(Integer, nullable=False)  # prob * imp (1 a 25)
    prioridade = Column(String, nullable=False)  # Baixa, Média, Alta
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)

    projeto = relationship("Projeto", back_populates="riscos")
