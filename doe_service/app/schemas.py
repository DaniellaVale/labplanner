# doe_service/app/schemas.py

from __future__ import annotations

from typing import List, Literal, Optional

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
    center_points: Optional[int] = Field(default=None, ge=0)
    fractionality: Optional[int] = Field(
        default=None,
        ge=1,
        description="Nível de fracionamento p no planejamento 2^(k-p)",
    )
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