"""Pytest configuration and session-wide test isolation for UPSKILL AI.

Ensures that:
1. Every test session runs against an isolated temporary SQLite database file
   created in a temporary directory.
2. The schema is created via Base.metadata.create_all and seeded cleanly.
3. No statlearn_ai.db or leftover database files are created in the workspace.
4. The temporary database file is cleanly removed at the end of the test session.
"""
import os
import sys
import tempfile
import pytest

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Configure temporary SQLite database URL before app modules are imported
_TEMP_DB_DIR = tempfile.mkdtemp(prefix="upskill_test_db_")
_TEMP_DB_PATH = os.path.join(_TEMP_DB_DIR, "test_session.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEMP_DB_PATH}"
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test-session-isolated-secret-key-1234567890"

from app.config import settings
from app.database import Base, engine, ensure_schema
from app.seed import seed_demo_data


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-wide fixture ensuring clean schema and seed in the temporary database."""
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    seed_demo_data()
    yield
    # Cleanup temporary database file and directory on session tear-down
    try:
        engine.dispose()
        if os.path.exists(_TEMP_DB_PATH):
            os.remove(_TEMP_DB_PATH)
        if os.path.exists(_TEMP_DB_DIR):
            os.rmdir(_TEMP_DB_DIR)
    except Exception:
        pass
