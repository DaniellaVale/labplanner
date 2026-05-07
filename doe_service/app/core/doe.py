# doe_service/app/doe.py

from __future__ import annotations

import string
from typing import List, Optional

import numpy as np
from pyDOE2 import bbdesign, ccdesign, ff2n, fracfact

from app.schemas import DoeRequest


def get_factor_letters(k: int) -> list[str]:
    letters = list(string.ascii_lowercase)
    if k > len(letters):
        raise ValueError(
            f"Número de fatores ({k}) maior do que o suportado automaticamente ({len(letters)})."
        )
    return letters[:k]


def build_fractional_generator(k: int, p: int) -> str:
    """
    Retorna a string geradora para pyDOE2.fracfact no formato 2^(k-p).

    Estratégia:
    - Para maior robustez no MVP, usa combinações pré-definidas para casos comuns.
    - Isso evita gerar estruturas inadequadas automaticamente.

    Exemplos:
    - (3,1) -> "a b ab"
    - (4,1) -> "a b c abc"
    - (5,1) -> "a b c d abcd"
    - (5,2) -> "a b c ab ac"
    """
    predefined = {
        (3, 1): "a b ab",
        (4, 1): "a b c abc",
        (5, 1): "a b c d abcd",
        (5, 2): "a b c ab ac",
        (6, 1): "a b c d e abcde",
        (6, 2): "a b c d ab ac",
        (7, 1): "a b c d e f abcdef",
        (7, 2): "a b c d e ab ac",
    }

    key = (k, p)
    if key not in predefined:
        raise ValueError(
            f"Combinação de planejamento fracionado não suportada ainda: 2^({k}-{p}). "
            f"Use uma das combinações suportadas: {sorted(predefined.keys())}"
        )

    return predefined[key]


def coded_to_real(matrix: np.ndarray, levels) -> list[list[float]]:
    """
    Converte matriz codificada (-1, 0, +1, etc.) em níveis reais
    usando min e max de cada fator.

    Para CCD, os pontos axiais podem gerar valores fora do intervalo
    se alpha > 1. Neste caso a transformação linear extrapola.
    """
    real_matrix: list[list[float]] = []

    for row in matrix:
        real_row: list[float] = []
        for j, coded_value in enumerate(row):
            min_v = levels[j].minimum
            max_v = levels[j].maximum
            center = (min_v + max_v) / 2.0
            half_range = (max_v - min_v) / 2.0
            real_value = center + float(coded_value) * half_range
            real_row.append(float(real_value))
        real_matrix.append(real_row)

    return real_matrix


def validate_levels(levels: Optional[list], k: int) -> None:
    if levels is None:
        return

    if len(levels) != k:
        raise ValueError(
            f"A quantidade de níveis reais ({len(levels)}) deve ser igual ao número de fatores ({k})."
        )

    for idx, lvl in enumerate(levels, start=1):
        if lvl.minimum >= lvl.maximum:
            raise ValueError(
                f"O fator {idx} ('{lvl.name}') possui mínimo >= máximo."
            )


def generate_design(request: DoeRequest) -> dict:
    design_type = request.design_type
    k = request.factors

    validate_levels(request.levels, k)

    matrix: np.ndarray
    design_notation: str

    if design_type == "fatorial_2k":
        matrix = np.array(ff2n(k), dtype=float)
        design_notation = f"2^{k}"

    elif design_type == "fatorial_fracionado":
        if request.fractionality is None:
            raise ValueError("Para planejamento fatorial fracionado, informe o valor de p.")

        p = request.fractionality
        generator = build_fractional_generator(k, p)
        matrix = np.array(fracfact(generator), dtype=float)
        design_notation = f"2^({k}-{p})"

    elif design_type == "composto_central":
        center_points = request.center_points if request.center_points is not None else 1

        # ccdesign retorna matriz com pontos fatoriais, centrais e axiais
        # center=(nc, ns): nc = centros no cubo, ns = centros na estrela
        matrix = np.array(ccdesign(k, center=(center_points, center_points)), dtype=float)
        design_notation = f"CCD ({k} fatores)"

    elif design_type == "box_behnken":
        if k < 3:
            raise ValueError("Box-Behnken requer pelo menos 3 fatores.")
        matrix = np.array(bbdesign(k), dtype=float)
        design_notation = f"Box-Behnken ({k} fatores)"

    elif design_type == "fatorial_3k":
        raise NotImplementedError("Planejamento fatorial 3k ainda não foi implementado.")

    else:
        raise ValueError(f"Tipo de planejamento inválido: {design_type}")

    if request.levels:
        factor_names = [lvl.name for lvl in request.levels]
        matrix_real = coded_to_real(matrix, request.levels)
    else:
        factor_names = [f"X{i+1}" for i in range(k)]
        matrix_real = None

    return {
        "design_type": design_type,
        "factors": k,
        "rows": int(matrix.shape[0]),
        "matrix": matrix.tolist(),
        "factor_names": factor_names,
        "matrix_real": matrix_real,
        "fractionality": request.fractionality,
        "design_notation": design_notation,
    }