"""Smoke tests opcionais contra MySQL de teste; nunca apontar para produção."""
import os

import pytest
from sqlalchemy import create_engine, inspect, text


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Defina TEST_DATABASE_URL para executar a integração com MySQL.",
)


def test_mysql_has_schema_and_supports_queries_used_by_analytics():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    required_tables = {
        "usuario",
        "perfil",
        "conteudo",
        "genero",
        "conteudo_genero",
        "historico_visualizacao",
        "assinatura",
        "plano",
        "episodio",
    }
    try:
        with engine.connect() as connection:
            table_names = set(inspect(connection).get_table_names())
            missing = required_tables - table_names
            assert not missing, f"Tabelas ausentes no banco de teste: {sorted(missing)}"

            result = connection.execute(text("""
                SELECT
                    DATE_FORMAT(CURRENT_TIMESTAMP, '%Y-%m') AS periodo,
                    DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY) AS amanha
            """)).mappings().one()
            assert len(result["periodo"]) == 7
            assert result["amanha"] is not None
    finally:
        engine.dispose()
