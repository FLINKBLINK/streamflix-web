import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("A variável de ambiente DATABASE_URL não foi configurada.")

# Aiven exige TLS. Ativamos SSL no driver PyMySQL sem passar "ssl-mode"
# na URL, pois esse parâmetro não é reconhecido diretamente pelo PyMySQL.
connect_args = {}
if "aivencloud.com" in DATABASE_URL.lower():
    connect_args["ssl"] = {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=2,
    max_overflow=1,
    pool_timeout=30,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
