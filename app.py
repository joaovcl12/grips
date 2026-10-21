"""
GRIPS - Sistema de Gestão de Riscos
Front-end em Streamlit 100% integrado ao Back-end FastAPI + PostgreSQL (Zero dados estáticos)
"""

import base64
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Configuração da página
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GRIPS · Sistema de Gestão de Riscos",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"

# Cores da grelha 5x5 (referencial visual da matriz de risco, não são dados de projetos)
MAPA = [
    ["#f8e4bb", "#f8e4bb", "#f5ddac", "#f5ddac", "#f5c9bd"],
    ["#dbece5", "#dbece5", "#dbece5", "#f5ddac", "#f5ddac"],
    ["#dbece5", "#dbece5", "#dbece5", "#d9eae3", "#f5ddac"],
    ["#dbece5", "#dbece5", "#dbece5", "#f8d7c8", "#f4c8bc"],
    ["#dbece5", "#dbece5", "#dbece5", "#f8d7c8", "#f0c5ba"],
]

NIVEL_ESTILO = {
    "Alto": ("#fbedeb", "#d65b48"),
    "Alta": ("#fbedeb", "#d65b48"),
    "Médio": ("#fbf2e2", "#dfa442"),
    "Média": ("#fbf2e2", "#dfa442"),
    "Baixo": ("#e8f3ef", "#388b7e"),
    "Baixa": ("#e8f3ef", "#388b7e"),
}

# ──────────────────────────────────────────────────────────────────────────────
# Ícones (estilo Lucide)
# ──────────────────────────────────────────────────────────────────────────────
ICONES = {
    "grid": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "chart": '<line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
}


def svg_inline(nome, size=18, cor="currentColor", sw=2):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{cor}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
        f"{ICONES[nome]}</svg>"
    )


def svg_mask(nome, sw=2):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" '
        f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICONES[nome]}</svg>'
    )
    return f'url("data:image/svg+xml;utf8,{quote(svg, safe="")}")'


def compacto(html: str) -> str:
    return "".join(linha.strip() for linha in html.splitlines())


# ──────────────────────────────────────────────────────────────────────────────
# Funções de Comunicação com o Back-end (FastAPI)
# ──────────────────────────────────────────────────────────────────────────────
def carregar_dados_dashboard():
    try:
        r = requests.get(f"{API_URL}/dashboard", timeout=5)
        if r.status_code == 200:
            return r.json(), None
        return None, f"Erro da API ({r.status_code})"
    except requests.exceptions.RequestException:
        return None, "Servidor FastAPI offline. Execute `python main.py` no terminal."


