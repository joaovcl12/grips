"""
Dados fictícios usados só quando a API está fora do ar (modo demonstração).
Nada daqui é gravado em lugar nenhum.
"""

import datetime
from statistics import mean

from constantes import prioridade


def _exposicao(riscos: list[dict]) -> tuple[float, str, str]:
    if not riscos:
        return 0.0, "Baixo", "Sem análise"
    exp = round(mean(r["criticidade_score"] for r in riscos) / 25 * 100, 1)
    if exp >= 60 or any(r["prioridade"] == "Alta" for r in riscos):
        return exp, "Alto", "Em mitigação"
    if exp >= 35:
        return exp, "Médio", "Monitorando"
    return exp, "Baixo", "Controlado"


def _viabilidade(prazo: int, roi: float, payback: float, equipe: str) -> tuple[float, str]:
    def lim(v: float) -> float:
        return max(0.0, min(1.0, v))

    nota_equipe = {"Alta": 1.0, "Média": 0.5, "Baixa": 0.0}[equipe]
    total = (
        0.30 * lim(roi / 100)
        + 0.25 * (1 - lim(payback / 36))
        + 0.15 * (1 - lim(prazo / 36))
        + 0.30 * nota_equipe
    )
    v = round(total * 100, 1)
    return v, ("Aprovado" if v >= 70 else "Com ressalvas" if v >= 45 else "Restrições")


def _projeto(id_, nome, escopo, prazo, roi, payback, equipe, riscos_brutos, parecer=None) -> dict:
    riscos = []
    for n, (titulo, resp, prob, imp) in enumerate(riscos_brutos, start=1):
        score = prob * imp
        riscos.append({
            "id": id_ * 100 + n, "titulo": titulo, "responsavel": resp,
            "probabilidade": prob, "impacto": imp,
            "criticidade_score": score, "prioridade": prioridade(score),
        })
    exp, nivel, status_risco = _exposicao(riscos)
    viab, status_viab = _viabilidade(prazo, roi, payback, equipe)
    return {
        "id": id_, "codigo": f"PRJ-2026-{id_:02d}", "nome": nome, "escopo": escopo,
        "prazo_meses": prazo, "roi_esperado": roi, "payback_meses": payback,
        "experiencia_equipe": equipe, "viabilidade_score": viab,
        "status_viabilidade": status_viab, "risco_global_score": exp,
        "nivel_risco": nivel, "status_risco": status_risco,
        "parecer_tecnico": parecer, "riscos": riscos, "rev": "20/10/2026",
    }


def projetos_demo() -> list[dict]:
    parecer = (
        "**Visão geral.** A integração depende de uma API parceira sem SLA formal, "
        "o que concentra a exposição do projeto.\n\n"
        "**Indisponibilidade da API parceira (score 12).** Definir contrato de nível de "
        "serviço e implementar tentativas com recuo exponencial [1].\n\n"
        "---\n**Fontes citadas no parecer**\n\n- [1] pmbok.pdf, p. 441"
    )
    return [
        _projeto(1, "Migração Cloud AWS", "Migração dos serviços legados para a AWS.", 12, 60, 14, "Alta",
                 [("Falta de conhecimento em IaC", "João Vitor", 4, 5),
                  ("Estouro de custos de nuvem", "Rickson", 3, 4),
                  ("Janela de migração curta", "João Vitor", 4, 4)]),
        _projeto(2, "Portal do Cliente 2.0", "Novo portal com autoatendimento.", 8, 35, 10, "Média",
                 [("Indisponibilidade da API parceira", "Rickson", 3, 4),
                  ("Mudança de escopo", "João Vitor", 3, 3)], parecer),
        _projeto(3, "Integração ERP Financeiro", "Integração do ERP com o módulo fiscal.", 10, 45, 18, "Baixa",
                 [("Dados legados inconsistentes", "Rickson", 2, 3)]),
        _projeto(4, "App Operações", "Aplicativo de campo para as equipes de operação.", 6, 80, 6, "Alta", []),
    ]


def historico_demo(projeto: dict) -> list[dict]:
    """Evolução fictícia: um ponto por risco adicionado, a cada 3 dias."""
    inicio = datetime.datetime(2026, 10, 20, 12, 0)
    pontos = [{"data": inicio.isoformat(), "exposicao": 0.0, "nivel": "Baixo", "total_riscos": 0}]
    acumulados: list[dict] = []
    for i, risco in enumerate(projeto["riscos"], start=1):
        acumulados.append(risco)
        exp, nivel, _ = _exposicao(acumulados)
        pontos.append({
            "data": (inicio + datetime.timedelta(days=3 * i)).isoformat(),
            "exposicao": exp, "nivel": nivel, "total_riscos": i,
        })
    return pontos
