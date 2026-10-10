"""
UPSKILL AI - Competencies API (Phase 2)
GET /api/v1/competencies
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Competency

router = APIRouter(prefix="/competencies", tags=["Competencies"])


@router.get("")
def list_competencies(db: Session = Depends(get_db)):
    """Return all available competencies."""
    comps = db.query(Competency).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "is_demo": c.is_demo,
        }
        for c in comps
    ]
