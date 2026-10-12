from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.routers import api, auth


BASE_DIR = Path(__file__).resolve().parent.parent

# Em produção, a chave precisa ser configurada explicitamente em qualquer provedor.
app_env = os.getenv("APP_ENV", "development").strip().lower()
is_production = app_env == "production" or bool(os.getenv("RENDER"))
session_secret = os.getenv("SESSION_SECRET")

if not session_secret:
    if is_production:
        raise RuntimeError(
            "Configure SESSION_SECRET nas variáveis de ambiente antes de iniciar "
            "a aplicação em produção."
        )

    # Chave previsível apenas para desenvolvimento local. Nunca usar em produção.
    session_secret = "local-dev-only-change-before-deploy"


app = FastAPI(
    title="StreamFlix - A1 Banco de Dados",
    description="Webapp para demonstrar e testar o banco streaming_db.",
    version="1.1.0",
)

# Sessões de autenticação.
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="streamflix_session",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
    https_only=is_production,
    path="/",
)

# Como o frontend é servido pelo próprio FastAPI,
# não é necessário liberar todas as origens por padrão.
# Se o frontend for hospedado separadamente, configure
# suas origens explicitamente.
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

# Rotas da aplicação.
app.include_router(api.router, prefix="/api", tags=["Streaming"])
app.include_router(auth.router, prefix="/api")

# Arquivos HTML, CSS e JavaScript do frontend.
app.mount(
    "/",
    StaticFiles(directory=BASE_DIR / "frontend", html=True),
    name="frontend",
)
