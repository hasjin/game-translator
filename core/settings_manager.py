"""사용자 설정 관리"""
import yaml
from pathlib import Path
from typing import Any, Optional


class SettingsManager:
    """사용자 설정 저장 및 로드"""

    def __init__(self, settings_file: str = "config/settings.yaml"):
        self.settings_file = Path(settings_file)
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self._settings = self._load()

    def _load(self) -> dict:
        """설정 파일 로드"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except:
                return {}
        return {}

    def _save(self):
        """설정 파일 저장"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._settings, f, allow_unicode=True, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """설정 값 저장"""
        self._settings[key] = value
        self._save()

    def get_translation_settings(self) -> dict:
        """번역 관련 설정 가져오기"""
        return {
            'engine': self.get('translation_engine', 'Claude Haiku 3.5'),
            'source_lang': self.get('source_language', '일본어'),
            'target_lang': self.get('target_language', '한국어'),
            'use_tm': self.get('use_translation_memory', True),
            'use_quality': self.get('use_quality_check', True),
            'include_font': self.get('include_font_info', True),
        }

    def save_translation_settings(
        self,
        engine: str,
        source_lang: str,
        target_lang: str,
        use_tm: bool = True,
        use_quality: bool = True,
        include_font: bool = True
    ):
        """번역 설정 저장"""
        self.set('translation_engine', engine)
        self.set('source_language', source_lang)
        self.set('target_language', target_lang)
        self.set('use_translation_memory', use_tm)
        self.set('use_quality_check', use_quality)
        self.set('include_font_info', include_font)
