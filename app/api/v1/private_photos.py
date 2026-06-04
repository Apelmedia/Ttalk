"""공개 요청 사진의 등록과 열람 권한 — 슬라이스 5~6.

owner는 요청 본문이 아니라 인증된 프로필로 결정한다. 사진 바이너리 업로드,
암호화 저장소, 만료 URL은 아직 보류하며 여기서는 메타데이터(object_key)와
열람 권한(grant) 레코드만 다룬다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_profile
from app.models.entities import PrivatePhoto, PrivatePhotoGrant, Profile, now_utc
from app.schemas.api import (
    PrivatePhotoCreateRequest,
    PrivatePhotoGrantRequest,
    PrivatePhotoGrantView,
    PrivatePhotoView,
)

router = APIRouter(prefix="/private-photos", tags=["private-photos"])


def _grant_view(grant: PrivatePhotoGrant) -> PrivatePhotoGrantView:
    return PrivatePhotoGrantView(
        id=grant.id,
        photo_id=grant.photo_id,
        owner_profile_id=grant.owner_profile_id,
        viewer_profile_id=grant.viewer_profile_id,
        revoked_at=grant.revoked_at,
        created_at=grant.created_at,
    )


@router.post("", response_model=PrivatePhotoView)
def register_photo(
    request: PrivatePhotoCreateRequest,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    """공개 요청 사진의 메타데이터를 등록한다(소유자=인증 프로필)."""
    photo = PrivatePhoto(owner_profile_id=me.id, object_key=request.object_key)
    db.add(photo)
    try:
        db.commit()
    except IntegrityError:  # object_key unique 충돌
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 사진 키입니다.",
        )
    db.refresh(photo)
    return PrivatePhotoView(
        id=photo.id,
        owner_profile_id=photo.owner_profile_id,
        object_key=photo.object_key,
        status=photo.status,
        created_at=photo.created_at,
    )


@router.post("/grants", response_model=PrivatePhotoGrantView)
def create_grant(
    request: PrivatePhotoGrantRequest,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    """사진 소유자가 특정 상대에게 열람 권한을 부여한다."""
    if request.viewer_profile_id == me.id:
        raise HTTPException(status_code=400, detail="자기 자신에게는 권한을 줄 수 없습니다.")

    photo = db.query(PrivatePhoto).filter(PrivatePhoto.id == request.photo_id).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다.")
    if photo.owner_profile_id != me.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인 사진에만 권한을 부여할 수 있습니다.",
        )

    viewer = db.query(Profile).filter(Profile.id == request.viewer_profile_id).first()
    if viewer is None:
        raise HTTPException(status_code=404, detail="대상 프로필을 찾을 수 없습니다.")

    # uq_photo_viewer 때문에 (photo, viewer)는 한 행만 존재한다. 이미 있으면
    # 철회 여부를 되살려 멱등 upsert로 처리한다.
    grant = (
        db.query(PrivatePhotoGrant)
        .filter(
            PrivatePhotoGrant.photo_id == photo.id,
            PrivatePhotoGrant.viewer_profile_id == viewer.id,
        )
        .first()
    )
    if grant is None:
        grant = PrivatePhotoGrant(
            photo_id=photo.id,
            owner_profile_id=me.id,
            viewer_profile_id=viewer.id,
        )
        db.add(grant)
        try:
            db.commit()
        except IntegrityError:  # 동시 요청으로 uq_photo_viewer 위반
            db.rollback()
            grant = (
                db.query(PrivatePhotoGrant)
                .filter(
                    PrivatePhotoGrant.photo_id == photo.id,
                    PrivatePhotoGrant.viewer_profile_id == viewer.id,
                )
                .first()
            )
            grant.revoked_at = None
            db.commit()
        else:
            db.refresh(grant)
    elif grant.revoked_at is not None:
        grant.revoked_at = None
        db.commit()

    return _grant_view(grant)


@router.delete("/grants/{grant_id}", response_model=PrivatePhotoGrantView)
def revoke_grant(
    grant_id: str,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    """사진 소유자가 부여한 열람 권한을 철회한다."""
    grant = (
        db.query(PrivatePhotoGrant).filter(PrivatePhotoGrant.id == grant_id).first()
    )
    if grant is None:
        raise HTTPException(status_code=404, detail="권한을 찾을 수 없습니다.")
    if grant.owner_profile_id != me.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 부여한 권한만 철회할 수 있습니다.",
        )

    if grant.revoked_at is None:
        grant.revoked_at = now_utc()
        db.commit()
        db.refresh(grant)

    return _grant_view(grant)
