"""Model version management, promotion, rejection, and rollback endpoints."""

from fastapi import APIRouter, HTTPException

from backend.app.dependencies import monitoring_service, pipeline_service, registry_service
from backend.app.schemas.models import RollbackRequest

router = APIRouter(prefix="/api/models", tags=["Model Management"])


@router.get("")
def list_models():
    reg = registry_service.get_registry()
    return reg


@router.post("/train-v1")
def train_initial_model():
    try:
        return pipeline_service.bootstrap_v1()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{version}/promote")
def promote_model(version: str):
    try:
        record = registry_service.promote_version(version, reason="Manually promoted via dashboard")
        monitoring_service.log_deployment(
            version=version,
            action="manual_promote",
            details=f"Manually promoted {version} to active production",
        )
        return {"status": "promoted", "model": record}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{version}/reject")
def reject_model(version: str):
    try:
        record = registry_service.reject_version(version, reason="Manually rejected via dashboard")
        monitoring_service.log_deployment(
            version=version,
            action="manual_reject",
            details=f"Manually rejected {version}",
        )
        return {"status": "rejected", "model": record}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rollback")
def rollback_model(req: RollbackRequest):
    try:
        event = registry_service.rollback(target_version=req.target_version, reason=req.reason)
        monitoring_service.log_deployment(
            version=event["to_version"],
            action="rollback",
            details=f"Rolled back from {event['from_version']} to {event['to_version']}: {req.reason}",
        )
        return {"status": "rolled_back", "event": event}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
