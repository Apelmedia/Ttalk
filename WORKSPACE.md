# Warm Haven 작업 기록

## 2026-06-04 슬라이스 4~6 (safety / private-photos DB 전환)

- 차단·신고·공개 요청 사진(등록·열람 권한)을 데모 영수증 → 인증 프로필 기준 DB 저장으로 전환.
- safety: 차단 멱등(uq_block_pair), 신고는 매번 INSERT(대화방 근거 첨부 시 참가자 검증).
- private-photos: 사진 메타 등록 엔드포인트(`POST /private-photos`) 추가, 권한 부여/철회/재부여
  (uq_photo_viewer 충돌 시 기존 행 되살리는 멱등 upsert).
- 스키마에서 actor id 필드(blocker/reporter/owner) 제거 — 인증 프로필로 결정(likes/chats와 일관).
- 테스트 32개 green. 검증: `python -m unittest discover -s tests -t .`
- 잔여 정리거리: `app/services/demo_catalog.py`의 receipt/PEOPLE/CHATS는 죽은 코드.

## 2026-06-01 초기 생성

### 가져온 자산

- `static/index.html`: 사용자가 제공한 `Warm Haven (standalone) (1).html` 원본 복사본
- `static/assets/legal-links.js`: AHTTY의 외부 링크 보안 처리 스크립트 복사본
- `static/assets/legal-footer.reference.css`: AHTTY 법률 링크 UI의 참고용 CSS 복사본

### 구조 결정

- AHTTY의 `FastAPI + /v1 라우터 + /health + static mount` 패턴만 재사용
- AHTTY 브랜드 로고, Firebase 프로젝트 값, LLM 라우팅, 결제, Secret Manager 값은 가져오지 않음
- 초기 로컬 DB는 SQLite
- GPS 위치 저장은 아직 구현하지 않음
- 화면 연결용 응답은 `DEMO_MODE=true`에서만 제공

### 다음 구현 우선순위

1. 시험용 HTML에서 API 호출 지점을 분리하고 데모 API와 연결
2. Firebase Auth 또는 별도 인증 제공자 결정
3. 성인 확인 제공자와 동의 이력 저장 방식 결정
4. 관리자 신고 처리 화면과 증거 보존 정책 구현
5. 공개 요청 사진의 암호화 저장소와 만료 URL 구현

### 추가 문서

- `docs/FRONTEND_BACKEND_COMPARISON.md`: 현재 프론트엔드와 백엔드의 실제 연결 상태, 화면별 API·DB 대응표, 운영 전환 구조
- `docs/FINAL_HANDOFF.md`: 초안 완료 범위, 의도적으로 보류한 항목, 다음 세션 시작점
