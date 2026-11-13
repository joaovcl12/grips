"""
Cria o primeiro ponto do histórico de exposição dos projetos que já existiam
antes do recurso de histórico (só os que ainda não têm nenhum ponto).

Uso (na raiz do projeto, com o Postgres do Docker ligado):
    python -m scripts.iniciar_historico
"""

from sqlalchemy.orm import Session

from backend import models
from backend.database import engine
from backend.servico_projetos import registrar_historico


def iniciar() -> None:
    # Garante que a tabela nova exista, mesmo sem a API ter sido iniciada ainda
    models.Base.metadata.create_all(bind=engine)

    with Session(engine) as sessao:
        criados = 0
        for projeto in sessao.query(models.Projeto).all():
            if not projeto.historico:
                registrar_historico(projeto)
                criados += 1
        sessao.commit()
    print(f"{criados} projeto(s) receberam o ponto inicial do histórico.")


if __name__ == "__main__":
    iniciar()
