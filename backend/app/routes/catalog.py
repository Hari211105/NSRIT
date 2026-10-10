"""
UPSKILL AI - Learning Catalog API (Phase 4)
GET /api/v1/catalog/resources

Returns available demo learning resources mapped to competencies.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LearningResource, get_level_label

router = APIRouter(prefix="/catalog/resources", tags=["Learning Catalog"])


@router.get("")
def get_catalog_resources(db: Session = Depends(get_db)):
    """
    Return all available learning resources in the catalog.
    Clearly marks demo catalog resources.
    """
    resources = db.query(LearningResource).filter(LearningResource.active == True).all()

    items = []
    for r in resources:
        items.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "source": r.source,
            "resource_type": r.resource_type,
            "competency_id": r.competency_id,
            "competency_name": r.competency.name if r.competency else None,
            "minimum_level": r.minimum_level,
            "minimum_level_label": get_level_label(r.minimum_level),
            "maximum_level": r.maximum_level,
            "maximum_level_label": get_level_label(r.maximum_level),
            "duration_hours": r.duration_hours,
            "url": r.url,
            "is_demo": r.is_demo,
            "active": r.active,
        })

    return {
        "total": len(items),
        "resources": items,
    }
