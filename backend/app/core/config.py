import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "IntelliIncident"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
    ]

    # backend/app/core/config.py -> backend/app/core -> backend/app -> backend
    BACKEND_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    SQLITE_DB_PATH: str = os.path.join(
        BACKEND_DIR, "data", "intelli_incident.db"
    )
    MODELS_DIR: str = os.path.join(BACKEND_DIR, "models")
    DATA_DIR: str = os.path.join(BACKEND_DIR, "data")

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO_OWNER: str = "124shubham2093-bit"
    GITHUB_REPO_NAME: str = "IntelliIncident"
    GITHUB_DEFAULT_BRANCH: str = "main"
    GITHUB_API_URL: str = "https://api.github.com"

    # Sentry REST API Integration — evidence reading
    SENTRY_AUTH_TOKEN: Optional[str] = None
    SENTRY_ORG_SLUG: Optional[str] = None
    SENTRY_PROJECT_SLUG: Optional[str] = None
    SENTRY_BASE_URL: str = "https://sentry.io"

    # Sentry SDK — runtime error reporting
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    # Prometheus Integration — metrics telemetry and baseline deviation
    PROMETHEUS_URL: str = "http://localhost:9090"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=(".env", "backend/.env"),
        extra="ignore",
    )


settings = Settings()