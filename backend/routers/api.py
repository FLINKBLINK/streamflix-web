
from fastapi import APIRouter, HTTPException, Depends
from backend.security import current_user, admin_user
from sqlalchemy import text
from backend.database import SessionLocal
from typing import Optional
from backend.services.analytics_service import (
    normalizar_filtros,
    desempenho_catalogo,
)

router = APIRouter()


# ============================================================
# FUNÇÃO AUXILIAR PARA CONSULTAS
# ============================================================

def query(sql, params=None):
    with SessionLocal() as db:
        result = db.execute(
            text(sql),
            params or {}
        ).fetchall()

        return [dict(row._mapping) for row in result]


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
def health():
    try:
        query("SELECT 1 AS ok")

        return {
            "status": "ok",
            "database": "conectado"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponível. Tente novamente mais tarde."
        )


# ============================================================
# DASHBOARD — SOMENTE ADMINISTRADOR
# ============================================================

@router.get("/dashboard", dependencies=[Depends(admin_user)])
def dashboard():
    rows = query("""
        SELECT 'usuarios' AS tabela, COUNT(*) AS total
        FROM usuario

        UNION ALL

        SELECT 'conteudos', COUNT(*)
        FROM conteudo

        UNION ALL

        SELECT 'planos', COUNT(*)
        FROM plano

        UNION ALL

        SELECT 'assinaturas', COUNT(*)
        FROM assinatura

        UNION ALL

        SELECT 'perfis', COUNT(*)
        FROM perfil

        UNION ALL

        SELECT 'visualizacoes', COUNT(*)
        FROM historico_visualizacao
    """)

    return {
        r["tabela"]: r["total"]
        for r in rows
    }


# ============================================================
# CATÁLOGO DE CONTEÚDOS — PÚBLICO
# ============================================================

@router.get("/conteudos")
def conteudos(
    tipo: Optional[str] = None,
    genero: Optional[str] = None
):
    sql = """
        SELECT DISTINCT
            c.id_conteudo,
            c.titulo,
            c.tipo,
            c.ano_lancamento,
            c.classificacao_indicativa,
            c.duracao_min,
            c.sinopse,
            c.data_adicao_catalogo

        FROM conteudo c

        LEFT JOIN conteudo_genero cg
            ON cg.id_conteudo = c.id_conteudo

        LEFT JOIN genero g
            ON g.id_genero = cg.id_genero

        WHERE
            (:tipo IS NULL OR c.tipo = :tipo)
            AND (:genero IS NULL OR g.nome_genero = :genero)

        ORDER BY c.titulo
    """

    return query(
        sql,
        {
            "tipo": tipo.upper() if tipo else None,
            "genero": genero or None
        }
    )


# ============================================================
# DETALHES DE UM CONTEÚDO — PÚBLICO
# ============================================================

@router.get("/conteudos/{id_conteudo}")
def conteudo(id_conteudo: int):
    rows = query("""
        SELECT
            c.*,

            GROUP_CONCAT(
                g.nome_genero
                ORDER BY g.nome_genero
                SEPARATOR ', '
            ) AS generos

        FROM conteudo c

        LEFT JOIN conteudo_genero cg
            ON cg.id_conteudo = c.id_conteudo

        LEFT JOIN genero g
            ON g.id_genero = cg.id_genero

        WHERE c.id_conteudo = :id

        GROUP BY c.id_conteudo
    """, {
        "id": id_conteudo
    })

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Conteúdo não encontrado"
        )

    result = rows[0]

    if result["tipo"] == "SERIE":
        result["episodios"] = query("""
            SELECT
                id_episodio,
                numero_temporada,
                numero_episodio,
                titulo_episodio,
                duracao_min,
                data_lancamento

            FROM episodio

            WHERE id_conteudo = :id

            ORDER BY
                numero_temporada,
                numero_episodio
        """, {
            "id": id_conteudo
        })

    return result


# ============================================================
# GÊNEROS — PÚBLICO
# ============================================================

@router.get("/generos")
def generos():
    return query("""
        SELECT
            id_genero,
            nome_genero

        FROM genero

        ORDER BY nome_genero
    """)


# ============================================================
# ANALYTICS — FILTROS
# ============================================================

