from fastapi import APIRouter

from app.api.v1.accounts import router as accounts_router
from app.api.v1.chats import router as chats_router
from app.api.v1.matches import router as matches_router
from app.api.v1.people import router as people_router
from app.api.v1.private_photos import router as private_photos_router
from app.api.v1.public import router as public_router
from app.api.v1.safety import router as safety_router

router = APIRouter()
router.include_router(public_router)
router.include_router(accounts_router)
router.include_router(people_router)
router.include_router(matches_router)
router.include_router(chats_router)
router.include_router(safety_router)
router.include_router(private_photos_router)

