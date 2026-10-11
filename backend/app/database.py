from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLite needs check_same_thread=False for multithreaded FastAPI workers
engine_kwargs = {"echo": False}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production PostgreSQL connection pool configuration
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Columns added to existing tables after they were first created.
# Base.metadata.create_all() only creates missing tables, it never alters an
# existing one, so without this an upgraded model would break every query
# against that table on a database created by an earlier version.
_ADDED_COLUMNS = {
    "documents": {
        "normalized_text": "TEXT",
        "competency_id": "INTEGER",
    },
    "users": {
        # Phase 7A - added to pre-existing users tables. ALTER TABLE ADD COLUMN
        # cannot add a NOT NULL column to a non-empty table, hence VARCHAR(200)
        # with no NOT NULL (the model keeps it nullable).
        "hashed_password": "VARCHAR(200)",
        # Phase 8 - learner onboarding profile columns (all nullable for the
        # same reason; profile_completed defaults to 0 = not onboarded).
        "designation": "VARCHAR(200)",
        "department": "VARCHAR(200)",
        "assignment": "TEXT",
        "education": "TEXT",
        "work_experience": "TEXT",
        "previous_training": "TEXT",
        "profile_completed": "BOOLEAN DEFAULT FALSE",
        # Phase 10 - learning mode (ROLE or GOAL) and course_id
        "learning_mode": "VARCHAR(20) DEFAULT 'ROLE'",
        "course_id": "INTEGER",
    },
    "roles": {
        # Phase 9 - multi-sector expansion
        "sector_id": "INTEGER",
    },
    "courses": {
        # Phase 11 - estimated hours
        "estimated_hours": "INTEGER DEFAULT 20",
    },
    "diagnostic_questions": {
        # Phase 11 - MCQ vs SCENARIO questions & course scoping
        "question_type": "VARCHAR(20) DEFAULT 'MCQ'",
        "course_id": "INTEGER",
    },
}


def ensure_schema():
    """Add any missing columns to already-created tables (idempotent)."""
    inspector = inspect(engine)
    for table_name, columns in _ADDED_COLUMNS.items():
        if not inspector.has_table(table_name):
            continue
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, column_type in columns.items():
            if column_name in existing:
                continue
            with engine.begin() as connection:
                connection.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                ))


def get_db():
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