def analytics_filters(
    tipo=None,
    genero=None,
    data_inicio=None,
    data_fim=None
):
    """Normaliza e valida filtros para todos os endpoints analíticos."""
    try:
        return normalizar_filtros(tipo, genero, data_inicio, data_fim)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


ANALYTICS_FROM = """
    FROM historico_visualizacao h
    JOIN conteudo c ON c.id_conteudo = h.id_conteudo
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
        AND (
            :data_inicio IS NULL
            OR h.data_hora_inicio >= :data_inicio
        )
        AND (
            :data_fim IS NULL
            OR h.data_hora_inicio < DATE_ADD(:data_fim, INTERVAL 1 DAY)
        )
"""


# ============================================================
# ANALYTICS — RESUMO — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/analytics/resumo",
    dependencies=[Depends(admin_user)]
)
def analytics_resumo(
    tipo: Optional[str] = None,
    genero: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    params = analytics_filters(
        tipo,
        genero,
        data_inicio,
        data_fim
    )

    consumo = query("""
        SELECT
            COUNT(DISTINCT h.id_historico) AS total_visualizacoes,
            COALESCE(SUM(h.tempo_assistido_min), 0) AS minutos_assistidos,
            COALESCE(
                ROUND(
                    100 * AVG(
                        CASE
                            WHEN h.concluido = 1 THEN 1.0
                            ELSE 0.0
                        END
                    ),
                    1
                ),
                0
            ) AS taxa_conclusao,
            COUNT(DISTINCT c.id_conteudo) AS conteudos_assistidos
    """ + ANALYTICS_FROM, params)

    receita = query("""
        SELECT
            COALESCE(SUM(pl.preco_mensal), 0)
            AS receita_mensal_estimada

        FROM assinatura a

        JOIN plano pl
            ON pl.id_plano = a.id_plano

        WHERE a.status = 'ATIVA'
    """)

    result = consumo[0]

    result["horas_assistidas"] = round(
        float(result.pop("minutos_assistidos") or 0) / 60,
        1
    )

    result["receita_mensal_estimada"] = float(
        receita[0]["receita_mensal_estimada"] or 0
    )

    return result


# ============================================================
# ANALYTICS — VISUALIZAÇÕES — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/analytics/visualizacoes",
    dependencies=[Depends(admin_user)]
)
def analytics_visualizacoes(
    tipo: Optional[str] = None,
    genero: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    return query("""
        SELECT
            DATE_FORMAT(h.data_hora_inicio, '%Y-%m') AS periodo,
            COUNT(DISTINCT h.id_historico) AS visualizacoes,
            ROUND(
                COALESCE(SUM(h.tempo_assistido_min), 0) / 60,
                1
            ) AS horas_assistidas
    """ + ANALYTICS_FROM + """
        GROUP BY DATE_FORMAT(h.data_hora_inicio, '%Y-%m')
        ORDER BY periodo
    """, analytics_filters(
        tipo,
        genero,
        data_inicio,
        data_fim
    ))


# ============================================================
# ANALYTICS — GÊNEROS — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/analytics/generos",
    dependencies=[Depends(admin_user)]
)
def analytics_generos(
    tipo: Optional[str] = None,
    genero: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    return query("""
        SELECT
            g.nome_genero AS genero,
            COUNT(DISTINCT h.id_historico) AS visualizacoes

        FROM historico_visualizacao h

        JOIN conteudo c
            ON c.id_conteudo = h.id_conteudo

        JOIN conteudo_genero cg
            ON cg.id_conteudo = c.id_conteudo

        JOIN genero g
            ON g.id_genero = cg.id_genero

        WHERE
            (:tipo IS NULL OR c.tipo = :tipo)
            AND (:genero IS NULL OR g.nome_genero = :genero)
            AND (
                :data_inicio IS NULL
                OR h.data_hora_inicio >= :data_inicio
            )
            AND (
                :data_fim IS NULL
                OR h.data_hora_inicio < DATE_ADD(:data_fim, INTERVAL 1 DAY)
            )

        GROUP BY g.id_genero, g.nome_genero

        ORDER BY visualizacoes DESC, genero

        LIMIT 8
    """, analytics_filters(
        tipo,
        genero,
        data_inicio,
        data_fim
    ))


# ============================================================
# DESEMPENHO DO CATÁLOGO — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/analytics/catalogo",
    dependencies=[Depends(admin_user)]
)
def analytics_catalogo(
    tipo: Optional[str] = None,
    genero: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    ordenar_por: str = "visualizacoes",
    ordem: str = "desc"
):
    try:
        filtros = normalizar_filtros(
            tipo,
            genero,
            data_inicio,
            data_fim
        )

        return desempenho_catalogo(
            filtros,
            ordenar_por,
            ordem
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc


# ============================================================
# USUÁRIOS — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/usuarios",
    dependencies=[Depends(admin_user)]
)
def usuarios():
    return query("""
        SELECT
            id_usuario,
            nome,
            pais

        FROM usuario

        ORDER BY nome
    """)


