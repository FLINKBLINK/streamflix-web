
import os
from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

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

        conn.execute(text("""
            CREATE TABLE conteudo (
                id_conteudo INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo VARCHAR(150) NOT NULL,
                tipo VARCHAR(10) NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE TABLE episodio (
                id_episodio INTEGER PRIMARY KEY AUTOINCREMENT,
                id_conteudo INTEGER NOT NULL,
                numero_temporada INTEGER NOT NULL,
                numero_episodio INTEGER NOT NULL,
                titulo_episodio VARCHAR(150) NOT NULL,
                duracao_min INTEGER,
                data_lancamento DATE
            )
        """))

        conn.execute(text("""
            CREATE TABLE historico_visualizacao (
                id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
                id_perfil INTEGER NOT NULL,
                id_conteudo INTEGER NOT NULL,
                id_episodio INTEGER,
                data_hora_inicio DATETIME NOT NULL,
                tempo_assistido_min INTEGER NOT NULL DEFAULT 0,
                concluido BOOLEAN NOT NULL DEFAULT 0
            )
        """))

    TestSession = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    monkeypatch.setattr(auth, "SessionLocal", TestSession)
    monkeypatch.setattr(security, "SessionLocal", TestSession)
    monkeypatch.setattr(api, "SessionLocal", TestSession)

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

    token = obter_csrf(client)

    response = client.post(
        "/api/auth/register",
        json=dados_cadastro(),
        headers={"x-csrf-token": token},
    )

    assert response.status_code == 409


def test_login_rejeita_senha_incorreta(client):
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
            "senha": "SenhaErrada123!",
        },
        headers={"x-csrf-token": token},
    )

    assert response.status_code == 401



def test_login_correto_e_logout(client):
    cadastro = cadastrar(client)
    assert cadastro.status_code == 201

    # Guarda o token e o cookie da sessão autenticada pelo cadastro.
    token_cadastro = cadastro.json()["csrf_token"]

    # Encerra a sessão criada pelo cadastro.
    logout_cadastro = client.post(
        "/api/auth/logout",
        headers={"x-csrf-token": token_cadastro},
    )
    assert logout_cadastro.status_code == 200
    assert client.get("/api/auth/me").json()["autenticado"] is False

    # Obtém um token para a nova sessão anônima.
    token_anonimo = obter_csrf(client)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "teste@example.com",
            "senha": "SenhaSegura123!",
        },
        headers={"x-csrf-token": token_anonimo},
    )

    assert response.status_code == 200
    assert response.json()["usuario"]["email"] == "teste@example.com"
    assert client.get("/api/auth/me").json()["autenticado"] is True

    # O login deve emitir um novo token CSRF.
    token_login = response.json()["csrf_token"]
    assert token_login
    assert token_login != token_anonimo

    # O logout deve invalidar a autenticação atual.
    logout = client.post(
        "/api/auth/logout",
        headers={"x-csrf-token": token_login},
    )

    assert logout.status_code == 200
    assert client.get("/api/auth/me").json()["autenticado"] is False

    # O token da sessão autenticada não deve autorizar outro logout.
    logout_repetido = client.post(
        "/api/auth/logout",
        headers={"x-csrf-token": token_login},
    )
    assert logout_repetido.status_code == 403


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
    assert response.json()["detail"] == (
        "Acesso restrito a administradores."
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/dashboard",
        "/api/analytics/resumo",
        "/api/analytics/visualizacoes",
        "/api/analytics/generos",
        "/api/analytics/catalogo",
        "/api/usuarios",
        "/api/perfis",
        "/api/assinaturas",
        "/api/receita",
    ],
)
def test_usuario_comum_nao_acessa_endpoints_admin(client, endpoint):
    response_cadastro = cadastrar(
        client,
        "usuario_comum@example.com",
    )
    assert response_cadastro.status_code == 201

    response = client.get(endpoint)

    assert response.status_code == 403, (
        f"O endpoint {endpoint} deveria bloquear usuários comuns, "
        f"mas retornou {response.status_code}: {response.text}"
    )



def test_permissao_admin_e_reavaliada_a_cada_requisicao(
    client,
    monkeypatch,
):
    assert cadastrar(client).status_code == 201

    with auth.SessionLocal() as db:
        db.execute(
            text(
                "UPDATE usuario SET papel = 'ADMIN' "
                "WHERE email = :email"
            ),
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



def test_usuario_nao_acessa_historico_de_outro_usuario(client):
    # Cadastra o primeiro usuário.
    response = cadastrar(client, "usuario1@example.com")
    assert response.status_code == 201

    # Obtém o ID real do primeiro usuário e do perfil dele.
    with auth.SessionLocal() as db:
        usuario1 = db.execute(
            text(
                "SELECT id_usuario FROM usuario "
                "WHERE email = :email"
            ),
            {"email": "usuario1@example.com"},
        ).scalar_one()

        perfil1 = db.execute(
            text(
                "SELECT id_perfil FROM perfil "
                "WHERE id_usuario = :id_usuario"
            ),
            {"id_usuario": usuario1},
        ).scalar_one()

        # Cria o segundo usuário.
        resultado = db.execute(
            text("""
                INSERT INTO usuario (
                    nome, email, senha_hash, data_nascimento, papel
                )
                VALUES (
                    'Usuario Dois',
                    'usuario2@example.com',
                    'hash-teste',
                    '1990-01-01',
                    'USUARIO'
                )
            """)
        )
        usuario2 = resultado.lastrowid

        # Cria o perfil do segundo usuário.
        resultado = db.execute(
            text("""
                INSERT INTO perfil (id_usuario, nome_perfil)
                VALUES (:id_usuario, 'Perfil Dois')
            """),
            {"id_usuario": usuario2},
        )
        perfil2 = resultado.lastrowid

        # Cria um conteúdo de teste.
        resultado = db.execute(
            text("""
                INSERT INTO conteudo (titulo, tipo)
                VALUES ('Filme do teste', 'FILME')
            """)
        )
        conteudo_id = resultado.lastrowid

        # Registra um histórico para cada perfil.
        db.execute(
            text("""
                INSERT INTO historico_visualizacao (
                    id_perfil,
                    id_conteudo,
                    data_hora_inicio,
                    tempo_assistido_min,
                    concluido
                )
                VALUES (
                    :perfil1, :conteudo, '2026-01-01 10:00:00', 30, 0
                )
            """),
            {"perfil1": perfil1, "conteudo": conteudo_id},
        )

        db.execute(
            text("""
                INSERT INTO historico_visualizacao (
                    id_perfil,
                    id_conteudo,
                    data_hora_inicio,
                    tempo_assistido_min,
                    concluido
                )
                VALUES (
                    :perfil2, :conteudo, '2026-01-02 10:00:00', 45, 1
                )
            """),
            {"perfil2": perfil2, "conteudo": conteudo_id},
        )

        db.commit()

    # O usuário autenticado vê apenas o próprio histórico.
    response_proprio = client.get("/api/historico")

    assert response_proprio.status_code == 200
    assert len(response_proprio.json()) == 1
    assert response_proprio.json()[0]["id_perfil"] == perfil1

    # Tentar consultar o perfil de outra pessoa não revela dados.
    response_outro = client.get(
        f"/api/historico?id_perfil={perfil2}"
    )

    assert response_outro.status_code == 200
    assert response_outro.json() == []
