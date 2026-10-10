from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, ensure_schema
import app.models  # noqa: F401
from app.routes import roles, competencies, learner, gaps, catalog, recommendations, documents, diagnostic, auth, sectors, courses

# ---------------------------------------------------------------
# Security Validation: Refuse startup in production if secret is insecure
# ---------------------------------------------------------------
settings.validate_production_security()

# ---------------------------------------------------------------
# Create database tables and ensure schema
# In development/local, Base.metadata.create_all is executed.
# In production, Alembic handles migrations, while create_all remains safe and idempotent.
# ---------------------------------------------------------------
Base.metadata.create_all(bind=engine)
ensure_schema()

# ---------------------------------------------------------------
# Seed demo data on startup (idempotent, skips existing records)
# In production, seed only if DB is completely fresh
# ---------------------------------------------------------------
from app.seed import seed_demo_data
seed_demo_data()

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
