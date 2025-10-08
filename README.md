# 🎮 Game Translator

Unity 게임(Naninovel) 텍스트 자동 번역 및 게임 적용 도구

## ✨ 주요 기능

- **Unity Bundle 추출**: Asset Bundle에서 게임 스크립트 자동 추출
- **AI 자동 번역**: Claude API를 사용한 고품질 일본어→한국어 번역
- **Excel 검수**: Excel로 번역 내보내기/수정/가져오기
- **게임 적용**: 번역을 게임 Asset Bundle에 자동 패키징 및 교체
- **번역 메모리**: 중복 번역 방지 및 일관성 유지
- **품질 관리**: 번역 규칙 및 용어집 관리

## 🔄 전체 워크플로우

```
1. Unity Bundle 추출 → 2. AI 번역 → 3. Excel 검수 → 4. 게임 적용
```

### 1️⃣ Unity Bundle 추출
- 게임 폴더에서 Asset Bundle 자동 감지
- TextAsset 추출 및 Naninovel 스크립트 파싱
- 챕터별 선택 추출 가능

### 2️⃣ AI 번역
- Claude API로 일본어→한국어 자동 번역
- 번역 규칙 및 용어집 자동 적용
- 프롬프트 캐싱으로 비용 90% 절감
- 멀티라인 중국어 처리 지원

### 3️⃣ Excel 검수
- 번역 내보내기: AI 번역을 Excel로 내보내기
- 수정: Excel에서 번역 검수 및 수정
- 가져오기: 수정된 번역을 스마트 병합

### 4️⃣ 게임 적용
- 게임 언어 자동 감지
- 대체 언어 선택 (예: 중국어 → 한국어)
- 원본 자동 백업
- Asset Bundle에 번역 패키징 및 교체

## 🚀 빠른 시작

### 설치

```bash
# 의존성 설치
pip install -r requirements.txt
```

**필수 패키지:**
- Python 3.10+
- PyQt6
- UnityPy
- anthropic (Claude API)
- pandas, openpyxl

### 실행

```bash
# GUI 실행
python run_translator_gui.py
```

## 📖 사용법

### 1. 프로젝트 생성
1. GUI에서 "새 프로젝트" 탭 선택
2. 프로젝트 이름 입력
3. 게임 폴더 선택
4. "프로젝트 생성" 클릭

### 2. 번역 추출 및 번역
1. "번역" 탭 선택
2. 챕터 선택 (선택사항)
3. "번역 시작" 클릭
4. preview 폴더에 번역 결과 저장

### 3. Excel 검수 (선택사항)
1. "검수" 탭에서 "Excel 내보내기"
2. Excel 파일 열어서 "수정본" 열에 수정 내용 입력
3. "Excel 가져오기"로 수정 내용 반영

### 4. 게임에 적용
1. "적용" 탭 선택
2. "게임 언어 감지" 버튼으로 게임 언어 확인
3. 대체할 언어 선택 (예: 중국어 간체)
4. "게임에 적용" 클릭
5. 원본 자동 백업 후 번역 적용

### 5. 게임 실행
- **중요**: Steam 게임 속성 → 언어를 **대체한 언어**로 설정
- 예: 중국어 Bundle을 교체했다면 → 게임 언어를 "Chinese (Simplified)"로 설정

## ⚙️ 설정

### API 키 설정
1. GUI에서 "설정" → "API 키 설정"
2. Claude API 키 입력
3. 저장

### 번역 규칙
- `examples/translation_rules_ja_ko.yaml` - 일본어→한국어 규칙 예시
- `examples/translation_rules_en_ko.yaml` - 영어→한국어 규칙 예시
- `examples/translation_rules_zh_ko.yaml` - 중국어→한국어 규칙 예시
- 감탄사, 말투, 금지 패턴 등 정의
- 사용 시 `config/` 폴더로 복사하여 커스터마이징

### 용어집
- `examples/glossary_ja_ko.json` - 일본어→한국어 용어집 예시
- `examples/glossary_en_ko.json` - 영어→한국어 용어집 예시
- `examples/glossary_zh_ko.json` - 중국어→한국어 용어집 예시
- 일관된 번역을 위한 용어 매핑

## 🔧 핵심 모듈

### Core
- `translator.py` - AI 번역 엔진 (Claude API)
- `excel_manager.py` - Excel 검수 워크플로우
- `bundle_packer.py` - Asset Bundle 패키징 및 교체
- `game_language_detector.py` - 게임 언어 자동 감지

### GUI
- `main_window.py` - PyQt6 메인 GUI
- 번역, 검수, 적용 탭 통합

## 📁 프로젝트 구조

```
gametranslator/
├── gui/                  # GUI 인터페이스
│   └── main_window.py
├── core/                 # 핵심 엔진
│   ├── translator.py
│   ├── excel_manager.py
│   ├── bundle_packer.py
│   └── game_language_detector.py
├── examples/             # 번역 규칙 및 용어집 예시
│   ├── translation_rules_ja_ko.yaml
│   ├── translation_rules_en_ko.yaml
│   ├── translation_rules_zh_ko.yaml
│   ├── glossary_ja_ko.json
│   ├── glossary_en_ko.json
│   └── glossary_zh_ko.json
├── config/               # 사용자 설정 (gitignore)
│   └── .gitkeep
├── projects/             # 프로젝트 폴더 (gitignore)
│   └── [project_name]/
│       └── preview/      # 번역 결과
├── backups/              # 게임 백업 (gitignore)
└── _archived/            # 이전 버전 파일
```

## 🛡️ 백업 및 복원

### 자동 백업
- 게임 적용 시 원본 Asset Bundle 자동 백업
- 백업 위치: `backups/bundle_backup_[timestamp]/`

### 수동 복원
```python
from core.bundle_packer import BundlePacker
from pathlib import Path

packer = BundlePacker()
packer.restore_backup(
    backup_dir=Path("backups/bundle_backup_20250108_120000"),
    game_path=Path("C:/Your/Game/Path")
)
```

## ⚠️ 주의사항

1. **게임 언어 설정**: 번역을 적용한 언어로 게임 언어를 설정해야 함
2. **백업 필수**: 게임 적용 전 자동 백업되지만, 게임 폴더 전체 백업 권장
3. **Steam 무결성 검사**: Steam 게임 무결성 검사 시 원본으로 복구됨
4. **API 키 보안**: API 키는 암호화되어 저장되지만 절대 공유하지 말 것

## 🐛 문제 해결

### 게임이 한국어로 안 나올 때
1. 게임 언어 설정 확인 (Steam 속성 → 언어)
2. 적용한 Bundle과 게임 언어가 일치하는지 확인
3. 게임 재시작

### 번역이 이상할 때
1. Excel로 내보내기 → 수정 → 가져오기
2. 번역 규칙 수정
   - `examples/translation_rules_ja_ko.yaml`을 `config/`로 복사
   - 규칙 수정 후 GUI에서 해당 파일 선택
3. 용어집 추가
   - `examples/glossary_ja_ko.json`을 `config/`로 복사
   - 용어 추가 후 GUI에서 해당 파일 선택

### 백업 복원이 필요할 때
```bash
# 백업 폴더에서 원본 복원
cp backups/bundle_backup_*/[bundle_name].bundle [game_path]/
```

## 📝 라이선스

개인 사용 목적으로만 사용하세요.

## 🙏 크레딧

- **UnityPy**: Unity Asset Bundle 추출/패킹
- **Claude API (Anthropic)**: AI 번역
- **PyQt6**: GUI 프레임워크
