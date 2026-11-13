"""
GRIPS · Protótipo do novo front-end (v2)

Uso (na raiz do projeto):
    streamlit run frontend/exemplo_v2.py

- Com a API no ar, mostra os dados reais do banco.
- Sem a API, mostra dados de demonstração (fictícios; nada é salvo).

Ideia central: usar componentes nativos do Streamlit (navegação, métricas,
tabelas com seleção de linha, gráficos Altair, abas, modais) e deixar quase
nenhum CSS/HTML na mão. O visual vem do tema em .streamlit/config.toml.
"""

import os
from pathlib import Path
from statistics import mean

import altair as alt
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

_ = load_dotenv()

API_URL = os.getenv("GRIPS_API_URL", "http://localhost:8000")
LOGO = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(page_title="GRIPS · Gestão de Riscos", page_icon="🛡️", layout="wide")

# ──────────────────────────────────────────────────────────────────────────────
# Constantes visuais
# ──────────────────────────────────────────────────────────────────────────────
COR_NIVEL = {"Alto": "#d65b48", "Médio": "#e2a13b", "Baixo": "#4c9a87"}
COR_PRIORIDADE = {"Alta": "#d65b48", "Média": "#e2a13b", "Baixa": "#4c9a87"}
BADGE_NIVEL = {"Alto": "red", "Médio": "orange", "Baixo": "green"}
BADGE_VIABILIDADE = {
    "Aprovado": "green",
    "Com ressalvas": "orange",
    "Restrições": "red",
}
BOLINHA = {
    "Alto": "🔴",
    "Médio": "🟠",
    "Baixo": "🟢",
    "Alta": "🔴",
    "Média": "🟠",
    "Baixa": "🟢",
}
NIVEIS_PROBABILIDADE = [
    "1 · Muito baixa",
    "2 · Baixa",
    "3 · Média",
    "4 · Alta",
    "5 · Muito alta",
]
NIVEIS_IMPACTO = [
    "1 · Muito baixo",
    "2 · Baixo",
    "3 · Médio",
    "4 · Alto",
    "5 · Muito alto",
]

# Pouquíssimo CSS: só o espaçamento do topo da página.
st.markdown(
    "<style>.block-container{padding-top:2.2rem;}</style>", unsafe_allow_html=True
)


def prioridade(score: int) -> str:
    """Espelha o motor_riscos (usado só para pré-visualizar na tela)."""
    return "Alta" if score >= 15 else "Média" if score >= 8 else "Baixa"


# ──────────────────────────────────────────────────────────────────────────────
# Dados de demonstração (usados só quando a API está fora do ar)
# ──────────────────────────────────────────────────────────────────────────────
def _exposicao_demo(riscos: list[dict]) -> tuple[float, str, str]:
    if not riscos:
        return 0.0, "Baixo", "Sem análise"
    exp = round(mean(r["criticidade_score"] for r in riscos) / 25 * 100, 1)
    if exp >= 60 or any(r["prioridade"] == "Alta" for r in riscos):
        return exp, "Alto", "Em mitigação"
    if exp >= 35:
        return exp, "Médio", "Monitorando"
    return exp, "Baixo", "Controlado"


def _viabilidade_demo(
    prazo: int, roi: float, payback: float, equipe: str
) -> tuple[float, str]:
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


def _projeto_demo(
    id_, nome, escopo, prazo, roi, payback, equipe, riscos_brutos, parecer=None
):
    riscos = []
    for n, (titulo, resp, prob, imp) in enumerate(riscos_brutos, start=1):
        score = prob * imp
        riscos.append(
            {
                "id": id_ * 100 + n,
                "titulo": titulo,
                "responsavel": resp,
                "probabilidade": prob,
                "impacto": imp,
                "criticidade_score": score,
                "prioridade": prioridade(score),
            }
        )
    exp, nivel, status_risco = _exposicao_demo(riscos)
    viab, status_viab = _viabilidade_demo(prazo, roi, payback, equipe)
    return {
        "id": id_,
        "codigo": f"PRJ-2026-{id_:02d}",
        "nome": nome,
        "escopo": escopo,
        "prazo_meses": prazo,
        "roi_esperado": roi,
        "payback_meses": payback,
        "experiencia_equipe": equipe,
        "viabilidade_score": viab,
        "status_viabilidade": status_viab,
        "risco_global_score": exp,
        "nivel_risco": nivel,
        "status_risco": status_risco,
        "parecer_tecnico": parecer,
        "riscos": riscos,
        "rev": "20/10/2026",
    }


