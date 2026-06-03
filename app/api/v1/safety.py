from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.api import BlockRequest, ReportRequest
from app.services.demo_catalog import receipt

router = APIRouter(prefix="/safety", tags=["safety"])


@router.post("/blocks")
def create_block(request: BlockRequest):
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=503, detail="운영 저장소 연결이 필요합니다.")
    return receipt(
        "block",
        blocker_profile_id=request.blocker_profile_id,
        blocked_profile_id=request.blocked_profile_id,
    )


@router.post("/reports")
def create_report(request: ReportRequest):
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=503, detail="운영 저장소 연결이 필요합니다.")
    return receipt(
        "report",
        queue_status="queued_for_review",
        category=request.category,
        reporter_profile_id=request.reporter_profile_id,
        target_profile_id=request.target_profile_id,
    )

