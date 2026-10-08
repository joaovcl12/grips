import os
import time

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

_ = load_dotenv()  # "_ =" só pra silenciar o aviso reportUnusedCallResult

# IMPORTANTE: langchain_postgres exige o driver psicopg3 na string de conexão.
STRING_CONEXAO_BD = "postgresql+psycopg://admin:adminpassword@localhost:5432/grips_db"
NOME_COLECAO = "referenciais_teoricos"

# O free tier do modelo gemini-embedding-001 permite no máximo 100
# requisições por minuto (RPM). Usamos uma margem de segurança abaixo
# disso para não estourar a cota, mesmo contando com retentativas.
TAMANHO_LOTE = 80
ESPERA_ENTRE_LOTES_SEGUNDOS = 65
MAX_TENTATIVAS_POR_LOTE = 5
ESPERA_INICIAL_RETRY_SEGUNDOS = 35


def _dividir_em_lotes(lista: list, tamanho: int) -> list[list]:
    return [lista[i : i + tamanho] for i in range(0, len(lista), tamanho)]


def _embutir_lote_com_retry(
    vetor_store: PGVector | None, embedding, lote, engine_args
) -> PGVector:
    """
    Envia um lote de documentos para embedding + persistência, com
    retentativa automática caso a API do Gemini retorne 429
    (RESOURCE_EXHAUSTED / limite de requisições por minuto excedido).
    """
    tentativa = 1
    espera = ESPERA_INICIAL_RETRY_SEGUNDOS

    while True:
        try:
            if vetor_store is None:
                # primeiro lote: cria a coleção/tabela no Postgres
                return PGVector.from_documents(
                    embedding=embedding,
                    documents=lote,
                    **engine_args,
                )
            else:
                vetor_store.add_documents(lote)
                return vetor_store
        except Exception as erro:
            mensagem = str(erro)
            e_erro_de_cota = "RESOURCE_EXHAUSTED" in mensagem or "429" in mensagem

            if not e_erro_de_cota or tentativa >= MAX_TENTATIVAS_POR_LOTE:
                raise

            print(
                f"  Limite de requisições da API atingido (tentativa {tentativa}/"
                f"{MAX_TENTATIVAS_POR_LOTE}). Aguardando {espera}s antes de tentar de novo..."
            )
            time.sleep(espera)
            tentativa += 1
            espera *= 2  # backoff exponencial para tentativas subsequentes


def alimentar_base_conhecimento(caminho_pdf: str) -> None:
    """Extrai texto de um PDF, gera embeddings e guarda no PostgreSQL (pgvector)."""
    print(f"Iniciando extração do documento: {caminho_pdf}")

    carregador = PyPDFLoader(caminho_pdf)
    paginas = carregador.load()

    divisor_texto = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    blocos_documento = divisor_texto.split_documents(paginas)

    print(f"O documento foi dividido em {len(blocos_documento)} blocos semânticos.")

    modelo_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    lotes = _dividir_em_lotes(blocos_documento, TAMANHO_LOTE)
    print(
        f"Processando em {len(lotes)} lote(s) de até {TAMANHO_LOTE} blocos, "
        f"respeitando o limite de 100 req/min do free tier..."
    )

    vetor_store: PGVector | None = None
    engine_args = {
        "collection_name": NOME_COLECAO,
        "connection": STRING_CONEXAO_BD,
        "use_jsonb": True,
    }

    for indice, lote in enumerate(lotes, start=1):
        print(
            f"Lote {indice}/{len(lotes)}: gerando embeddings e persistindo no PostgreSQL..."
        )
        vetor_store = _embutir_lote_com_retry(
            vetor_store, modelo_embeddings, lote, engine_args
        )

        # Pausa entre lotes para não estourar o limite de requisições por
        # minuto (não é necessário depois do último lote).
        if indice < len(lotes):
            time.sleep(ESPERA_ENTRE_LOTES_SEGUNDOS)

    print("Base de conhecimento vetorial atualizada com sucesso!")


if __name__ == "__main__":
    documento_teste = "documentos/pmbok.pdf"

    if os.path.exists(documento_teste):
        alimentar_base_conhecimento(documento_teste)
    else:
        print(f"ERRO: o documento '{documento_teste}' não foi encontrado")
