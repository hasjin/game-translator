"""RPG Maker 게임 언어 감지"""
import json
from pathlib import Path
from typing import Dict, Optional


class RPGMakerLanguageDetector:
    """RPG Maker 게임의 원본 언어 감지"""

    def detect_language(self, game_path: Path) -> Dict[str, str]:
        """게임의 원본 언어 감지

        Args:
            game_path: 게임 루트 폴더

        Returns:
            {
                'locale': 'ja_JP',
                'language': '일본어',
                'language_code': 'ja',
                'currency': '円',
                'game_title': '게임 제목'
            }
        """
        result = {
            'locale': 'unknown',
            'language': '알 수 없음',
            'language_code': 'unknown',
            'currency': '',
            'game_title': ''
        }

        system_file = game_path / "data" / "System.json"
        if not system_file.exists():
            return result

        try:
            with open(system_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # locale 정보 읽기
            locale = data.get('locale', '')
            result['locale'] = locale

            # locale에서 언어 추출
            language_map = {
                'ja_JP': ('일본어', 'ja'),
                'ja': ('일본어', 'ja'),
                'en_US': ('영어', 'en'),
                'en': ('영어', 'en'),
                'ko_KR': ('한국어', 'ko'),
                'ko': ('한국어', 'ko'),
                'zh_CN': ('중국어 간체', 'zh'),
                'zh_TW': ('중국어 번체', 'zh'),
            }

            if locale in language_map:
                result['language'], result['language_code'] = language_map[locale]
            elif locale.startswith('ja'):
                result['language'], result['language_code'] = '일본어', 'ja'
            elif locale.startswith('en'):
                result['language'], result['language_code'] = '영어', 'en'
            elif locale.startswith('ko'):
                result['language'], result['language_code'] = '한국어', 'ko'
            elif locale.startswith('zh'):
                result['language'], result['language_code'] = '중국어', 'zh'

            # 통화 단위
            result['currency'] = data.get('currencyUnit', '')

            # 게임 제목
            result['game_title'] = data.get('gameTitle', '')

            # locale이 없으면 대사로 언어 감지
            if not locale or locale == 'unknown':
                result.update(self._detect_from_dialogue(game_path))

            return result

        except Exception as e:
            print(f"[ERROR] System.json 읽기 실패: {e}")
            return result

    def _detect_from_dialogue(self, game_path: Path) -> Dict[str, str]:
        """대사 샘플로 언어 감지"""
        try:
            # Map001.json에서 샘플 추출
            map_file = game_path / "data" / "Map001.json"
            if not map_file.exists():
                return {}

            with open(map_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 대사 샘플 수집
            dialogues = []
            events = [e for e in data.get('events', []) if e]
            for event in events[:5]:  # 처음 5개 이벤트만
                for page in event.get('pages', []):
                    for cmd in page.get('list', []):
                        if cmd.get('code') == 401:  # 대사
                            text = cmd.get('parameters', [''])[0]
                            if text:
                                dialogues.append(text)
                                if len(dialogues) >= 10:
                                    break
                    if len(dialogues) >= 10:
                        break
                if len(dialogues) >= 10:
                    break

            if not dialogues:
                return {}

            # 문자 유니코드 범위로 언어 추측
            sample_text = ''.join(dialogues[:5])

            # 일본어 문자 체크 (히라가나, 카타카나, 한자)
            hiragana = sum(1 for c in sample_text if '\u3040' <= c <= '\u309F')
            katakana = sum(1 for c in sample_text if '\u30A0' <= c <= '\u30FF')
            kanji = sum(1 for c in sample_text if '\u4E00' <= c <= '\u9FFF')

            # 한글 문자 체크
            hangul = sum(1 for c in sample_text if '\uAC00' <= c <= '\uD7AF')

            # 중국어 문자 체크 (간체/번체는 구분 어려움)
            chinese = kanji  # 한자는 중국어일 수도

            total = len(sample_text)
            if total == 0:
                return {}

            # 언어 비율 계산
            ja_ratio = (hiragana + katakana + kanji) / total
            ko_ratio = hangul / total
            zh_ratio = chinese / total if (hiragana + katakana) == 0 else 0

            if ja_ratio > 0.3:
                return {
                    'locale': 'ja',
                    'language': '일본어',
                    'language_code': 'ja'
                }
            elif ko_ratio > 0.3:
                return {
                    'locale': 'ko',
                    'language': '한국어',
                    'language_code': 'ko'
                }
            elif zh_ratio > 0.3:
                return {
                    'locale': 'zh',
                    'language': '중국어',
                    'language_code': 'zh'
                }

            return {}

        except Exception as e:
            print(f"[ERROR] 대사 언어 감지 실패: {e}")
            return {}

    def check_multilang_support(self, game_path: Path) -> Dict[str, any]:
        """다국어 플러그인 지원 여부 확인

        Returns:
            {
                'has_plugin': bool,
                'plugin_name': str,
                'languages_folder_exists': bool,
                'available_languages': list
            }
        """
        result = {
            'has_plugin': False,
            'plugin_name': None,
            'languages_folder_exists': False,
            'available_languages': []
        }

        # 플러그인 폴더 확인
        plugins_folder = game_path / "js" / "plugins"
        if plugins_folder.exists():
            # 다국어 플러그인 패턴
            multilang_patterns = [
                'language',
                'multilang',
                'localization',
                'i18n',
                'translation'
            ]

            for plugin_file in plugins_folder.glob("*.js"):
                name_lower = plugin_file.stem.lower()
                if any(pattern in name_lower for pattern in multilang_patterns):
                    result['has_plugin'] = True
                    result['plugin_name'] = plugin_file.stem
                    break

        # data_languages 폴더 확인
        lang_folder = game_path / "data_languages"
        if lang_folder.exists():
            result['languages_folder_exists'] = True

            # 사용 가능한 언어 목록
            for subfolder in lang_folder.iterdir():
                if subfolder.is_dir():
                    result['available_languages'].append(subfolder.name)

        return result
