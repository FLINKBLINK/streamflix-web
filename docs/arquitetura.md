# Arquitetura do StreamFlix

## Visão geral

O StreamFlix é uma aplicação web demonstrativa composta por uma interface JavaScript, uma API REST em FastAPI e um banco MySQL acessado por SQLAlchemy.

```text
Navegador (HTML/CSS/JavaScript)
             |
             | HTTP / JSON
             v
       API FastAPI
             |
      Routers / Services
             |
        Repositories
             |
       SQLAlchemy / SQL
             |
          MySQL
```

## Responsabilidades

- **Frontend:** navegação, filtros, tabelas, indicadores e gráficos.
- **Router:** recebe parâmetros HTTP, valida entradas e devolve respostas JSON.
- **Service:** valida filtros e aplica regras de negócio.
- **Repository:** executa consultas SQL e converte resultados em estruturas Python.
- **Banco MySQL:** armazena catálogo, usuários, perfis, assinaturas, gêneros, episódios e histórico.

A separação de serviços e repositórios é aplicada ao módulo de desempenho do catálogo. Os endpoints anteriores são preservados para reduzir o risco de regressões.

## Ambiente e segurança

A conexão usa a variável de ambiente `DATABASE_URL`. Não versionar credenciais nem arquivos `.env`. O painel administrativo é demonstrativo e não possui autenticação; não deve ser usado com dados pessoais reais.
