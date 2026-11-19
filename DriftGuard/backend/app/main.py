"""DriftGuard FastAPI application entrypoint."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.routes import auth, datasets, drift, health, models, pipeline, predict, projects

app = FastAPI(
    title="DriftGuard API",
    description="Automated Machine Learning Model Monitoring and Self-Healing Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(projects.router, dependencies=[Depends(auth.require_user)])
app.include_router(datasets.router, dependencies=[Depends(auth.require_user)])
app.include_router(predict.router, dependencies=[Depends(auth.require_user)])
app.include_router(drift.router, dependencies=[Depends(auth.require_user)])
app.include_router(models.router, dependencies=[Depends(auth.require_user)])
app.include_router(pipeline.router, dependencies=[Depends(auth.require_user)])


@app.get("/")
def root():
    return {
        "name": "DriftGuard",
        "docs": "/docs",
        "health": "/api/health",
    }