def _projetos_demo() -> list[dict]:
    parecer = (
        "**Visão geral.** A integração depende de uma API parceira sem SLA formal, "
        "o que concentra a exposição do projeto.\n\n"
        "**Indisponibilidade da API parceira (score 12).** Definir contrato de nível de "
        "serviço e implementar tentativas com recuo exponencial [1].\n\n"
        "---\n**Fontes citadas no parecer**\n\n- [1] pmbok.pdf, p. 441"
    )
    return [
        _projeto_demo(
            1,
            "Migração Cloud AWS",
            "Migração dos serviços legados para a AWS.",
            12,
            60,
            14,
            "Alta",
            [
                ("Falta de conhecimento em IaC", "João Vitor", 4, 5),
                ("Estouro de custos de nuvem", "Rickson", 3, 4),
                ("Janela de migração curta", "João Vitor", 4, 4),
            ],
        ),
        _projeto_demo(
            2,
            "Portal do Cliente 2.0",
            "Novo portal com autoatendimento.",
            8,
            35,
            10,
            "Média",
            [
                ("Indisponibilidade da API parceira", "Rickson", 3, 4),
                ("Mudança de escopo", "João Vitor", 3, 3),
            ],
            parecer,
        ),
        _projeto_demo(
            3,
            "Integração ERP Financeiro",
            "Integração do ERP com o módulo fiscal.",
            10,
            45,
            18,
            "Baixa",
            [("Dados legados inconsistentes", "Rickson", 2, 3)],
        ),
        _projeto_demo(
            4,
            "App Operações",
            "Aplicativo de campo para as equipes de operação.",
            6,
            80,
            6,
            "Alta",
            [],
        ),
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Comunicação com a API
# ──────────────────────────────────────────────────────────────────────────────
def _get(caminho: str) -> object:
    r = requests.get(f"{API_URL}{caminho}", timeout=4)
    r.raise_for_status()
    return r.json()


CAMPOS_OBRIGATORIOS = {
    "id",
    "codigo",
    "nome",
    "escopo",
    "prazo_meses",
    "roi_esperado",
    "payback_meses",
    "experiencia_equipe",
    "viabilidade_score",
    "status_viabilidade",
    "risco_global_score",
    "nivel_risco",
    "status_risco",
    "parecer_tecnico",
    "riscos",
}


@st.cache_data(ttl=15, show_spinner=False)
def carregar_projetos() -> tuple[list[dict], str | None]:
    """Retorna (projetos com riscos, erro). Se a API falhar, cai nos dados de demonstração."""
    try:
        resumo = _get("/projetos")
        projetos = []
        for item in resumo:
            detalhe = _get(f"/projetos/{item['id']}")
            faltando = CAMPOS_OBRIGATORIOS - set(detalhe)
            if faltando:
                raise ValueError(
                    f"a API respondeu sem os campos {sorted(faltando)}; reinicie o `python main.py`"
                )
            detalhe["rev"] = item.get("rev", "")
            projetos.append(detalhe)
        return projetos, None
    except (requests.exceptions.RequestException, ValueError, KeyError) as erro:
        return _projetos_demo(), str(erro)[:140]


def modo_demo() -> bool:
    return carregar_projetos()[1] is not None


def enviar(metodo: str, caminho: str, timeout: int = 15, **kwargs):
    """Retorna (resposta, None) ou (None, mensagem de erro)."""
    if modo_demo():
        return None, "modo demonstração: nada é salvo."
    try:
        resposta = requests.request(
            metodo, f"{API_URL}{caminho}", timeout=timeout, **kwargs
        )
    except requests.exceptions.RequestException as erro:
        return None, f"não foi possível falar com a API ({erro})"
    if resposta.status_code >= 400:
        try:
            detalhe = resposta.json().get("detail", resposta.text)
        except ValueError:
            detalhe = resposta.text
        return None, str(detalhe)
    return resposta, None


# ──────────────────────────────────────────────────────────────────────────────
# Gráficos (Altair)
# ──────────────────────────────────────────────────────────────────────────────
def grafico_exposicao(projetos: list[dict]):
    dados = pd.DataFrame(
        [
            {
                "projeto": f"{p['codigo']} · {p['nome']}",
                "exposicao": p["risco_global_score"],
                "nivel": p["nivel_risco"],
            }
            for p in projetos
        ]
    )
    return (
        alt.Chart(dados)
        .mark_bar(cornerRadiusEnd=4, size=18)
        .encode(
            x=alt.X(
                "exposicao:Q",
                title="Exposição ao risco (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y("projeto:N", title=None, sort="-x"),
            color=alt.Color(
                "nivel:N",
                title=None,
                scale=alt.Scale(domain=list(COR_NIVEL), range=list(COR_NIVEL.values())),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("projeto:N", title="Projeto"),
                alt.Tooltip("exposicao:Q", title="Exposição (%)"),
                alt.Tooltip("nivel:N", title="Nível"),
            ],
        )
        .properties(height=max(150, 48 * len(dados)))
    )


def grafico_matriz(riscos: list[dict], altura: int = 300):
    """Matriz 5×5: fundo colorido por faixa + bolhas com a quantidade de riscos em cada célula."""
    grade = pd.DataFrame(
        [
            {"prob": p, "imp": i, "score": p * i, "faixa": prioridade(p * i)}
            for p in range(1, 6)
            for i in range(1, 6)
        ]
    )
    ordem = [1, 2, 3, 4, 5]
    x = alt.X("prob:O", title="Probabilidade", sort=ordem, axis=alt.Axis(labelAngle=0))
    y = alt.Y("imp:O", title="Impacto", sort=ordem[::-1])
    escala = alt.Scale(domain=list(COR_PRIORIDADE), range=list(COR_PRIORIDADE.values()))

    fundo = (
        alt.Chart(grade)
        .mark_rect(cornerRadius=4, stroke="white", strokeWidth=3, opacity=0.28)
        .encode(
            x=x,
            y=y,
            color=alt.Color("faixa:N", scale=escala, legend=None),
            tooltip=[
                alt.Tooltip("prob:O", title="Probabilidade"),
                alt.Tooltip("imp:O", title="Impacto"),
                alt.Tooltip("score:Q", title="Criticidade"),
                alt.Tooltip("faixa:N", title="Prioridade"),
            ],
        )
    )
    if not riscos:
        return fundo.properties(height=altura)

    contagem = (
        pd.DataFrame(riscos)
        .rename(columns={"probabilidade": "prob", "impacto": "imp"})
        .groupby(["prob", "imp"])
        .size()
        .reset_index(name="qtd")
    )
    contagem["faixa"] = (contagem["prob"] * contagem["imp"]).map(prioridade)
    base = alt.Chart(contagem).encode(x=x, y=y)
    bolhas = base.mark_circle(size=650, opacity=1).encode(
        color=alt.Color("faixa:N", scale=escala, legend=None)
    )
    numeros = base.mark_text(color="white", fontWeight="bold", fontSize=13).encode(
        text="qtd:Q"
    )
    return (fundo + bolhas + numeros).properties(height=altura)


# ──────────────────────────────────────────────────────────────────────────────
# Tabelas (DataFrames)
# ──────────────────────────────────────────────────────────────────────────────
def tabela_projetos(projetos: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": p["id"],
                "Projeto": p["nome"],
                "Código": p["codigo"],
                "Nível": f"{BOLINHA.get(p['nivel_risco'], '')} {p['nivel_risco']}",
                "Exposição (%)": p["risco_global_score"],
                "Status do risco": p["status_risco"],
                "Viabilidade (%)": p["viabilidade_score"],
                "Status da viabilidade": p["status_viabilidade"],
                "Riscos": len(p["riscos"]),
                "Criado em": p.get("rev", ""),
            }
            for p in projetos
        ]
    )


