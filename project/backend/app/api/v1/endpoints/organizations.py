"""
Organizations endpoints — read-only directory of healthcare organisations
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationListResponse, OrganizationResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_response(org: Organization) -> OrganizationResponse:
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        address=org.address,
        city=org.city,
        state=org.state,
        zip=org.zip,
        phone=org.phone,
        revenue=float(org.revenue) if org.revenue is not None else None,
        utilization=org.utilization,
        lat=org.lat,
        lon=org.lon,
        created_at=org.created_at,
    )


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a paginated list of all organisations (any authenticated user).

    Results are ordered alphabetically by name.
    """
    base_query = db.query(Organization).order_by(Organization.name.asc())
    total = base_query.count()
    rows = base_query.offset((page - 1) * page_size).limit(page_size).all()
    return OrganizationListResponse(
        organizations=[_build_response(o) for o in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single organisation by ID (any authenticated user).
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organisation {org_id} not found",
        )
    return _build_response(org)
