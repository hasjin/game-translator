"""번역 엔진 (Google Translate, DeepL)"""
import time
from typing import List, Optional
from abc import ABC, abstractmethod
import requests


class TranslationEngine(ABC):
    """번역 엔진 기본 클래스"""

    @abstractmethod
    def translate(self, text: str, source_lang: str = "en", target_lang: str = "ko") -> str:
        pass

    def translate_batch(self, texts: List[str], source_lang: str = "en", target_lang: str = "ko") -> List[str]:
        results = []
        for text in texts:
            try:
                translated = self.translate(text, source_lang, target_lang)
                results.append(translated)
                time.sleep(0.1)
            except Exception as e:
                print(f"Translation error: {e}")
                results.append(text)
        return results


class GoogleTranslateEngine(TranslationEngine):
    """Google Translate 무료 API"""

    def __init__(self):
        self.base_url = "https://translate.googleapis.com/translate_a/single"

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "ko") -> str:
        params = {'client': 'gtx', 'sl': source_lang, 'tl': target_lang, 'dt': 't', 'q': text}
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result and len(result) > 0 and len(result[0]) > 0:
                translated = ''.join([item[0] for item in result[0] if item[0]])
                return translated
            return text
        except Exception as e:
            print(f"Google Translate error: {e}")
            return text


class DeepLEngine(TranslationEngine):
    """DeepL API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2/translate"

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "ko") -> str:
        if not self.api_key:
            raise ValueError("DeepL API key required")

        headers = {'Authorization': f'DeepL-Auth-Key {self.api_key}'}
        data = {'text': [text], 'source_lang': source_lang.upper(), 'target_lang': target_lang.upper()}

        try:
            response = requests.post(self.base_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if 'translations' in result and len(result['translations']) > 0:
                return result['translations'][0]['text']
            return text
        except Exception as e:
            print(f"DeepL error: {e}")
            return text

    def translate_batch(self, texts: List[str], source_lang: str = "en", target_lang: str = "ko") -> List[str]:
        if not self.api_key:
            raise ValueError("DeepL API key required")

        headers = {'Authorization': f'DeepL-Auth-Key {self.api_key}'}
        batch_size = 50
        all_results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            data = {'text': batch, 'source_lang': source_lang.upper(), 'target_lang': target_lang.upper()}
            try:
                response = requests.post(self.base_url, headers=headers, data=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                if 'translations' in result:
                    all_results.extend([t['text'] for t in result['translations']])
                else:
                    all_results.extend(batch)
                time.sleep(0.5)
            except Exception as e:
                print(f"DeepL batch error: {e}")
                all_results.extend(batch)

        return all_results


class MockTranslationEngine(TranslationEngine):
    """테스트용 Mock 엔진"""

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "ko") -> str:
        return f"[KO] {text}"


def get_engine(engine_type: str = "google", api_key: Optional[str] = None) -> TranslationEngine:
    """번역 엔진 생성"""
    if engine_type == "google":
        return GoogleTranslateEngine()
    elif engine_type == "deepl":
        return DeepLEngine(api_key)
    elif engine_type == "mock":
        return MockTranslationEngine()
    else:
        raise ValueError(f"Unknown engine type: {engine_type}")
