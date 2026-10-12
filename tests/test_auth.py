
from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from backend.routers import api, auth
import backend.security as security


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE usuario (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                senha_hash VARCHAR(255) NOT NULL,
                data_nascimento DATE NOT NULL,
                pais VARCHAR(2) NOT NULL DEFAULT 'BR',
                papel VARCHAR(20) NOT NULL DEFAULT 'USUARIO'
            )
        """))
        conn.execute(text("""
            CREATE TABLE perfil (
                id_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                nome_perfil VARCHAR(50) NOT NULL
            )
        """))

    TestSession = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
    monkeypatch.setattr(auth, "SessionLocal", TestSession)
    monkeypatch.setattr(security, "SessionLocal", TestSession)

    app = FastAPI()
    app.add_middleware(
        SessionMiddleware,
        secret_key="test-only-secret-key",
        session_cookie="streamflix_test_session",
    )
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")

    with TestClient(app) as test_client:
        yield test_client

    engine.dispose()


def obter_csrf(client):
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    return response.json()["csrf_token"]


def dados_cadastro(email="teste@example.com"):
    return {
        "nome": "Usuario Teste",
        "email": email,
        "senha": "SenhaSegura123!",
        "data_nascimento": (
            date.today() - timedelta(days=365 * 25)
        ).isoformat(),
    }


def cadastrar(client, email="teste@example.com"):
    token = obter_csrf(client)
    return client.post(
        "/api/auth/register",
        json=dados_cadastro(email),
        headers={"x-csrf-token": token},
    )


def test_cadastro_cria_usuario_perfil_e_sessao(client):
    response = cadastrar(client)

    assert response.status_code == 201
    assert response.json()["usuario"]["email"] == "teste@example.com"
    assert response.json()["usuario"]["papel"] == "USUARIO"

    with client as _:
        usuario = client.get("/api/auth/me").json()
        assert usuario["autenticado"] is True

    with auth.SessionLocal() as db:
        total_usuarios = db.execute(
            text("SELECT COUNT(*) FROM usuario")
        ).scalar_one()
        total_perfis = db.execute(
            text("SELECT COUNT(*) FROM perfil")
        ).scalar_one()

    assert total_usuarios == 1
    assert total_perfis == 1


def test_cadastro_rejeita_email_duplicado(client):
    assert cadastrar(client).status_code == 201

    # Recupera o token da sessão após o primeiro cadastro.
    token = obter_csrf(client)
    response = client.post(
        "/api/auth/register",
        json=dados_cadastro(),
        headers={"x-csrf-token": token},
    )

    assert response.status_code == 409


def test_login_rejeita_senha_incorreta(client):
    assert cadastrar(client).status_code == 201
    client.post("/api/auth/logout", headers={
        "x-csrf-token": obter_csrf(client)
    })

    token = obter_csrf(client)
    response = client.post(
        "/api/auth/login",
        json={
            "email": "teste@example.com",
            "senha": "SenhaErrada123!",
        },
        headers={"x-csrf-token": token},
    )

    assert response.status_code == 401


def test_login_correto_e_logout(client):
    assert cadastrar(client).status_code == 201

    client.post(
        "/api/auth/logout",
        headers={"x-csrf-token": obter_csrf(client)},
    )

    token = obter_csrf(client)
    response = client.post(
        "/api/auth/login",
        json={
            "email": "teste@example.com",
            "senha": "SenhaSegura123!",
        },
        headers={"x-csrf-token": token},
    )

    assert response.status_code == 200
    assert response.json()["usuario"]["email"] == "teste@example.com"
    assert client.get("/api/auth/me").json()["autenticado"] is True

    token = response.json()["csrf_token"]
    logout = client.post(
        "/api/auth/logout",
        headers={"x-csrf-token": token},
    )

    assert logout.status_code == 200
    assert client.get("/api/auth/me").json()["autenticado"] is False


def test_cadastro_sem_csrf_e_bloqueado(client):
    response = client.post(
        "/api/auth/register",
        json=dados_cadastro(),
    )

    assert response.status_code == 403



def test_historico_exige_autenticacao(client):
    response = client.get("/api/historico")

    assert response.status_code == 401


def test_usuario_comum_nao_acessa_dashboard_admin(client):
    assert cadastrar(client).status_code == 201

    response = client.get("/api/dashboard")

    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso restrito a administradores."


def test_permissao_admin_e_reavaliada_a_cada_requisicao(client, monkeypatch):
    assert cadastrar(client).status_code == 201

    # O papel é lido do banco a cada requisição, não confiado apenas ao cookie.
    with auth.SessionLocal() as db:
        db.execute(
            text("UPDATE usuario SET papel = 'ADMIN' WHERE email = :email"),
            {"email": "teste@example.com"},
        )
        db.commit()

    monkeypatch.setattr(
        api,
        "query",
        lambda sql, params=None: [
            {"tabela": "usuarios", "total": 1}
        ],
    )

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json() == {"usuarios": 1}
