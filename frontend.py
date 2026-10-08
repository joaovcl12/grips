import pandas as pd
import requests
import streamlit as st

# 1. Configuração base da interface web
st.set_page_config(page_title="RiskEngine", page_icon="📊", layout="wide")

# Endereço onde o seu FastAPI está rodando
API_URL = "http://localhost:8000"

# 2. Construção do Menu Lateral
st.sidebar.title("R | RiskEngine")
st.sidebar.markdown("---")
pagina = st.sidebar.radio("Navegação", ["Painel Executivo", "Novo Projeto"])

# ==========================================
# TELA 1: PAINEL EXECUTIVO
# ==========================================
if pagina == "Painel Executivo":
    st.title("Painel Executivo")
    st.write("Visão geral da viabilidade e matrizes de riscos ativas.")

    try:
        # Consome a rota GET /dashboard que criamos no FastAPI
        resposta = requests.get(f"{API_URL}/dashboard")

        if resposta.status_code == 200:
            dados = resposta.json()
            indicadores = dados["indicadores"]

            # Desenha os 4 cartões de métricas (Cards)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Projetos Analisados", indicadores["total_projetos"])
            col2.metric("Taxa de Aprovados", f"{indicadores['taxa_aprovacao']}%")
            col3.metric("Riscos Críticos", indicadores["riscos_criticos_ativos"])
            col4.metric("Score Médio", indicadores["score_medio_risco"])

            st.markdown("---")
            st.subheader("Análises Recentes")

            # Desenha a tabela com os projetos salvos
            projetos_recentes = dados["analises_recentes"]
            if projetos_recentes:
                df = pd.DataFrame(projetos_recentes)
                # Formatação visual para esconder o índice padrão do Pandas
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum projeto cadastrado no sistema ainda.")
        else:
            st.error("Erro ao carregar os dados. Verifique a API.")

    except requests.exceptions.ConnectionError:
        st.error(
            "Falha de conexão. O servidor do FastAPI (main.py) está rodando na porta 8000?"
        )

# ==========================================
# TELA 2: NOVO PROJETO
# ==========================================
elif pagina == "Novo Projeto":
    st.title("Novo Projeto de Análise")
    st.write("Insira os parâmetros técnicos e financeiros para calcular a viabilidade.")

    # Cria o formulário visual
    with st.form("form_novo_projeto"):
        nome = st.text_input("NOME DO PROJETO")

        col1, col2 = st.columns(2)
        prazo = col1.number_input("PRAZO (MESES)", min_value=1, step=1, value=12)
        roi = col2.number_input("ROI ESPERADO (%)", min_value=0.0, step=0.1, value=15.0)

        payback = col1.number_input(
            "PAYBACK (MESES)", min_value=0.0, step=0.1, value=6.0
        )
        experiencia = col2.selectbox(
            "EXPERIÊNCIA DA EQUIPE", ["Alta", "Média", "Baixa"]
        )

        # Campos visuais extras do seu protótipo
        contingencia = col1.number_input(
            "RESERVA DE CONTINGÊNCIA (%)", min_value=0, step=1
        )

        st.write("")  # Espaçamento
        tec_inedita = st.checkbox("Tecnologia Inédita no Mercado")
        dep_externas = st.checkbox("Altas Dependências Externas")

        # Botão de submissão
        submit = st.form_submit_button("Calcular Viabilidade & Salvar", type="primary")

        if submit:
            if not nome:
                st.warning("Por favor, preencha o nome do projeto.")
            else:
                # Monta o pacote JSON exatamente com os dados que o seu models.py aceita hoje
                payload = {
                    "nome": nome,
                    "prazo_meses": int(prazo),
                    "roi_esperado": float(roi),
                    "payback_meses": float(payback),
                    "experiencia_equipe": experiencia,
                }

                try:
                    # Envia os dados para a rota POST /projetos
                    res = requests.post(f"{API_URL}/projetos", json=payload)

                    if res.status_code == 200:
                        projeto_salvo = res.json()
                        st.success(
                            f"Projeto salvo com sucesso! Código gerado: {projeto_salvo['codigo']}"
                        )
                    else:
                        st.error(f"Erro na validação do back-end: {res.text}")
                except Exception as e:
                    st.error(f"Não foi possível conectar à API: {e}")
