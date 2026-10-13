# Arquitetura do StreamFlix

## Visão geral

O StreamFlix é uma aplicação web demonstrativa composta por interface JavaScript, API REST em FastAPI e banco MySQL acessado por SQLAlchemy.

```text
Navegador (HTML/CSS/JavaScript)
             |
             | HTTP / JSON + cookie de sessão
             v
       API FastAPI
       /          \
Autenticação    Routers de API
       |          |
 Segurança     Services
       |          |
       |       Repositories
       |          |
       +---- SQLAlchemy / SQL
                  |
                MySQL
```

## Responsabilidades

- **Frontend:** navegação, formulários, filtros, tabelas e indicadores.
- **Router:** recebe parâmetros HTTP, aplica validações e devolve JSON.
- **Autenticação:** cadastro, login/logout e consulta da sessão.
- **Segurança:** hash de senha Argon2, token CSRF, sessão assinada e autorização por papel.
- **Service:** valida filtros e aplica regras de negócio do ranking.
- **Repository:** executa consultas SQL analíticas.
- **Banco MySQL:** armazena usuários, perfis, catálogo, assinaturas, gêneros, episódios e histórico.

A separação de serviços e repositórios é aplicada ao módulo de desempenho do catálogo. Os endpoints restantes continuam em `backend/routers/api.py`.

## Sessões e autorização

O middleware de sessão usa cookie assinado e uma chave obtida de `SESSION_SECRET`. Em produção, a aplicação falha ao iniciar se essa chave não estiver definida. O cookie usa `SameSite=Lax` e é marcado como `Secure` quando o ambiente é reconhecido como produção.

O token CSRF é exigido em cadastro, login e logout. Endpoints administrativos consultam o papel atual do usuário no banco em cada requisição; o cadastro público sempre cria usuários com papel `USUARIO`.

## Proteção contra tentativas de login

`backend/rate_limit.py` limita a 20 tentativas malsucedidas por cliente em uma janela de cinco minutos. O contador é mantido em memória por processo, portanto não é compartilhado entre workers ou instâncias. Em ambientes escalados, use também um limitador no proxy/WAF ou um armazenamento compartilhado.

## Ambiente e CORS

A conexão usa `DATABASE_URL`. O CORS fica desativado por padrão porque o frontend é servido pela própria API. Se forem usadas origens separadas, informe uma lista explícita em `CORS_ORIGINS`; não habilite origens arbitrárias com credenciais.

Nunca versione credenciais, arquivos `.env`, chaves de sessão ou dados pessoais reais.
