"""Shared service singletons and project-scoped service resolver."""

from backend.app.services.pipeline_service import PipelineService
from backend.app.services.project_service import ProjectService

project_service = ProjectService()


def get_active_context():
    """Return (processed_dir, models_dir, registry_service, monitoring_service, pipeline_service)."""
    processed_dir, models_dir, registry, monitoring = project_service.get_services()
    pipeline = PipelineService(registry, monitoring, processed_dir=processed_dir, models_dir=models_dir)
    return processed_dir, models_dir, registry, monitoring, pipeline
