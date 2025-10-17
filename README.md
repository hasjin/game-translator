# 🎮 Game Translator

게임 자동 번역 및 게임 적용 도구 (GUI 기반)

## ✨ 주요 기능

### 🖥️ GUI로 모든 게임 번역 (클릭만으로!)
- **자동 추출**: 게임 스크립트 자동 감지 및 추출
- **AI 자동 번역**: Claude/Google Translate를 사용한 고품질 번역
- **번역 검수**: 페이징 뷰어와 Excel 검수 기능
- **게임 적용**: 번역을 게임에 자동 패키징 및 교체
- **번역 메모리**: 중복 번역 방지 및 일관성 유지
- **품질 관리**: 번역 규칙 및 용어집 관리

### 🎮 지원하는 게임
- **RPG Maker MV/MZ**: 완벽 지원 ✅
- **Unity 게임** (Naninovel): 지원 ✅
- **일반 Unity 게임**: 기본 지원 ✅
- **Ren'Py**: 향후 지원 예정 🔜

**모든 작업은 GUI에서 클릭만으로 완료됩니다. CLI 명령어는 필요 없습니다!**

## 🚀 빠른 시작

### 1단계: Python 패키지 설치

```bash
# 자동 설치 (권장)
install.bat

# 또는 수동 설치
pip install -r requirements.txt
```

**필수 요구사항:**
- Python 3.10 이상
- PyQt6 (GUI)
- UnityPy (Unity 게임 처리)
- anthropic (Claude API)

### 2단계: 외부 도구 설치 (선택사항)

일부 특수한 Unity 게임은 AssetsTools.NET이 필요합니다. (대부분은 UnityPy만으로 충분)

