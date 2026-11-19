"""Application configuration loaded from .env and environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    drift_threshold: float = float(os.getenv("DRIFT_THRESHOLD", "0.30"))
    psi_threshold: float = float(os.getenv("PSI_THRESHOLD", "0.20"))
    ks_alpha: float = float(os.getenv("KS_ALPHA", "0.05"))

    admin_user: str = os.getenv("APP_ADMIN_USER", "admin")
    admin_password: str = os.getenv("APP_ADMIN_PASSWORD", "driftguard123")
    auth_required: bool = os.getenv("AUTH_REQUIRED", "true").strip().lower() in {"1", "true", "yes"}

    frontend_origins: str = os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )

    @property
    def allowed_frontend_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def authentication_enabled(self) -> bool:
        return self.auth_required

    data_raw_path: Path = PROJECT_ROOT / os.getenv(
        "DATA_RAW_PATH", "data/raw/PRSA_data_2010.1.1-2014.12.31.csv"
    )
    data_processed_dir: Path = PROJECT_ROOT / os.getenv("DATA_PROCESSED_DIR", "data/processed")
    artifacts_models_dir: Path = PROJECT_ROOT / os.getenv("ARTIFACTS_MODELS_DIR", "artifacts/models")
    artifacts_monitoring_dir: Path = PROJECT_ROOT / os.getenv(
        "ARTIFACTS_MONITORING_DIR", "artifacts/monitoring"
    )

    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_owner: str = os.getenv("GITHUB_OWNER", "")
    github_repo: str = os.getenv("GITHUB_REPO", "DriftGuard")
    github_workflow_event: str = os.getenv("GITHUB_WORKFLOW_EVENT", "drift-detected")


settings = Settings()
