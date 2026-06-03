"""사람들 탭 — 발견 가능한 프로필 목록.

차단 관계(양방향)와 본인은 제외하고, is_discoverable=true인 프로필만 반환한다.
GPS는 아직 도입하지 않으므로 거리 대신 지역 기준 라벨만 제공한다.
"""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_profile
from app.models.entities import Profile
from app.schemas.api import PersonCard

router = APIRouter(prefix="/people", tags=["people"])


def _to_card(profile: Profile, my_region: str) -> PersonCard:
    tags = json.loads(profile.identity_tags_json or "[]") + json.loads(
        profile.orientation_tags_json or "[]"
    )
    return PersonCard(
        id=profile.id,
        nickname=profile.nickname,
        age=profile.age,
        approx_distance="같은 지역" if profile.region_code == my_region else "지역 기반",
        region=profile.region_code,
        tags=tags,
        online=False,  # 접속 상태 추적은 아직 없음
    )


@router.get("", response_model=list[PersonCard])
def list_people(
    region: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    me: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    from app.services.social import blocked_profile_ids

    excluded = blocked_profile_ids(db, me.id)
    excluded.add(me.id)

    query = db.query(Profile).filter(
        Profile.is_discoverable.is_(True),
        Profile.id.notin_(excluded),
    )
    if region:
        query = query.filter(Profile.region_code.contains(region))

    # 태그는 JSON 문자열 컬럼이라 초안 단계에서는 조회 후 파이썬에서 필터한다.
    # 운영 PostgreSQL 전환 시 JSONB 또는 별도 태그 테이블로 옮긴다.
    candidates = query.order_by(Profile.created_at.desc()).limit(limit * 3).all()

    cards: list[PersonCard] = []
    for profile in candidates:
        card = _to_card(profile, me.region_code)
        if tag and tag not in card.tags:
            continue
        cards.append(card)
        if len(cards) >= limit:
            break
    return cards