**AssetsTools.NET 설치:**
1. [AssetsTools.NET Release](https://github.com/nesrak1/AssetsTools.NET/releases) 다운로드
2. `AssetsTools.NET.dll` 파일 다운로드
3. `gametranslator/lib/` 폴더에 복사
4. (선택) `classdata.tpk` 파일도 `lib/` 폴더에 복사

**설치 후 폴더 구조:**
```
gametranslator/
└── lib/
    ├── SETUP.txt (안내 파일)
    ├── AssetsTools.NET.dll  ← 여기
    └── classdata.tpk (선택)
```

> **참고**: 이 파일들이 없어도 대부분의 게임은 UnityPy로 번역 가능합니다.
> 자세한 내용은 `lib/SETUP.txt` 파일을 참고하세요.

### 3단계: 프로그램 실행

```bash
# GUI 실행
run_gui.bat

# 또는
python gui/main_window.py
```

---

## 📖 게임 번역 사용법 (GUI)

### 1️⃣ 게임 폴더 선택 및 프로젝트 생성
1. **"번역"** 탭에서 **"게임 폴더 선택"** 클릭
2. 게임이 설치된 폴더 선택 (예: `game_folder/`)
3. 게임 형식 자동 감지 (RPG Maker, Unity, Naninovel 등)
4. 프로젝트 자동 생성 또는 선택

### 2️⃣ 번역 실행
1. **번역 엔진 선택** (Claude Haiku 3.5 권장)
2. **원본 언어/대상 언어** 설정
3. **배치 크기** 설정 (10개씩 권장)
4. **"번역 시작 (미리보기)"** 클릭
5. `projects/[게임명]/preview/` 폴더에 번역 결과 저장

> **자동으로 처리되는 것들:**
> - 게임 형식 감지 (RPG Maker JSON, Unity Asset, Naninovel 스크립트)
> - 패턴 감지 및 API 비용 절감
> - 사전 시스템 (고유명사, 화자명, 감탄사)
> - 민감한 단어 처리 및 조사 교정

### 3️⃣ 번역 검수 (Excel 검수 탭)
#### 방법 1: 뷰어에서 직접 검수
1. **"번역 결과 불러오기"** 클릭
2. 검색/페이징으로 원하는 항목 찾기 (페이지당 50개)
3. **"수정본"** 컬럼에서 직접 수정
4. **"수정 사항 저장"** 클릭

#### 방법 2: Excel로 검수
1. **"Excel 내보내기"** 클릭
2. Excel에서 **"수정본"** 컬럼 수정
3. **"수정본 Excel 가져오기"** 클릭
4. 뷰어에서 변경사항 확인 (연두색 강조)
5. **"수정 사항 저장"** 클릭

### 4️⃣ 게임에 적용
1. **"번역"** 탭에서 **"게임에 적용하기"** 클릭
2. 원본 자동 백업 후 번역 적용

> **RPG Maker**: JSON 파일 직접 교체
> **Unity/Naninovel**: Asset Bundle 또는 스크립트 교체

### 5️⃣ 게임 실행
- **RPG Maker**: 게임 실행 → 한국어로 표시
- **Unity (Naninovel)**: 게임 설정에서 대체한 언어 선택
- **Steam 게임**: 게임 속성 → 언어를 대체한 언어로 설정

---

## 🎮 지원하는 게임 형식

### ✅ 자동 감지 및 번역 지원

| 게임 형식 | 지원 여부 | 추출 방식 | 비고 |
|----------|---------|----------|------|
| **RPG Maker MV/MZ** | ✅ 완벽 지원 | JSON 파일 (Map*.json, CommonEvents.json 등) | 이벤트 대사, 선택지, 화자명, 시스템 메시지 |
| **Unity (Naninovel)** | ✅ 지원 | .nani 스크립트 파일 | 대사, 주석, 언어별 폴더 |
| **일반 Unity 게임** | ✅ 기본 지원 | UnityPy (data.unity3d, .assets) | TextAsset 교체 방식 |
| **Ren'Py** | 🔜 향후 지원 | - | - |

**모든 게임은 GUI에서 동일한 방법으로 번역됩니다!**

**번역 엔진 선택** (GUI 설정 탭에서):

| 엔진 | 비용 | 품질 | API 키 필요 |
|------|------|------|-------------|
| **Claude Haiku 3.5** | 저렴 (1M tokens: $0.8/$4) | 최고 | ✅ (권장) |
| **Claude Sonnet 3.5** | 고가 (1M tokens: $3/$15) | 최고 | ✅ |
| Google Translate | 무료 | 중 | ❌ |

---

## ⚙️ 설정

### API 키 설정

#### Claude API (추천)
1. [Anthropic Console](https://console.anthropic.com/)에서 API Key 발급
2. GUI: `설정` → `API 설정` → Claude API Key 입력
3. 비용: Claude 3.5 Haiku ($1/$5 per 1M tokens), Sonnet ($3/$15 per 1M tokens)

#### DeepL API
1. [DeepL API](https://www.deepl.com/pro-api)에서 API Key 발급
2. GUI: `설정` → `API 설정` → DeepL API Key 입력
3. 비용: 월 500,000자 무료, 이후 유료

#### Google Translate
- API Key 불필요
- 완전 무료
- 인터넷 연결만 있으면 사용 가능

### 번역 규칙 설정

`examples/translation_rules_ja_ko.yaml`을 `config/`로 복사하여 커스터마이징

```yaml
# 기본 규칙 예시
target_language: "한국어"
source_language: "일본어"

rules:
  - 존댓말/반말 일관성 유지
  - 고유명사는 번역하지 않음
  - 게임 용어는 통일
  - 자연스러운 한국어 표현 사용
  - {name}, [item] 등 게임 태그는 그대로 유지
```

**지원 언어 쌍:**
- `translation_rules_ja_ko.yaml` - 일본어 → 한국어
- `translation_rules_en_ko.yaml` - 영어 → 한국어
- `translation_rules_zh_ko.yaml` - 중국어 → 한국어

### 용어집 설정

`examples/glossary_ja_ko.json`을 `config/`로 복사하여 고유명사 관리

```json
{
  "고유명사": {
    "プレイヤー": "플레이어",
    "モンスター": "몬스터"
  },
  "게임 용어": {
    "レベル": "레벨",
    "スキル": "스킬",
    "クエスト": "퀘스트"
  }
}
```

---

## 📁 프로젝트 구조

```
gametranslator/
├── gui/                       # PyQt6 GUI (메인 인터페이스)
│   ├── main_window.py         # 메인 윈도우
│   ├── widgets/               # UI 위젯
│   │   └── translation_viewer.py  # 번역 검수 뷰어 (페이징, 검색)
│   ├── dialogs/               # 다이얼로그
│   ├── workers/               # 백그라운드 작업
│   │   └── translation_worker.py  # 번역 워커 (사전, 패턴 감지)
│   ├── managers/              # 프로젝트/세션 관리
│   ├── handlers/              # Excel 검수 처리
│   │   └── excel_handler.py   # Excel 내보내기/가져오기
│   └── ui/                    # UI 빌더
│       └── tab_builder.py     # 탭 생성
├── core/                      # 핵심 번역 엔진
│   ├── translator.py          # AI 번역 엔진 (민감한 단어 처리)
│   ├── rpgmaker_extractor.py  # RPG Maker JSON 추출
│   ├── excel_manager.py       # Excel 검수 관리
│   ├── game_language_detector.py  # 게임 형식 감지
│   ├── korean_particle_fixer.py   # 한국어 조사 교정
│   └── settings_manager.py    # 설정 관리
├── config/                    # 설정 파일 (사용자가 수정)
│   └── dicts/                 # 번역 사전
│       ├── proper_nouns.json  # 고유명사 (111개)
│       ├── speaker_names.json # 화자명 (88개)
│       ├── interjections.json # 감탄사 (59개)
│       └── sensitive_terms.json # 민감한 단어 (141개)
├── examples/                  # 번역 규칙 및 용어집 예시
│   ├── translation_rules_*.yaml
│   └── glossary_*.json
└── utils/                     # 유틸리티
    └── game_detector.py       # 게임 형식 감지 유틸
```

> **참고**: `config/`, `projects/` 폴더는 Git에 커밋되지 않습니다 (사용자 설정 및 작업 파일).

---

## 🛡️ 백업 및 복원

### 자동 백업
게임 적용 시 원본 파일이 자동으로 백업됩니다:
- **RPG Maker**: `[게임 폴더]_backup/` 폴더에 data 폴더 백업
- **Unity/Naninovel**: Asset Bundle 또는 스크립트 파일 백업

### 수동 복원
백업 폴더의 파일을 원본 위치로 복사하여 복원합니다.

---

## 🐛 문제 해결

### ❌ GUI가 실행되지 않을 때
```bash
pip install -r requirements.txt
python --version  # 3.10 이상인지 확인
```

### 📦 설치 시 의존성 충돌 오류
**증상**: `pip install -r requirements.txt` 실행 시 `anthropic`과 `httpx` 관련 오류
```
ERROR: Cannot install anthropic and googletrans...
```

**원인**: 이전 버전의 requirements.txt 사용 중

**해결**:
```bash
# 1. 최신 코드로 업데이트
git pull

# 2. 기존 패키지 제거 후 재설치
pip uninstall googletrans deep-translator -y
pip install -r requirements.txt

# 3. 또는 새 가상환경에서 재설치
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**참고**: Google Translate는 `requests` 라이브러리를 통해 직접 API를 호출하므로 별도 패키지가 필요 없습니다.

### 🌐 게임이 번역된 언어로 안 나올 때
**가장 흔한 원인**: 게임 언어 설정이 잘못됨

**해결 방법**:
1. **Steam**: 게임 우클릭 → 속성 → 언어 → **교체한 언어 선택**
   - 예: 중국어를 교체했으면 "Chinese (Simplified)" 선택
2. 게임 재시작
3. 여전히 안 되면 게임 내 설정에서 언어 변경

### ✏️ 번역이 이상하거나 오역이 있을 때
1. **Excel 검수 사용**: "검수" 탭 → Excel 내보내기 → 수정 → 가져오기
2. **번역 규칙 추가**: `config/translation_rules_ja_ko.yaml` 파일 수정
3. **용어집 설정**: `config/glossary_ja_ko.json`에 고유명사 추가

### 🔍 "번역 가능한 텍스트를 찾을 수 없습니다" 오류
- 게임 폴더가 올바른지 확인 (Game.exe가 있는 폴더)
- 게임 형식이 지원되는지 확인 (RPG Maker MV/MZ, Unity 등)
- 일부 게임은 특수한 암호화로 번역 불가능할 수 있음

---

## ⚠️ 주의사항

1. **게임 언어 설정**: 번역을 적용한 언어로 게임 언어를 설정해야 함
2. **백업 필수**: 게임 적용 전 자동 백업되지만, 게임 폴더 전체 백업 권장
3. **Steam 무결성 검사**: Steam 게임 무결성 검사 시 원본으로 복구됨
4. **API 키 보안**: API 키는 암호화되어 저장되지만 절대 공유하지 말 것
5. **비용 주의**: Claude/DeepL은 유료 서비스 (사용량에 따라 과금)

---

## 💡 비용 절감 및 품질 향상 팁

### 번역 비용 줄이기
- **Translation Memory 사용**: 같은 문장은 한 번만 번역 (자동 활성화)
- **Haiku 모델 선택**: Sonnet보다 5배 저렴 (설정 → 번역 엔진)
- **패턴 감지 활용**: 5회 이상 반복되는 패턴 자동 절감 (자동 활성화)
- **사전 시스템**: config/dicts/에 자주 쓰는 용어 추가
- **배치 크기 증가**: 10개씩 또는 50개씩 설정 (API 호출 감소)

### 번역 품질 향상
- **Excel 검수**: 검수 탭에서 번역 확인 및 수정
- **번역 규칙 설정**: examples/translation_rules_ja_ko.yaml 참고
- **용어집 활용**: config/glossary_ja_ko.json에 고유명사 등록
- **조사 자동 교정**: 한국어 조사(이/가, 을/를) 자동 처리

---

## 📝 라이선스

개인 사용 목적으로만 사용하세요.

## 🙏 크레딧

- **UnityPy**: Unity Asset Bundle 추출/패킹
- **Claude API (Anthropic)**: AI 번역
- **PyQt6**: GUI 프레임워크
- **openpyxl**: Excel 파일 처리
