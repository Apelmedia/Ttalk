"""채팅 목록과 메시지.

대화방 참가자만 조회/전송할 수 있고, 양방향 차단 시 메시지 전송을 막는다.
sender는 인증된 프로필로 결정한다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_profile
from app.models.entities import Conversation, Match, Message, Profile
from app.schemas.api import ChatSummary, MessageRequest, MessageView
from app.services.social import conversation_partner_id, is_blocked_between

router = APIRouter(prefix="/chats", tags=["chats"])


def _load_conversation_for_member(
    db: Session, conversation_id: str, me_id: str
) -> tuple[Conversation, Match, str]:
    """대화방·매치를 로드하고 내가 참가자인지 검증한다. 상대 ID를 함께 반환."""
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="대화방을 찾을 수 없습니다.")
    match = db.query(Match).filter(Match.id == conversation.match_id).first()
    partner_id = conversation_partner_id(match, me_id) if match else None
    if partner_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 대화방의 참가자가 아닙니다.",
        )
    return conversation, match, partner_id


@router.get("", response_model=list[ChatSummary])
def list_chats(
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .filter(
            Match.status == "active",
            or_(Match.profile_a_id == me.id, Match.profile_b_id == me.id),
        )
        .all()
    )
    match_by_id = {m.id: m for m in matches}
    if not match_by_id:
        return []

    conversations = (
        db.query(Conversation)
        .filter(Conversation.match_id.in_(match_by_id.keys()))
        .all()
    )

    summaries: list[ChatSummary] = []
    for conversation in conversations:
        match = match_by_id[conversation.match_id]
        partner_id = conversation_partner_id(match, me.id)
        partner = db.query(Profile).filter(Profile.id == partner_id).first()
        last = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        summaries.append(
            ChatSummary(
                conversation_id=conversation.id,
                partner_profile_id=partner_id,
                partner_nickname=partner.nickname if partner else "(알 수 없음)",
                last_message=last.body if last else None,
                updated_at=last.created_at if last else conversation.created_at,
            )
        )
    # updated_at은 마지막 메시지 시각 또는 대화방 생성 시각으로 항상 채워진다.
    summaries.sort(key=lambda s: s.updated_at, reverse=True)
    return summaries


@router.get("/{conversation_id}/messages", response_model=list[MessageView])
def list_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    _load_conversation_for_member(db, conversation_id, me.id)
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        MessageView(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_profile_id=m.sender_profile_id,
            body=m.body,
            created_at=m.created_at,
        )
        for m in rows
    ]


@router.post("/{conversation_id}/messages", response_model=MessageView)
def create_message(
    conversation_id: str,
    request: MessageRequest,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    _, _, partner_id = _load_conversation_for_member(db, conversation_id, me.id)

    if is_blocked_between(db, me.id, partner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="차단 관계에서는 메시지를 보낼 수 없습니다.",
        )

    message = Message(
        conversation_id=conversation_id,
        sender_profile_id=me.id,
        body=request.body,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return MessageView(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_profile_id=message.sender_profile_id,
        body=message.body,
        created_at=message.created_at,
    )
