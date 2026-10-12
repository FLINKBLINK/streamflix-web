# StreamFlix Web

Aplicação demonstrativa de uma plataforma de streaming, com interface web, API em FastAPI e banco de dados MySQL. Este repositório é independente da entrega acadêmica original.

## Estrutura

- `backend/`: API e conexão SQLAlchemy com MySQL.
- `frontend/`: HTML, CSS e JavaScript servidos pelo FastAPI.
- `database/schema.sql`: esquema consolidado do banco para a aplicação web.
- `database/seed.sql`: dados fictícios para demonstração.
- `render.yaml`: configuração inicial de deploy no Render.

## Executar localmente

Requisitos: Python 3.11+ e um servidor MySQL acessível.

1. Crie um banco chamado `streaming_db` no MySQL.
2. Execute `database/schema.sql` no banco vazio.
3. Execute `database/seed.sql` uma única vez.
4. Crie um ambiente virtual e instale as dependências:

   ```bash
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. Copie `.env.example` para `.env` e configure `DATABASE_URL` com os dados do seu banco. Não envie `.env` ao GitHub.
6. Inicie a aplicação:

   ```bash
   uvicorn backend.main:app --reload
   ```

7. Acesse `http://127.0.0.1:8000` e a documentação da API em `http://127.0.0.1:8000/docs`.

## Publicar

A configuração `render.yaml` prepara o serviço web. No painel do Render, configure `DATABASE_URL` como variável secreta usando a URL fornecida pelo provedor MySQL. O banco precisa aceitar conexões externas e ter o esquema e os dados de demonstração carregados.

Planos gratuitos podem ter limites, suspensão por inatividade e mudanças de política; confirme as condições atuais antes de publicar. Não há garantia de disponibilidade contínua ou de custo zero permanente.

## Segurança e escopo

- Nunca publique credenciais, arquivos `.env` ou dumps que contenham dados pessoais reais.
- Os dados de demonstração são fictícios.
- Este protótipo não implementa autenticação real; o painel administrativo é apenas demonstrativo e não deve ser usado para administrar dados sensíveis em produção.
- Este projeto não substitui nem altera os arquivos de entrega acadêmica do repositório original.
