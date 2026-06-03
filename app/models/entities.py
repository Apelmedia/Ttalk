from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def new_id() -> str:
    return str(uuid4())


def now_utc() -> datetime:
    return datetime.now(UTC)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    auth_subject: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_adult_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("age >= 19 AND age <= 120", name="ck_profiles_age_adult_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(60))
    age: Mapped[int] = mapped_column(Integer)
    region_code: Mapped[str] = mapped_column(String(32), index=True)
    body_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    identity_tags_json: Mapped[str] = mapped_column(Text, default="[]")
    orientation_tags_json: Mapped[str] = mapped_column(Text, default="[]")
    bio: Mapped[str] = mapped_column(Text, default="")
    is_discoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("actor_profile_id", "target_profile_id", name="uq_like_pair"),
        CheckConstraint("actor_profile_id <> target_profile_id", name="ck_likes_no_self"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    target_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    decision: Mapped[str] = mapped_column(String(16), default="like")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("profile_a_id", "profile_b_id", name="uq_match_pair"),
        CheckConstraint("profile_a_id < profile_b_id", name="ck_matches_canonical_pair"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    profile_a_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    profile_b_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    media_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (
        UniqueConstraint("blocker_profile_id", "blocked_profile_id", name="uq_block_pair"),
        CheckConstraint("blocker_profile_id <> blocked_profile_id", name="ck_blocks_no_self"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    blocker_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    blocked_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reporter_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    target_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(40), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(24), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PrivatePhoto(Base):
    __tablename__ = "private_photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PrivatePhotoGrant(Base):
    __tablename__ = "private_photo_grants"
    __table_args__ = (
        UniqueConstraint("photo_id", "viewer_profile_id", name="uq_photo_viewer"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    photo_id: Mapped[str] = mapped_column(ForeignKey("private_photos.id"), index=True)
    owner_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    viewer_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    consent_type: Mapped[str] = mapped_column(String(64), index=True)
    policy_version: Mapped[str] = mapped_column(String(64))
    is_granted: Mapped[bool] = mapped_column(Boolean)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    actor_subject: Mapped[str] = mapped_column(String(255))
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PrivatePhotoAccessLog(Base):
    __tablename__ = "private_photo_access_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    photo_id: Mapped[str] = mapped_column(ForeignKey("private_photos.id"), index=True)
    viewer_profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    grant_id: Mapped[str | None] = mapped_column(
        ForeignKey("private_photo_grants.id"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
