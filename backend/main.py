from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.routers import api, auth

BASE_DIR = Path(__file__).resolve().parent.parent
session_secret = os.getenv("SESSION_SECRET")
if not session_secret:
    if os.getenv("RENDER"):
        raise RuntimeError("Configure SESSION_SECRET nas variáveis de ambiente do Render.")
    session_secret = "local-dev-only-change-before-deploy"

app = FastAPI(
    title="StreamFlix - A1 Banco de Dados",
    description="Webapp para demonstrar e testar o banco streaming_db.",
    version="1.1.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="streamflix_session",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
    https_only=bool(os.getenv("RENDER")),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api", tags=["Streaming"])
app.include_router(auth.router, prefix="/api")
app.mount("/", StaticFiles(directory=BASE_DIR / "frontend", html=True), name="frontend")
