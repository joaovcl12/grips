import re
from pathlib import Path
from typing import Sequence, TypedDict

from google import genai
from google.genai import types
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

from backend.config import (
    GEMINI_MODEL,
    NOME_COLECAO_VETORIAL,
    obter_chave_gemini,
    url_banco,
)
from backend.motor_riscos import RiscoSaida

# ── Parâmetros da recuperação (RAG) ───────────────────────────────────────────
MAX_RISCOS_BUSCADOS = 5  # só os mais críticos geram consulta (1 chamada de embedding cada)
TRECHOS_POR_RISCO = 3  # candidatos recuperados por consulta
MAX_TRECHOS_CONTEXTO = 8  # teto de trechos enviados ao modelo
TIMEOUT_API_MS = 60_000


class ErroParecer(Exception):
    """Falha ao gerar o parecer: base vazia, banco/embeddings fora do ar ou erro do Gemini."""


class Trecho(TypedDict):
    numero: int
    fonte: str
    pagina: str
    texto: str


def _rotulo_pagina(metadados: dict) -> str:
    """Página do PDF. PyPDFLoader guarda `page` começando em 0; `page_label` (se existir) vem pronto."""
    rotulo = metadados.get("page_label")
    if rotulo:
        return str(rotulo)
    pagina = metadados.get("page")
    return str(pagina + 1) if isinstance(pagina, int) else "?"


class AgenteDiagnostico:
    client: genai.Client
    banco_vetorial: PGVector

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=obter_chave_gemini(),
            http_options=types.HttpOptions(timeout=TIMEOUT_API_MS),
        )

        modelo_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )
        self.banco_vetorial = PGVector(
            embeddings=modelo_embeddings,
            collection_name=NOME_COLECAO_VETORIAL,
            connection=url_banco(),
            use_jsonb=True,
        )

    def buscar_trechos_literatura(self, riscos: Sequence[RiscoSaida]) -> list[Trecho]:
        """
        Faz uma consulta vetorial por risco (os mais críticos primeiro, pois o
        motor já entrega a lista ordenada por score), remove trechos repetidos
        e devolve os melhores, numerados para serem citados no parecer.
        """
        melhores: dict[str, tuple[float, Document]] = {}

        for risco in riscos[:MAX_RISCOS_BUSCADOS]:
            consulta = (
                "mitigação e resposta ao risco em projetos de software: "
                f"{risco['variavel']}"
            )
            resultados = self.banco_vetorial.similarity_search_with_score(
                consulta, k=TRECHOS_POR_RISCO
            )
            for doc, distancia in resultados:
                # distância menor = mais parecido; se o mesmo trecho aparecer
                # em várias consultas, fica com a melhor.
                atual = melhores.get(doc.page_content)
                if atual is None or distancia < atual[0]:
                    melhores[doc.page_content] = (distancia, doc)

        ordenados = sorted(melhores.values(), key=lambda par: par[0])
        trechos: list[Trecho] = []
        for numero, (_, doc) in enumerate(ordenados[:MAX_TRECHOS_CONTEXTO], start=1):
            trechos.append(
                {
                    "numero": numero,
                    "fonte": Path(str(doc.metadata.get("source", "documento"))).name,
                    "pagina": _rotulo_pagina(doc.metadata),
                    "texto": doc.page_content.strip(),
                }
            )
        return trechos

    @staticmethod
    def _formatar_contexto(trechos: Sequence[Trecho]) -> str:
        return "\n\n".join(
            f"[{t['numero']}] ({t['fonte']}, p. {t['pagina']})\n{t['texto']}"
            for t in trechos
        )

    @staticmethod
    def _formatar_fontes(texto_parecer: str, trechos: Sequence[Trecho]) -> str:
        """Lista de fontes montada pelo código (o modelo não escreve referências)."""
        citados = {int(n) for n in re.findall(r"\[(\d+)\]", texto_parecer)}
        usados = [t for t in trechos if t["numero"] in citados]
        titulo = "**Fontes citadas no parecer**"
        if not usados:
            usados = list(trechos)
            titulo = "**Trechos consultados** (o parecer não citou fontes explicitamente)"
        linhas = "\n".join(
            f"- [{t['numero']}] {t['fonte']}, p. {t['pagina']}" for t in usados
        )
        return f"\n\n---\n{titulo}\n\n{linhas}"

    def gerar_parecer_tecnico(
        self, escopo_projeto: str, riscos_identificados: Sequence[RiscoSaida]
    ) -> str:
        """Retorna o parecer em Markdown, já com a lista de fontes. Levanta ErroParecer em falhas."""
        try:
            trechos = self.buscar_trechos_literatura(riscos_identificados)
        except Exception as erro:
            raise ErroParecer(f"Falha ao consultar a base vetorial: {erro}") from erro

        if not trechos:
            raise ErroParecer(
                "Nenhum trecho encontrado na base de conhecimento. "
                "Rode a ingestão (python -m scripts.ingestao_pdf) antes de gerar o parecer."
            )

        lista_riscos = "\n".join(
            f"- {r['variavel']} (score {r['criticidade_score']}/25, prioridade {r['prioridade']})"
            for r in riscos_identificados
        )

        prompt = f"""
Você é um analista sênior de riscos em projetos de software.

REGRAS ABSOLUTAS:
1. Baseie o parecer e as mitigações EXCLUSIVAMENTE nos trechos numerados abaixo.
   Não use conhecimento externo.
2. Ao propor uma mitigação, cite o trecho que a sustenta no formato [n], por exemplo [2].
3. Se nenhum trecho cobrir um risco, escreva literalmente: "A base consultada não traz
   mitigação específica para este risco." Não invente mitigações.
4. Seja sucinto e use Markdown. Trate os riscos na ordem recebida (do mais crítico ao menos).
5. Não escreva lista de referências; ela será adicionada automaticamente.

[BASE DE CONHECIMENTO — TRECHOS RECUPERADOS]
{self._formatar_contexto(trechos)}

[DADOS DO PROJETO]
Escopo: {escopo_projeto}

Riscos mapeados:
{lista_riscos}

Gere o parecer técnico diagnóstico: uma visão geral de 2 a 3 frases e, para cada risco,
o diagnóstico curto seguido das mitigações com suas citações.
"""

        try:
            resposta = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
        except Exception as erro:
            raise ErroParecer(f"Falha ao consultar a API do Gemini: {erro}") from erro

        texto = (resposta.text or "").strip()
        if not texto:
            raise ErroParecer("A API do Gemini retornou uma resposta vazia.")

        return texto + self._formatar_fontes(texto, trechos)
