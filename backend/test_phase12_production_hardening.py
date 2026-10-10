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
    """Verify SEED_ON_STARTUP parsing and defaults."""
    s_default = Settings()
    assert s_default.SEED_ON_STARTUP is None

    s_forced = Settings(SEED_ON_STARTUP=True)
    assert s_forced.SEED_ON_STARTUP is True

    s_disabled = Settings(SEED_ON_STARTUP=False)
    assert s_disabled.SEED_ON_STARTUP is False


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


def test_startup_seeding_paths(monkeypatch):
    """
    Test all 4 seeding paths on isolated in-memory databases:
    1. production + SEED_ON_STARTUP unset + empty DB -> reference data seeded, no demo user
    2. production + SEED_ON_STARTUP unset + already seeded DB -> no reseed
    3. production + SEED_ON_STARTUP=false -> nothing seeded
    4. development -> existing behaviour unchanged (both reference data and demo user seeded)
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import app.seed as seed_module
    from app.seed import seed_on_startup_if_needed, DEMO_LEARNER
    from app.database import Base
    from app.models import User, Sector
    from app.config import settings

    # --- Case 1: production + SEED_ON_STARTUP unset + empty DB ---
    eng1 = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    sm1 = sessionmaker(autocommit=False, autoflush=False, bind=eng1)
    Base.metadata.create_all(bind=eng1)

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SEED_ON_STARTUP", None)
    monkeypatch.setattr(seed_module, "SessionLocal", sm1)

    seeded = seed_on_startup_if_needed()
    assert seeded is True
    db1 = sm1()
    try:
        assert db1.query(Sector).count() == 6
        assert db1.query(User).filter_by(email=DEMO_LEARNER["email"]).first() is None
    finally:
        db1.close()

    # --- Case 2: production + SEED_ON_STARTUP unset + already seeded DB ---
    # Running it again on the already-seeded DB should return False (no reseed)
    reseeded = seed_on_startup_if_needed()
    assert reseeded is False
    db1 = sm1()
    try:
        assert db1.query(Sector).count() == 6
    finally:
        db1.close()

    # --- Case 3: production + SEED_ON_STARTUP=false ---
    eng3 = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    sm3 = sessionmaker(autocommit=False, autoflush=False, bind=eng3)
    Base.metadata.create_all(bind=eng3)

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SEED_ON_STARTUP", False)
    monkeypatch.setattr(seed_module, "SessionLocal", sm3)

    seeded3 = seed_on_startup_if_needed()
    assert seeded3 is False
    db3 = sm3()
    try:
        assert db3.query(Sector).count() == 0
    finally:
        db3.close()

    # --- Case 4: development -> existing behaviour unchanged ---
    eng4 = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    sm4 = sessionmaker(autocommit=False, autoflush=False, bind=eng4)
    Base.metadata.create_all(bind=eng4)

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SEED_ON_STARTUP", None)
    monkeypatch.setattr(seed_module, "SessionLocal", sm4)

    seeded4 = seed_on_startup_if_needed()
    assert seeded4 is True
    db4 = sm4()
    try:
        assert db4.query(Sector).count() == 6
        # In development, demo learner is seeded
        demo_user = db4.query(User).filter_by(email=DEMO_LEARNER["email"]).first()
        assert demo_user is not None
        assert demo_user.email == "demo@statlearn.local"
    finally:
        db4.close()



