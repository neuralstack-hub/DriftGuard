"""Project management endpoints for per-dataset isolation."""

from fastapi import APIRouter, HTTPException

from backend.app.dependencies import project_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
def list_projects():
    return project_service.list_projects()


@router.post("/{project_id}/activate")
def activate_project(project_id: str):
    try:
        return project_service.set_active_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
