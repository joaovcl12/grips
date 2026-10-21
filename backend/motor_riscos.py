from typing import Final, Sequence, TypedDict

# ── Regras de exposição global do projeto ─────────────────────────────────────
LIMIAR_EXPOSICAO_ALTA: Final[float] = 60.0  # % da escala máxima (média dos scores)
LIMIAR_EXPOSICAO_MEDIA: Final[float] = 35.0

STATUS_SEM_ANALISE: Final[str] = "Sem análise"  # projeto ainda sem riscos mapeados
STATUS_EM_MITIGACAO: Final[str] = "Em mitigação"
STATUS_MONITORANDO: Final[str] = "Monitorando"
STATUS_CONTROLADO: Final[str] = "Controlado"


class RiscoEntrada(TypedDict):
    nome: str
    probabilidade: int
    impacto: int


class RiscoSaida(TypedDict):
    variavel: str
    criticidade_score: int
    prioridade: str


class ExposicaoProjeto(TypedDict):
    exposicao_pct: float
    nivel: str
    status: str


class MotorDeRisco:
    escala_maxima: int = 25

    def calcular_criticidade(self, probabilidade: int, impacto: int) -> int:
        """
        Cruza matematicamente as chances de ocorrência com a gravidade.
        """
        if not (1 <= probabilidade <= 5) or not (1 <= impacto <= 5):
            raise ValueError("Probabilidade e Impacto devem estar entre 1 e 5.")

        return probabilidade * impacto

    def classificar_risco(self, criticidade: int) -> str:
        """
        Classifica a prioridade da ameaça operacional com base na criticidade.
        """
        if criticidade >= 15:
            return "Alta"
        elif criticidade >= 8:
            return "Média"
        else:
            return "Baixa"

    def avaliar_exposicao_projeto(
        self, scores: Sequence[int], prioridades: Sequence[str]
    ) -> ExposicaoProjeto:
        """
        Consolida os riscos de um projeto em exposição (%), nível e status.

        Regra de decisão (princípio da precaução): a média dos scores dilui
        riscos isolados muito graves, então QUALQUER risco de prioridade
        "Alta" eleva o projeto para o nível "Alto", mesmo que a exposição
        média esteja baixa.
        """
        if not scores:
            return {
                "exposicao_pct": 0.0,
                "nivel": "Baixo",
                "status": STATUS_SEM_ANALISE,
            }

        media = sum(scores) / len(scores)
        exposicao = round((media / self.escala_maxima) * 100, 1)

        if exposicao >= LIMIAR_EXPOSICAO_ALTA or "Alta" in prioridades:
            nivel, status = "Alto", STATUS_EM_MITIGACAO
        elif exposicao >= LIMIAR_EXPOSICAO_MEDIA:
            nivel, status = "Médio", STATUS_MONITORANDO
        else:
            nivel, status = "Baixo", STATUS_CONTROLADO

        return {"exposicao_pct": exposicao, "nivel": nivel, "status": status}

    def processar_variaveis_escopo(
        self, riscos_operacionais: Sequence[RiscoEntrada]
    ) -> list[RiscoSaida]:
        """
        Processa uma lista de entradas brutas do formulário estruturado.

        Usamos `Sequence` (covariante) em vez de `list` (invariante) no
        parâmetro porque aqui só fazemos leitura dos itens — isso permite
        que o type checker aceite `list[RiscoEntrada]` sem reclamar de
        incompatibilidade de tipos genéricos.
        """
        relatorio_basico: list[RiscoSaida] = []

        for risco in riscos_operacionais:
            criticidade = self.calcular_criticidade(
                risco["probabilidade"], risco["impacto"]
            )
            classificacao = self.classificar_risco(criticidade)

            relatorio_basico.append(
                {
                    "variavel": risco["nome"],
                    "criticidade_score": criticidade,
                    "prioridade": classificacao,
                }
            )

        relatorio_basico.sort(key=lambda x: x["criticidade_score"], reverse=True)
        return relatorio_basico
