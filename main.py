"""Ponto de entrada da API. Uso (na raiz do projeto): python main.py"""

import uvicorn


def main() -> None:
    print("Iniciando o servidor da API GRIPS em http://127.0.0.1:8000 ...")
    uvicorn.run(
        "backend.api:app",
        host="127.0.0.1",  # sem autenticação por enquanto: não expor na rede local
        port=8000,
        reload=True,
        reload_dirs=["backend"],  # vigia só o código, não o venv nem os PDFs
    )


if __name__ == "__main__":
    main()
