"""계정·프로필 엔드포인트.

로그인 계정 본인의 프로필만 생성/수정/조회한다. 요청 본문의 사용자 ID를
신뢰하지 않고 인증된 계정으로 대상을 결정한다.
"""

import json

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_account, require_adult_verified
from app.core.db import get_db
from app.models.entities import Account, Profile
from app.schemas.api import AccountMeView, ProfileUpsertRequest, ProfileView

router = APIRouter(prefix="/accounts", tags=["accounts"])


def profile_to_view(profile: Profile) -> ProfileView:
    return ProfileView(
        id=profile.id,
        nickname=profile.nickname,
        age=profile.age,
        region_code=profile.region_code,
        body_type=profile.body_type,
        identity_tags=json.loads(profile.identity_tags_json or "[]"),
        orientation_tags=json.loads(profile.orientation_tags_json or "[]"),
        bio=profile.bio,
        is_discoverable=profile.is_discoverable,
    )


@router.get("/me", response_model=AccountMeView)
def get_me(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.account_id == account.id).first()
    return AccountMeView(
        account_id=account.id,
        email=account.email,
        is_adult_verified=account.is_adult_verified,
        status=account.status,
        profile=profile_to_view(profile) if profile else None,
    )


@router.put("/me/profile", response_model=ProfileView)
def upsert_my_profile(
    payload: ProfileUpsertRequest,
    account: Account = Depends(require_adult_verified),
    db: Session = Depends(get_db),
):
    """로그인 계정의 프로필을 생성하거나 수정한다(계정당 1개)."""
    profile = db.query(Profile).filter(Profile.account_id == account.id).first()
    if profile is None:
        profile = Profile(account_id=account.id)
        db.add(profile)

    profile.nickname = payload.nickname
    profile.age = payload.age
    profile.region_code = payload.region_code
    profile.body_type = payload.body_type
    profile.identity_tags_json = json.dumps(payload.identity_tags, ensure_ascii=False)
    profile.orientation_tags_json = json.dumps(payload.orientation_tags, ensure_ascii=False)
    profile.bio = payload.bio
    profile.is_discoverable = payload.is_discoverable
    db.commit()
    db.refresh(profile)
    return profile_to_view(profile)


@router.post("/me/adult-verification", status_code=status.HTTP_200_OK)
def mark_adult_verified(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """[개발용 데모] 성인 확인을 통과 처리한다.

    운영에서는 본인확인 제공자 결과로만 갱신해야 하며 이 엔드포인트는 제거한다.
    """
    account.is_adult_verified = True
    db.commit()
    return {
        "account_id": account.id,
        "is_adult_verified": True,
        "note": "개발용 데모 — 실제 본인확인 제공자 연동 전까지만 사용",
        "demo_mode": settings.DEMO_MODE,
    }
