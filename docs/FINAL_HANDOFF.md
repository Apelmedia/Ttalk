# Warm Haven 초안 마무리 인수인계

## 현재 완료된 것

- 사용자가 제공한 Warm Haven standalone HTML을 `static/index.html`에 보존했습니다.
- AHTTY의 단일 FastAPI 구조를 참고해 `/health`, `/v1` 라우터, CORS, 정적 파일 제공을 구성했습니다.
- 사람들, 좋아요, 채팅, 차단, 신고, 공개 요청 사진 승인·철회의 데모 API를 만들었습니다.
- 계정, 프로필, 좋아요, 매치, 대화방, 메시지, 차단, 신고, 사진 권한 DB 모델을 만들었습니다.
- 민감정보 동의 이력, 관리자 조치 기록, 사진 접근 기록 모델을 추가했습니다.
- 잘못된 자기 자신 좋아요·차단, 성인 범위 밖 프로필 나이, 뒤집힌 중복 매치를 막는 DB 제약을 추가했습니다.
- 기본 보안 응답 헤더를 추가했습니다.
- (슬라이스 1~3) 인증 레이어와 people/likes/matches/chats를 인증 프로필 기준 DB 저장으로 전환했습니다.
- (슬라이스 4~6) 차단·신고·공개 요청 사진 등록·열람 권한을 인증 프로필 기준 DB 저장으로 전환했습니다.
  차단은 멱등, 신고는 매번 기록(대화방 근거 첨부 시 참가자 검증), 사진 권한은 부여/철회/재부여를 지원합니다.

## 현재 의도적으로 보류한 것

- 프론트 HTML과 `/v1` API 실제 연결
- 로그인과 성인 확인 제공자(Firebase 등) 실제 연동 — 현재는 개발용 dev 토큰으로 단독 검증
- 관리자 신고 검토 화면(ModerationAction 와이어링)
- 사진 바이너리 업로드, 암호화 저장소, 만료 URL — 현재는 메타데이터(object_key)만 등록
- 차단 해제(unblock) 엔드포인트
- WebSocket 또는 SSE 실시간 채팅
- FCM/APNs 푸시 알림
- GPS 주변 탐색
- Cloud Run, PostgreSQL, Secret Manager 운영 배포

## 다음 세션 시작점

백엔드 `/v1` API는 사람들·좋아요·매치·채팅·차단·신고·사진 권한까지 모두 인증 프로필 기준
DB 저장으로 전환됐습니다. 다음 단계는 `static/index.html`의 화면 흐름을 유지하면서
이 실제 API에 프론트를 연결하는 작업입니다.

현재 HTML은 Claude standalone 번들이므로 바로 크게 수정하기보다 운영형 프론트 구조로 분리할지 먼저 결정하는 편이 안전합니다.

## 검증 명령

```powershell
cd C:\dev\lgbt_app
python -m unittest discover -s tests -t . -v
```

`-t .`(top-level=프로젝트 루트)가 있어야 `tests/__init__.py`가 실행되어 테스트가
운영 `warm_haven.db`가 아닌 격리된 임시 DB를 사용합니다. 생략하면 테스트 데이터가
누적되어 플래키해집니다.

```powershell
cd C:\dev\lgbt_app
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

확인 주소:

- 앱: `http://127.0.0.1:8080/`
- API 문서: `http://127.0.0.1:8080/docs`
- 상태 확인: `http://127.0.0.1:8080/health`