def tabela_riscos(riscos: list[dict], projeto: dict | None = None) -> pd.DataFrame:
    linhas = []
    for r in sorted(riscos, key=lambda r: -r["criticidade_score"]):
        linha = {
            "Risco": r["titulo"],
            "Responsável": r["responsavel"],
            "Prob.": r["probabilidade"],
            "Imp.": r["impacto"],
            "Score": r["criticidade_score"],
            "Prioridade": f"{BOLINHA.get(r['prioridade'], '')} {r['prioridade']}",
        }
        if "_projeto" in r:
            linha = {"Projeto": r["_projeto"], **linha}
        linhas.append(linha)
    return pd.DataFrame(linhas)


COLUNAS_RISCO = {
    "Score": st.column_config.ProgressColumn(
        "Score (1–25)", min_value=0, max_value=25, format="%d"
    ),
}
COLUNAS_PROJETO = {
    "Exposição (%)": st.column_config.ProgressColumn(
        "Exposição (%)", min_value=0, max_value=100, format="%.0f"
    ),
    "Viabilidade (%)": st.column_config.ProgressColumn(
        "Viabilidade (%)", min_value=0, max_value=100, format="%.1f"
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Peças reutilizáveis
# ──────────────────────────────────────────────────────────────────────────────
def aviso_de_modo(erro: str | None) -> None:
    if erro is not None:
        st.warning(
            f"Modo demonstração: não consegui ler a API ({erro}). "
            "Os dados abaixo são fictícios e nada é salvo.",
            icon="🧪",
        )


def cabecalho(
    titulo: str, subtitulo: str, rotulo_botao: str | None = None, acao=None
) -> None:
    col_titulo, col_botao = st.columns([4, 1], vertical_alignment="center")
    with col_titulo:
        st.markdown(f"## {titulo}")
        st.caption(subtitulo)
    if rotulo_botao and acao:
        with col_botao:
            if st.button(rotulo_botao, type="primary", icon=":material/add:"):
                acao()


def cartao_kpi(coluna, rotulo: str, valor: str, legenda: str) -> None:
    with coluna, st.container(border=True):
        st.metric(rotulo, valor)
        st.caption(legenda)


def abrir_projeto(projeto_id: int) -> None:
    st.session_state["projeto_atual"] = int(projeto_id)
    st.switch_page(PAGINAS["projetos"])


# ──────────────────────────────────────────────────────────────────────────────
# Modais
# ──────────────────────────────────────────────────────────────────────────────
@st.dialog("Novo projeto", width="large")
def modal_novo_projeto() -> None:
    st.caption(
        "Cadastre os parâmetros técnicos e financeiros. A viabilidade é calculada automaticamente."
    )
    nome = st.text_input("Título do projeto", placeholder="Ex.: Migração Cloud AWS")
    escopo = st.text_area(
        "Escopo técnico",
        placeholder="Objetivo e arquitetura, para contextualizar a IA...",
    )
    c1, c2, c3 = st.columns(3)
    prazo = c1.number_input(
        "Prazo (meses)", min_value=1, max_value=120, value=6, step=1
    )
    roi = c2.number_input(
        "ROI esperado (%)", min_value=0.0, max_value=1000.0, value=25.0, step=1.0
    )
    payback = c3.number_input(
        "Payback (meses)", min_value=0.5, max_value=120.0, value=4.0, step=0.5
    )
    equipe = st.selectbox("Experiência da equipe", ["Alta", "Média", "Baixa"])

    if st.button("Salvar projeto", type="primary"):
        if not nome.strip():
            st.warning("Informe o título do projeto.")
            return
        resposta, erro = enviar(
            "POST",
            "/projetos",
            json={
                "nome": nome.strip(),
                "escopo": escopo.strip(),
                "prazo_meses": int(prazo),
                "roi_esperado": float(roi),
                "payback_meses": float(payback),
                "experiencia_equipe": equipe,
            },
        )
        if erro or resposta is None:
            st.error(f"Erro ao salvar projeto: {erro}")
            return
        criado = resposta.json()
        carregar_projetos.clear()
        st.toast(f"Projeto {criado['codigo']} salvo!")
        abrir_projeto(criado["id"])


@st.dialog("Novo risco", width="large")
def modal_novo_risco(id_padrao: int | None = None) -> None:
    projetos, _ = carregar_projetos()
    if not projetos:
        st.info("Cadastre um projeto antes de mapear riscos.")
        return

    rotulos = {p["id"]: f"{p['codigo']} · {p['nome']}" for p in projetos}
    ids = list(rotulos)
    indice = ids.index(id_padrao) if id_padrao in ids else 0

    titulo = st.text_input(
        "Título do risco", placeholder="Ex.: Falta de conhecimento da equipe em Docker"
    )
    c1, c2 = st.columns(2)
    alvo = c1.selectbox("Projeto", ids, index=indice, format_func=rotulos.get)
    responsavel = c2.text_input(
        "Responsável pela mitigação", placeholder="Ex.: João Vitor"
    )
    c3, c4 = st.columns(2)
    prob = c3.selectbox(
        "Probabilidade",
        [1, 2, 3, 4, 5],
        index=2,
        format_func=lambda v: NIVEIS_PROBABILIDADE[v - 1],
    )
    imp = c4.selectbox(
        "Impacto", [1, 2, 3, 4, 5], index=3, format_func=lambda v: NIVEIS_IMPACTO[v - 1]
    )

    score = prob * imp
    st.info(
        f"Criticidade resultante: **{score}/25** · prioridade **{prioridade(score)}**",
        icon="🎯",
    )

    if st.button("Salvar risco", type="primary"):
        if not titulo.strip():
            st.warning("Informe o título do risco.")
            return
        _, erro = enviar(
            "POST",
            f"/projetos/{alvo}/riscos",
            json={
                "titulo": titulo.strip(),
                "responsavel": responsavel.strip() or "Equipe Técnica",
                "probabilidade": int(prob),
                "impacto": int(imp),
            },
        )
        if erro:
            st.error(f"Erro ao salvar risco: {erro}")
            return
        carregar_projetos.clear()
        st.toast("Risco mapeado e exposição recalculada!")
        st.session_state["projeto_atual"] = int(alvo)
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Página: Visão geral
# ──────────────────────────────────────────────────────────────────────────────
def pagina_visao_geral() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)
    cabecalho(
        "Visão geral",
        "Pontos de atenção do portfólio, calculados em tempo real.",
        "Novo projeto",
        modal_novo_projeto,
    )

    if not projetos:
        st.info("Nenhum projeto cadastrado ainda. Use **Novo projeto** para começar.")
        return

    riscos = [r for p in projetos for r in p["riscos"]]
    aprovados = sum(p["status_viabilidade"] == "Aprovado" for p in projetos)
    criticos = sum(r["prioridade"] == "Alta" for r in riscos)
    viab_media = round(mean(p["viabilidade_score"] for p in projetos), 1)
    exposicao_media = round(mean(p["risco_global_score"] for p in projetos), 1)

    k1, k2, k3, k4 = st.columns(4)
    cartao_kpi(
        k1, "Projetos", str(len(projetos)), f"{aprovados} com viabilidade aprovada"
    )
    cartao_kpi(
        k2, "Riscos críticos", str(criticos), f"de {len(riscos)} riscos mapeados"
    )
    cartao_kpi(k3, "Viabilidade média", f"{viab_media}%", "média do portfólio")
    cartao_kpi(k4, "Exposição média", f"{exposicao_media}%", "média do portfólio")

    g1, g2 = st.columns([1.7, 1])
    with g1, st.container(border=True):
        st.markdown("**Exposição por projeto**")
        st.caption("Ranking: quanto mais à direita, maior a exposição ao risco.")
        st.altair_chart(grafico_exposicao(projetos))
    with g2, st.container(border=True):
        st.markdown("**Mapa de exposição**")
        st.caption("Probabilidade × impacto; o número é a quantidade de riscos.")
        st.altair_chart(grafico_matriz(riscos))

    st.markdown("#### Projetos em atenção")
    f1, f2 = st.columns([3, 2])
    busca = f1.text_input(
        "Buscar",
        placeholder="Buscar por nome ou código...",
        label_visibility="collapsed",
        icon=":material/search:",
    )
    nivel = f2.segmented_control(
        "Nível",
        ["Todos", "Alto", "Médio", "Baixo"],
        default="Todos",
        label_visibility="collapsed",
    )

    tabela = tabela_projetos(projetos)
    if busca:
        termo = busca.lower()
        tabela = tabela[
            tabela["Projeto"].str.lower().str.contains(termo, regex=False)
            | tabela["Código"].str.lower().str.contains(termo, regex=False)
        ]
    if nivel and nivel != "Todos":
        tabela = tabela[tabela["Nível"].str.contains(nivel, regex=False)]
    tabela = tabela.sort_values("Exposição (%)", ascending=False).reset_index(drop=True)

    st.caption("Clique em uma linha para abrir o projeto.")
    evento = st.dataframe(
        tabela.drop(columns="id"),
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tabela_projetos",
        column_config=COLUNAS_PROJETO,
    )
    if evento.selection.rows:
        abrir_projeto(tabela.iloc[evento.selection.rows[0]]["id"])


# ──────────────────────────────────────────────────────────────────────────────
# Página: Projetos (detalhe)
# ──────────────────────────────────────────────────────────────────────────────
def pagina_projetos() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)

    if not projetos:
        cabecalho(
            "Projetos",
            "Nenhum projeto cadastrado ainda.",
            "Novo projeto",
            modal_novo_projeto,
        )
        return

    ids = [p["id"] for p in projetos]
    atual = st.session_state.get("projeto_atual", ids[0])
    if atual not in ids:
        atual = ids[0]
    rotulos = {p["id"]: f"{p['codigo']} · {p['nome']}" for p in projetos}

    c_sel, c_novo, c_risco, c_ia = st.columns(
        [3, 1.2, 1.2, 1.5], vertical_alignment="bottom"
    )
    escolhido = c_sel.selectbox(
        "Projeto", ids, index=ids.index(atual), format_func=rotulos.get
    )
    st.session_state["projeto_atual"] = escolhido
    p = next(x for x in projetos if x["id"] == escolhido)

    if c_novo.button("Novo projeto", icon=":material/add:"):
        modal_novo_projeto()
    if c_risco.button("Adicionar risco", type="primary", icon=":material/add_alert:"):
        modal_novo_risco(p["id"])
    if c_ia.button("Gerar parecer IA", icon=":material/auto_awesome:"):
        if not p["riscos"]:
            st.warning("Cadastre ao menos um risco antes de gerar o parecer.")
        else:
            with st.spinner(
                "Consultando a base de conhecimento e gerando o parecer..."
            ):
                _, erro_ia = enviar(
                    "POST", f"/projetos/{p['id']}/analisar-ia", timeout=120
                )
            if erro_ia:
                st.warning(f"Não foi possível gerar o parecer: {erro_ia}")
            else:
                carregar_projetos.clear()
                st.toast("Parecer técnico gerado!")
                st.rerun()

    st.markdown(f"### {p['nome']}")
    cor_nivel = BADGE_NIVEL.get(p["nivel_risco"], "gray")
    cor_viab = BADGE_VIABILIDADE.get(p["status_viabilidade"], "gray")
    st.markdown(
        f"`{p['codigo']}` &nbsp; :{cor_nivel}-badge[Risco {p['nivel_risco']}] "
        f":{cor_viab}-badge[{p['status_viabilidade']}] :gray-badge[{p['status_risco']}]"
    )
    if p.get("escopo"):
        st.caption(p["escopo"])

    k1, k2, k3, k4 = st.columns(4)
    cartao_kpi(k1, "Viabilidade", f"{p['viabilidade_score']}%", p["status_viabilidade"])
    cartao_kpi(
        k2,
        "Exposição ao risco",
        f"{p['risco_global_score']}%",
        f"nível {p['nivel_risco']} · {p['status_risco']}",
    )
    cartao_kpi(
        k3,
        "ROI esperado",
        f"{p['roi_esperado']}%",
        f"payback de {p['payback_meses']} meses",
    )
    cartao_kpi(
        k4, "Prazo", f"{p['prazo_meses']} meses", f"{len(p['riscos'])} riscos mapeados"
    )

    aba_riscos, aba_matriz, aba_parecer, aba_dados = st.tabs(
        ["Riscos", "Matriz 5×5", "Parecer IA", "Dados do projeto"]
    )

    with aba_riscos:
        if p["riscos"]:
            st.dataframe(
                tabela_riscos(p["riscos"]), hide_index=True, column_config=COLUNAS_RISCO
            )
        else:
            st.info(
                "Nenhum risco mapeado. Use **Adicionar risco** para iniciar a análise."
            )

    with aba_matriz:
        _, centro, _ = st.columns([1, 2, 1])
        with centro:
            st.altair_chart(grafico_matriz(p["riscos"], altura=380))
            st.caption("Verde: prioridade baixa · Laranja: média · Vermelho: alta.")

    with aba_parecer:
        if p.get("parecer_tecnico"):
            with st.container(border=True):
                st.markdown(p["parecer_tecnico"])
            st.download_button(
                "Baixar parecer (.md)",
                data=p["parecer_tecnico"],
                file_name=f"parecer_{p['codigo']}.md",
                mime="text/markdown",
                icon=":material/download:",
            )
        else:
            st.info(
                "Parecer ainda não gerado. Mapeie os riscos e clique em **Gerar parecer IA**."
            )

    with aba_dados:
        d1, d2 = st.columns(2)
        with d1:
            st.markdown("**Parâmetros de entrada**")
            st.write(f"Prazo: {p['prazo_meses']} meses")
            st.write(f"ROI esperado: {p['roi_esperado']}%")
            st.write(f"Payback: {p['payback_meses']} meses")
            st.write(f"Experiência da equipe: {p['experiencia_equipe']}")
        with d2:
            st.markdown("**Resultados calculados**")
            st.write(
                f"Viabilidade: {p['viabilidade_score']}% ({p['status_viabilidade']})"
            )
            st.write(
                f"Exposição: {p['risco_global_score']}% (nível {p['nivel_risco']})"
            )
            st.write(f"Status do risco: {p['status_risco']}")
            st.write(f"Criado em: {p.get('rev', '—')}")


