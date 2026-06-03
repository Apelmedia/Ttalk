from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=60)
    age: int = Field(ge=19, le=120)
    region_code: str = Field(min_length=1, max_length=32)
    body_type: str | None = Field(default=None, max_length=40)
    identity_tags: list[str] = Field(default_factory=list, max_length=20)
    orientation_tags: list[str] = Field(default_factory=list, max_length=20)
    bio: str = Field(default="", max_length=2000)
    is_discoverable: bool = True


class ProfileView(BaseModel):
    id: str
    nickname: str
    age: int
    region_code: str
    body_type: str | None
    identity_tags: list[str]
    orientation_tags: list[str]
    bio: str
    is_discoverable: bool


class AccountMeView(BaseModel):
    account_id: str
    email: str | None
    is_adult_verified: bool
    status: str
    profile: ProfileView | None


class PersonCard(BaseModel):
    id: str
    nickname: str
    age: int
    approx_distance: str
    region: str
    tags: list[str]
    online: bool = False


class LikeRequest(BaseModel):
    # actor는 요청 본문이 아니라 인증된 프로필로 결정한다.
    target_profile_id: str
    decision: Literal["like", "pass"] = "like"


class LikeResult(BaseModel):
    decision: Literal["like", "pass"]
    target_profile_id: str
    is_match: bool = False
    match_id: str | None = None
    conversation_id: str | None = None


class MessageRequest(BaseModel):
    # sender는 인증된 프로필로 결정한다.
    body: str = Field(min_length=1, max_length=2000)


class MessageView(BaseModel):
    id: str
    conversation_id: str
    sender_profile_id: str
    body: str
    created_at: datetime


class ChatSummary(BaseModel):
    conversation_id: str
    partner_profile_id: str
    partner_nickname: str
    last_message: str | None = None
    unread_count: int = 0  # read 추적 모델이 아직 없어 항상 0 (stub)
    updated_at: datetime | None = None


class BlockRequest(BaseModel):
    blocker_profile_id: str
    blocked_profile_id: str


class ReportRequest(BaseModel):
    reporter_profile_id: str
    target_profile_id: str
    conversation_id: str | None = None
    category: Literal[
        "prostitution",
        "stalking",
        "harassment",
        "impersonation",
        "minor_suspected",
        "image_abuse",
        "other",
    ]
    summary: str = Field(default="", max_length=2000)


class PrivatePhotoGrantRequest(BaseModel):
    owner_profile_id: str
    viewer_profile_id: str
    photo_id: str

