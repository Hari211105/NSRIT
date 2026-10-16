from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, ensure_schema
import app.models  # noqa: F401
from app.routes import roles, competencies, learner, gaps, catalog, recommendations, documents, diagnostic, auth, sectors, courses, trainer, admin, lessons

# ---------------------------------------------------------------
# Security Validation: Refuse startup in production if secret is insecure
# ---------------------------------------------------------------
settings.validate_production_security()

# ---------------------------------------------------------------
# Database Schema Initialization
# In production, migrations are strictly applied via Alembic before startup.
# In development/testing, create_all and ensure_schema run automatically.
# ---------------------------------------------------------------
if settings.ENVIRONMENT != "production":
    Base.metadata.create_all(bind=engine)
    ensure_schema()

# ---------------------------------------------------------------
# Seed reference and demo data on startup
# Behavior driven by seed_on_startup_if_needed():
# - SEED_ON_STARTUP unset: seeds reference data if database is empty (0 sectors); skips if already populated.
# - SEED_ON_STARTUP=true: forces seeding on every startup.
# - SEED_ON_STARTUP=false: skips seeding entirely.
# Demo user (demo@statlearn.local) is NEVER created when ENVIRONMENT=production.
# ---------------------------------------------------------------
from app.seed import seed_on_startup_if_needed
seed_on_startup_if_needed()

# ---------------------------------------------------------------
# Phase 13 - Promote initial administrator on startup if configured
# In production, sets account_type='ADMIN' for the user matching INITIAL_ADMIN_EMAIL.
# ---------------------------------------------------------------
def promote_initial_admin_if_configured():
    if settings.INITIAL_ADMIN_EMAIL and settings.INITIAL_ADMIN_EMAIL.strip():
        admin_email = settings.INITIAL_ADMIN_EMAIL.strip().lower()
        from app.database import SessionLocal
        from app.models import User
        db = SessionLocal()
        try:
            target_user = db.query(User).filter(User.email == admin_email).first()
            if target_user and target_user.account_type != "ADMIN":
                target_user.account_type = "ADMIN"
                db.commit()
                print(f"  Promoted initial admin user: {admin_email}")
        finally:
            db.close()

promote_initial_admin_if_configured()

# ---------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
)

# CORS configuration for local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------
# Routers
# ---------------------------------------------------------------
PREFIX = settings.API_V1_STR

app.include_router(roles.router,           prefix=PREFIX)
app.include_router(competencies.router,    prefix=PREFIX)
app.include_router(learner.router,         prefix=PREFIX)
app.include_router(gaps.router,            prefix=PREFIX)
app.include_router(catalog.router,         prefix=PREFIX)
app.include_router(recommendations.router, prefix=PREFIX)
app.include_router(documents.router,       prefix=PREFIX)
app.include_router(diagnostic.router,     prefix=PREFIX)
app.include_router(auth.router,           prefix=PREFIX)
app.include_router(sectors.router,        prefix=PREFIX)
app.include_router(courses.router,        prefix=PREFIX)
app.include_router(lessons.router,        prefix=PREFIX)
app.include_router(trainer.router,        prefix=PREFIX)
app.include_router(admin.router,          prefix=PREFIX)



# ---------------------------------------------------------------
# Core endpoints (kept from Phase 1)
# ---------------------------------------------------------------

@app.get(f"{PREFIX}/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return {
        "status": "ok",
        "application": settings.PROJECT_NAME,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Visit /docs for API documentation.",
        "health": f"{PREFIX}/health",
    }
