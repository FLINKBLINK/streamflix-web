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

## Módulos analíticos

- **Analytics:** indicadores gerais de consumo, visualizações por mês e por gênero, com filtros por tipo e período.
- **Desempenho do catálogo:** ranking por visualizações, horas assistidas, média assistida e taxa de conclusão; permite ordenar e filtrar por tipo, gênero e período.
- **API:** documentação interativa em `/docs`; endpoint analítico adicional em `/api/analytics/catalogo`.

As métricas são calculadas sobre os registros de histórico. A receita exibida é uma estimativa baseada em assinaturas com status `ATIVA`, não um registro de pagamentos realizados.

## Estrutura da entrega acadêmica

- `backend/routers/`: endpoints HTTP.
- `backend/services/`: validações e regras de negócio.
- `backend/repositories/`: consultas SQL analíticas.
- `tests/`: testes automatizados da validação dos filtros e ordenação.
- `docs/arquitetura.md`: visão geral da arquitetura.
- `docs/dicionario_dados.md`: tabelas e campos relevantes.
- `docs/metricas.md`: fórmulas, interpretações e limitações.
- `docs/consultas_sql.md`: consultas para conferência direta no MySQL.

## Executar testes

Instale as dependências de desenvolvimento e execute:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Os testes de serviço não precisam de conexão com o MySQL; eles verificam a validação dos filtros e da ordenação.

## Publicar

A configuração `render.yaml` prepara o serviço web. No painel do Render, configure `DATABASE_URL` como variável secreta usando a URL fornecida pelo provedor MySQL. O banco precisa aceitar conexões externas e ter o esquema e os dados de demonstração carregados.

Planos gratuitos podem ter limites, suspensão por inatividade e mudanças de política; confirme as condições atuais antes de publicar. Não há garantia de disponibilidade contínua ou de custo zero permanente.

## Segurança e escopo

- Nunca publique credenciais, arquivos `.env` ou dumps que contenham dados pessoais reais.
- Os dados de demonstração são fictícios.
- Este protótipo não implementa autenticação real; o painel administrativo é apenas demonstrativo e não deve ser usado para administrar dados sensíveis em produção.
- Este projeto não substitui nem altera os arquivos de entrega acadêmica do repositório original.
