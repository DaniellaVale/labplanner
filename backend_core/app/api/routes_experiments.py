from __future__ import annotations

import itertools
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models import (
    DoeResponse,
    Experiment,
    ExperimentCreate,
    ExperimentResponsesUpdate,
    ExperimentSummary,
)
from app.services.analysis import regression_analysis
from app.services.experiments_storage import (
    list_experiments as storage_list_experiments,
    load_experiment,
    save_new_experiment,
    update_experiment_responses,
)
from app.services.plotting import generate_pareto, generate_surface_plot

router = APIRouter()

PLOTS_DIR = Path("/tmp/labplanner_plots")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------- utilidades ----------------

def coded_to_real(coded_value: float, minimum: float, maximum: float) -> float:
    return (coded_value + 1.0) / 2.0 * (maximum - minimum) + minimum


def matrix_to_real(matrix, levels):
    real_matrix = []

    for row in matrix:
        real_row = []
        for value, level in zip(row, levels):
            if hasattr(level, "minimum"):
                minimum = float(level.minimum)
                maximum = float(level.maximum)
            else:
                minimum = float(level["minimum"])
                maximum = float(level["maximum"])

            real_row.append(coded_to_real(float(value), minimum, maximum))
        real_matrix.append(real_row)

    return real_matrix


def apply_replicates(matrix, replicates: int):
    if replicates < 1:
        raise ValueError("O número de replicatas por ensaio deve ser pelo menos 1.")

    replicated = []
    for row in matrix:
        for _ in range(replicates):
            replicated.append(list(row))
    return replicated


def append_center_points(matrix, k: int, center_points: int):
    if center_points < 0:
        raise ValueError("O número de pontos centrais não pode ser negativo.")

    final_matrix = [list(row) for row in matrix]
    for _ in range(center_points):
        final_matrix.append([0.0] * k)
    return final_matrix


# ---------------- geradores DOE ----------------

def generate_2k_matrix(k: int):
    levels = [-1, 1]
    return [list(row) for row in itertools.product(levels, repeat=k)]


def generate_3k_matrix(k: int):
    levels = [-1, 0, 1]
    return [list(row) for row in itertools.product(levels, repeat=k)]


def generate_fractional_2k_matrix(k: int, p: int):
    """
    Gera um planejamento fracionado regular 2^(k-p) em níveis codificados.
    """
    if p <= 0:
        return generate_2k_matrix(k)

    if k < 3:
        raise ValueError("Planejamento fracionado requer pelo menos 3 fatores.")

    if p >= k:
        raise ValueError("No planejamento fracionado, p deve ser menor que k.")

    n_base = k - p
    if n_base < 2:
        raise ValueError("O número de fatores básicos deve ser pelo menos 2.")

    base_matrix = generate_2k_matrix(n_base)

    combos = []
    for r in range(2, n_base + 1):
        combos.extend(itertools.combinations(range(n_base), r))

    if len(combos) < p:
        raise ValueError("Não foi possível gerar colunas suficientes para o fracionamento solicitado.")

    generator_combos = combos[:p]

    matrix = []
    for row in base_matrix:
        new_row = list(row)

        for combo in generator_combos:
            value = 1
            for idx in combo:
                value *= row[idx]
            new_row.append(float(value))

        matrix.append(new_row)

    return matrix


def generate_ccd_base_matrix(k: int, alpha: float | None = None):
    """
    Parte base do composto central:
    - pontos fatoriais
    - pontos axiais
    Sem pontos centrais, que serão adicionados depois.
    """
    if k < 2:
        raise ValueError("CCD requer pelo menos 2 fatores.")

    factorial = generate_2k_matrix(k)

    if alpha is None:
        alpha = (2 ** k) ** 0.25

    axial = []
    for i in range(k):
        plus = [0.0] * k
        minus = [0.0] * k
        plus[i] = float(alpha)
        minus[i] = -float(alpha)
        axial.append(plus)
        axial.append(minus)

    return factorial + axial


def generate_box_behnken_base_matrix(k: int):
    """
    Parte base do Box-Behnken, sem pontos centrais.
    """
    if k < 3:
        raise ValueError("Box-Behnken requer pelo menos 3 fatores.")

    matrix = []
    pair_levels = list(itertools.product([-1, 1], repeat=2))

    for i, j in itertools.combinations(range(k), 2):
        for lv_i, lv_j in pair_levels:
            row = [0.0] * k
            row[i] = lv_i
            row[j] = lv_j
            matrix.append(row)

    return matrix


# ---------------- criar experimento ----------------

