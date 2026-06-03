from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.api import PrivatePhotoGrantRequest
from app.services.demo_catalog import receipt

router = APIRouter(prefix="/private-photos", tags=["private-photos"])


@router.post("/grants")
def create_grant(request: PrivatePhotoGrantRequest):
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=503, detail="운영 저장소 연결이 필요합니다.")
    return receipt(
        "private_photo_grant",
        owner_profile_id=request.owner_profile_id,
        viewer_profile_id=request.viewer_profile_id,
        photo_id=request.photo_id,
        access="approved",
    )


@router.delete("/grants/{grant_id}")
def revoke_grant(grant_id: str):
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=503, detail="운영 저장소 연결이 필요합니다.")
    return receipt("private_photo_grant_revoked", grant_id=grant_id, access="revoked")

