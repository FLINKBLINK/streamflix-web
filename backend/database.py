
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada.")

connect_args = {}

if "aivencloud.com" in DATABASE_URL.lower():
    connect_args["ssl"] = {
        "ca": "/etc/secrets/ca.pem"
    }

engine_options = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

# Opções de pool específicas para MySQL.
# Não aplicar essas opções ao SQLite usado nos testes.
if DATABASE_URL.startswith(("mysql://", "mysql+")):
    engine_options.update({
        "pool_recycle": 1800,
        "pool_size": 2,
        "max_overflow": 1,
        "pool_timeout": 30,
    })

engine = create_engine(
    DATABASE_URL,
    **engine_options,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
