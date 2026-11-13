# GRIPS — Sistema de Gerenciamento de Risco para Projetos

Plataforma de análise de riscos operacionais em projetos de software. Combina
cálculo determinístico (matriz probabilidade × impacto e viabilidade com pesos
explícitos) com um agente de IA (RAG) que gera o parecer técnico fundamentado em
referenciais teóricos (PMBOK, ISO 31000...), citando arquivo e página.

## Estrutura

```
GRIPS/
├── main.py                    # inicia a API (python main.py)
├── backend/                   # API FastAPI + regras de negócio
│   ├── api.py                 # rotas (projetos, riscos, histórico, IA)
│   ├── schemas.py             # contratos de entrada e saída (Pydantic)
│   ├── config.py              # configuração lida do .env
│   ├── database.py            # engine e sessão do SQLAlchemy
│   ├── models.py              # tabelas: Projeto, Risco, HistoricoExposicao
│   ├── motor_riscos.py        # criticidade, prioridade e exposição do projeto
│   ├── motor_viabilidade.py   # fórmula de viabilidade (pesos em constantes)
│   ├── servico_projetos.py    # aplica os motores aos projetos e riscos
│   └── analise_ai.py          # agente RAG (pgvector + Gemini)
├── frontend/                  # painel em Streamlit
│   ├── app.py                 # ponto de entrada: só configura a navegação
│   ├── paginas/               # visao_geral, projetos, riscos, relatorios
│   ├── api_client.py          # chamadas à API, cache e modo demonstração
│   ├── modais.py              # janelas de cadastro, edição e exclusão
│   ├── graficos.py, tabelas.py, componentes.py, constantes.py
│   ├── dados_demo.py          # dados fictícios (só quando a API está fora do ar)
│   └── assets/                # logo.png (opcional)
├── scripts/                   # ingestão de PDFs e migrações
├── tests/                     # motores e API (pytest)
├── documentos/                # PDFs dos referenciais (não vão para o Git)
├── .streamlit/config.toml     # tema do Streamlit
├── docker-compose.yml         # PostgreSQL + pgvector
└── .env.example               # modelo do .env
```

## Como rodar

Sempre a partir da raiz do projeto, com o ambiente virtual ativado.

```bash
cp .env.example .env              # preencha a senha do banco e a GEMINI_API_KEY
docker compose up -d              # sobe o PostgreSQL com pgvector
python -m scripts.ingestao_pdf documentos/pmbok.pdf   # uma vez por referencial
python main.py                    # API em http://127.0.0.1:8000 (docs em /docs)
streamlit run frontend/app.py     # painel em http://localhost:8501
```

Sem a API no ar, o painel abre em **modo demonstração** (dados fictícios, nada é salvo).

## Rotas da API

| Método | Rota | O que faz |
|---|---|---|
| POST | `/projetos` | cria o projeto e calcula a viabilidade |
| GET | `/projetos` | lista os projetos já com seus riscos |
| GET / PUT / DELETE | `/projetos/{id}` | detalha, edita (recalcula viabilidade) ou exclui |
| GET | `/projetos/{id}/historico` | exposição ao longo do tempo |
| POST | `/projetos/{id}/riscos` | adiciona risco e recalcula a exposição |
| PUT / DELETE | `/projetos/{id}/riscos/{risco_id}` | edita ou exclui o risco e recalcula |
| POST | `/projetos/{id}/analisar-ia` | gera o parecer (RAG), com fontes e páginas |

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Atualizando um banco que já existia

```bash
python -m scripts.migrar_status      # só se o banco é anterior à separação dos status
python -m scripts.iniciar_historico  # dá o primeiro ponto do histórico aos projetos antigos
```
