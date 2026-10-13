import pytest

from backend.services.analytics_service import normalizar_filtros, desempenho_catalogo


def test_normalizar_filtros_padroniza_tipo_e_genero():
    filtros = normalizar_filtros(" filme ", " Drama ", "2026-01-01", "2026-01-31")
    assert filtros == {
        "tipo": "FILME",
        "genero": "Drama",
        "data_inicio": "2026-01-01",
        "data_fim": "2026-01-31",
    }


def test_normalizar_filtros_aceita_filtros_vazios():
    assert normalizar_filtros() == {
        "tipo": None,
        "genero": None,
        "data_inicio": None,
        "data_fim": None,
    }


@pytest.mark.parametrize("inicio,fim", [
    ("2026-02-01", "2026-01-01"),
    ("data-invalida", "2026-02-01"),
])
def test_normalizar_filtros_rejeita_periodo_invalido(inicio, fim):
    with pytest.raises(ValueError):
        normalizar_filtros(data_inicio=inicio, data_fim=fim)


def test_desempenho_rejeita_ordenacao_invalida():
    with pytest.raises(ValueError):
        desempenho_catalogo({}, ordenar_por="coluna_sql")


def test_normalizar_filtros_trata_tipo_em_branco_como_todos():
    assert normalizar_filtros(tipo="   ")["tipo"] is None
