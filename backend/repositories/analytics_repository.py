"""Consultas SQL do módulo de Analytics.

As consultas ficam separadas da camada HTTP para facilitar manutenção e validação.
"""
from sqlalchemy import text

from backend.database import SessionLocal


def listar_desempenho_catalogo(filtros: dict, ordenar_por: str, ordem: str) -> list[dict]:
    """Retorna indicadores por conteúdo, inclusive conteúdos sem visualizações."""
    colunas_ordenacao = {
        "visualizacoes": "visualizacoes",
        "horas_assistidas": "horas_assistidas",
        "media_assistida": "media_minutos_assistidos",
        "conclusao": "taxa_conclusao",
        "titulo": "titulo",
    }
    coluna = colunas_ordenacao.get(ordenar_por, "visualizacoes")
    direcao = "ASC" if ordem.lower() == "asc" else "DESC"

    sql = f"""
        SELECT
            c.id_conteudo,
            c.titulo,
            c.tipo,
            c.ano_lancamento,
            COUNT(h.id_historico) AS visualizacoes,
            ROUND(COALESCE(SUM(h.tempo_assistido_min), 0) / 60, 2) AS horas_assistidas,
            ROUND(COALESCE(AVG(h.tempo_assistido_min), 0), 1) AS media_minutos_assistidos,
            COALESCE(SUM(CASE WHEN h.concluido = 1 THEN 1 ELSE 0 END), 0) AS reproducoes_concluidas,
            ROUND(
                COALESCE(
                    100 * SUM(CASE WHEN h.concluido = 1 THEN 1.0 ELSE 0.0 END)
                    / NULLIF(COUNT(h.id_historico), 0),
                    0
                ),
                1
            ) AS taxa_conclusao
        FROM conteudo c
        LEFT JOIN historico_visualizacao h
            ON h.id_conteudo = c.id_conteudo
            AND (:data_inicio IS NULL OR h.data_hora_inicio >= :data_inicio)
            AND (:data_fim IS NULL OR h.data_hora_inicio < DATE_ADD(:data_fim, INTERVAL 1 DAY))
        WHERE
            (:tipo IS NULL OR c.tipo = :tipo)
            AND (
                :genero IS NULL OR EXISTS (
                    SELECT 1
                    FROM conteudo_genero cg
                    JOIN genero g ON g.id_genero = cg.id_genero
                    WHERE cg.id_conteudo = c.id_conteudo
                      AND g.nome_genero = :genero
                )
            )
        GROUP BY c.id_conteudo, c.titulo, c.tipo, c.ano_lancamento
        ORDER BY {coluna} {direcao}, c.titulo ASC
    """
    with SessionLocal() as db:
        rows = db.execute(text(sql), filtros).fetchall()
        return [dict(row._mapping) for row in rows]
