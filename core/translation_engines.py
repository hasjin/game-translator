"""멀티 번역 엔진 시스템

Claude, ChatGPT, Google, DeepL, Papago, 로컬 모델 등 지원
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import os
from enum import Enum


class TranslationEngine(Enum):
    """번역 엔진 종류"""
    CLAUDE = "Claude API"
    CLAUDE_SONNET = "Claude Sonnet 4"
    CLAUDE_HAIKU = "Claude Haiku 3.5"
    OPENAI_GPT4 = "ChatGPT-4"
    OPENAI_GPT4O = "ChatGPT-4o"
    OPENAI_GPT35 = "ChatGPT-3.5"
    GOOGLE_TRANSLATE = "Google Translate (무료)"
    DEEPL = "DeepL"
    DEEPL_FREE = "DeepL (무료)"
    PAPAGO = "Papago"
    LOCAL_MODEL = "로컬 모델 (Ollama/LLaMA)"


class BaseTranslator(ABC):
    """번역기 기본 클래스"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "ko") -> str:
        """단일 텍스트 번역"""
        pass

    @abstractmethod
    def translate_batch(self, texts: List[str], source_lang: str = "ja", target_lang: str = "ko") -> List[str]:
        """배치 번역"""
        pass

    @abstractmethod
    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        """비용 추정"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """사용 가능 여부"""
        pass


class ClaudeTranslator(BaseTranslator):
    """Claude API 번역기"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model

        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

        # 번역 규칙 (기본)
        self.system_prompt = kwargs.get('system_prompt', self._default_system_prompt())

    def _default_system_prompt(self) -> str:
        return """당신은 일본어→한국어 게임 번역 전문가입니다.

**번역 규칙:**
1. 일본인 이름은 원음 한글 표기
2. 자연스러운 한국어 (직역 금지)
3. 캐릭터 말투 보존
4. 태그 그대로 유지
5. 번호와 번역만 출력"""

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "ko") -> str:
        return self.translate_batch([text], source_lang, target_lang)[0]

    def translate_batch(self, texts: List[str], source_lang: str = "ja", target_lang: str = "ko") -> List[str]:
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        user_prompt = f"다음 {source_lang} 텍스트를 {target_lang}로 번역하세요:\n\n{numbered_texts}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=[{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_prompt}]
        )

        result_text = response.content[0].text
        translations = []

        for line in result_text.strip().split('\n'):
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                parts = line.split('.', 1)
                if len(parts) == 2:
                    translations.append(parts[1].strip())

        # 부족하면 원문 유지
        while len(translations) < len(texts):
            translations.append(texts[len(translations)])

        return translations

    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        # Haiku 3.5: $0.80 input / $4.00 output per 1M tokens
        # 대략 4 chars = 1 token
        input_tokens = (text_count * avg_length) / 4
        output_tokens = input_tokens  # 대충 비슷
        cost = (input_tokens * 0.80 + output_tokens * 4.00) / 1_000_000
        return cost

    def is_available(self) -> bool:
        return bool(self.api_key or os.environ.get("ANTHROPIC_API_KEY"))


class OpenAITranslator(BaseTranslator):
    """OpenAI/ChatGPT 번역기"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        except ImportError:
            print("⚠️ openai 패키지 필요: pip install openai")
            self.client = None

        self.system_prompt = kwargs.get('system_prompt', "당신은 일본어→한국어 게임 번역 전문가입니다. 자연스러운 한국어로 번역하세요.")

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "ko") -> str:
        return self.translate_batch([text], source_lang, target_lang)[0]

    def translate_batch(self, texts: List[str], source_lang: str = "ja", target_lang: str = "ko") -> List[str]:
        if not self.client:
            return texts

        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        user_prompt = f"다음 일본어를 한국어로 번역하세요:\n\n{numbered_texts}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        result_text = response.choices[0].message.content
        translations = []

        for line in result_text.strip().split('\n'):
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                parts = line.split('.', 1)
                if len(parts) == 2:
                    translations.append(parts[1].strip())

        while len(translations) < len(texts):
            translations.append(texts[len(translations)])

        return translations

    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        # GPT-4o: $2.50 input / $10.00 output per 1M tokens
        input_tokens = (text_count * avg_length) / 4
        output_tokens = input_tokens
        cost = (input_tokens * 2.50 + output_tokens * 10.00) / 1_000_000
        return cost

    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key or os.environ.get("OPENAI_API_KEY"))


class GoogleTranslator(BaseTranslator):
    """Google Translate (무료)"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = "https://translate.googleapis.com/translate_a/single"

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "ko") -> str:
        import requests
        import time

        params = {
            'client': 'gtx',
            'sl': source_lang,
            'tl': target_lang,
            'dt': 't',
            'q': text
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result and len(result) > 0 and len(result[0]) > 0:
                translated = ''.join([item[0] for item in result[0] if item[0]])
                return translated
            return text
        except Exception as e:
            print(f"⚠️ Google Translate 오류: {e}")
            return text

    def translate_batch(self, texts: List[str], source_lang: str = "ja", target_lang: str = "ko") -> List[str]:
        import time

        results = []
        for text in texts:
            try:
                translated = self.translate(text, source_lang, target_lang)
                results.append(translated)
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"⚠️ Google Translate 배치 오류: {e}")
                results.append(text)
        return results

    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        return 0.0  # 무료

    def is_available(self) -> bool:
        return True  # requests는 기본 의존성


