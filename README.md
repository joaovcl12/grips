# GRIPS — Sistema de Gerenciamento de Risco para Projetos

Plataforma de análise de riscos operacionais em projetos de software. Combina
cálculo determinístico (matriz probabilidade × impacto) com um agente de IA
(RAG) que gera o parecer técnico fundamentado em referenciais teóricos
(PMBOK, ISO 31000...), citando arquivo e página.

## Estrutura

```
GRIPS/
├── main.py                 # inicia a API (python main.py)
├── backend/                # API FastAPI + regras de negócio
│   ├── api.py              # rotas
│   ├── config.py           # configuração lida do .env
│   ├── database.py         # engine e sessão do SQLAlchemy
│   ├── models.py           # tabelas (Projeto, Risco)
│   ├── motor_riscos.py     # criticidade, prioridade e exposição do projeto
│   ├── motor_viabilidade.py# fórmula de viabilidade (pesos em constantes)
│   ├── servico_projetos.py # aplica os motores a um Projeto
│   └── analise_ai.py       # agente RAG (pgvector + Gemini)
├── frontend/
│   ├── app.py              # painel em Streamlit
│   └── assets/             # logo.png (opcional)
├── scripts/                # ingestão de PDFs e migrações
├── tests/                  # testes dos motores (pytest)
├── documentos/             # PDFs dos referenciais (não vão para o Git)
├── .streamlit/config.toml  # tema do Streamlit
├── docker-compose.yml      # PostgreSQL + pgvector
└── .env.example            # modelo do .env
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

## Testes

```bash
python -m pytest
```

## Migração (só para bancos criados antes da separação dos status)

```bash
python -m scripts.migrar_status
```
