"""범용 번역기

어떤 게임/포맷이든 사용 가능한 범용 번역 엔진 (Claude, Google, DeepL 지원)
"""
from anthropic import Anthropic
import os
import json
import re
from typing import List, Dict, Optional
import yaml
from pathlib import Path


class UniversalTranslator:
    """범용 번역기 (다국어 지원, 다중 엔진)"""

    def __init__(
        self,
        rules_file: Optional[str] = None,
        glossary_file: Optional[str] = None,
        source_lang: str = "일본어",
        target_lang: str = "한국어",
        engine: str = "Claude Haiku 3.5",
        model: Optional[str] = None
    ):
        """
        Args:
            rules_file: 번역 규칙 YAML 파일 경로
            glossary_file: 용어집 YAML 파일 경로
            source_lang: 원본 언어 (일본어, 영어, 중국어 등)
            target_lang: 대상 언어 (한국어, 영어 등)
            engine: 번역 엔진 (Claude Haiku 3.5, Google Translate 등)
            model: 모델 ID (선택사항, engine에서 자동 결정)
        """
        # 엔진 설정
        self.engine = engine
        self.source_lang = source_lang
        self.target_lang = target_lang

        # 번역 규칙 로드
        self.rules = self._load_rules(rules_file)
        self.glossary = self._load_glossary(glossary_file)

        # 민감한 단어 사전 로드
        self.sensitive_terms = self._load_sensitive_terms()

        # 토큰 사용량 추적
        self.last_usage = {}

        # 엔진별 초기화
        if "Google" in engine:
            from cli.translator import GoogleTranslateEngine
            self.translator = GoogleTranslateEngine()
            self.is_claude = False
        elif "DeepL" in engine:
            from cli.translator import DeepLEngine
            deepl_key = os.environ.get("DEEPL_API_KEY")
            self.translator = DeepLEngine(api_key=deepl_key)
            self.is_claude = False
        else:  # Claude
            self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            self.model = model or self._get_model_from_engine(engine)
            self.system_prompt = self._build_system_prompt()
            self.is_claude = True
            self.translator = None

    def _get_model_from_engine(self, engine: str) -> str:
        """엔진 이름으로부터 모델 ID 결정"""
        if "Haiku" in engine:
            return "claude-3-5-haiku-20241022"
        elif "Sonnet 4" in engine:
            return "claude-sonnet-4-20250514"
        elif "Sonnet 3.5" in engine:
            return "claude-3-5-sonnet-20241022"
        else:
            return "claude-3-5-haiku-20241022"  # 기본값

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

    def _load_sensitive_terms(self) -> dict:
        """민감한 단어 사전 로드 (검열 우회용)"""
        dict_path = Path("config/dicts/sensitive_terms.json")
        if dict_path.exists():
            with open(dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
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

    def translate(self, text: str) -> str:
        """단일 텍스트 번역

        Args:
            text: 번역할 텍스트

        Returns:
            번역된 텍스트
        """
        if not text or not text.strip():
            return text

        # Google/DeepL 엔진 사용
        if not self.is_claude:
            source_code = self._convert_lang_to_code(self.source_lang)
            target_code = self._convert_lang_to_code(self.target_lang)
            return self.translator.translate(text, source_code, target_code)

        # Claude 사용 (translate_batch 호출)
        result = self.translate_batch([text])
        return result[0] if result else text

    def _convert_lang_to_code(self, lang: str) -> str:
        """언어 이름을 코드로 변환"""
        lang_map = {
            "일본어": "ja",
            "영어": "en",
            "한국어": "ko",
            "중국어": "zh",
            "중국어 간체": "zh-CN",
            "중국어 번체": "zh-TW",
            "자동 감지": "auto"
        }
        return lang_map.get(lang, "auto")

    def _substitute_sensitive_terms(self, text: str) -> tuple:
        """민감한 단어를 플레이스홀더로 치환

        Returns:
            (치환된 텍스트, 플레이스홀더 맵)
        """
        if not self.sensitive_terms:
            return text, {}

        # 원형 숫자 기호
        circle_numbers = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚'

        placeholder_map = {}
        processed_text = text

        for i, (jp_term, ko_term) in enumerate(self.sensitive_terms.items()):
            if jp_term in processed_text:
                placeholder = circle_numbers[i] if i < len(circle_numbers) else f"<T{i}>"
                placeholder_map[placeholder] = ko_term
                processed_text = processed_text.replace(jp_term, placeholder)

        # 연속된 플레이스홀더 사이에 공백 삽입 (번역 품질 향상)
        for i in range(len(circle_numbers) - 1):
            consecutive = circle_numbers[i] + circle_numbers[i+1]
            spaced = circle_numbers[i] + ' ' + circle_numbers[i+1]
            processed_text = processed_text.replace(consecutive, spaced)

        return processed_text, placeholder_map

    def _restore_sensitive_terms(self, text: str, placeholder_map: dict) -> str:
        """플레이스홀더를 한국어로 복원하고 조사 교정"""
        if not placeholder_map:
            return text

        # 플레이스홀더 복원
        result = text
        for placeholder, ko_term in placeholder_map.items():
            result = result.replace(placeholder, ko_term)

        # 조사 교정
        from core.korean_particle_fixer import fix_all_particles
        result = fix_all_particles(result)

        return result

    def translate_batch(
        self,
        texts: List[str],
        context: Optional[List[str]] = None,
        bypass_censorship: bool = False
    ) -> List[str]:
        """배치 번역

        Args:
            texts: 번역할 텍스트 리스트
            context: 문맥 정보 (이전 대사 등)

        Returns:
            번역된 텍스트 리스트
        """
        # Google/DeepL 엔진 사용
        if not self.is_claude:
            source_code = self._convert_lang_to_code(self.source_lang)
            target_code = self._convert_lang_to_code(self.target_lang)
            return self.translator.translate_batch(texts, source_code, target_code)

        # Claude 사용
        # 빈 줄 필터링 및 민감한 단어 치환
        non_empty_indices = []
        non_empty_texts = []
        placeholder_maps = []

        for i, text in enumerate(texts):
            if text.strip():  # 빈 줄이 아닌 경우만
                non_empty_indices.append(i)

                # 민감한 단어 치환
                if bypass_censorship:
                    processed_text, placeholder_map = self._substitute_sensitive_terms(text)
                    non_empty_texts.append(processed_text)
                    placeholder_maps.append(placeholder_map)
                else:
                    non_empty_texts.append(text)
                    placeholder_maps.append({})

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

        # 토큰 사용량 저장
        self.last_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }

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

        # 플레이스홀더 복원 및 조사 교정
        if bypass_censorship:
            for i in range(len(translations)):
                translations[i] = self._restore_sensitive_terms(translations[i], placeholder_maps[i])

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
