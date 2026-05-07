# doe_service/app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.doe import generate_design
from app.schemas import DoeRequest, DoeResponse

app = FastAPI(
    title="DOE Service",
    version="1.0.0",
    description="Serviço para geração de planejamentos experimentais do LabPlanner.",
)

# Ajuste os origins conforme seu ambiente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "doe_service",
        "status": "ok",
        "message": "Serviço de planejamento experimental ativo."
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/generate", response_model=DoeResponse)
def generate_doe(request: DoeRequest):
    try:
        result = generate_design(request)
        return result
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao gerar planejamento: {str(exc)}"
        ) from exc