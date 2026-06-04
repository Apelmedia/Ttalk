"""차단과 신고 — 슬라이스 4.

blocker/reporter는 요청 본문이 아니라 인증된 프로필로 결정한다.
차단은 멱등(uq_block_pair), 신고는 같은 상대에게 여러 번 가능하므로 매번 INSERT.
관리자 신고 검토 화면(ModerationAction 와이어링)은 아직 보류한다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_profile
from app.models.entities import Block, Conversation, Match, Profile, Report
from app.schemas.api import BlockRequest, BlockView, ReportRequest, ReportView
from app.services.social import conversation_partner_id

router = APIRouter(prefix="/safety", tags=["safety"])


@router.post("/blocks", response_model=BlockView)
def create_block(
    request: BlockRequest,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    if request.blocked_profile_id == me.id:
        raise HTTPException(status_code=400, detail="자기 자신은 차단할 수 없습니다.")

    target = db.query(Profile).filter(Profile.id == request.blocked_profile_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="대상 프로필을 찾을 수 없습니다.")

    # 차단은 멱등 — 이미 차단했으면 기존 행을 반환한다.
    block = (
        db.query(Block)
        .filter(
            Block.blocker_profile_id == me.id,
            Block.blocked_profile_id == target.id,
        )
        .first()
    )
    if block is None:
        block = Block(blocker_profile_id=me.id, blocked_profile_id=target.id)
        db.add(block)
        try:
            db.commit()
        except IntegrityError:  # 동시 요청으로 uq_block_pair 위반
            db.rollback()
            block = (
                db.query(Block)
                .filter(
                    Block.blocker_profile_id == me.id,
                    Block.blocked_profile_id == target.id,
                )
                .first()
            )
        else:
            db.refresh(block)

    return BlockView(
        id=block.id,
        blocker_profile_id=block.blocker_profile_id,
        blocked_profile_id=block.blocked_profile_id,
        created_at=block.created_at,
    )


@router.post("/reports", response_model=ReportView)
def create_report(
    request: ReportRequest,
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    if request.target_profile_id == me.id:
        raise HTTPException(status_code=400, detail="자기 자신은 신고할 수 없습니다.")

    target = db.query(Profile).filter(Profile.id == request.target_profile_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="대상 프로필을 찾을 수 없습니다.")

    # 대화방을 근거로 첨부하면 신고자가 그 대화방 참가자인지 검증한다.
    if request.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == request.conversation_id)
            .first()
        )
        match = (
            db.query(Match).filter(Match.id == conversation.match_id).first()
            if conversation
            else None
        )
        if conversation is None or conversation_partner_id(match, me.id) is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="근거로 첨부한 대화방의 참가자가 아닙니다.",
            )

    # 신고는 멱등이 아니다 — 같은 상대를 여러 번 신고할 수 있으므로 매번 새로 기록한다.
    report = Report(
        reporter_profile_id=me.id,
        target_profile_id=target.id,
        conversation_id=request.conversation_id,
        category=request.category,
        summary=request.summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportView(
        id=report.id,
        reporter_profile_id=report.reporter_profile_id,
        target_profile_id=report.target_profile_id,
        conversation_id=report.conversation_id,
        category=report.category,
        summary=report.summary,
        status=report.status,
        created_at=report.created_at,
    )
