import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

senha_banco = os.getenv("POSTGRES_PASSWORD")
# A string de conexão com o PostgreSQL que está rodando no seu Docker
URL_BANCO_DADOS = f"postgresql://admin:{senha_banco}@localhost:5432/grips_db"

engine = create_engine(URL_BANCO_DADOS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Classe base declarativa (estilo SQLAlchemy 2.0). Substitui o antigo
    `declarative_base()` e é o que permite usar `Mapped[...]` nos models,
    dando tipagem real aos atributos das instâncias.
    """

    pass


# Função auxiliar para injetar a sessão do banco nas rotas da API
def obter_banco():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