@router.post("/", response_model=Experiment)
def create_experiment(payload: ExperimentCreate):
    req = payload.doe_request

    design_type = req.design_type
    k = int(req.factors)
    levels = req.levels or []
    p = req.fractionality
    center_points = int(req.center_points or 0)
    replicates = int(req.replicates or 1)

    try:
        if design_type == "fatorial_2k":
            base_matrix = generate_2k_matrix(k)
            base_matrix = apply_replicates(base_matrix, replicates)
            matrix = append_center_points(base_matrix, k, center_points)
            design_notation = f"2^{k}"

        elif design_type == "fatorial_3k":
            base_matrix = generate_3k_matrix(k)
            base_matrix = apply_replicates(base_matrix, replicates)
            matrix = append_center_points(base_matrix, k, center_points)
            design_notation = f"3^{k}"

        elif design_type == "fatorial_fracionado":
            if p is None:
                raise ValueError("Informe o nível de fracionamento (p).")
            base_matrix = generate_fractional_2k_matrix(k, int(p))
            base_matrix = apply_replicates(base_matrix, replicates)
            matrix = append_center_points(base_matrix, k, center_points)
            design_notation = f"2^({k}-{int(p)})"

        elif design_type == "composto_central":
            base_matrix = generate_ccd_base_matrix(k)
            base_matrix = apply_replicates(base_matrix, replicates)
            matrix = append_center_points(base_matrix, k, center_points)
            design_notation = f"CCD ({k} fatores)"

        elif design_type == "box_behnken":
            base_matrix = generate_box_behnken_base_matrix(k)
            base_matrix = apply_replicates(base_matrix, replicates)
            matrix = append_center_points(base_matrix, k, center_points)
            design_notation = f"Box-Behnken ({k} fatores)"

        else:
            raise ValueError("Tipo de planejamento ainda não implementado.")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    matrix_real = matrix_to_real(matrix, levels) if levels else None
    factor_names = [lvl.name for lvl in levels] if levels else None

    doe_result = DoeResponse(
        design_type=design_type,
        factors=k,
        rows=len(matrix),
        matrix=matrix,
        factor_names=factor_names,
        matrix_real=matrix_real,
        fractionality=p,
        design_notation=design_notation,
    )

    try:
        return save_new_experiment(payload, doe_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar experimento: {str(e)}")


# ---------------- listar experimentos ----------------

@router.get("/", response_model=list[ExperimentSummary])
def list_experiments():
    try:
        return storage_list_experiments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar experimentos: {str(e)}")


# ---------------- obter experimento ----------------

@router.get("/{exp_id}", response_model=Experiment)
def get_experiment(exp_id: str):
    try:
        return load_experiment(exp_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar experimento: {str(e)}")


# ---------------- salvar respostas ----------------

@router.put("/{exp_id}/responses", response_model=Experiment)
def save_responses(exp_id: str, payload: ExperimentResponsesUpdate):
    try:
        return update_experiment_responses(exp_id, payload.responses)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar respostas: {str(e)}")


# ---------------- análise ----------------

@router.get("/{exp_id}/analysis")
def get_analysis(exp_id: str):
    try:
        exp = load_experiment(exp_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar experimento: {str(e)}")

    responses = exp.responses
    if not responses:
        raise HTTPException(status_code=400, detail="Respostas ainda não preenchidas")

    try:
        matrix = exp.doe_result.matrix
        return regression_analysis(matrix, responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


# ---------------- Pareto ----------------

@router.get("/{exp_id}/pareto.png")
def get_pareto(exp_id: str):
    try:
        exp = load_experiment(exp_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar experimento: {str(e)}")

    responses = exp.responses
    if not responses:
        raise HTTPException(status_code=400, detail="Respostas não preenchidas")

    try:
        analysis = regression_analysis(exp.doe_result.matrix, responses)
        plot_path = PLOTS_DIR / f"{exp_id}_pareto.png"
        generate_pareto(analysis["terms"], str(plot_path))
        return FileResponse(str(plot_path), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar gráfico de Pareto: {str(e)}")


# ---------------- Superfície + Contorno ----------------

@router.get("/{exp_id}/surface.png")
def get_surface_plot(exp_id: str):
    try:
        exp = load_experiment(exp_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar experimento: {str(e)}")

    responses = exp.responses
    if not responses:
        raise HTTPException(status_code=400, detail="Respostas não preenchidas")

    matrix = exp.doe_result.matrix
    if not matrix or len(matrix[0]) != 2:
        raise HTTPException(
            status_code=400,
            detail="O gráfico de superfície está disponível apenas para experimentos com 2 fatores.",
        )

    try:
        analysis = regression_analysis(matrix, responses)
        plot_path = PLOTS_DIR / f"{exp_id}_surface.png"
        generate_surface_plot(exp.model_dump(), analysis, str(plot_path))
        return FileResponse(str(plot_path), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar gráfico de superfície: {str(e)}")