from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, model_validator


class FactorLevel(BaseModel):
    name: str
    minimum: float
    maximum: float


class DoeRequest(BaseModel):
    design_type: Literal[
        "fatorial_2k",
        "fatorial_3k",
        "fatorial_fracionado",
        "composto_central",
        "box_behnken",
    ]
    factors: int = Field(..., ge=2, description="Número de fatores (k)")
    center_points: Optional[int] = Field(default=0, ge=0)
    fractionality: Optional[int] = Field(
        default=None,
        ge=1,
        description="Nível de fracionamento p no planejamento 2^(k-p)",
    )
    replicates: int = Field(default=1, ge=1, description="Número de replicatas por ensaio")
    levels: Optional[List[FactorLevel]] = None

    @model_validator(mode="after")
    def validate_design_rules(self):
        if self.design_type == "fatorial_fracionado":
            if self.fractionality is None:
                raise ValueError(
                    "Para planejamento fatorial fracionado, informe fractionality (p)."
                )
            if self.fractionality >= self.factors:
                raise ValueError("No planejamento fracionado, p deve ser menor que k.")
            if self.factors < 3:
                raise ValueError("Planejamento fracionado requer pelo menos 3 fatores.")

        if self.design_type == "box_behnken" and self.factors < 3:
            raise ValueError("Box-Behnken requer pelo menos 3 fatores.")

        if self.levels is not None and len(self.levels) != self.factors:
            raise ValueError(
                "A quantidade de fatores em 'levels' deve ser igual ao número de fatores."
            )

        for idx, lvl in enumerate(self.levels or [], start=1):
            if lvl.minimum >= lvl.maximum:
                raise ValueError(
                    f"O fator {idx} ('{lvl.name}') possui mínimo maior ou igual ao máximo."
                )

        return self


class DoeResponse(BaseModel):
    design_type: str
    factors: int
    rows: int
    matrix: List[List[float]]
    factor_names: Optional[List[str]] = None
    matrix_real: Optional[List[List[float]]] = None
    fractionality: Optional[int] = None
    design_notation: Optional[str] = None


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    doe_request: DoeRequest


class Experiment(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    doe_request: DoeRequest
    doe_result: DoeResponse
    responses: Optional[List[float]] = None


class ExperimentSummary(BaseModel):
    id: str
    name: str
    design_type: str
    rows: int
    factors: Optional[int] = None
    created_at: Optional[datetime] = None


class ExperimentResponsesUpdate(BaseModel):
    responses: List[float]


class RegressionCoefficient(BaseModel):
    term: str
    value: float
    std_error: Optional[float] = None
    t_value: Optional[float] = None
    p_value: Optional[float] = None


class AnovaRow(BaseModel):
    source: str
    ss: Optional[float] = None
    df: Optional[int] = None
    ms: Optional[float] = None
    f: Optional[float] = None
    p_value: Optional[float] = None


class Diagnostics(BaseModel):
    observed: List[float]
    predicted: List[float]
    residuals: List[float]


class RegressionResult(BaseModel):
    r_squared: Optional[float] = None
    r_squared_adj: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    equation: Optional[str] = None
    terms: List[RegressionCoefficient]
    anova: List[AnovaRow]
    diagnostics: Diagnostics
    is_saturated_model: bool
    message: Optional[str] = None