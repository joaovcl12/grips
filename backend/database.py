from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import url_banco

# pool_pre_ping evita erro de conexão quebrada quando o contêiner do Docker reinicia
engine = create_engine(url_banco(), pool_pre_ping=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base declarativa (SQLAlchemy 2.0): permite usar `Mapped[...]` nos models."""


def obter_banco() -> Iterator[Session]:
    """Dependência do FastAPI: abre uma sessão por requisição e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
