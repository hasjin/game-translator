# Examples - 번역 규칙 및 용어집 예시

이 폴더에는 언어별 번역 규칙과 용어집 예시가 포함되어 있습니다.

## 📁 파일 구조

### 번역 규칙 (Translation Rules)
- `translation_rules_ja_ko.yaml` - 일본어→한국어 번역 규칙 예시
- `translation_rules_en_ko.yaml` - 영어→한국어 번역 규칙 예시
- `translation_rules_zh_ko.yaml` - 중국어→한국어 번역 규칙 예시

### 용어집 (Glossary)
- `glossary_ja_ko.json` - 일본어→한국어 용어집 예시
- `glossary_en_ko.json` - 영어→한국어 용어집 예시
- `glossary_zh_ko.json` - 중국어→한국어 용어집 예시

> **참고**: 실제 사용 시 이 파일들을 `config/` 폴더로 복사하여 수정하세요.

## 🔧 사용 방법

### GUI에서 사용 (권장)
1. 예시 파일을 `config/` 폴더로 복사
   ```bash
   # Windows
   copy examples\translation_rules_ja_ko.yaml config\
   copy examples\glossary_ja_ko.json config\
   ```
2. GUI 실행: `run_gui.bat` 또는 `python -m gui.main_window`
3. **설정** 탭에서 번역 규칙 확인 및 수정
4. **번역** 탭에서 번역 실행 시 자동 적용

## 📝 커스터마이징

### 번역 규칙 수정
1. `examples/translation_rules_ja_ko.yaml`을 `config/`로 복사
2. 텍스트 에디터로 열어서 수정
3. GUI에서 번역 시 자동 적용

### 용어집 추가
`config/glossary_ja_ko.json` 파일에 게임별 용어 추가:
```json
{
  "고유명사": {
    "プレイヤー": "플레이어",
    "モンスター": "몬스터"
  },
  "게임 용어": {
    "レベル": "레벨",
    "スキル": "스킬"
  }
}
```

## 🌐 지원 언어 조합

- **일본어 → 한국어** (ja → ko) - 가장 많이 사용됨
- 영어 → 한국어 (en → ko)
- 중국어 → 한국어 (zh → ko)

## ⚙️ 번역 규칙 형식 예시

번역 규칙은 YAML 형식으로 작성합니다:

```yaml
target_language: "한국어"
source_language: "일본어"

rules:
  - 존댓말/반말 일관성 유지
  - 고유명사는 번역하지 않음
  - 게임 용어는 통일
  - 자연스러운 한국어 표현 사용
  - {name}, [item] 등 게임 태그는 그대로 유지
```

## 📚 참고

- 번역 규칙은 YAML 형식 (`.yaml` 파일)
- 용어집은 JSON 형식 (`.json` 파일)
- 모든 파일은 UTF-8 인코딩 필수
- `config/` 폴더의 파일은 Git에 커밋되지 않습니다 (개인 설정)
