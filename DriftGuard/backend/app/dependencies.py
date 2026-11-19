"""Shared service singletons for FastAPI dependency injection."""

from backend.app.config import settings
from backend.app.services.monitoring_service import MonitoringService
from backend.app.services.pipeline_service import PipelineService
from backend.app.services.registry_service import RegistryService

registry_service = RegistryService(settings.artifacts_models_dir)
monitoring_service = MonitoringService(
    settings.artifacts_monitoring_dir,
    settings.data_processed_dir,
)
pipeline_service = PipelineService(registry_service, monitoring_service)
