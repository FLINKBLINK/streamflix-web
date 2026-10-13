# StreamFlix Web

Aplicação demonstrativa de uma plataforma de streaming, com frontend em HTML/CSS/JavaScript, API REST em FastAPI e banco de dados MySQL. Este repositório é independente da entrega acadêmica original.

## Funcionalidades

- Catálogo público de filmes e séries, com filtros por tipo e gênero.
- Cadastro, login e logout com sessão assinada, hash de senha Argon2 e proteção CSRF.
- Histórico de visualizações privado por usuário; cada usuário consulta apenas os próprios registros.
- Área administrativa protegida por papel `ADMIN`.
- Indicadores de consumo, visualizações por mês e gênero e ranking de desempenho do catálogo.
- API documentada automaticamente pelo FastAPI em `/docs`.
- Testes automatizados e workflow de CI no GitHub Actions.

A receita mensal exibida é uma estimativa da soma dos preços de planos associados a assinaturas `ATIVA`; não representa pagamentos processados ou receita contábil. Os dados de demonstração são fictícios.

## Arquitetura e estrutura

- `backend/main.py`: inicialização do FastAPI, sessão, CORS configurável e montagem do frontend.
- `backend/routers/auth.py`: cadastro, login, logout e consulta da sessão.
- `backend/routers/api.py`: endpoints de catálogo, histórico, administração e analytics.
- `backend/security.py`: hash de senhas, token CSRF e autorização por papel.
- `backend/rate_limit.py`: limitação local de tentativas malsucedidas de login.
- `backend/services/analytics_service.py`: validação de filtros e regras do ranking.
- `backend/repositories/analytics_repository.py`: consultas de desempenho do catálogo.
- `frontend/`: interface web.
- `database/schema.sql`: esquema completo para um banco novo.
- `database/seed.sql`: dados fictícios para demonstração, a executar uma única vez.
- `database/migrations/001_authentication.sql`: migração de uma base anterior que ainda não possui o campo `papel`.
- `tests/`: testes automatizados; a verificação de integração MySQL é opcional.
- `docs/`: arquitetura, métricas, dicionário de dados, consultas SQL e implantação.
- `.github/workflows/tests.yml`: validações executadas em push e pull request.
- `render.yaml`: configuração de implantação no Render.

Veja [arquitetura](docs/arquitetura.md) e [instruções de implantação](docs/implantacao.md).

## Executar localmente

Requisitos: Python 3.11+ e um servidor MySQL acessível.

1. Crie o banco `streaming_db`.
2. Para um banco **novo e vazio**, execute `database/schema.sql` e depois `database/seed.sql`, uma única vez.
3. Para um banco **existente**, faça backup e leia [docs/implantacao.md](docs/implantacao.md). Não execute o esquema consolidado nem a migração às cegas sobre uma base existente.
4. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

5. Instale as dependências: `pip install -r requirements.txt`.
6. Copie `.env.example` para `.env` e configure `DATABASE_URL`. Em desenvolvimento, o backend usa uma chave de sessão local padrão se `SESSION_SECRET` não for definida; nunca use esse padrão em produção.
7. Inicie a aplicação:

   ```bash
   uvicorn backend.main:app --reload
   ```

8. Acesse `http://127.0.0.1:8000`; a documentação da API fica em `http://127.0.0.1:8000/docs`.

## Configurar o primeiro administrador

O cadastro público cria sempre um usuário com papel `USUARIO`. Para configurar um administrador:

1. Inicie a aplicação e crie uma conta pela interface.
2. No MySQL, confira o e-mail exato da conta e promova somente essa conta:

   ```sql
   UPDATE usuario
   SET papel = 'ADMIN'
   WHERE email = 'seu-email@exemplo.com';
   ```

3. Confirme que apenas uma linha foi alterada e saia/entre novamente na aplicação.

Os usuários incluídos no `seed.sql` têm hashes de senha de demonstração intencionalmente inutilizáveis para login. Não use essas contas como contas administrativas.

## Testes e validações

Instale as dependências de desenvolvimento e execute:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q backend tests
node --check frontend/app.js
```

Os testes padrão usam SQLite em memória para testar rotas e regras sem tocar no banco hospedado. Para executar também o teste de integração MySQL, defina `TEST_DATABASE_URL` apontando **exclusivamente para um banco de teste descartável** e execute `python -m pytest -q` novamente. Não aponte testes para um banco de produção.

O GitHub Actions executa os testes, a compilação sintática de Python e a verificação sintática do JavaScript.

## Publicar no Render

A configuração `render.yaml` declara o serviço web e gera uma chave `SESSION_SECRET` secreta. Configure `DATABASE_URL` no painel do Render com a URL do provedor MySQL. Confirme que o banco permite conexões a partir do serviço e que o esquema/dados foram carregados. Se o provedor exigir um certificado CA, configure o arquivo secreto e o caminho esperado pela aplicação.

Após o deploy, valide `/api/health`, cadastro, login/logout, acesso ao histórico e autorização administrativa. O health check confirma a conexão com o banco, não a correção de todas as funcionalidades.

Planos gratuitos podem ter limites, suspensão por inatividade e mudanças de política; confirme as condições atuais. Não há garantia de disponibilidade contínua ou de custo zero permanente.

## Segurança e limitações

- Credenciais e arquivos `.env` nunca devem ser enviados ao GitHub.
- A sessão usa cookie assinado, `HttpOnly`, `SameSite=Lax` e `Secure` em produção.
- Operações de autenticação que alteram estado exigem token CSRF.
- Endpoints administrativos verificam o papel atual do usuário no banco.
- O rate limiting de login é local a cada processo e não compartilha contadores entre instâncias. Em produção escalada, configure também limitação no proxy/WAF ou um backend compartilhado.
- Antes de usar com dados reais, faça revisão de segurança, configure monitoramento, backups, política de retenção e testes de integração.
- Este projeto não substitui nem altera os arquivos da entrega acadêmica original.
