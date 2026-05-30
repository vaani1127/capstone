"""
Providers endpoints — read-only directory of healthcare providers
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.provider import Provider
from app.models.user import User
from app.schemas.provider import ProviderListResponse, ProviderResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_response(prov: Provider) -> ProviderResponse:
    return ProviderResponse(
        id=prov.id,
        user_id=prov.user_id,
        organization_id=prov.organization_id,
        organization_name=prov.organization.name if prov.organization else None,
        name=prov.name,
        gender=prov.gender,
        speciality=prov.speciality,
        address=prov.address,
        city=prov.city,
        state=prov.state,
        zip=prov.zip,
        lat=prov.lat,
        lon=prov.lon,
        encounter_count=prov.encounter_count,
        procedure_count=prov.procedure_count,
        created_at=prov.created_at,
    )


# NOTE: /by-speciality must be registered BEFORE /{provider_id} so FastAPI
# matches the literal path segment before the integer path parameter.
@router.get("/by-speciality", response_model=List[str])
async def list_specialities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the distinct non-null speciality values in sorted order (any authenticated user).

    Used to populate the speciality filter dropdown on the providers list screen.
    """
    rows = (
        db.query(Provider.speciality)
        .filter(Provider.speciality.isnot(None))
        .distinct()
        .order_by(Provider.speciality.asc())
        .all()
    )
    return [row[0] for row in rows]


@router.get("/", response_model=ProviderListResponse)
async def list_providers(
    speciality: Optional[str] = Query(None, description="Filter by speciality (exact match)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a paginated list of providers, optionally filtered by speciality (any authenticated user).

    Results are ordered alphabetically by provider name.
    """
    base_query = db.query(Provider).order_by(Provider.name.asc())
    if speciality:
        base_query = base_query.filter(Provider.speciality == speciality)
    total = base_query.count()
    rows = base_query.offset((page - 1) * page_size).limit(page_size).all()
    return ProviderListResponse(
        providers=[_build_response(p) for p in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single provider by ID (any authenticated user).
    """
    prov = db.query(Provider).filter(Provider.id == provider_id).first()
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found",
        )
    return _build_response(prov)
