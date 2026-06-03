# 자산 인벤토리

## Warm Haven 프로토타입

`static/index.html`은 사용자가 제공한 Claude Design standalone HTML 원본입니다. 폰트와 이미지가 번들 내부에 포함되어 있어 한 파일로 실행할 수 있습니다.

이 파일은 화면 흐름 검증용입니다. 운영 배포 전에 다음 작업이 필요합니다.

- 2026-06-01 점검에서 `claude.ai` 외부 URL이 포함된 것을 확인했습니다. 운영 UI로 분해할 때 제거합니다.
- 번들 내부의 이미지, 폰트, 외부 URL 목록 검토
- 필요한 자산을 별도 파일로 추출하고 출처·사용권 기록
- 외부 CDN 또는 생성 도구 도메인 의존성 제거
- React 또는 정적 컴포넌트 구조로 화면 분리
- CSP, 개인정보 처리방침, 이용약관 링크 연결

## AHTTY 참고 자산

- `static/assets/legal-links.js`: 외부 링크에 `noopener noreferrer`를 적용하는 범용 스크립트
- `static/assets/legal-footer.reference.css`: 법률 링크 패널 스타일 참고본

AHTTY 로고와 AHTTY 브랜드 문구는 Warm Haven에 복사하지 않았습니다.
