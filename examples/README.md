# Examples - 번역 규칙 및 용어집 예시

이 폴더에는 언어별 번역 규칙과 용어집 예시가 포함되어 있습니다.

## 📁 파일 구조

### 번역 규칙 (Translation Rules)
- `translation_rules_ja_ko.yaml` - 일본어→한국어 번역 규칙
- `translation_rules_en_ko.yaml` - 영어→한국어 번역 규칙
- `translation_rules_zh_ko.yaml` - 중국어→한국어 번역 규칙

### 용어집 (Glossary)
- `glossary_ja_ko.json` - 일본어→한국어 용어집
- `glossary_en_ko.json` - 영어→한국어 용어집
- `glossary_zh_ko.json` - 중국어→한국어 용어집

## 🔧 사용 방법

### 1. 번역 규칙 적용
```python
from core.translator import UniversalTranslator

translator = UniversalTranslator(
    source_lang="ja",
    target_lang="ko",
    rules_file="examples/translation_rules_ja_ko.yaml"
)
```

### 2. 용어집 적용
```python
import json

with open("examples/glossary_ja_ko.json", "r", encoding="utf-8") as f:
    glossary = json.load(f)

translator = UniversalTranslator(
    source_lang="ja",
    target_lang="ko",
    glossary=glossary
)
```

### 3. GUI에서 사용
1. GUI 실행
2. "설정" → "번역 규칙 파일 선택"
3. `examples/translation_rules_ja_ko.yaml` 선택
4. "설정" → "용어집 파일 선택"
5. `examples/glossary_ja_ko.json` 선택

## 📝 커스터마이징

### 번역 규칙 수정
1. 예시 파일을 `config/` 폴더로 복사
2. 프로젝트에 맞게 수정
3. GUI 또는 코드에서 경로 지정

### 용어집 추가
```json
{
  "원본 용어": "번역될 용어",
  "キャラクター名": "캐릭터명",
  "固有名詞": "고유명사"
}
```

## 🌐 지원 언어 조합

- 일본어 → 한국어 (ja → ko)
- 영어 → 한국어 (en → ko)
- 중국어 간체 → 한국어 (zh-Hans → ko)
- 중국어 번체 → 한국어 (zh-Hant → ko)

## ⚙️ 번역 규칙 형식

```yaml
# 감탄사
interjections:
  あれ: "어라"
  えっ: "응?"

# 말투
tone:
  です: "입니다"
  だ: "이다"

# 금지 패턴
forbidden:
  - "직역 금지"
  - "어색한 표현"
```

## 📚 참고

- 번역 규칙은 YAML 형식
- 용어집은 JSON 형식
- UTF-8 인코딩 필수
