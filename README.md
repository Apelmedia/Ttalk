# Warm Haven

성인 LGBTQ+ 이용자를 위한 안전 중심 매칭·채팅 앱의 초기 작업 폴더입니다.

현재 범위는 다음과 같습니다.

- Claude Design에서 만든 시험용 HTML을 `static/index.html`로 보존
- AHTTY의 검증된 FastAPI 골격을 참고한 독립 백엔드
- 프론트 연결을 위한 데모 API
- 운영 전 검토할 안전·법률 체크리스트

## 로컬 실행

```powershell
cd C:\dev\lgbt_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

브라우저에서 다음 주소를 확인합니다.

- 앱 초안: `http://127.0.0.1:8080/`
- API 문서: `http://127.0.0.1:8080/docs`
- 상태 확인: `http://127.0.0.1:8080/health`

## 중요

현재 API는 `DEMO_MODE=true`일 때만 동작하는 화면 연결용 초안입니다. 실제 출시 전에는 인증, 성인 확인, 관리자 신고 처리, 사진 저장소, 개인정보 동의 이력, 위치정보 검토를 연결해야 합니다.

## 문서

- 상세 구조 비교: `docs/FRONTEND_BACKEND_COMPARISON.md`
- 백엔드 요약: `docs/ARCHITECTURE.md`
- API 초안: `docs/API_DRAFT.md`
- 안전·법률 체크리스트: `docs/SAFETY_AND_LEGAL.md`
- 자산 인벤토리: `docs/ASSET_INVENTORY.md`
- 마무리 인수인계: `docs/FINAL_HANDOFF.md`
