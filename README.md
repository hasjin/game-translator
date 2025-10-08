# 🎮 Game Translator

Unity 게임 자동 번역 및 게임 적용 도구 (GUI 기반)

## ✨ 주요 기능

### 🖥️ GUI로 모든 게임 번역 (클릭만으로!)
- **Unity Bundle 추출**: Asset Bundle에서 게임 스크립트 자동 추출
- **AI 자동 번역**: Claude API를 사용한 고품질 번역
- **Excel 검수**: Excel로 번역 내보내기/수정/가져오기
- **게임 적용**: 번역을 게임 Asset Bundle에 자동 패키징 및 교체
- **번역 메모리**: 중복 번역 방지 및 일관성 유지
- **품질 관리**: 번역 규칙 및 용어집 관리

### 🎮 지원하는 게임
- **Unity 게임**: 완벽 지원 하려고 노력중 ✅
- **RPG Maker**: 향후 지원 예정 🔜
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

### 1️⃣ 프로젝트 생성
1. **"새 프로젝트"** 탭에서 프로젝트 이름 입력
2. **게임 폴더 선택** - 게임이 설치된 폴더 선택 (예: `C:\Program Files\Steam\steamapps\common\YourGame`)
3. **"프로젝트 생성"** 클릭 → 게임 구조 자동 분석

### 2️⃣ 번역 실행
1. **"번역"** 탭에서 번역 옵션 설정
2. **"번역 시작"** 클릭 → 자동으로 대사 파일 찾아서 번역
3. `preview` 폴더에 번역 결과 저장

> **자동으로 처리되는 것들:**
> - 게임 내 대사/텍스트 파일 자동 검색
> - Asset Bundle, Unity 패키지 구조 자동 감지
> - 번역 가능한 모든 텍스트 추출

### 3️⃣ Excel 검수 (선택사항)
1. **"검수"** 탭에서 **"Excel 내보내기"**
2. Excel 파일 열어서 **"수정본"** 열에 수정 내용 입력
3. **"Excel 가져오기"**로 수정 반영

### 4️⃣ 게임에 적용
1. **"적용"** 탭 선택
2. **대체할 언어 선택** (예: 중국어 간체 → 이 언어 파일을 한국어로 교체)
3. **"게임에 적용"** 클릭 → 원본 자동 백업 후 번역 적용

### 5️⃣ 게임 실행
- **Steam 게임**: 게임 속성 → 언어를 **대체한 언어**로 설정
  - 예: 중국어를 교체했다면 → "Chinese (Simplified)" 선택
- **일반 게임**: 게임 설정에서 해당 언어 선택

---

## 🎮 지원하는 게임 형식

### ✅ 자동 감지 및 번역 지원

| 게임 형식 | 지원 여부 | 비고 |
|----------|---------|------|
| **Unity 게임** | ✅ 완벽 지원 | Asset Bundle, 패키지 구조 자동 감지 |
| **RPG Maker** | 🔜 향후 지원 | - |
| **Ren'Py** | 🔜 향후 지원 | - |

**모든 게임은 GUI에서 동일한 방법으로 번역됩니다!**

**번역 엔진 선택** (GUI 설정 탭에서):

| 엔진 | 비용 | 품질 | API 키 필요 |
|------|------|------|-------------|
| Google Translate | 무료 | 중 | ❌ |
| DeepL | 유료 (월 500,000자 무료) | 고 | ✅ |
| Claude | 유료 (사용량 기반) | 최고 | ✅ |

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
├── gui/                  # PyQt6 GUI (메인 인터페이스)
│   ├── main_window.py    # 메인 윈도우
│   ├── dialogs/          # 다이얼로그
│   ├── workers/          # 백그라운드 작업
│   ├── managers/         # 프로젝트/세션 관리
│   └── handlers/         # Excel 검수 처리
├── core/                 # 핵심 번역 엔진
│   ├── translator.py     # AI 번역 엔진
│   ├── bundle_packer.py  # Bundle 패킹
│   ├── excel_manager.py  # Excel 검수
│   ├── game_language_detector.py  # 게임 구조 감지
│   ├── naninovel.py      # 게임 엔진 파서
│   └── settings_manager.py  # 설정 관리
├── cli/                  # 내부 도구 (GUI에서 호출)
│   ├── extractor.py      # 텍스트 추출
│   ├── translator.py     # 번역 엔진 래퍼
│   └── patcher.py        # 게임 패치
├── security/             # 보안 모듈
│   ├── secure_storage.py # API 키 암호화
│   └── secure_config.py  # 보안 설정
├── tools/                # 개발 도구
│   ├── analytics_dashboard.py
│   └── batch_compare.py
├── examples/             # 번역 규칙 및 용어집 예시
│   ├── translation_rules_*.yaml
│   └── glossary_*.json
├── config/               # 사용자 설정 (gitignore)
├── lib/                  # 외부 라이브러리 (선택사항)
│   ├── SETUP.txt         # 설치 가이드
│   ├── AssetsTools.NET.dll (gitignore)
│   └── classdata.tpk   (gitignore)
└── archive/              # 개발 아카이브 (gitignore)
```

> **참고**: `lib/` 폴더의 외부 파일들은 Git에 커밋되지 않습니다. 필요시 위 [2단계: 외부 도구 설치](#2단계-외부-도구-설치-선택사항)를 참고하세요.

---

## 🛡️ 백업 및 복원

### 자동 백업
- 게임 적용 시 원본 파일 자동 백업
  - Asset Bundle: `backups/bundle_backup_[timestamp]/`
  - 기타 파일: `게임_Data_backup/`

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

또는 수동으로:
```bash
cp backups/bundle_backup_*/[bundle_name].bundle [game_path]/
```

---

## 🐛 문제 해결

### ❌ GUI가 실행되지 않을 때
```bash
pip install -r requirements.txt
python --version  # 3.10 이상인지 확인
```

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
- 게임이 특수한 암호화를 사용 중일 가능성
- AssetsTools.NET 설치 후 재시도 (위 [2단계](#2단계-외부-도구-설치-선택사항) 참고)
- 일부 게임은 번역 불가능할 수 있음

---

## ⚠️ 주의사항

1. **게임 언어 설정**: 번역을 적용한 언어로 게임 언어를 설정해야 함
2. **백업 필수**: 게임 적용 전 자동 백업되지만, 게임 폴더 전체 백업 권장
3. **Steam 무결성 검사**: Steam 게임 무결성 검사 시 원본으로 복구됨
4. **API 키 보안**: API 키는 암호화되어 저장되지만 절대 공유하지 말 것
5. **비용 주의**: Claude/DeepL은 유료 서비스 (사용량에 따라 과금)

---

## 💡 비용 절감 팁

### 번역 비용 줄이기
- **Translation Memory 사용**: 같은 문장은 한 번만 번역 (자동 활성화)
- **Haiku 모델 선택**: Sonnet보다 10배 저렴 (설정 → 번역 엔진)
- **챕터별 번역**: 필요한 챕터만 선택해서 번역

### 번역 속도 높이기
- 작은 챕터부터 번역 테스트
- 배치 번역 자동 적용 (20개씩 묶어서 처리)
- CPU 코어 수만큼 자동 병렬 처리

---

## 📝 라이선스

개인 사용 목적으로만 사용하세요.

## 🙏 크레딧

- **UnityPy**: Unity Asset Bundle 추출/패킹
- **AssetsTools.NET**: 일반 Unity 게임 지원
- **Claude API (Anthropic)**: AI 번역
- **PyQt6**: GUI 프레임워크
