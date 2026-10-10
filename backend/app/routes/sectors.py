"""
UPSKILL AI - Sectors API (Phase 9 - Multi-Sector Expansion)

GET /api/v1/sectors             - List all sectors with active roles
GET /api/v1/sectors/{id}/roles  - List all roles in a given sector
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Sector, Role

router = APIRouter(prefix="/sectors", tags=["Sectors"])


class RoleBrief(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_demo: bool = False
    sector_id: Optional[int] = None

    class Config:
        from_attributes = True


class SectorOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    icon: str = "briefcase"
    display_order: int = 0
    role_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[SectorOut])
def list_sectors(db: Session = Depends(get_db)):
    """List all available industry/public sectors ordered by display_order."""
    sectors = db.query(Sector).order_by(Sector.display_order.asc(), Sector.id.asc()).all()
    results = []
    for s in sectors:
        role_count = db.query(Role).filter(Role.sector_id == s.id).count()
        results.append(
            SectorOut(
                id=s.id,
                code=s.code,
                name=s.name,
                description=s.description,
                icon=s.icon or "briefcase",
                display_order=s.display_order or 0,
                role_count=role_count,
            )
        )
    return results


@router.get("/{sector_id}/roles", response_model=List[RoleBrief])
def list_sector_roles(sector_id: int, db: Session = Depends(get_db)):
    """List all positions/roles belonging to the specified sector."""
    sector = db.query(Sector).filter(Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sector with ID {sector_id} not found."
        )
    roles = db.query(Role).filter(Role.sector_id == sector_id).order_by(Role.id.asc()).all()
    return [
        RoleBrief(
            id=r.id,
            name=r.name,
            description=r.description,
            is_demo=r.is_demo,
            sector_id=r.sector_id,
        )
        for r in roles
    ]
