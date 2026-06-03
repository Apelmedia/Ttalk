# API 초안

현재 엔드포인트는 `DEMO_MODE=true`인 로컬 프로토타입 전용입니다.

| 메서드 | 경로 | 목적 |
|---|---|---|
| GET | `/health` | 서버 상태 |
| GET | `/v1/public/bootstrap` | 화면 기능 플래그와 안전 문구 |
| GET | `/v1/people` | 사람들 탭 데모 목록 |
| POST | `/v1/matches/likes` | 좋아요 또는 패스 기록 초안 |
| GET | `/v1/chats` | 채팅 목록 데모 |
| POST | `/v1/chats/{conversation_id}/messages` | 메시지 전송 초안 |
| POST | `/v1/safety/blocks` | 차단 요청 초안 |
| POST | `/v1/safety/reports` | 신고 접수 초안 |
| POST | `/v1/private-photos/grants` | 공개 요청 사진 열람 승인 초안 |
| DELETE | `/v1/private-photos/grants/{grant_id}` | 열람 승인 철회 초안 |

## 운영 전 필수 변경

- 모든 쓰기 API에 로그인 사용자 기반 권한 검증 추가
- `actor_profile_id`, `reporter_profile_id`, `owner_profile_id`를 요청 본문에서 신뢰하지 않고 로그인 사용자로 결정
- 메시지, 차단, 신고, 사진 권한을 DB 트랜잭션으로 저장
- 신고 증거 첨부는 파일 형식·크기 검증과 별도 저장소 정책 적용
- 관리자 전용 신고 검토 API와 감사 로그 추가

