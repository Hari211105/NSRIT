"""
UPSKILL AI - Roles API (Phase 2)
GET /api/v1/roles
GET /api/v1/roles/{role_id}/competencies
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Role, RoleCompetency, get_level_label

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("")
def list_roles(db: Session = Depends(get_db)):
    """Return all available roles."""
    roles = db.query(Role).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_demo": r.is_demo,
        }
        for r in roles
    ]


@router.get("/{role_id}/competencies")
def get_role_competencies(role_id: int, db: Session = Depends(get_db)):
    """Return all competencies required by a given role, including required levels."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    mappings = db.query(RoleCompetency).filter(RoleCompetency.role_id == role_id).all()
    return {
        "role_id": role.id,
        "role_name": role.name,
        "required_competencies": [
            {
                "id": m.competency.id,
                "name": m.competency.name,
                "description": m.competency.description,
                "required_level": m.required_level,
                "required_level_label": get_level_label(m.required_level),
                "priority": m.priority,
            }
            for m in mappings
        ],
    }
