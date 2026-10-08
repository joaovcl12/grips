import os
from typing import Sequence

from dotenv import load_dotenv
from google import genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

from motor_riscos import RiscoSaida

_ = load_dotenv()

MODELO_PADRAO = "gemini-3.6-flash"
STRING_CONEXAO_BD = "postgresql+psycopg://admin:adminpassword@localhost:5432/grips_db"
NOME_COLECAO = "referenciais_teoricos"


class AgenteDiagnostico:
    client: genai.Client
    banco_vetorial: PGVector

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Chave da API não encontrada no arquivo .env")

        self.client = genai.Client(api_key=api_key)

        modelo_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )
        self.banco_vetorial = PGVector(
            embeddings=modelo_embeddings,
            collection_name=NOME_COLECAO,
            connection=STRING_CONEXAO_BD,
            use_jsonb=True,
        )

    def buscar_contexto_literatura(self, riscos: Sequence[RiscoSaida]) -> str:
        """Busca os artigos mais relevantes no banco de dados baseados nos riscos."""
        # Cria uma string de busca baseada nos nomes dos riscos operacionais
        query_busca = " ".join([risco["variavel"] for risco in riscos])

        # O pgvector calcula a distância matemática e traz os 4 trechos mais relevantes do PMBOK
        documentos_recuperados = self.banco_vetorial.similarity_search(query_busca, k=4)

        # Concatena o texto dos blocos encontrados
        contexto = "\n\n".join([doc.page_content for doc in documentos_recuperados])
        return contexto

    def gerar_parecer_tecnico(
        self, escopo_projeto: str, riscos_identificados: Sequence[RiscoSaida]
    ) -> str:

        contexto_banco = self.buscar_contexto_literatura(riscos_identificados)

        prompt = f"""
        Você é um analista Sênior de riscos em projetos de software.

        REGRA ABSOLUTA: Baseie seu parecer e planos de mitigação EXCLUSIVAMENTE
        nos trechos da literatura fornecidos abaixo. Não invente informações externas.

        [BASE DE CONHECIMENTO (LITERATURA RECUPERADA DO BANCO DE DADOS)]
        {contexto_banco}

        [DADOS DO PROJETO ATUAL]
        Escopo: '{escopo_projeto}'
        Riscos operacionais críticos: {riscos_identificados}

        Gere um parecer técnico diagnóstico sucinto aplicando apenas as mitigações da base.
        """

        try:
            response = self.client.models.generate_content(
                model=MODELO_PADRAO,
                contents=prompt,
            )
        except Exception as erro:
            return f"Erro ao consultar a API do Gemini: {erro}"

        return response.text or "Erro: Não foi possível gerar o parecer técnico"
