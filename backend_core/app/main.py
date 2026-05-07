from fastapi import FastAPI
from .api import routes_health, routes_doe, routes_experiments


def create_app() -> FastAPI:
    app = FastAPI(
        title="LabPlanner Backend Core",
        version="0.2.0",
    )

    app.include_router(routes_health.router, prefix="/health", tags=["health"])
    app.include_router(routes_doe.router, prefix="/doe", tags=["doe"])
    app.include_router(routes_experiments.router, prefix="/experiments", tags=["experiments"])

    return app


app = create_app()