class DeepLTranslator(BaseTranslator):
    """DeepL 번역기"""

    def __init__(self, api_key: Optional[str] = None, free_api: bool = False, **kwargs):
        super().__init__(api_key, **kwargs)
        self.free_api = free_api

        try:
            import deepl
            self.translator = deepl.Translator(api_key or os.environ.get("DEEPL_API_KEY"))
        except ImportError:
            print("⚠️ deepl 패키지 필요: pip install deepl")
            self.translator = None

    def translate(self, text: str, source_lang: str = "JA", target_lang: str = "KO") -> str:
        if not self.translator:
            return text

        try:
            result = self.translator.translate_text(text, source_lang=source_lang, target_lang=target_lang)
            return result.text
        except Exception as e:
            print(f"⚠️ DeepL 오류: {e}")
            return text

    def translate_batch(self, texts: List[str], source_lang: str = "JA", target_lang: str = "KO") -> List[str]:
        if not self.translator:
            return texts

        try:
            results = self.translator.translate_text(texts, source_lang=source_lang, target_lang=target_lang)
            return [r.text for r in results]
        except Exception as e:
            print(f"⚠️ DeepL 배치 오류: {e}")
            return texts

    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        # DeepL: $25 per 1M characters (Pro), 무료는 500k/month
        total_chars = text_count * avg_length
        if self.free_api:
            return 0.0
        return (total_chars / 1_000_000) * 25.0

    def is_available(self) -> bool:
        return self.translator is not None


