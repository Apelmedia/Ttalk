# 정적 자산 메모

- `index.html`은 사용자가 제공한 Claude Design standalone HTML을 그대로 보존한 프로토타입입니다.
- 번들 내부에 폰트와 이미지가 포함되어 있어 파일 크기가 큽니다.
- 원본 번들은 외부 URL을 포함할 수 있으므로 운영 배포 전에 `docs/ASSET_INVENTORY.md` 기준으로 분리·검토해야 합니다.
- `assets/legal-links.js`는 AHTTY에서 가져온 범용 외부 링크 보안 처리 스크립트입니다.
- `assets/legal-footer.reference.css`는 향후 약관·개인정보 링크 UI를 붙일 때 참고하기 위한 AHTTY CSS입니다. 현재 프로토타입에는 아직 삽입하지 않았습니다.
