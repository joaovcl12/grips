import uvicorn


def main() -> None:
    print("Iniciando o servidor da API GRIPS...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
