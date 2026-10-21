import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _agora_utc() -> datetime.datetime:
    """UTC sem fuso (naive), igual ao antigo utcnow(), que está depreciado."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String, unique=True, index=True)  # PRJ-2026-01
    nome: Mapped[str] = mapped_column(String)
    escopo: Mapped[str] = mapped_column(Text, default="")
    prazo_meses: Mapped[int] = mapped_column(Integer)
    roi_esperado: Mapped[float] = mapped_column(Float)
    payback_meses: Mapped[float] = mapped_column(Float)
    experiencia_equipe: Mapped[str] = mapped_column(String)  # Alta, Média, Baixa

    # Dados calculados pelo sistema
    viabilidade_score: Mapped[float] = mapped_column(Float, default=0.0)
    # Aprovado / Com ressalvas / Restrições (derivado de viabilidade_score)
    status_viabilidade: Mapped[str] = mapped_column(String, default="Restrições")
    risco_global_score: Mapped[float] = mapped_column(Float, default=0.0)
    nivel_risco: Mapped[str] = mapped_column(String, default="Baixo")  # Baixo, Médio, Alto
    # Sem análise / Controlado / Monitorando / Em mitigação (derivado dos riscos)
    status_risco: Mapped[str] = mapped_column(String, default="Sem análise")
    parecer_tecnico: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_criacao: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=_agora_utc
    )

    # Relacionamento 1-para-Muitos com Riscos
    riscos: Mapped[list["Risco"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan"
    )


class Risco(Base):
    __tablename__ = "riscos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id"))
    titulo: Mapped[str] = mapped_column(String)
    responsavel: Mapped[str] = mapped_column(String, default="Não atribuído")
    probabilidade: Mapped[int] = mapped_column(Integer)  # 1 a 5
    impacto: Mapped[int] = mapped_column(Integer)  # 1 a 5
    criticidade_score: Mapped[int] = mapped_column(Integer)  # prob * imp (1 a 25)
    prioridade: Mapped[str] = mapped_column(String)  # Baixa, Média, Alta
    data_criacao: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=_agora_utc
    )

    projeto: Mapped["Projeto"] = relationship(back_populates="riscos")
