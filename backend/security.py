"""Helpers for signed-cookie authentication and password hashing."""
import hashlib
import hmac
import os
import secrets

from fastapi import HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy import text

from backend.database import SessionLocal

password_hasher = PasswordHash.recommended()
DEMO_PASSWORD_HASH = hashlib.sha256(b"demo-only-not-for-auth").hexdigest()


def csrf_token() -> str:
    return secrets.token_urlsafe(32)


def require_csrf(request: Request) -> None:
    expected = request.session.get("csrf_token")
    supplied = request.headers.get("x-csrf-token", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=403, detail="Token CSRF ausente ou inválido.")


def current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Faça login para acessar este recurso.")
    with SessionLocal() as db:
        row = db.execute(
            text("SELECT id_usuario, nome, email, papel FROM usuario WHERE id_usuario = :id"),
            {"id": user_id},
        ).mappings().first()
    if not row:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sessão inválida. Entre novamente.")
    return dict(row)


def admin_user(request: Request):
    user = current_user(request)
    if user["papel"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return user