# ──────────────────────────────────────────────────────────────────────────────
# Página: Riscos (visão global)
# ──────────────────────────────────────────────────────────────────────────────
def pagina_riscos() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)
    cabecalho(
        "Riscos",
        "Todos os riscos mapeados, do mais crítico ao menos crítico.",
        "Novo risco",
        modal_novo_risco,
    )

    todos = [{**r, "_projeto": p["codigo"]} for p in projetos for r in p["riscos"]]
    if not todos:
        st.info("Nenhum risco mapeado ainda.")
        return

    f1, f2 = st.columns([2, 2])
    projeto_filtro = f1.selectbox(
        "Projeto", ["Todos"] + [p["codigo"] for p in projetos]
    )
    prioridade_filtro = f2.segmented_control(
        "Prioridade", ["Todas", "Alta", "Média", "Baixa"], default="Todas"
    )

    if projeto_filtro != "Todos":
        todos = [r for r in todos if r["_projeto"] == projeto_filtro]
    if prioridade_filtro and prioridade_filtro != "Todas":
        todos = [r for r in todos if r["prioridade"] == prioridade_filtro]

    st.caption(f"{len(todos)} risco(s) exibido(s)")
    if todos:
        st.dataframe(tabela_riscos(todos), hide_index=True, column_config=COLUNAS_RISCO)
    else:
        st.info("Nenhum risco corresponde aos filtros.")


