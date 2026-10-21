"""
Configuração centralizada do GRIPS.

Tudo vem do arquivo .env (veja .env.example): nenhuma senha ou chave fica no
código. Importar este módulo também carrega o .env para o processo, o que
inclui as variáveis usadas pelas bibliotecas de embeddings.
"""

import os
from typing import Final

from dotenv import load_dotenv
from sqlalchemy.engine import URL

_ = load_dotenv()

# ── Banco de dados (PostgreSQL + pgvector no Docker) ──────────────────────────
POSTGRES_USER: Final[str] = os.getenv("POSTGRES_USER", "admin")
POSTGRES_DB: Final[str] = os.getenv("POSTGRES_DB", "grips_db")
POSTGRES_HOST: Final[str] = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT: Final[int] = int(os.getenv("POSTGRES_PORT", "5432"))

# Coleção do pgvector onde ficam os trechos dos referenciais teóricos
NOME_COLECAO_VETORIAL: Final[str] = "referenciais_teoricos"

# ── IA (Gemini) ───────────────────────────────────────────────────────────────
GEMINI_MODEL: Final[str] = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# ── API ───────────────────────────────────────────────────────────────────────
CORS_ORIGINS: Final[list[str]] = [
    origem.strip()
    for origem in os.getenv(
        "CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"
    ).split(",")
    if origem.strip()
]


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(f"Variável {nome} não encontrada no arquivo .env")
    return valor


def obter_chave_gemini() -> str:
    return _obrigatoria("GEMINI_API_KEY")


def url_banco() -> str:
    """
    URL única do PostgreSQL (driver psycopg 3), usada pelo SQLAlchemy, pelo
    pgvector e pelos scripts. A senha é escapada corretamente, mesmo com
    caracteres especiais.
    """
    return URL.create(
        drivername="postgresql+psycopg",
        username=POSTGRES_USER,
        password=_obrigatoria("POSTGRES_PASSWORD"),
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
    ).render_as_string(hide_password=False)
