import datetime

from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(unique=True, index=True)  # Ex: PRJ-2026-001
    nome: Mapped[str] = mapped_column(nullable=False)
    prazo_meses: Mapped[int] = mapped_column()
    roi_esperado: Mapped[float] = mapped_column()
    payback_meses: Mapped[float] = mapped_column()
    experiencia_equipe: Mapped[str] = mapped_column()  # Alta, Media, Baixa

    # Dados calculados pelo sistema
    viabilidade_score: Mapped[float] = mapped_column(default=0.0)
    risco_global_score: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(
        default="Pendente"
    )  # Aprovado, Restrições, Reprovado

    data_criacao: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC)
    )
