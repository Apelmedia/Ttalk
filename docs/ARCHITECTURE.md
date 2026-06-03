# Warm Haven 백엔드 초안

## 목표

첫 버전은 GPS 없이 사용자가 선택한 지역과 프로필 조건으로 사람을 찾고, 상호 좋아요 이후에만 채팅을 허용하는 안전 매치형 MVP입니다.

## 현재 구조

```text
모바일 웹 프로토타입
  -> FastAPI
     -> /health
     -> /v1/public/bootstrap
     -> /v1/people
     -> /v1/matches
     -> /v1/chats
     -> /v1/safety
     -> /v1/private-photos
  -> SQLite (로컬 모델 검증용)
```

데모 API는 프론트 연결 계약을 확인하기 위한 고정 응답입니다. 실제 데이터 쓰기는 아직 연결하지 않았습니다.

## 운영 전환 구조

```text
앱
  -> 인증·성인 확인
  -> Cloud Run FastAPI
     -> PostgreSQL: 계정, 프로필, 매치, 채팅 메타데이터, 신고
     -> 암호화 Object Storage: 공개 요청 사진, 신고 증거
     -> FCM/APNs: 새 메시지 알림
     -> 관리자 화면: 신고 검토, 제한, 증거 보존
```

## 데이터 원칙

- GPS를 도입하기 전에는 시·구 단위 사용자의 선택 지역만 저장합니다.
- 성별정체성, 성적 지향, 세부 성향은 항목별 공개 여부를 둡니다.
- 정확한 생년월일과 신분증 원본은 앱 DB에 저장하지 않는 방향을 우선 검토합니다.
- 사진 URL은 영구 공개 URL로 만들지 않습니다.
- 차단 관계는 검색, 매칭, 채팅 조회 모두에 적용합니다.
- 신고 증거는 일반 채팅 데이터와 분리하고 접근 권한을 제한합니다.
- 정책 동의 이력은 `consent_records`, 관리자 신고 조치는 `moderation_actions`, 공개 요청 사진 접근 기록은 `private_photo_access_logs`로 분리합니다.
- 프로필 나이는 `19~120`, 자기 자신 좋아요·차단은 금지하고, 매치 쌍은 항상 정렬된 순서로 저장하도록 DB 제약을 둡니다.

## 초기 보안 헤더

FastAPI는 정적 HTML과 API 응답에 다음 헤더를 추가합니다.

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), camera=(), microphone=()`

현재 GPS와 카메라 권한은 의도적으로 차단합니다. 사진 업로드나 GPS 주변 탐색을 구현할 때 필요한 화면과 경로에만 권한을 좁혀 다시 설정합니다.

`Content-Security-Policy`는 아직 적용하지 않았습니다. 현재 standalone HTML에 inline 스크립트와 `claude.ai` 외부 URL이 포함되어 있어, 운영형 프론트로 분리한 뒤 허용 목록을 정해야 합니다.

## GPS 확장 조건

주변 탐색은 초기 운영이 안정된 뒤 별도 단계로 추가합니다. 위치 권한, 위치정보 이용약관, 별도 동의, 신고 대상 여부, 보관 기간을 먼저 검토하고 정확한 좌표 대신 거리 구간만 노출합니다.
