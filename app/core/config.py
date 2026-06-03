from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Warm Haven API"
    ENVIRONMENT: str = "local"
    DEMO_MODE: bool = True
    DATABASE_URL: str = "sqlite:///./warm_haven.db"
    ALLOWED_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080"

    # 인증 — USE_FIREBASE_AUTH=true이면 Firebase ID 토큰을 검증하고,
    # false(기본)이면 개발용 dev 토큰만 허용해 이 폴더 안에서 단독 검증한다.
    # firebase-admin은 선택 의존성이며 requirements에 강제로 넣지 않는다.
    USE_FIREBASE_AUTH: bool = False
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""

    # 관리자 이메일 화이트리스트(콤마 구분). 운영에서는 환경 변수로 주입한다.
    ADMIN_EMAILS: str = ""

    # 성인 확인 게이트. 운영에서는 true가 기본이어야 한다.
    REQUIRE_ADULT_VERIFICATION: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

