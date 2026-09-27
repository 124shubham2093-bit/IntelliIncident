import os
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
    BACKEND_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    SQLITE_DB_PATH: str = os.path.join(BACKEND_DIR, "data", "intelli_incident.db")
    MODELS_DIR: str = os.path.join(BACKEND_DIR, "models")
    DATA_DIR: str = os.path.join(BACKEND_DIR, "data")

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
