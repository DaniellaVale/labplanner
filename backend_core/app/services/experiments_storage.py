from pathlib import Path
from typing import List
from uuid import uuid4
from datetime import datetime
import json

from fastapi.encoders import jsonable_encoder

from ..models import (
    Experiment,
    ExperimentCreate,
    ExperimentSummary,
)


BASE_DIR = Path("/data/experiments")
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _experiment_file_path(exp_id: str) -> Path:
    return BASE_DIR / f"{exp_id}.json"


def save_new_experiment(payload: ExperimentCreate, doe_result) -> Experiment:
    """
    Cria um novo experimento com ID e timestamp,
    salva em disco como JSON e retorna o objeto.
    """
    exp_id = str(uuid4())
    created_at = datetime.utcnow()

    exp = Experiment(
        id=exp_id,
        name=payload.name,
        description=payload.description,
        created_at=created_at,
        doe_request=payload.doe_request,
        doe_result=doe_result,
        responses=None,
    )

    data = jsonable_encoder(exp)
    path = _experiment_file_path(exp_id)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return exp


def list_experiments() -> List[ExperimentSummary]:
    """
    Lê todos os arquivos de experimento e devolve
    uma lista resumida ordenada do mais recente para o mais antigo.
    """
    summaries: List[ExperimentSummary] = []

    for file in BASE_DIR.glob("*.json"):
        raw = json.loads(file.read_text(encoding="utf-8"))
        exp = Experiment(**raw)

        summaries.append(
            ExperimentSummary(
                id=exp.id,
                name=exp.name,
                design_type=exp.doe_result.design_type or exp.doe_request.design_type,
                factors=exp.doe_result.factors,
                rows=exp.doe_result.rows,
                created_at=exp.created_at,
            )
        )

    summaries.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
    return summaries


def load_experiment(exp_id: str) -> Experiment:
    """
    Lê um experimento específico pelo ID.
    """
    path = _experiment_file_path(exp_id)
    if not path.exists():
        raise FileNotFoundError(f"Experimento {exp_id} não encontrado.")

    raw = json.loads(path.read_text(encoding="utf-8"))
    return Experiment(**raw)


def update_experiment_responses(exp_id: str, responses: List[float]) -> Experiment:
    """
    Atualiza as respostas experimentais (Y) de um experimento.
    """
    exp = load_experiment(exp_id)

    n_runs = exp.doe_result.rows
    if len(responses) != n_runs:
        raise ValueError(
            f"Número de respostas ({len(responses)}) diferente do número de execuções ({n_runs})."
        )

    exp.responses = responses

    data = jsonable_encoder(exp)
    path = _experiment_file_path(exp_id)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return exp