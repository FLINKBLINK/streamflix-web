from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
import secrets
from backend.routers import api, auth

BASE_DIR = Path(__file__).resolve().parent.parent

session_secret = os.getenv("SESSION_SECRET")\nif not session_secret:\n    if os.getenv("RENDER"):\n        raise RuntimeError("Configure SESSION_SECRET nas variáveis de ambiente do Render.")\n    session_secret = "local-dev-only-change-before-deploy"\n\napp = FastAPI(
    title="StreamFlix - A1 Banco de Dados",
    description="Webapp para demonstrar e testar o banco streaming_db.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api", tags=["Streaming"])\napp.include_router(auth.router, prefix="/api")
app.mount("/", StaticFiles(directory=BASE_DIR / "frontend", html=True), name="frontend")