# ──────────────────────────────────────────────────────────────────────────────
# Página: Relatórios
# ──────────────────────────────────────────────────────────────────────────────
def pagina_relatorios() -> None:
    projetos, erro = carregar_projetos()
    aviso_de_modo(erro)
    cabecalho(
        "Relatórios",
        "Pareceres técnicos gerados pela IA. A exportação em PDF entra na próxima etapa.",
    )

    com_parecer = [p for p in projetos if p.get("parecer_tecnico")]
    if not com_parecer:
        st.info("Nenhum parecer gerado ainda. Gere um na página do projeto.")
        return
    for p in com_parecer:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1], vertical_alignment="center")
            c1.markdown(
                f"**{p['nome']}**  \n`{p['codigo']}` · exposição {p['risco_global_score']}% · {p['status_viabilidade']}"
            )
            c2.download_button(
                "Baixar (.md)",
                data=p["parecer_tecnico"],
                file_name=f"parecer_{p['codigo']}.md",
                mime="text/markdown",
                key=f"dl_{p['id']}",
            )


# ──────────────────────────────────────────────────────────────────────────────
# Navegação nativa (cada página ganha uma URL própria: /projetos, /riscos...)
# ──────────────────────────────────────────────────────────────────────────────
PAGINAS = {
    "visao": st.Page(
        pagina_visao_geral,
        title="Visão geral",
        icon=":material/dashboard:",
        url_path="visao-geral",
        default=True,
    ),
    "projetos": st.Page(
        pagina_projetos, title="Projetos", icon=":material/folder:", url_path="projetos"
    ),
    "riscos": st.Page(
        pagina_riscos, title="Riscos", icon=":material/warning:", url_path="riscos"
    ),
    "relatorios": st.Page(
        pagina_relatorios,
        title="Relatórios",
        icon=":material/description:",
        url_path="relatorios",
    ),
}

if LOGO.exists():
    st.logo(str(LOGO), size="large")

with st.sidebar:
    _, _erro_api = carregar_projetos()
    if _erro_api is None:
        st.caption("🟢 API conectada")
    else:
        st.caption("🟠 Modo demonstração")

st.navigation(list(PAGINAS.values())).run()
