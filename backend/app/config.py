import os
from typing import List
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "statlearn_ai.db").replace("\\", "/")

class Settings(BaseSettings):
    PROJECT_NAME: str = "UPSKILL AI"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    
    # OpenRouter API settings
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # JWT authentication settings (Phase 7A)
    # JWT_SECRET_KEY must be overridden via the environment / backend/.env in
    # any deployed or shared environment. The default below is for local
    # development only and must never be used in production.
    JWT_SECRET_KEY: str = "upskill-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        case_sensitive = True
        env_file = os.path.join(BASE_DIR, ".env")
        extra = "ignore"

settings = Settings()
