"""Pipeline execution and CI/CD monitoring endpoints."""

from fastapi import APIRouter, HTTPException

from backend.app.dependencies import monitoring_service, pipeline_service, registry_service
from backend.app.schemas.models import RetrainRequest

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline Monitoring"])


@router.post("/retrain")
def trigger_retrain(req: RetrainRequest):
    try:
        return pipeline_service.trigger_retraining(
            n_estimators=req.n_estimators,
            max_depth=req.max_depth,
            simulate_worse_candidate=req.simulate_worse_candidate,
            trigger_reason=req.trigger_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/history")
def get_pipeline_history():
    hist = monitoring_service.get_history()
    reg = registry_service.get_registry()
    return {
        "retraining_history": hist.get("retraining_history", []),
        "deployment_logs": hist.get("deployment_logs", []),
        "github_actions_runs": hist.get("github_actions_runs", []),
        "rollback_history": reg.get("rollback_history", []),
    }
