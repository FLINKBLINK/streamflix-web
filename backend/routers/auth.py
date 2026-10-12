from datetime import date
import hashlib
import hmac
import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from backend.database import SessionLocal
from backend.security import DEMO_PASSWORD_HASH, csrf_token, password_hasher, require_csrf

router = APIRouter(prefix="/auth", tags=["Autenticacao"])

class Cadastro(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    senha: str = Field(min_length=10, max_length=128)
    data_nascimento: date

class Credenciais(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    senha: str = Field(min_length=1, max_length=128)

@router.get("/csrf")
def get_csrf(request: Request):
    """Cria ou recupera o token necessário para operações de autenticação."""
    if not request.session.get("csrf_token"):
        request.session["csrf_token"] = csrf_token()
    return {"csrf_token": request.session["csrf_token"]}

def validar_email(email):
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="Informe um e-mail valido.")
    return email

def publico(row):
    return {k: row[k] for k in ("id_usuario", "nome", "email", "papel")}

@router.post("/register", status_code=201)
def register(data: Cadastro, request: Request):
    require_csrf(request)
    email = validar_email(data.email)
    if data.data_nascimento >= date.today():
        raise HTTPException(status_code=400, detail="Data de nascimento invalida.")
    nome = data.nome.strip()
    if len(nome) < 2:
        raise HTTPException(status_code=400, detail="Informe um nome valido.")
    with SessionLocal() as db:
        if db.execute(text("SELECT id_usuario FROM usuario WHERE LOWER(email)=:e"), {"e": email}).first():
            raise HTTPException(status_code=409, detail="Ja existe uma conta com este e-mail.")
        try:
            with db.begin():
                result = db.execute(text("""INSERT INTO usuario
                    (nome,email,senha_hash,data_nascimento,pais,papel)
                    VALUES (:n,:e,:s,:d,'BR','USUARIO')"""),
                    {"n": nome, "e": email, "s": password_hasher.hash(data.senha), "d": data.data_nascimento})
                uid = result.lastrowid
                db.execute(text("INSERT INTO perfil (id_usuario,nome_perfil) VALUES (:u,:n)"),
                    {"u": uid, "n": nome[:50]})
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Nao foi possivel criar a conta.") from exc
        row = db.execute(text("SELECT id_usuario,nome,email,papel FROM usuario WHERE id_usuario=:u"),
                         {"u": uid}).mappings().one()
    request.session.clear()
    request.session["user_id"] = uid
    request.session["csrf_token"] = csrf_token()
    return {"usuario": publico(row), "csrf_token": request.session["csrf_token"]}

@router.post("/login")
def login(data: Credenciais, request: Request):
    require_csrf(request)
    email = validar_email(data.email)
    with SessionLocal() as db:
        row = db.execute(text("""SELECT id_usuario,nome,email,senha_hash,papel
            FROM usuario WHERE LOWER(email)=:e"""), {"e": email}).mappings().first()
        valido = False
        if row and not hmac.compare_digest(row["senha_hash"], DEMO_PASSWORD_HASH):
            try:
                valido = password_hasher.verify(data.senha, row["senha_hash"])
            except Exception:
                valido = False
            if not valido and len(row["senha_hash"]) == 64:
                antigo = hashlib.sha256(data.senha.encode("utf-8")).hexdigest()
                if hmac.compare_digest(antigo, row["senha_hash"]):
                    valido = True
                    db.execute(text("UPDATE usuario SET senha_hash=:s WHERE id_usuario=:u"),
                        {"s": password_hasher.hash(data.senha), "u": row["id_usuario"]})
                    db.commit()
    if not row or not valido:
        raise HTTPException(status_code=401, detail="E-mail ou senha invalidos.")
    request.session.clear()
    request.session["user_id"] = row["id_usuario"]
    request.session["csrf_token"] = csrf_token()
    return {"usuario": publico(row), "csrf_token": request.session["csrf_token"]}

@router.get("/me")
def me(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return {"autenticado": False, "usuario": None, "csrf_token": None}
    with SessionLocal() as db:
        row = db.execute(text("SELECT id_usuario,nome,email,papel FROM usuario WHERE id_usuario=:u"),
                         {"u": uid}).mappings().first()
    if not row:
        request.session.clear()
        return {"autenticado": False, "usuario": None, "csrf_token": None}
    if not request.session.get("csrf_token"):
        request.session["csrf_token"] = csrf_token()
    return {"autenticado": True, "usuario": publico(row), "csrf_token": request.session["csrf_token"]}

@router.post("/logout")
def logout(request: Request):
    require_csrf(request)
    request.session.clear()
    return {"ok": True}
