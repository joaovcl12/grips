"""
Migração única: separa `projetos.status` em `status_viabilidade` e `status_risco`.

Passos (idempotente, pode rodar mais de uma vez):
  1. cria as duas colunas novas, se ainda não existirem;
  2. recalcula viabilidade (fórmula nova) e exposição/status de risco de TODOS
     os projetos existentes, usando os mesmos motores da API;
  3. remove a coluna antiga `status`.

Uso (na raiz do projeto, com o Postgres do Docker ligado):
    python -m scripts.migrar_status
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import models
from backend.database import engine
from backend.servico_projetos import atualizar_exposicao, atualizar_viabilidade


def migrar() -> None:
    with engine.begin() as conexao:
        conexao.execute(
            text(
                "ALTER TABLE projetos "
                "ADD COLUMN IF NOT EXISTS status_viabilidade VARCHAR, "
                "ADD COLUMN IF NOT EXISTS status_risco VARCHAR"
            )
        )

    with Session(engine) as sessao:
        projetos = sessao.query(models.Projeto).all()
        for projeto in projetos:
            atualizar_viabilidade(projeto)
            atualizar_exposicao(projeto)
        sessao.commit()
        print(f"{len(projetos)} projeto(s) recalculado(s).")

    with engine.begin() as conexao:
        conexao.execute(text("ALTER TABLE projetos DROP COLUMN IF EXISTS status"))

    print("Migração concluída.")


if __name__ == "__main__":
    migrar()
