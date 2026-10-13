"""Regras de negócio e validação das análises."""
from datetime import date

from backend.repositories.analytics_repository import listar_desempenho_catalogo


ORDENACOES_PERMITIDAS = {"visualizacoes", "horas_assistidas", "media_assistida", "conclusao", "titulo"}


def normalizar_filtros(tipo=None, genero=None, data_inicio=None, data_fim=None):
    tipo_normalizado = (tipo or "").strip().upper() or None
    if tipo_normalizado and tipo_normalizado not in {"FILME", "SERIE"}:
        raise ValueError("O tipo deve ser FILME ou SERIE.")

    inicio = _validar_data(data_inicio, "data_inicio")
    fim = _validar_data(data_fim, "data_fim")
    if inicio and fim and inicio > fim:
        raise ValueError("A data inicial não pode ser posterior à data final.")

    return {
        "tipo": tipo_normalizado,
        "genero": genero.strip() if genero and genero.strip() else None,
        "data_inicio": inicio,
        "data_fim": fim,
    }


def _validar_data(valor, nome):
    if not valor:
        return None
    try:
        data = date.fromisoformat(valor)
        if data.isoformat() != valor:
            raise ValueError
        return data.isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"{nome} deve estar no formato AAAA-MM-DD.") from None


def desempenho_catalogo(filtros, ordenar_por="visualizacoes", ordem="desc"):
    if ordenar_por not in ORDENACOES_PERMITIDAS:
        raise ValueError("Ordenação inválida.")
    ordem_normalizada = ordem.lower()
    if ordem_normalizada not in {"asc", "desc"}:
        raise ValueError("A ordem deve ser asc ou desc.")
    return listar_desempenho_catalogo(filtros, ordenar_por, ordem_normalizada)
