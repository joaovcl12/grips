from typing import Sequence, TypedDict


class RiscoEntrada(TypedDict):
    nome: str
    probabilidade: int
    impacto: int


class RiscoSaida(TypedDict):
    variavel: str
    criticidade_score: int
    prioridade: str


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
