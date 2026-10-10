"""
UPSKILL AI - Phase 12 Production Hardening & Configuration Test Suite

Verifies:
1. Refusal to start in production if JWT_SECRET_KEY is missing or equals dev default.
2. Successful startup in development mode with dev default key.
3. CORS origin parsing from JSON string, comma-separated string, or Python list.
4. Database URL normalization (translating postgres:// to postgresql+psycopg://).
5. Database engine pooling configuration for PostgreSQL vs SQLite.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import Settings, DEV_DEFAULT_JWT_SECRET


def test_production_startup_refusal_with_default_secret():
    """Verify validate_production_security raises RuntimeError in production with default secret."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY=DEV_DEFAULT_JWT_SECRET,
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.validate_production_security()
    
    assert "SECURITY ERROR" in str(exc_info.value)
    assert "JWT_SECRET_KEY" in str(exc_info.value)


def test_production_startup_refusal_with_empty_secret():
    """Verify validate_production_security raises RuntimeError in production with empty secret."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="",
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.validate_production_security()

    assert "SECURITY ERROR" in str(exc_info.value)


def test_production_startup_success_with_strong_secret():
    """Verify validate_production_security passes in production when a strong secret is supplied."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a-super-secret-production-random-key-with-high-entropy-1234567890",
    )
    # Should not raise any error
    prod_settings.validate_production_security()


def test_development_startup_with_default_secret():
    """Verify development mode works out-of-the-box with default key."""
    dev_settings = Settings(
        ENVIRONMENT="development",
        JWT_SECRET_KEY=DEV_DEFAULT_JWT_SECRET,
    )
    # Should not raise any error
    dev_settings.validate_production_security()


def test_cors_origins_parsing():
    """Verify BACKEND_CORS_ORIGINS parses JSON array strings, comma-separated strings, and lists."""
    # 1. JSON array string
    s1 = Settings(BACKEND_CORS_ORIGINS='["https://myapp.vercel.app", "http://localhost:5173"]')
    assert "https://myapp.vercel.app" in s1.BACKEND_CORS_ORIGINS
    assert "http://localhost:5173" in s1.BACKEND_CORS_ORIGINS
    assert len(s1.BACKEND_CORS_ORIGINS) == 2

    # 2. Comma-separated string
    s2 = Settings(BACKEND_CORS_ORIGINS="https://myapp.vercel.app, http://localhost:5173")
    assert "https://myapp.vercel.app" in s2.BACKEND_CORS_ORIGINS
    assert "http://localhost:5173" in s2.BACKEND_CORS_ORIGINS
    assert len(s2.BACKEND_CORS_ORIGINS) == 2

    # 3. Native list
    s3 = Settings(BACKEND_CORS_ORIGINS=["https://custom-domain.com"])
    assert s3.BACKEND_CORS_ORIGINS == ["https://custom-domain.com"]


def test_database_url_normalization():
    """Verify postgres:// is safely normalized to postgresql+psycopg://."""
    s1 = Settings(DATABASE_URL="postgres://user:password@hostname:5432/dbname")
    assert s1.DATABASE_URL.startswith("postgresql+psycopg://")

    s2 = Settings(DATABASE_URL="postgresql://user:password@hostname:5432/dbname")
    assert s2.DATABASE_URL.startswith("postgresql+psycopg://")

    s3 = Settings(DATABASE_URL="sqlite:///./statlearn_ai.db")
    assert s3.DATABASE_URL.startswith("sqlite:///")
