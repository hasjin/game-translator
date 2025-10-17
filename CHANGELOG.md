# 변경 이력 (Changelog)

## [0.1.0] - 2025-10-14

### 🔧 수정 (Fixed)
- **의존성 충돌 해결**: `googletrans`와 `anthropic` 패키지 간 httpx 버전 충돌 해결
  - `googletrans==4.0.0-rc1` 패키지 제거
  - Google Translate를 `requests`를 통해 직접 API 호출하도록 변경
  - 기능은 동일하게 유지되며, 설치 시간 단축

### 📝 변경 (Changed)
- `core/translation_engines.py`: `GoogleTranslator` 클래스를 `requests` 기반으로 재작성
- `requirements.txt`: `googletrans` 패키지 제거, 주석 추가
- `cli/translator.py`와 구현 방식 통일

### 📚 문서 (Documentation)
- `README.md`: 의존성 충돌 트러블슈팅 섹션 추가
- `project_architecture.md`: 의존성 목록 업데이트
- `REFACTORING_HISTORY.md`: 변경 이력 추가
- `CHANGELOG.md`: 새로 생성

### ✅ 검증 (Verified)
- ✅ Google Translate 정상 작동 확인
- ✅ 모든 번역 엔진 import 성공
- ✅ 기존 가상환경(venv310)에서 정상 작동

---

## [0.0.2] - 2025-10-08

### 🎉 추가 (Added)
- GUI 대규모 리팩토링 (Mixin 패턴)
- 폴더 구조 최적화 (cli/, security/, tools/)
- 일반 Unity 게임 번역 지원 (AssetsTools.NET 통합)
- 번역 메모리 시스템 (SQLite)
- 세션 자동 복원 기능

### 🔧 개선 (Improved)
- `main_window.py` 2,600줄 → 914줄 (65% 감소)
- 코드 가독성 및 유지보수성 향상
- 모듈 독립성 강화

자세한 내용은 `REFACTORING_HISTORY.md` 참조

---

## [0.0.1] - 2025-01-08

### 🎉 초기 릴리스
- Naninovel 게임 번역 지원
- Claude API 기반 AI 번역
- Excel 검수 워크플로우
- Unity Asset Bundle 패킹
- GUI 인터페이스

---

**버전 형식**: [Major.Minor.Patch]
- **Major**: 주요 기능 추가 또는 호환성 변경
- **Minor**: 새로운 기능 추가
- **Patch**: 버그 수정 및 개선
