"""
인증/권한 공통 유틸 (Warm Haven).

설계 원칙:
- firebase-admin은 선택 의존성이다. 미설치여도 import 단계에서 죽지 않는다.
- USE_FIREBASE_AUTH=true이면 Bearer 토큰을 Firebase ID 토큰으로 검증한다.
- USE_FIREBASE_AUTH=false(기본)이면 개발용 dev 토큰만 허용해
  C:\\dev\\lgbt_app 안에서 외부 의존 없이 단독 검증한다.

개발용 dev 토큰 형식:
    Authorization: Bearer dev:<subject>
  예) "dev:alice" → auth_subject="dev:alice" 계정으로 조회/생성한다.
  이 경로는 개발·테스트 전용이며 운영(USE_FIREBASE_AUTH=true)에서는 거부된다.
"""

import logging
from pathlib import Path

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.entities import Account, Profile

logger = logging.getLogger(__name__)

DEV_TOKEN_PREFIX = "dev:"

try:  # firebase-admin은 선택 의존성
    import firebase_admin
    from firebase_admin import auth, credentials
except ImportError:  # pragma: no cover
    firebase_admin = None  # type: ignore[assignment]
    auth = None  # type: ignore[assignment]
    credentials = None  # type: ignore[assignment]


def _get_admin_emails() -> set[str]:
    raw = (settings.ADMIN_EMAILS or "").strip()
    if not raw:
        return set()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def init_firebase() -> None:
    """Firebase Admin SDK를 1회 초기화한다. 이미 초기화돼 있으면 no-op."""
    if not firebase_admin:
        logger.warning("firebase_admin 미설치 — Firebase 인증 비활성화")
        return
    if firebase_admin._apps:  # type: ignore[attr-defined]
        return
    cred_path = (settings.FIREBASE_CREDENTIALS_PATH or "").strip()
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(
            cred, options={"projectId": settings.FIREBASE_PROJECT_ID}
        )
        source = f"certificate:{Path(cred_path).name}"
    else:
        firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
        source = "ADC"
    logger.info(
        "Firebase Admin SDK 초기화 완료 (projectId=%s, source=%s)",
        settings.FIREBASE_PROJECT_ID,
        source,
    )


if settings.USE_FIREBASE_AUTH:
    try:
        init_firebase()
    except Exception:  # pragma: no cover - 검증 시점에 재시도
        logger.exception("초기 Firebase 초기화 실패 — verify 시점에 재시도")


security = HTTPBearer(auto_error=False)


def _resolve_subject(token: str) -> tuple[str, str | None, str]:
    """토큰에서 (auth_subject, email, provider)를 해석한다.

    Firebase 모드면 ID 토큰을 검증하고, 개발 모드면 dev 토큰을 해석한다.
    """
    if settings.USE_FIREBASE_AUTH:
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase Admin SDK가 설치되지 않았습니다.",
            )
        try:
            init_firebase()  # import 시 실패한 경우 대비
            decoded = auth.verify_id_token(token)
        except Exception as exc:
            logger.debug("Firebase ID 토큰 검증 실패: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        info = decoded.get("firebase", {})
        provider = info.get("sign_in_provider") or "firebase"
        return decoded["uid"], decoded.get("email"), provider

    # 개발 모드: dev 토큰만 허용
    if not token.startswith(DEV_TOKEN_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="개발 모드에서는 'dev:<subject>' 토큰만 허용됩니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    subject = token[len(DEV_TOKEN_PREFIX) :].strip()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="dev 토큰의 subject가 비어 있습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # dev 토큰은 'dev:<subject>@<email>' 형태로 이메일을 옵션 지정할 수 있다(개발용).
    email = None
    if "@" in subject:
        email = subject if "." in subject.split("@", 1)[1] else None
    return f"dev:{subject}", email, "dev"


def get_current_account(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Security(security),
    db: Session = Depends(get_db),
) -> Account:
    """Authorization Bearer 토큰으로 현재 계정을 조회/생성한다."""
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_subject, email, _provider = _resolve_subject(creds.credentials)

    account = db.query(Account).filter(Account.auth_subject == auth_subject).first()
    if account is None:
        account = Account(auth_subject=auth_subject, email=email)
        db.add(account)
        db.commit()
        db.refresh(account)
    elif email and account.email != email:
        account.email = email
        db.commit()

    if account.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이용이 제한된 계정입니다.",
        )
    return account


def require_adult_verified(account: Account = Depends(get_current_account)) -> Account:
    """성인 확인 게이트. REQUIRE_ADULT_VERIFICATION=false이면 통과시킨다."""
    if settings.REQUIRE_ADULT_VERIFICATION and not account.is_adult_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="성인 확인이 필요합니다.",
        )
    return account


def get_current_profile(
    account: Account = Depends(require_adult_verified),
    db: Session = Depends(get_db),
) -> Profile:
    """로그인 계정의 프로필을 반환한다. 없으면 409로 프로필 생성을 요구한다."""
    profile = db.query(Profile).filter(Profile.account_id == account.id).first()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="프로필을 먼저 생성해야 합니다.",
        )
    return profile


def require_admin(account: Account = Depends(get_current_account)) -> Account:
    """관리자 권한 가드. ADMIN_EMAILS 화이트리스트로 판정한다."""
    admins = _get_admin_emails()
    email = (account.email or "").lower()
    if not email or email not in admins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return account
