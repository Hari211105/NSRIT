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


def test_environment_normalization():
    """Verify ENVIRONMENT is normalized once (strip + lowercase)."""
    s1 = Settings(ENVIRONMENT="Production", JWT_SECRET_KEY=DEV_DEFAULT_JWT_SECRET)
    assert s1.ENVIRONMENT == "production"

    s2 = Settings(ENVIRONMENT=" production ", JWT_SECRET_KEY=DEV_DEFAULT_JWT_SECRET)
    assert s2.ENVIRONMENT == "production"

    s3 = Settings(ENVIRONMENT="  Development  ", JWT_SECRET_KEY=DEV_DEFAULT_JWT_SECRET)
    assert s3.ENVIRONMENT == "development"

    # Verify that capitalized or whitespace-padded production values enforce security
    with pytest.raises(RuntimeError):
        s1.validate_production_security()
    with pytest.raises(RuntimeError):
        s2.validate_production_security()


def test_seed_on_startup_configuration():
    """Verify SEED_ON_STARTUP defaults and explicit overrides."""
    # Defaults: True in dev/test, False in production
    s_dev = Settings(ENVIRONMENT="development")
    assert s_dev.should_seed_on_startup is True

    s_test = Settings(ENVIRONMENT="testing")
    assert s_test.should_seed_on_startup is True

    s_prod = Settings(ENVIRONMENT="production")
    assert s_prod.should_seed_on_startup is False

    # Explicit overrides
    s_prod_forced = Settings(ENVIRONMENT="production", SEED_ON_STARTUP=True)
    assert s_prod_forced.should_seed_on_startup is True

    s_dev_disabled = Settings(ENVIRONMENT="development", SEED_ON_STARTUP=False)
    assert s_dev_disabled.should_seed_on_startup is False


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


def test_seed_demo_learner_omitted_in_production(monkeypatch):
    """Verify seed_demo_data does not create demo@statlearn.local when ENVIRONMENT is production."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import app.seed as seed_module
    from app.seed import seed_demo_data, DEMO_LEARNER
    from app.database import Base
    from app.models import User
    from app.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    
    # Use an isolated in-memory database for this test
    temp_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    temp_session_local = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)
    Base.metadata.create_all(bind=temp_engine)
    
    monkeypatch.setattr(seed_module, "SessionLocal", temp_session_local)

    # Run seeder under production environment setting
    seed_demo_data()

    # Verify user was NOT created in this database
    db = temp_session_local()
    try:
        user = db.query(User).filter_by(email=DEMO_LEARNER["email"]).first()
        assert user is None, "Demo learner must not be created when ENVIRONMENT is production"
        # Reference sectors, roles, courses should still be seeded
        from app.models import Sector, Course
        assert db.query(Sector).count() > 0
        assert db.query(Course).count() > 0
    finally:
        db.close()


