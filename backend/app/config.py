import os
import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "statlearn_ai.db").replace("\\", "/")
DEV_DEFAULT_JWT_SECRET = "upskill-dev-secret-change-in-production"

class Settings(BaseSettings):
    PROJECT_NAME: str = "UPSKILL AI"
    API_V1_STR: str = "/api/v1"
    
    # Environment mode: "development" | "production" | "testing"
    ENVIRONMENT: str = "development"

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return "development"
    
    # Seeding on startup: Optional[bool]
    # - None (unset): seed reference data only if the database is empty (sectors count == 0)
    # - True: explicitly force seeding on every startup
    # - False: explicitly disable seeding on startup
    SEED_ON_STARTUP: Union[bool, None] = None
    
    # CORS origins: can be passed as JSON array or comma-separated string
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            # Comma-separated fallback
            return [part.strip() for part in v.split(",") if part.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    # Database URL
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            # Render / Heroku / Fly.io often provide "postgres://" or "postgresql://"
            # Normalize to modern psycopg driver "postgresql+psycopg://" if not specified
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            if v.startswith("postgresql://") and "+psycopg" not in v and "+asyncpg" not in v:
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v
    
    # OpenRouter AI settings
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # JWT authentication settings (Phase 7A & Phase 3)
    JWT_SECRET_KEY: str = DEV_DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    def validate_production_security(self):
        """
        Validate security settings.
        Refuses to run in production if JWT_SECRET_KEY is unset or equals the dev default.
        """
        if self.ENVIRONMENT == "production":
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == DEV_DEFAULT_JWT_SECRET:
                raise RuntimeError(
                    "SECURITY ERROR: Application is set to ENVIRONMENT=production but JWT_SECRET_KEY "
                    "is either unset or still equals the insecure development default. "
                    "Generate a cryptographically secure key and set JWT_SECRET_KEY in your environment."
                )

    class Config:
        case_sensitive = True
        env_file = os.path.join(BASE_DIR, ".env")
        extra = "ignore"

settings = Settings()