class PapagoTranslator(BaseTranslator):
    """Papago 번역기"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client_id = api_key or os.environ.get("PAPAGO_CLIENT_ID")
        self.client_secret = kwargs.get('client_secret') or os.environ.get("PAPAGO_CLIENT_SECRET")

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "ko") -> str:
        import urllib.request
        import json

        if not self.client_id or not self.client_secret:
            return text

        encText = urllib.parse.quote(text)
        data = f"source={source_lang}&target={target_lang}&text={encText}"
        url = "https://openapi.naver.com/v1/papago/n2mt"

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", self.client_id)
        request.add_header("X-Naver-Client-Secret", self.client_secret)

        try:
            response = urllib.request.urlopen(request, data=data.encode("utf-8"))
            result = json.loads(response.read().decode('utf-8'))
            return result['message']['result']['translatedText']
        except Exception as e:
            print(f"⚠️ Papago 오류: {e}")
            return text

    def translate_batch(self, texts: List[str], source_lang: str = "ja", target_lang: str = "ko") -> List[str]:
        return [self.translate(t, source_lang, target_lang) for t in texts]

    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        # Papago: 10,000자/일 무료, 초과 시 유료
        total_chars = text_count * avg_length
        if total_chars <= 10000:
            return 0.0
        # 초과분 요금 (대략)
        return ((total_chars - 10000) / 10000) * 0.02

    def is_available(self) -> bool:
        return bool(self.client_id and self.client_secret)


class LocalModelTranslator(BaseTranslator):
    """로컬 모델 번역기 (Ollama/LLaMA)"""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama3:8b", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.api_url = kwargs.get('api_url', 'http://localhost:11434')  # Ollama 기본

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "ko") -> str:
        import requests

        prompt = f"다음 일본어를 한국어로 번역하세요: {text}\n\n번역:"

        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={"model": self.model, "prompt": prompt}
            )
            result = response.json()
            return result.get('response', text).strip()
        except Exception as e:
            print(f"⚠️ 로컬 모델 오류: {e}")
            return text

    def translate_batch(self, texts: List[str], source_lang: str = "ja", target_lang: str = "ko") -> List[str]:
        return [self.translate(t, source_lang, target_lang) for t in texts]

    def get_cost_estimate(self, text_count: int, avg_length: int) -> float:
        return 0.0  # 로컬 모델은 무료

    def is_available(self) -> bool:
        import requests
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


class TranslationEngineFactory:
    """번역 엔진 팩토리"""

    @staticmethod
    def create(
        engine: TranslationEngine,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseTranslator:
        """번역 엔진 생성

        Args:
            engine: 번역 엔진 종류
            api_key: API 키
            **kwargs: 추가 설정

        Returns:
            BaseTranslator 인스턴스
        """
        if engine == TranslationEngine.CLAUDE_HAIKU:
            return ClaudeTranslator(api_key, model="claude-3-5-haiku-20241022", **kwargs)
        elif engine == TranslationEngine.CLAUDE_SONNET:
            return ClaudeTranslator(api_key, model="claude-sonnet-4-20250514", **kwargs)
        elif engine == TranslationEngine.OPENAI_GPT4O:
            return OpenAITranslator(api_key, model="gpt-4o", **kwargs)
        elif engine == TranslationEngine.OPENAI_GPT4:
            return OpenAITranslator(api_key, model="gpt-4-turbo", **kwargs)
        elif engine == TranslationEngine.OPENAI_GPT35:
            return OpenAITranslator(api_key, model="gpt-3.5-turbo", **kwargs)
        elif engine == TranslationEngine.GOOGLE_TRANSLATE:
            return GoogleTranslator(**kwargs)
        elif engine == TranslationEngine.DEEPL:
            return DeepLTranslator(api_key, free_api=False, **kwargs)
        elif engine == TranslationEngine.DEEPL_FREE:
            return DeepLTranslator(api_key, free_api=True, **kwargs)
        elif engine == TranslationEngine.PAPAGO:
            return PapagoTranslator(api_key, **kwargs)
        elif engine == TranslationEngine.LOCAL_MODEL:
            return LocalModelTranslator(**kwargs)
        else:
            raise ValueError(f"지원하지 않는 엔진: {engine}")

    @staticmethod
    def get_available_engines() -> List[Dict]:
        """사용 가능한 엔진 목록

        Returns:
            [{'engine': TranslationEngine, 'name': str, 'cost': str, 'available': bool}, ...]
        """
        engines = [
            {
                'engine': TranslationEngine.CLAUDE_HAIKU,
                'name': 'Claude Haiku 3.5 (가성비 최고)',
                'cost': '약 $0.52/1000대사',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.CLAUDE_SONNET,
                'name': 'Claude Sonnet 4 (고품질)',
                'cost': '약 $2.00/1000대사',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.OPENAI_GPT4O,
                'name': 'ChatGPT-4o',
                'cost': '약 $1.25/1000대사',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.OPENAI_GPT35,
                'name': 'ChatGPT-3.5 (저렴)',
                'cost': '약 $0.15/1000대사',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.GOOGLE_TRANSLATE,
                'name': 'Google Translate (무료)',
                'cost': '무료',
                'requires_key': False
            },
            {
                'engine': TranslationEngine.DEEPL_FREE,
                'name': 'DeepL 무료 (500k자/월)',
                'cost': '무료',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.DEEPL,
                'name': 'DeepL Pro',
                'cost': '약 $0.50/1000대사',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.PAPAGO,
                'name': 'Papago (10k자/일 무료)',
                'cost': '제한적 무료',
                'requires_key': True
            },
            {
                'engine': TranslationEngine.LOCAL_MODEL,
                'name': '로컬 모델 (Ollama/LLaMA)',
                'cost': '무료 (로컬)',
                'requires_key': False
            }
        ]

        # 사용 가능 여부 체크
        for engine_info in engines:
            try:
                translator = TranslationEngineFactory.create(engine_info['engine'])
                engine_info['available'] = translator.is_available()
            except:
                engine_info['available'] = False

        return engines


# 사용 예시
if __name__ == "__main__":
    # 1. 사용 가능한 엔진 목록
    engines = TranslationEngineFactory.get_available_engines()
    for e in engines:
        status = "✅" if e['available'] else "❌"
        print(f"{status} {e['name']} - {e['cost']}")

    # 2. 번역 테스트
    translator = TranslationEngineFactory.create(TranslationEngine.CLAUDE_HAIKU)
    result = translator.translate("こんにちは")
    print(f"\n번역 결과: {result}")
