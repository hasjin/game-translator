# 🎮 게임 번역기 - 시작 가이드

## 📋 프로젝트 개요

Unity 게임 번역을 위한 GUI 기반 도구입니다.

### 주요 기능
- AI 기반 게임 텍스트 자동 번역
- 챕터별 선택 번역
- Excel 검수 워크플로우
- Translation Memory (비용 절감)

---

## 🚀 빠른 시작

### 1️⃣ 설치
```bash
install.bat
```

### 2️⃣ 실행
```bash
run_gui.bat
```

### 3️⃣ 기본 사용법
1. **게임 폴더 선택**
   - 게임 스크립트 파일이 있는 폴더 선택
   - 자동으로 프로젝트 생성 또는 이전 작업 이어하기

2. **번역 엔진 선택**
   - Claude Haiku 3.5 (빠르고 저렴)
   - Claude Sonnet 4 (고품질)

3. **챕터 감지** (선택사항)
   - 특정 챕터만 번역하려면 감지 후 선택

4. **번역 시작 (미리보기)**
   - preview 폴더에 번역 결과 저장
   - 비용 계산 및 진행상황 표시

5. **게임에 적용하기**
   - 미리보기 확인 후 실제 게임에 적용
   - Excel 파일 자동 생성

---

## 📂 프로젝트 구조

```
gametranslator/
├── gui/
│   └── main_window.py
├── core/
│   ├── translator.py
│   └── excel_manager.py
├── utils/
│   └── secure_storage.py
├── examples/
│   ├── translation_rules.txt
│   └── glossary_example.json
├── projects/
│   └── [게임명]/
│       ├── preview/
│       ├── translated/
│       └── translation_review.xlsx
└── run_translator_gui.py
```

---

## 🎯 번역 워크플로우

### 기본 흐름
```
1. 번역 시작 (미리보기)
   ↓
2. projects/[게임명]/preview/ 에 임시 저장
   ↓
3. 번역 결과 확인
   ↓
4. 게임에 적용하기 클릭
   ↓
5. translated/ 폴더로 복사 + Excel 생성
```

### Excel 검수 워크플로우
```
1. 번역 완료 후 Excel 탭 이동
   ↓
2. Excel 내보내기
   ↓
3. Excel에서 '수정된 번역' 컬럼 수정
   ↓
4. 수정된 Excel 가져오기
   ↓
5. 번역 파일 자동 업데이트
```

---

## ⚙️ 설정 가이드

### API 키 설정
1. [Anthropic Console](https://console.anthropic.com/)에서 API Key 발급
2. GUI에서 `설정` → `API 설정` → Claude API Key 입력

### 번역 규칙 설정
- `설정` → `번역 규칙 편집`
- 인명 처리, 말투 보존 등 커스터마이징 가능

### 용어집 설정
- `설정` → `용어집 편집`
- JSON 형식으로 고유명사 관리

---

## 📊 주요 기능 상세

### 챕터 선택 번역
- Unity Bundle 또는 텍스트 파일에서 챕터 자동 감지
- Act01_Chapter01 패턴 인식
- 여러 챕터 동시 선택 가능

### Translation Memory
- 중복 번역 방지
- 비용 50-80% 절감
- 자동으로 활성화

### 품질 검증
- 태그 보존 확인
- 자연스러운 한국어 검사
- 말투 일관성 체크

### 비용 계산
- 실시간 토큰 사용량 추적
- API 비용 자동 계산
- 원화 환산 표시

---

## 🔧 지원 게임 포맷

### 텍스트 파일
- .txt (Naninovel 등)
- .json
- .csv

### Unity Bundle
- .bundle 파일에서 TextAsset 자동 추출
- 선택된 챕터만 추출

---

## 📚 번역 품질 관리

### 기본 규칙
- 일본어 인명: 원음 한글 표기
- 자연스러운 한국어 표현
- 캐릭터 말투 보존
- 태그 및 플레이스홀더 유지

### 커스터마이징
```yaml
translation_rules.yaml
glossary.yaml
```

---

## 🚨 트러블슈팅

### GUI 실행 안됨
```bash
pip install -r requirements.txt
python --version
```

### 챕터 감지 안됨
- 파일명 또는 폴더명에 Act_Chapter 패턴 포함 확인
- Bundle 파일 우선 처리됨

### 번역 실패
- API 키 확인
- 인터넷 연결 확인
- 로그 확인

---

## ⚡ 성능 최적화

### 비용 절감
- Haiku 3.5 사용 (Sonnet 4 대비 90% 저렴)
- Translation Memory 활성화
- 배치 번역 (10줄씩)

### 속도 향상
- 챕터 선택으로 작업량 감소
- 병렬 처리 자동 활용

---

## 📞 현재 상태

### ✅ 완료 기능
- GUI 기반 번역
- 챕터 감지 및 선택
- 미리보기 + 적용 2단계 프로세스
- Excel 검수 워크플로우
- Unity Bundle 자동 추출
- 프로젝트 기반 작업 관리
- Translation Memory
- 비용 계산

### 🔄 최근 변경
- 프로젝트 관리 UI 간소화
- 번역 → 적용 2단계 분리
- Excel 컬럼 간소화 (상태, 검수자, 검수일 제거)
- 이전 작업 이어하기/새로 시작 다이얼로그 추가

---

**시작하기**: `run_gui.bat` 실행!
