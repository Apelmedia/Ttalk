from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/bootstrap")
def get_bootstrap():
    return {
        "app_name": "Warm Haven",
        "demo_mode": settings.DEMO_MODE,
        "features": {
            "gps_nearby": False,
            "region_filter": True,
            "mutual_match_before_chat": True,
            "private_photo_grants": True,
            "report_and_block": True,
        },
        "safety_notice": "성매매 권유, 스토킹, 괴롭힘, 불법 촬영물 유포는 금지됩니다.",
    }

