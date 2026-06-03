"""좋아요·패스와 상호 좋아요 매치 성사.

actor는 인증된 프로필로 결정한다. 상호 좋아요이면 canonical 매치와 대화방을
생성하고 is_match=true를 반환한다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_profile
from app.models.entities import Like, Profile
from app.schemas.api import LikeRequest, LikeResult
from app.services.social import ensure_match_and_conversation, is_blocked_between

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/likes", response_model=LikeResult)
def create_like(
    request: LikeRequest,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    if request.target_profile_id == me.id:
        raise HTTPException(status_code=400, detail="자기 자신에게는 보낼 수 없습니다.")

    target = db.query(Profile).filter(Profile.id == request.target_profile_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="대상 프로필을 찾을 수 없습니다.")

    if is_blocked_between(db, me.id, target.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="차단 관계인 상대에게는 보낼 수 없습니다.",
        )

    # 좋아요/패스는 멱등 upsert — 재호출 시 결정만 갱신한다.
    like = (
        db.query(Like)
        .filter(Like.actor_profile_id == me.id, Like.target_profile_id == target.id)
        .first()
    )
    if like is None:
        like = Like(
            actor_profile_id=me.id,
            target_profile_id=target.id,
            decision=request.decision,
        )
        db.add(like)
    else:
        like.decision = request.decision
    db.commit()

    result = LikeResult(decision=request.decision, target_profile_id=target.id)

    if request.decision == "like":
        reverse = (
            db.query(Like)
            .filter(
                Like.actor_profile_id == target.id,
                Like.target_profile_id == me.id,
                Like.decision == "like",
            )
            .first()
        )
        if reverse is not None:
            match, conversation = ensure_match_and_conversation(db, me.id, target.id)
            result.is_match = True
            result.match_id = match.id
            result.conversation_id = conversation.id

    return result
