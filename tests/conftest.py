import os

# O módulo database cria o engine do Postgres ao ser importado (sem conectar).
# Nos testes basta existir uma senha; o banco real nunca é tocado.
os.environ.setdefault("POSTGRES_PASSWORD", "senha-de-teste")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from backend import models  # noqa: E402
from backend.api import app  # noqa: E402
from backend.database import obter_banco  # noqa: E402


@pytest.fixture()
def client():
    """Cliente HTTP da API ligado a um SQLite em memória (um banco novo por teste)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(engine)
    sessao = sessionmaker(bind=engine, autoflush=False)

    def banco_de_teste():
        db = sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[obter_banco] = banco_de_teste
    yield TestClient(app)  # sem `with`: o ciclo de vida (create_all no Postgres) não roda
    app.dependency_overrides.clear()