def carregar_detalhes_projeto(projeto_id: int):
    try:
        r = requests.get(f"{API_URL}/projetos/{projeto_id}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Estado de Navegação
# ──────────────────────────────────────────────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "home"
if "projeto_selecionado_id" not in st.session_state:
    st.session_state.projeto_selecionado_id = None

dados_dash, erro_api = carregar_dados_dashboard()
total_riscos_criticos_badge = dados_dash["kpis"]["riscos_criticos"] if dados_dash else 0

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"
LOGO_B64 = (
    base64.b64encode(LOGO_PATH.read_bytes()).decode() if LOGO_PATH.exists() else ""
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS global (Limpo das quebras de layout estáticas)
# ──────────────────────────────────────────────────────────────────────────────
NAV = [
    ("home", "Visão geral", "grid"),
    ("projetos", "Projetos", "folder"),
    ("riscos", "Riscos", "alert"),
    ("analises", "Análises", "chart"),
    ("relatorios", "Relatórios", "file"),
    ("config", "Configurações", "settings"),
]

css_icones = ""
for chave, _, ic in NAV:
    css_icones += f".st-key-nav_{chave} button::before{{-webkit-mask-image:{svg_mask(ic)};mask-image:{svg_mask(ic)};}}\n"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="st-"], .stApp, button, input, select, textarea {{
    font-family: 'DM Sans', -apple-system, 'Segoe UI', Roboto, sans-serif !important;
}}

header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

.stApp {{ background: #f5f7f6; }}
[data-testid="stMainBlockContainer"], .block-container {{
    padding: 0 40px 40px 40px !important;
    max-width: none !important;
}}

/* Espaçamento corrigido entre as colunas nativas do Streamlit */
[data-testid="stMain"] [data-testid="stHorizontalBlock"] {{ gap: 14px !important; }}
[data-testid="stMain"] .st-key-row_chart [data-testid="stHorizontalBlock"] {{ gap: 18px !important; }}
[data-testid="stMain"] .stMarkdown p {{ margin: 0; }}
[data-testid="stElementContainer"] {{ width: 100%; }}

/* ── Sidebar ───────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: #0f172a !important;
    width: 244px !important; min-width: 244px !important; max-width: 244px !important;
    border-right: 0 !important;
}}
[data-testid="stSidebar"] > div:first-child {{ width: 244px !important; background: #0f172a; }}
[data-testid="stSidebarContent"] {{ overflow: hidden; }}
[data-testid="stSidebarUserContent"] {{ padding: 12px 18px 0 18px !important; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 4px !important; }}
[data-testid="stSidebar"] [data-testid="stElementContainer"] {{ margin: 0; }}

.sb-logo {{ display: flex; justify-content: center; margin: 0 -18px; }}
.sb-logo img {{ width: 120px; height: auto; display: block; }}
.sb-label {{
    font-size: 9.5px; letter-spacing: .14em; font-weight: 500; color: #7c879b;
    text-transform: uppercase; margin: 8px 0 8px 12px; line-height: 14px;
}}

[data-testid="stSidebar"] .stButton {{ width: 100%; }}
[data-testid="stSidebar"] .stButton > button {{
    width: 100%; height: 44px; border: 0 !important; border-radius: 10px;
    background: transparent; color: #cdd5e1; box-shadow: none !important;
    display: flex; align-items: center; justify-content: flex-start; gap: 12px;
    padding: 0 14px; font-size: 13.5px; font-weight: 500;
}}
[data-testid="stSidebar"] .stButton > button:hover {{ background: rgba(255,255,255,.04); color: #fff; }}
[data-testid="stSidebar"] .stButton > button:focus {{ outline: none; box-shadow: none !important; }}
[data-testid="stSidebar"] .stButton > button p {{ margin: 0; font-size: 13.5px; font-weight: 500; }}
[data-testid="stSidebar"] .stButton > button::before {{
    content: ""; width: 18px; height: 18px; flex: none; background: #94a3b8;
    -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
    -webkit-mask-position: center; mask-position: center;
    -webkit-mask-size: contain; mask-size: contain;
}}
{css_icones}
.st-key-nav_{st.session_state.pagina} button {{
    background: #26334a !important; color: #ffffff !important;
    box-shadow: inset 3px 0 0 #60a5fa !important;
}}
.st-key-nav_{st.session_state.pagina} button::before {{ background: #e6edf7; }}
.st-key-nav_riscos button::after {{
    content: "{total_riscos_criticos_badge}"; margin-left: auto; width: 20px; height: 20px; border-radius: 50%;
    background: #d6f360; color: #0f172a; font-size: 10.5px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
}}

.st-key-sb_bottom {{
    position: fixed; bottom: 0; left: 0; width: 244px; padding: 0 18px; z-index: 5;
    background: #0f172a;
}}
.sb-profile {{
    border-top: 1px solid #1e293b; margin-top: 14px; height: 73px;
    display: flex; align-items: center; gap: 12px; padding: 0 4px;
}}
.sb-avatar {{
    width: 36px; height: 36px; border-radius: 50%; background: #d9e4df; color: #1f4f48;
    display: flex; align-items: center; justify-content: center;
    font-size: 11.5px; font-weight: 600; flex: none;
}}
.sb-name {{ color: #fff; font-size: 12px; font-weight: 600; line-height: 16px; }}
.sb-role {{ color: #7c879b; font-size: 10.5px; line-height: 14px; }}
.sb-dots {{ margin-left: auto; color: #64748b; font-size: 14px; letter-spacing: 1px; }}

/* ── Topbar ────────────────────────────────────────────────────── */
.st-key-topbar {{
    position: sticky; top: 0; z-index: 60; background: #ffffff;
    border-bottom: 1px solid #e5eae7; margin: 0 -40px; padding: 16px 40px;
    height: 72px;
}}
.st-key-topbar [data-testid="stHorizontalBlock"] {{ gap: 12px !important; align-items: center; }}

.st-key-search [data-baseweb="input"] {{
    position: relative; height: 39px; background: #f5f7f6 !important;
    border: 1px solid #e5eae7 !important; border-radius: 10px !important; overflow: visible;
}}
.st-key-search [data-baseweb="base-input"] {{ background: transparent !important; }}
.st-key-search input {{
    height: 37px; padding-left: 40px !important; padding-right: 60px !important;
    font-size: 12px; color: #172725; background: transparent !important;
}}
.st-key-search [data-baseweb="input"]::before {{
    content: ""; position: absolute; left: 14px; top: 50%; width: 15px; height: 15px;
    transform: translateY(-50%); background: #7d8985; z-index: 2; pointer-events: none;
    -webkit-mask: {svg_mask("search")} center/contain no-repeat; mask: {svg_mask("search")} center/contain no-repeat;
}}
[data-testid="InputInstructions"] {{ display: none !important; }}

.bell-wrap {{ display: flex; justify-content: flex-end; }}
.bell {{
    position: relative; width: 38px; height: 38px; background: #fff; border: 1px solid #e5eae7;
    border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #475569;
}}

.st-key-novo_risco .stButton, .st-key-novo_risco {{ width: 100%; }}
.st-key-novo_risco button {{
    width: 100%; height: 40px; background: #0f172a; border: 0; border-radius: 10px; color: #fff;
    box-shadow: 0 4px 12px rgba(15,23,42,.22); display: flex; align-items: center; justify-content: center;
    gap: 8px; padding: 0 18px; white-space: nowrap;
}}
.st-key-novo_risco button:hover {{ background: #1b2540; color: #fff; }}
.st-key-novo_risco button p {{ font-size: 12.5px; font-weight: 600; color: #fff; }}
.st-key-novo_risco button::before {{
    content: ""; width: 15px; height: 15px; background: #fff; flex: none;
    -webkit-mask: {svg_mask("plus", 2.2)} center/contain no-repeat; mask: {svg_mask("plus", 2.2)} center/contain no-repeat;
}}

/* ── Hero & Cards (Adicionado margin-bottom para não sobrepor KPI) */
.hero {{ margin-top: 32px; margin-bottom: 28px; display: block; }}
.hero .eyebrow {{
    font-size: 9.5px; font-weight: 600; letter-spacing: .2em; color: #1f7a78; line-height: 12px;
    text-transform: uppercase;
}}
.hero h1 {{
    font-size: 31px; font-weight: 500; color: #172725; letter-spacing: -0.02em;
    line-height: 38px; margin: 10px 0 0 0; padding: 0;
}}
.hero .sub {{ font-size: 11.5px; color: #66736f; margin-top: 4px; line-height: 16px; }}

.card {{ background: #fff; border: 1px solid #e5eae7; border-radius: 16px; box-sizing: border-box; overflow: hidden; }}
.kpi {{ height: auto; min-height: 88px; display: flex; align-items: center; gap: 14px; padding: 16px 18px; }}
.kpi .ico {{
    width: 46px; height: 46px; border-radius: 12px; display: flex; align-items: center;
    justify-content: center; flex: none;
}}
.kpi .lbl {{ font-size: 9.5px; color: #66736f; line-height: 13px; }}
.kpi .line {{ display: flex; align-items: center; gap: 8px; margin-top: 3px; }}
.kpi .val {{ font-size: 23px; font-weight: 700; color: #111c1a; line-height: 28px; white-space: nowrap; }}
.kpi .pill {{
    font-size: 8px; font-weight: 500; color: #3c8576; background: #e8f4f0; padding: 3px 7px;
    border-radius: 8px; white-space: nowrap; line-height: 10px;
}}

.row-chart {{ margin-top: 18px; }}
.c-title {{ font-size: 14px; font-weight: 500; color: #172725; line-height: 20px; }}
.c-sub {{ font-size: 9.5px; color: #66736f; margin-top: 4px; line-height: 13px; }}

.card-chart {{ height: 335px; padding: 22px 22px 0 22px; position: relative; overflow: visible; }}
.legend-top {{
    position: absolute; right: 22px; top: 27px; display: flex; align-items: center; gap: 6px;
    font-size: 8.5px; color: #66736f;
}}
.legend-top i {{ width: 7px; height: 7px; border-radius: 50%; background: #1f7a78; display: inline-block; }}
.chart-wrap {{ display: flex; margin-top: 22px; }}
.yaxis {{ width: 32px; height: 210px; position: relative; flex: none; }}
.yaxis span {{ position: absolute; left: 0; font-size: 8.5px; color: #8b9692; transform: translateY(-50%); }}
.plot-col {{ flex: 1; margin-right: 4px; }}
.plot {{ position: relative; height: 210px; }}
.plot svg {{ width: 100%; height: 100%; display: block; overflow: visible; }}
.end-dot {{
    position: absolute; width: 8px; height: 8px; border-radius: 50%; background: #fff;
    border: 2.5px solid #1f7a78; transform: translate(-50%, -50%); box-sizing: content-box;
}}
.xaxis {{ display: flex; justify-content: space-between; margin-top: 14px; }}
.xaxis span {{ font-size: 8.5px; color: #8b9692; }}

.card-heat {{ height: 335px; padding: 22px; position: relative; }}
.heat-wrap {{ display: flex; margin-top: 26px; }}
.ylabel {{ width: 22px; flex: none; position: relative; }}
.ylabel span {{
    position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%) rotate(-90deg);
    font-size: 7.5px; font-weight: 600; letter-spacing: .14em; color: #6b7773; white-space: nowrap;
}}
.heat {{ position: relative; flex: 1; margin-right: 8px; height: 182px; }}
.heat-grid {{
    display: grid; grid-template-columns: repeat(5, 1fr); grid-template-rows: repeat(5, 1fr);
    gap: 3.5px; width: 100%; height: 100%;
}}
.heat-grid div {{ border-radius: 4px; }}
.mk {{
    position: absolute; width: 21px; height: 21px; border-radius: 50%; color: #fff;
    font-size: 8.5px; font-weight: 700; display: flex; align-items: center; justify-content: center;
    transform: translate(-50%, -50%); border: 2.5px solid #fff; box-sizing: content-box;
    box-shadow: 0 2px 6px rgba(15,23,42,.18);
}}
.heat-legend {{ text-align: center; margin-top: 18px; }}
.heat-legend .t {{ font-size: 7.5px; font-weight: 600; letter-spacing: .14em; color: #6b7773; }}
.heat-legend .l {{ display: flex; justify-content: center; gap: 12px; margin-top: 7px; font-size: 8px; color: #6b7773; }}
.heat-legend .l span {{ display: flex; align-items: center; gap: 4px; }}
.heat-legend .l i {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; }}

/* Tabela */
.row-table {{ margin-top: 18px; }}
.card-table {{ padding: 22px 22px 14px 22px; }}
.t-head {{ display: flex; justify-content: space-between; align-items: flex-start; }}
.grid-row {{
    display: grid; grid-template-columns: 2.2fr 1.1fr 1.45fr 1.15fr 1.25fr .8fr; align-items: center;
    padding: 0 12px;
}}
.t-cols {{ margin-top: 22px; height: 35px; border-bottom: 1px solid #edf1ef; }}
.t-cols span {{ font-size: 8px; font-weight: 600; letter-spacing: .12em; color: #7d8985; text-transform: uppercase; }}
.t-row {{ height: 58px; border-bottom: 1px solid #edf1ef; }}
.t-row:last-child {{ border-bottom: 0; }}
.proj {{ display: flex; align-items: center; gap: 14px; }}
.proj .av {{
    width: 31px; height: 31px; border-radius: 8px; background: #edf2f0; color: #4b5a56;
    font-size: 8.5px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex: none;
}}
.proj .n {{ font-size: 10.5px; font-weight: 600; color: #172725; line-height: 14px; }}
.proj .c {{ font-size: 8px; color: #8b9692; line-height: 12px; margin-top: 2px; }}
.badge {{
    display: inline-flex; align-items: center; gap: 5px; font-size: 9px; font-weight: 500;
    padding: 4px 9px; border-radius: 12px; line-height: 12px;
}}
.badge i {{ width: 5px; height: 5px; border-radius: 50%; display: inline-block; }}
.exp {{ display: flex; align-items: center; gap: 8px; }}
.exp .bar {{ width: 58px; height: 4px; border-radius: 3px; background: #e9edeb; overflow: hidden; }}
.exp .bar b {{ display: block; height: 100%; background: #dc7965; border-radius: 3px; }}
.exp .v {{ font-size: 9.5px; font-weight: 700; color: #172725; }}
.chip {{
    display: inline-block; background: #f0f3f2; color: #4b5a56; font-size: 9px; font-weight: 500;
    padding: 5px 9px; border-radius: 7px; line-height: 12px;
}}
.rev {{ font-size: 10px; color: #3b4a46; font-weight: 600; }}

/* ── Modais (Limpo das regras que quebravam a janela nativa do Streamlit) ── */
.dlg-body {{ padding: 8px 0px 0 0px; }}
.dlg-eyebrow {{ font-size: 9px; font-weight: 600; letter-spacing: .16em; color: #1f7a78; text-transform: uppercase; }}
.dlg-title {{ font-size: 20px; font-weight: 500; color: #172725; margin-top: 10px; line-height: 26px; }}
.dlg-sub {{ font-size: 11.5px; color: #66736f; margin-top: 6px; }}
.dlg-sep {{ border-top: 1px solid #e8edea; margin: 16px 0 12px 0; }}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Modal 1: Cadastrar Novo Projeto (No Dashboard Principal)
# ──────────────────────────────────────────────────────────────────────────────
@st.dialog("Novo Projeto de Análise", width="large")
def modal_novo_projeto():
    st.markdown(
        compacto(
            """
            <div class="dlg-body">
              <div class="dlg-eyebrow">Cadastro de Projeto</div>
              <div class="dlg-title">Novo Projeto de Análise</div>
              <div class="dlg-sub">Insira os parâmetros técnicos e financeiros para calcular a viabilidade e gerar o código único.</div>
              <div class="dlg-sep"></div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    nome = st.text_input("Nome do Projeto", placeholder="Ex.: Migração Cloud AWS")
    escopo = st.text_area(
        "Escopo Técnico do Projeto",
        placeholder="Descreva brevemente o objetivo e a arquitetura para contextualizar a IA...",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        prazo = st.number_input(
            "Prazo (Meses)", min_value=1, max_value=120, value=6, step=1
        )
    with c2:
        roi = st.number_input(
            "ROI Esperado (%)", min_value=0.0, max_value=1000.0, value=25.0, step=1.0
        )
    with c3:
        payback = st.number_input(
            "Payback (Meses)", min_value=0.5, max_value=120.0, value=4.0, step=0.5
        )

    experiencia = st.selectbox(
        "Experiência da Equipe", ["Alta", "Média", "Baixa"], index=0
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()
    with b2:
        if st.button(
            "Calcular Viabilidade & Salvar", type="primary", use_container_width=True
        ):
            if not nome.strip():
                st.warning("Informe o nome do projeto.")
            else:
                payload = {
                    "nome": nome.strip(),
                    "escopo": escopo.strip(),
                    "prazo_meses": int(prazo),
                    "roi_esperado": float(roi),
                    "payback_meses": float(payback),
                    "experiencia_equipe": experiencia,
                }
                res = requests.post(f"{API_URL}/projetos", json=payload)
                if res.status_code == 200:
                    proj_criado = res.json()
                    st.toast(f"Projeto {proj_criado['codigo']} salvo com sucesso!")
                    st.session_state.projeto_selecionado_id = proj_criado["id"]
                    st.session_state.pagina = "projetos"
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar projeto: {res.text}")


# ──────────────────────────────────────────────────────────────────────────────
# Modal 2: Adicionar Risco (Movido para DENTRO de um Projeto)
# ──────────────────────────────────────────────────────────────────────────────
@st.dialog("Mapear Novo Risco", width="large")
def modal_novo_risco(projeto_id: int, nome_projeto: str):
    st.markdown(
        compacto(
            f"""
            <div class="dlg-body">
              <div class="dlg-eyebrow">Projeto: {nome_projeto}</div>
              <div class="dlg-title">Mapear Novo Risco</div>
              <div class="dlg-sub">Registre a variável de risco para cálculo na matriz 5x5 (PMBOK).</div>
              <div class="dlg-sep"></div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    titulo = st.text_input(
        "Título do Risco", placeholder="Ex.: Falta de conhecimento da equipe em Docker"
    )
    responsavel = st.text_input(
        "Responsável pela Mitigação", placeholder="Ex.: João Vitor"
    )

    c1, c2 = st.columns(2)
    with c1:
        prob = st.slider("Probabilidade (1 = Muito Baixa, 5 = Muito Alta)", 1, 5, 3)
    with c2:
        impacto = st.slider("Impacto (1 = Muito Baixo, 5 = Muito Alto)", 1, 5, 4)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()
    with b2:
        if st.button(
            "Salvar Risco na Matriz", type="primary", use_container_width=True
        ):
            if not titulo.strip():
                st.warning("Informe o título do risco.")
            else:
                payload = {
                    "titulo": titulo.strip(),
                    "responsavel": responsavel.strip() or "Equipe Técnica",
                    "probabilidade": int(prob),
                    "impacto": int(impacto),
                }
                res = requests.post(
                    f"{API_URL}/projetos/{projeto_id}/riscos", json=payload
                )
                if res.status_code == 200:
                    st.toast("Risco mapeado e matriz atualizada!")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar risco: {res.text}")


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f'<div class="sb-logo"><img src="data:image/png;base64,{LOGO_B64}" alt="GRIPS"></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="sb-label">Espaço de trabalho</div>', unsafe_allow_html=True
    )

    for chave, rotulo, _ in NAV[:-1]:
        if st.button(rotulo, key=f"nav_{chave}"):
            st.session_state.pagina = chave
            st.rerun()

    with st.container(key="sb_bottom"):
        if st.button("Configurações", key="nav_config"):
            st.session_state.pagina = "config"
            st.rerun()
        st.markdown(
            compacto(
                """
                <div class="sb-profile">
                  <div class="sb-avatar">GR</div>
                  <div><div class="sb-name">Painel GRIPS</div><div class="sb-role">Análise Operacional</div></div>
                  <div class="sb-dots">···</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# Topbar (Botão principal agora é "+ Novo projeto")
# ──────────────────────────────────────────────────────────────────────────────
with st.container(key="topbar"):
    t1, t2, t3, t4 = st.columns([43.3, 38.9, 3.8, 14.0], vertical_alignment="center")
    with t1:
        with st.container(key="search"):
            termo_busca = st.text_input(
                "Buscar",
                placeholder="Buscar projetos pelo nome ou código...",
                label_visibility="collapsed",
                key="busca",
            )
    with t3:
        st.markdown(
            f'<div class="bell-wrap"><div class="bell">{svg_inline("bell", 16, "currentColor", 1.8)}</div></div>',
            unsafe_allow_html=True,
        )
    with t4:
        with st.container(key="novo_risco"):
            if st.button("Novo projeto", key="btn_novo_projeto_top"):
                modal_novo_projeto()

if erro_api:
    st.error(erro_api)
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# ABA: PROJETOS (Detalhes do Projeto + Adicionar Risco + Parecer IA)
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.pagina == "projetos":
    projetos_disp = dados_dash["projetos"]
    if not projetos_disp:
        st.markdown(
            compacto(
                """
                <div class="hero">
                  <div class="eyebrow">Projetos</div>
                  <h1>Nenhum projeto cadastrado</h1>
                  <div class="sub">Clique em "+ Novo projeto" no canto superior direito para iniciar sua primeira análise.</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        st.stop()

    # Seletor de projeto no topo da tela de Projetos
    opcoes_proj = {f"{p['cod']} · {p['nome']}": p["id"] for p in projetos_disp}
    idx_padrao = 0
    if st.session_state.projeto_selecionado_id in opcoes_proj.values():
        idx_padrao = list(opcoes_proj.values()).index(
            st.session_state.projeto_selecionado_id
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_sel, col_btn_risco, col_btn_ia = st.columns(
        [2.5, 1, 1.2], vertical_alignment="bottom"
    )
    with col_sel:
        escolha = st.selectbox(
            "Selecione o Projeto para gerenciar riscos:",
            list(opcoes_proj.keys()),
            index=idx_padrao,
        )
        id_atual = opcoes_proj[escolha]
        st.session_state.projeto_selecionado_id = id_atual

    detalhes = carregar_detalhes_projeto(id_atual)
    if not detalhes:
        st.error("Não foi possível carregar os detalhes deste projeto.")
        st.stop()

    with col_btn_risco:
        if st.button("+ Adicionar Risco", type="primary", use_container_width=True):
            modal_novo_risco(detalhes["id"], detalhes["nome"])

    with col_btn_ia:
        gerar_ia = st.button("✨ Gerar Parecer IA (RAG)", use_container_width=True)

    if gerar_ia:
        with st.spinner(
            "Consultando vetores no PostgreSQL (pgvector) e gerando parecer com Gemini..."
        ):
            res_ia = requests.post(f"{API_URL}/projetos/{detalhes['id']}/analisar-ia")
            if res_ia.status_code == 200:
                st.toast("Parecer técnico gerado com sucesso!")
                st.rerun()
            else:
                st.warning(res_ia.json().get("detail", "Erro ao gerar parecer."))

    # Cabeçalho e KPIs do Projeto Específico
    st.markdown(
        compacto(
            f"""
            <div class="hero" style="margin-top:16px">
              <div class="eyebrow">{detalhes["codigo"]} · Experiência: {detalhes["experiencia_equipe"]}</div>
              <h1>{detalhes["nome"]}</h1>
              <div class="sub">{detalhes["escopo"]}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    kpis_proj = [
        {
            "label": "Viabilidade calculada",
            "valor": f"{detalhes['viabilidade_score']}%",
            "delta": detalhes["status_viabilidade"],
            "icone": "shield",
            "cor": "#2f8577",
            "bg": "#e6f3f0",
        },
        {
            "label": "Exposição ao risco",
            "valor": f"{detalhes['risco_global_score']}%",
            "delta": f"{detalhes['nivel_risco']} · {detalhes['status_risco']}",
            "icone": "alert",
            "cor": "#d65b48",
            "bg": "#fcede9",
        },
        {
            "label": "ROI / Payback",
            "valor": f"{detalhes['roi_esperado']}%",
            "delta": f"{detalhes['payback_meses']} meses",
            "icone": "chart",
            "cor": "#5b86ad",
            "bg": "#eaf1f7",
        },
        {
            "label": "Prazo estimado",
            "valor": f"{detalhes['prazo_meses']} m",
            "delta": f"{len(detalhes['riscos'])} riscos",
            "icone": "clock",
            "cor": "#dfa442",
            "bg": "#fbf1df",
        },
    ]
    st.markdown('<div class="row-kpi"></div>', unsafe_allow_html=True)
    cols_p = st.columns(4)
    for col, k in zip(cols_p, kpis_proj):
        with col:
            st.markdown(
                compacto(
                    f"""
                    <div class="card kpi">
                      <div class="ico" style="background:{k["bg"]}">{svg_inline(k["icone"], 19, k["cor"], 1.9)}</div>
                      <div>
                        <div class="lbl">{k["label"]}</div>
                        <div class="line"><span class="val">{k["valor"]}</span><span class="pill">{k["delta"]}</span></div>
                      </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    # Lista de Riscos do Projeto + Parecer da IA lado a lado
    st.markdown("<br>", unsafe_allow_html=True)
    col_esq, col_dir = st.columns([1.2, 1.3])

    with col_esq:
        st.markdown("#### Riscos Mapeados neste Projeto")
        if not detalhes["riscos"]:
            st.info("Nenhum risco mapeado ainda. Clique em '+ Adicionar Risco' acima.")
        else:
            for r in detalhes["riscos"]:
                bg, fg = NIVEL_ESTILO.get(r["prioridade"], ("#f0f3f2", "#4b5a56"))
                st.markdown(
                    compacto(
                        f"""
                        <div class="card" style="padding:14px 18px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                          <div>
                            <div style="font-size:13px; font-weight:600; color:#172725;">{r["titulo"]}</div>
                            <div style="font-size:11px; color:#66736f; margin-top:2px;">
                              Resp: {r["responsavel"]} · Prob: {r["probabilidade"]}/5 · Imp: {r["impacto"]}/5
                            </div>
                          </div>
                          <div>
                            <span class="badge" style="background:{bg};color:{fg}">
                              Score {r["criticidade_score"]} ({r["prioridade"]})
                            </span>
                          </div>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

    with col_dir:
        st.markdown("#### Parecer Técnico Diagnóstico (IA + Literatura PMBOK)")
        if detalhes["parecer_tecnico"]:
            with st.container(border=True):
                st.markdown(detalhes["parecer_tecnico"])
        else:
            st.info(
                "Adicione os riscos do projeto e clique em '✨ Gerar Parecer IA (RAG)' para obter o plano de mitigação fundamentado."
            )

    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# OUTRAS ABAS DO MENU LATERAL (Riscos Globais / Relatórios)
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.pagina != "home":
    nome_aba = next(r for c, r, _ in NAV if c == st.session_state.pagina)
    st.markdown(
        compacto(
            f"""
            <div class="hero">
              <div class="eyebrow">GRIPS</div>
              <h1>{nome_aba}</h1>
              <div class="sub">Selecione um projeto na aba 'Projetos' ou na tabela da 'Visão geral' para gerenciar riscos e relatórios.</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# TELA PRINCIPAL: VISÃO GERAL (PAINEL EXECUTIVO 100% DINÂMICO)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    compacto(
        """
        <div class="hero">
          <div class="eyebrow">Painel Executivo</div>
          <h1>Visão Geral de Projetos e Riscos</h1>
          <div class="sub">Métricas calculadas em tempo real a partir do banco de dados PostgreSQL.</div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

kpis_dinamicos = [
    {
        "label": "Projetos analisados",
        "valor": str(dados_dash["kpis"]["total_projetos"]),
        "delta": "Ativos no banco",
        "icone": "folder",
        "cor": "#5b86ad",
        "bg": "#eaf1f7",
    },
    {
        "label": "Taxa de aprovados",
        "valor": f"{dados_dash['kpis']['taxa_aprovados']}%",
        "delta": "Viabilidade ≥ 70%",
        "icone": "shield",
        "cor": "#2f8577",
        "bg": "#e6f3f0",
    },
    {
        "label": "Riscos críticos",
        "valor": str(dados_dash["kpis"]["riscos_criticos"]),
        "delta": f"De {dados_dash['kpis']['total_riscos']} mapeados",
        "icone": "alert",
        "cor": "#d65b48",
        "bg": "#fcede9",
    },
    {
        "label": "Viabilidade média",
        "valor": f"{dados_dash['kpis']['viabilidade_media']}%",
        "delta": "Score global",
        "icone": "chart",
        "cor": "#dfa442",
        "bg": "#fbf1df",
    },
]

st.markdown('<div class="row-kpi"></div>', unsafe_allow_html=True)
cols = st.columns(4)
for col, k in zip(cols, kpis_dinamicos):
    with col:
        st.markdown(
            compacto(
                f"""
                <div class="card kpi">
                  <div class="ico" style="background:{k["bg"]}">{svg_inline(k["icone"], 19, k["cor"], 1.9)}</div>
                  <div>
                    <div class="lbl">{k["label"]}</div>
                    <div class="line"><span class="val">{k["valor"]}</span><span class="pill">{k["delta"]}</span></div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Gráfico Dinâmico "Exposição por Projeto" + Mapa de Exposição 5x5 Real
# ──────────────────────────────────────────────────────────────────────────────
serie_api = dados_dash["serie_evolucao"]
eixo_x_api = dados_dash["eixo_x"]

if len(serie_api) >= 2:
    pontos = [(idx, item["valor"]) for idx, item in enumerate(serie_api)]
    max_x = len(pontos) - 1
    coords = [f"{(x / max_x) * 1000:.1f},{100 - y:.1f}" for x, y in pontos]
    linha = "M" + " L".join(coords)
    area = f"{linha} L1000,100 L0,100 Z"
    ultimo_y = 100 - pontos[-1][1]
    dot_html = f'<div class="end-dot" style="left:100%;top:{ultimo_y}%"></div>'
elif len(serie_api) == 1:
    y_val = 100 - serie_api[0]["valor"]
    linha = f"M0,{y_val:.1f} L1000,{y_val:.1f}"
    area = f"{linha} L1000,100 L0,100 Z"
    dot_html = f'<div class="end-dot" style="left:50%;top:{y_val}%"></div>'
else:
    linha = "M0,100 L1000,100"
    area = "M0,100 L1000,100 Z"
    dot_html = ""

grades = "".join(
    f'<line x1="0" x2="1000" y1="{y}" y2="{y}" stroke="#e8eeec" stroke-width="1" vector-effect="non-scaling-stroke"/>'
    for y in (0, 25, 50, 75, 100)
)
y_labels = "".join(
    f'<span style="top:{100 - v}%">{v}%</span>' for v in (100, 75, 50, 25, 0)
)
x_labels = "".join(
    f"<span>{x}</span>" for x in (eixo_x_api[-6:] if eixo_x_api else ["Sem dados"])
)

grafico_html = compacto(
    f"""
    <div class="card card-chart">
      <div class="c-title">Evolução da exposição ao risco</div>
      <div class="c-sub">Índice de risco global (%) por projeto cadastrado</div>
      <div class="legend-top"><i></i>Exposição calculada</div>
      <div class="chart-wrap">
        <div class="yaxis">{y_labels}</div>
        <div class="plot-col">
          <div class="plot">
            <svg viewBox="0 0 1000 100" preserveAspectRatio="none">
              <defs>
                <linearGradient id="gArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#1f7a78" stop-opacity="0.22"/>
                  <stop offset="100%" stop-color="#1f7a78" stop-opacity="0.02"/>
                </linearGradient>
              </defs>
              {grades}
              <path d="{area}" fill="url(#gArea)" stroke="none"/>
              <path d="{linha}" fill="none" stroke="#1f7a78" stroke-width="2.6" stroke-linecap="round" vector-effect="non-scaling-stroke"/>
            </svg>
            {dot_html}
          </div>
          <div class="xaxis">{x_labels}</div>
        </div>
      </div>
    </div>
    """
)

celulas = "".join(
    f'<div style="background:{cor}"></div>' for linha_ in MAPA for cor in linha_
)
marcadores = "".join(
    f'<div class="mk" style="left:{m["x"]}%;top:{m["y"]}%;background:{m["cor"]}">{m["qtd"]}</div>'
    for m in dados_dash["marcadores_mapa"]
)

mapa_html = compacto(
    f"""
    <div class="card card-heat">
      <div class="c-title">Mapa de exposição consolidado</div>
      <div class="c-sub">Distribuição real (Probabilidade × Impacto)</div>
      <div class="heat-wrap">
        <div class="ylabel"><span>IMPACTO</span></div>
        <div class="heat"><div class="heat-grid">{celulas}</div>{marcadores}</div>
      </div>
      <div class="heat-legend">
        <div class="t">PROBABILIDADE</div>
        <div class="l">
          <span><i style="background:#a9cfc3"></i>Baixo</span>
          <span><i style="background:#ecc46f"></i>Médio</span>
          <span><i style="background:#e0826d"></i>Alto</span>
        </div>
      </div>
    </div>
    """
)

st.markdown('<div class="row-chart"></div>', unsafe_allow_html=True)
with st.container(key="row_chart"):
    ca, cb = st.columns([2.13, 1])
    with ca:
        st.markdown(grafico_html, unsafe_allow_html=True)
    with cb:
        st.markdown(mapa_html, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Tabela Dinâmica: Análises Recentes
# ──────────────────────────────────────────────────────────────────────────────
projetos_filtrados = dados_dash["projetos"]
if termo_busca:
    termo = termo_busca.lower()
    projetos_filtrados = [
        p
        for p in projetos_filtrados
        if termo in p["nome"].lower() or termo in p["cod"].lower()
    ]

linhas = ""
for p in projetos_filtrados:
    bg, fg = NIVEL_ESTILO.get(p["nivel"], ("#e8f3ef", "#388b7e"))
    linhas += f"""
    <div class="grid-row t-row">
      <div class="proj">
        <div class="av">{p["ini"]}</div>
        <div><div class="n">{p["nome"]}</div><div class="c">{p["cod"]} · {p["total_riscos"]} risco(s)</div></div>
      </div>
      <div><span class="badge" style="background:{bg};color:{fg}"><i style="background:{fg}"></i>{p["nivel"]}</span></div>
      <div class="exp">
        <div class="bar"><b style="width:{p["exp"]}%"></b></div>
        <span class="v">{p["exp"]}%</span>
      </div>
      <div><span class="chip">{p["status_risco"]}</span></div>
      <div class="rev" style="color:#2f8577">{p["viabilidade"]}% · {p["status_viabilidade"]}</div>
      <div class="rev">{p["rev"]}</div>
    </div>
    """

if not linhas:
    linhas = '<div style="padding:28px 12px; font-size:12px; color:#66736f;">Nenhum projeto encontrado. Clique em <b>+ Novo projeto</b> no topo da página para cadastrar.</div>'

tabela_html = compacto(
    f"""
    <div class="card card-table">
      <div class="t-head">
        <div>
          <div class="c-title">Análises Recentes</div>
          <div class="c-sub">Projetos cadastrados com risco global e viabilidade calculados pelo sistema</div>
        </div>
      </div>
      <div class="grid-row t-cols">
        <span>Código / Projeto</span><span>Nível de risco</span><span>Risco Global</span><span>Status do risco</span><span>Viabilidade</span><span>Data</span>
      </div>
      {linhas}
    </div>
    """
)

st.markdown('<div class="row-table"></div>', unsafe_allow_html=True)
st.markdown(tabela_html, unsafe_allow_html=True)

# Atalho rápido abaixo da tabela para abrir os detalhes de qualquer projeto
if projetos_filtrados:
    st.markdown("<br>", unsafe_allow_html=True)
    c_atalho1, c_atalho2 = st.columns([3, 1], vertical_alignment="bottom")
    with c_atalho1:
        mapa_atalho = {
            f"Abrir detalhes de: {p['cod']} - {p['nome']}": p["id"]
            for p in projetos_filtrados
        }
        proj_escolhido = st.selectbox(
            "Acesso rápido aos detalhes e matriz de riscos do projeto:",
            list(mapa_atalho.keys()),
            label_visibility="collapsed",
        )
    with c_atalho2:
        if st.button("Ver Detalhes do Projeto →", use_container_width=True):
            st.session_state.projeto_selecionado_id = mapa_atalho[proj_escolhido]
            st.session_state.pagina = "projetos"
            st.rerun()
