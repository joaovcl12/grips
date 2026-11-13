"""Contratos da API (Pydantic): o que entra e o que sai de cada rota."""

import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Experiencia = Literal["Alta", "Média", "Baixa"]
RESPONSAVEL_PADRAO = "Equipe Técnica"


def _preenchido(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise ValueError("não pode ficar em branco")
    return valor


# ── Entrada ──────────────────────────────────────────────────────────────────
class ProjetoIn(BaseModel):
    nome: str = Field(max_length=200)
    escopo: str = ""
    prazo_meses: int = Field(gt=0, le=600)
    roi_esperado: float = Field(ge=-100)
    payback_meses: float = Field(ge=0)
    experiencia_equipe: Experiencia

    @field_validator("nome")
    @classmethod
    def _nome_preenchido(cls, valor: str) -> str:
        return _preenchido(valor)

    @field_validator("escopo")
    @classmethod
    def _escopo_sem_bordas(cls, valor: str) -> str:
        return valor.strip()


class RiscoIn(BaseModel):
    titulo: str = Field(max_length=200)
    responsavel: str = RESPONSAVEL_PADRAO
    probabilidade: int = Field(ge=1, le=5)
    impacto: int = Field(ge=1, le=5)

    @field_validator("titulo")
    @classmethod
    def _titulo_preenchido(cls, valor: str) -> str:
        return _preenchido(valor)

    @field_validator("responsavel")
    @classmethod
    def _responsavel_ou_padrao(cls, valor: str) -> str:
        return valor.strip() or RESPONSAVEL_PADRAO


# ── Saída ────────────────────────────────────────────────────────────────────
class RiscoOut(BaseModel):
    id: int
    titulo: str
    responsavel: str
    probabilidade: int
    impacto: int
    criticidade_score: int
    prioridade: str


class ProjetoOut(BaseModel):
    id: int
    codigo: str
    nome: str
    escopo: str
    prazo_meses: int
    roi_esperado: float
    payback_meses: float
    experiencia_equipe: str
    viabilidade_score: float
    status_viabilidade: str
    risco_global_score: float
    nivel_risco: str
    status_risco: str
    parecer_tecnico: str | None
    rev: str  # data de criação (dd/mm/aaaa)
    riscos: list[RiscoOut]


class HistoricoOut(BaseModel):
    data: datetime.datetime  # UTC
    exposicao: float
    nivel: str
    total_riscos: int


class ParecerOut(BaseModel):
    parecer_tecnico: str
