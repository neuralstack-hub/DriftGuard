"""DriftGuard FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import auth, datasets, drift, health, models, pipeline, predict, projects

app = FastAPI(
    title="DriftGuard API",
    description="Automated Machine Learning Model Monitoring and Self-Healing Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(predict.router)
app.include_router(drift.router)
app.include_router(models.router)
app.include_router(pipeline.router)


@app.get("/")
def root():
    return {
        "name": "DriftGuard",
        "docs": "/docs",
        "health": "/api/health",
    }