# ============================================================
# PERFIS — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/perfis",
    dependencies=[Depends(admin_user)]
)
def perfis():
    return query("""
        SELECT
            p.id_perfil,
            p.nome_perfil,
            p.idioma_preferido,
            p.classificacao_maxima,
            p.perfil_infantil,

            u.id_usuario,
            u.nome AS usuario

        FROM perfil p

        JOIN usuario u
            ON u.id_usuario = p.id_usuario

        ORDER BY
            u.nome,
            p.nome_perfil
    """)


# ============================================================
# HISTÓRICO — USUÁRIO AUTENTICADO OU ADMINISTRADOR
# ============================================================

@router.get("/historico")
def historico(
    id_perfil: Optional[int] = None,
    usuario: dict = Depends(current_user)
):
    eh_admin = usuario["papel"] == "ADMIN"

    return query("""
        SELECT
            h.id_historico,
            h.id_perfil,
            u.nome AS usuario,
            p.nome_perfil,
            h.id_conteudo,
            c.titulo,
            c.tipo,
            h.id_episodio,
            e.numero_temporada,
            e.numero_episodio,
            e.titulo_episodio,
            h.data_hora_inicio,
            h.tempo_assistido_min,
            h.concluido

        FROM historico_visualizacao h

        JOIN perfil p
            ON p.id_perfil = h.id_perfil

        JOIN usuario u
            ON u.id_usuario = p.id_usuario

        JOIN conteudo c
            ON c.id_conteudo = h.id_conteudo

        LEFT JOIN episodio e
            ON e.id_episodio = h.id_episodio

        WHERE
            (
                :id_perfil IS NULL
                OR h.id_perfil = :id_perfil
            )
            AND (
                :eh_admin = 1
                OR u.id_usuario = :id_usuario
            )

        ORDER BY h.data_hora_inicio DESC
    """, {
        "id_perfil": id_perfil,
        "eh_admin": int(eh_admin),
        "id_usuario": usuario["id_usuario"]
    })


# ============================================================
# ASSINATURAS — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/assinaturas",
    dependencies=[Depends(admin_user)]
)
def assinaturas():
    return query("""
        SELECT
            a.id_assinatura,

            u.nome AS usuario,

            pl.nome_plano,
            pl.preco_mensal,
            pl.qualidade_maxima,
            pl.telas_simultaneas,
            pl.permite_download,

            a.data_inicio,
            a.data_fim,
            a.status,
            a.forma_pagamento

        FROM assinatura a

        JOIN usuario u
            ON u.id_usuario = a.id_usuario

        JOIN plano pl
            ON pl.id_plano = a.id_plano

        ORDER BY
            a.status,
            u.nome
    """)


# ============================================================
# RECEITA — SOMENTE ADMINISTRADOR
# ============================================================

@router.get(
    "/receita",
    dependencies=[Depends(admin_user)]
)
def receita():
    return query("""
        SELECT
            pl.nome_plano,

            COUNT(a.id_assinatura)
                AS assinantes_ativos,

            SUM(pl.preco_mensal)
                AS receita_mensal

        FROM assinatura a

        JOIN plano pl
            ON pl.id_plano = a.id_plano

        WHERE a.status = 'ATIVA'

        GROUP BY pl.nome_plano

        ORDER BY receita_mensal DESC
    """)


# ============================================================
# PLANOS — PÚBLICO
# ============================================================

@router.get("/planos")
def planos():
    return query("""
        SELECT
            id_plano,
            nome_plano,
            preco_mensal,
            qualidade_maxima,
            telas_simultaneas,
            permite_download

        FROM plano

        ORDER BY preco_mensal
    """)
