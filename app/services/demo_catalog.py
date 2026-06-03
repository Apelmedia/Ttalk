from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.api import PersonCard


PEOPLE = [
    PersonCard(
        id="profile-haeun",
        nickname="하은",
        age=29,
        approx_distance="3km 이내",
        region="서울 마포구",
        tags=["대화", "카페", "전시"],
        online=True,
    ),
    PersonCard(
        id="profile-jun",
        nickname="준",
        age=31,
        approx_distance="5km 이내",
        region="서울 용산구",
        tags=["친구", "산책", "영화"],
        online=True,
    ),
    PersonCard(
        id="profile-mina",
        nickname="미나",
        age=27,
        approx_distance="같은 지역",
        region="서울 마포구",
        tags=["대화", "음악", "러닝"],
    ),
]


CHATS = [
    {
        "id": "conversation-demo-1",
        "nickname": "하은",
        "last_message": "안녕하세요. 프로필 보고 인사드려요.",
        "unread_count": 1,
        "updated_at": "2026-06-01T05:00:00+09:00",
    },
    {
        "id": "conversation-demo-2",
        "nickname": "준",
        "last_message": "주말에 전시 좋아하세요?",
        "unread_count": 0,
        "updated_at": "2026-05-31T21:15:00+09:00",
    },
]


def receipt(kind: str, **extra):
    return {
        "id": str(uuid4()),
        "kind": kind,
        "status": "demo_only",
        "created_at": datetime.now(UTC).isoformat(),
        **extra,
    }

