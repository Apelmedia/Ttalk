"""사회적 관계 공통 로직 — 차단 판정과 매치/대화방 생성.

people, matches, chats, safety 슬라이스가 공유한다. 모든 권한 판정은
요청 본문이 아니라 인증된 프로필 ID 기준으로 백엔드에서 결정한다.
"""

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Block, Conversation, Match


def conversation_partner_id(match: Match, me_id: str) -> str | None:
    """매치에서 내 상대 프로필 ID를 반환한다. 내가 참가자가 아니면 None."""
    if match.profile_a_id == me_id:
        return match.profile_b_id
    if match.profile_b_id == me_id:
        return match.profile_a_id
    return None


def blocked_profile_ids(db: Session, me_id: str) -> set[str]:
    """내가 차단했거나 나를 차단한 상대 프로필 ID 집합(양방향)."""
    rows = (
        db.query(Block.blocker_profile_id, Block.blocked_profile_id)
        .filter(
            or_(Block.blocker_profile_id == me_id, Block.blocked_profile_id == me_id)
        )
        .all()
    )
    result: set[str] = set()
    for blocker, blocked in rows:
        result.add(blocked if blocker == me_id else blocker)
    return result


def is_blocked_between(db: Session, a_id: str, b_id: str) -> bool:
    """두 프로필 사이에 어느 방향이든 차단이 있으면 True."""
    return (
        db.query(Block.id)
        .filter(
            or_(
                (Block.blocker_profile_id == a_id) & (Block.blocked_profile_id == b_id),
                (Block.blocker_profile_id == b_id) & (Block.blocked_profile_id == a_id),
            )
        )
        .first()
        is not None
    )


def canonical_pair(a_id: str, b_id: str) -> tuple[str, str]:
    """Match.ck_matches_canonical_pair(profile_a_id < profile_b_id)에 맞춰 정렬."""
    return (a_id, b_id) if a_id < b_id else (b_id, a_id)


def ensure_match_and_conversation(
    db: Session, a_id: str, b_id: str
) -> tuple[Match, Conversation]:
    """상호 좋아요 성사 시 매치와 대화방을 보장한다(멱등).

    양쪽이 거의 동시에 좋아요를 눌러 두 요청이 동시에 INSERT를 시도해도
    uq_match_pair 위반을 잡아 기존 행을 재조회한다.
    """
    low, high = canonical_pair(a_id, b_id)
    match = (
        db.query(Match)
        .filter(Match.profile_a_id == low, Match.profile_b_id == high)
        .first()
    )
    if match is None:
        match = Match(profile_a_id=low, profile_b_id=high)
        db.add(match)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            match = (
                db.query(Match)
                .filter(Match.profile_a_id == low, Match.profile_b_id == high)
                .first()
            )
        else:
            db.refresh(match)

    conversation = (
        db.query(Conversation).filter(Conversation.match_id == match.id).first()
    )
    if conversation is None:
        conversation = Conversation(match_id=match.id)
        db.add(conversation)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            conversation = (
                db.query(Conversation)
                .filter(Conversation.match_id == match.id)
                .first()
            )
        else:
            db.refresh(conversation)

    return match, conversation
