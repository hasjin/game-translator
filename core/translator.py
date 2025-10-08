"""범용 Claude 번역기

어떤 게임/포맷이든 사용 가능한 범용 번역 엔진
"""
from anthropic import Anthropic
import os
from typing import List, Dict, Optional
import yaml
from pathlib import Path


class UniversalTranslator:
    """범용 번역기 (다국어 지원)"""

    def __init__(
        self,
        rules_file: Optional[str] = None,
        glossary_file: Optional[str] = None,
        source_lang: str = "일본어",
        target_lang: str = "한국어"
    ):
        """
        Args:
            rules_file: 번역 규칙 YAML 파일 경로
            glossary_file: 용어집 YAML 파일 경로
            source_lang: 원본 언어 (일본어, 영어, 중국어 등)
            target_lang: 대상 언어 (한국어, 영어 등)
        """
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-haiku-20241022"

        # 언어 설정
        self.source_lang = source_lang
        self.target_lang = target_lang

        # 번역 규칙 로드
        self.rules = self._load_rules(rules_file)
        self.glossary = self._load_glossary(glossary_file)

        # 시스템 프롬프트 생성
        self.system_prompt = self._build_system_prompt()

    def _load_rules(self, rules_file: Optional[str]) -> dict:
        """번역 규칙 로드"""
        if rules_file and Path(rules_file).exists():
            # 규칙 파일 경로를 저장 (_build_system_prompt에서 사용)
            return {"file": rules_file}

        # 기본 규칙 (파일이 없을 때)
        return {}

    def _load_glossary(self, glossary_file: Optional[str]) -> dict:
        """용어집 로드"""
        if glossary_file and Path(glossary_file).exists():
            with open(glossary_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('terms', {})
        return {}

    def _build_system_prompt(self) -> str:
        """시스템 프롬프트 생성 (캐시 최적화)"""
        # 번역 규칙 파일이 있으면 로드
        rules_content = ""
        if self.rules and 'file' in self.rules:
            rules_file = Path(self.rules['file'])
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_content = f.read()

        # 규칙 파일이 있으면 그걸 사용, 없으면 기본 프롬프트
        if rules_content:
            prompt = rules_content
        else:
            # 언어별 이름 처리 규칙
            name_rules = {
                "일본어": "일본인 이름은 **원음 그대로** 한글로 표기",
                "중국어": "중국인 이름은 **원음 그대로** 한글로 표기",
                "영어": "서양인 이름은 한국식 통용 표기를 따름",
            }

            # 언어별 자연스러운 번역 예시
            natural_examples = {
                "일본어": """- 의문사: なんで → 왜 (절대 "뭐래" 아님!)
   - 말더듬기: な、なんで → 어, 어째서 / 왜, 왜
   - 인용 표현: だって → ~라고 (O), ~래 (X)
   - 감탄사: あれ → 어라?/어?/저거? (절대 "허", "거참" 아님!)
   - 놀람/의문: あれ、この音って → 어라, 이 소리는? / 어? 이 소리 뭐야?""",
                "중국어": """- 자연스러운 구어체 유지
   - 한국어 관용구로 자연스럽게 변환""",
                "영어": """- 자연스러운 한국어로 의역
   - 문화적 맥락 고려"""
            }

            prompt = f"""당신은 {self.source_lang}→{self.target_lang} 게임 번역 전문가입니다.

**번역 규칙:**

1. **인명 처리 (최우선!)**:
   - {name_rules.get(self.source_lang, "인명은 원음 한글 표기")}
"""

            # 자연스러운 번역
            prompt += f"""
2. **자연스러운 {self.target_lang}**:
   - 직역 금지, 문맥 파악 필수
{natural_examples.get(self.source_lang, "   - 자연스러운 번역 우선")}

3. **말투 보존**:
   - 캐릭터 특성에 맞는 말투 유지
   - 귀여운 표현, 우아한 어투, 거친 말투 등 구분

4. **태그 보존**:
   - __BR0__, __BR1__ 같은 플레이스홀더 유지
   - <br>, <ruby> 등 태그 그대로

5. **출력 형식**:
   - 번호와 번역만 출력 (설명 없이)
   - 예: 1. 번역문1
        2. 번역문2
"""

        # 용어집 추가 (별도 섹션으로, 캐시 효율성)
        if self.glossary:
            prompt += "\n\n---\n\n**용어집 (필수 준수!)**:\n\n"
            for src, tgt in self.glossary.items():
                prompt += f"- {src} → {tgt}\n"

        return prompt

    def translate_batch(
        self,
        texts: List[str],
        context: Optional[List[str]] = None
    ) -> List[str]:
        """배치 번역

        Args:
            texts: 번역할 텍스트 리스트
            context: 문맥 정보 (이전 대사 등)

        Returns:
            번역된 텍스트 리스트
        """
        # 빈 줄 필터링 (인덱스 기억)
        non_empty_indices = []
        non_empty_texts = []

        for i, text in enumerate(texts):
            if text.strip():  # 빈 줄이 아닌 경우만
                non_empty_indices.append(i)
                non_empty_texts.append(text)

        # 모두 빈 줄이면 그대로 반환
        if not non_empty_texts:
            return texts

        # 번역 요청 구성 (빈 줄 제외)
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(non_empty_texts)])

        user_prompt = f"다음 {self.source_lang} 대사를 {self.target_lang}로 번역하세요:\n\n{numbered_texts}"

        # 문맥 추가
        if context:
            context_text = "\n".join([f"- {c}" for c in context])
            user_prompt = f"**이전 문맥:**\n{context_text}\n\n{user_prompt}"

        # Claude API 호출
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=[
                {
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # 응답 파싱
        result_text = response.content[0].text
        translations = []

        for line in result_text.strip().split('\n'):
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                parts = line.split('.', 1)
                if len(parts) == 2:
                    translation = parts[1].strip()
                    # 빈 줄도 포함 (Claude가 빈 번호로 응답할 수 있음)
                    translations.append(translation)

        # 번역 개수가 맞지 않으면 경고 후 원문 채우기
        if len(translations) != len(non_empty_texts):
            print(f"⚠️ 번역 개수 불일치: 요청 {len(non_empty_texts)}, 응답 {len(translations)}")
            print(f"응답:\n{result_text}")
            # 부족한 부분은 원문 유지
            while len(translations) < len(non_empty_texts):
                translations.append(non_empty_texts[len(translations)])

        # 원래 위치에 번역 삽입 (빈 줄은 빈 줄로 유지)
        result = []
        translation_idx = 0

        for i, text in enumerate(texts):
            if i in non_empty_indices:
                result.append(translations[translation_idx])
                translation_idx += 1
            else:
                result.append(text)  # 빈 줄 그대로

        return result

    def clean_ruby_tags(self, text: str) -> str:
        """Ruby 태그 제거"""
        import re
        # <ruby="reading">kanji</ruby> → kanji
        text = re.sub(r'<ruby="[^"]*">([^<]+)</ruby>', r'\1', text)
        return text

    def restore_placeholders(self, text: str, placeholders: dict) -> str:
        """플레이스홀더 복원"""
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)
        return text


def create_translator_from_config(config_path: str) -> UniversalTranslator:
    """설정 파일로부터 번역기 생성

    Args:
        config_path: 프로젝트 설정 파일 경로

    Returns:
        UniversalTranslator 인스턴스
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    rules_file = config.get('translation_rules')
    glossary_file = config.get('glossary')

    return UniversalTranslator(rules_file, glossary_file)
