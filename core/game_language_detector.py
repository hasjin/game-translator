"""게임 내 사용 가능한 언어 감지"""
from pathlib import Path
from typing import List, Dict
import re


class GameLanguageDetector:
    """게임에서 사용 가능한 언어를 자동 감지"""

    # 언어 코드 매핑
    LANGUAGE_CODES = {
        'ja': '일본어 (Japanese)',
        'ja-JP': '일본어 (Japanese)',
        'en': '영어 (English)',
        'en-US': '영어 (English)',
        'zh-Hans': '중국어 간체 (Chinese Simplified)',
        'zh-CN': '중국어 간체 (Chinese Simplified)',
        'zh-Hant': '중국어 번체 (Chinese Traditional)',
        'zh-TW': '중국어 번체 (Chinese Traditional)',
        'ko': '한국어 (Korean)',
        'ko-KR': '한국어 (Korean)',
    }

    def detect_languages(self, game_path: Path) -> List[Dict[str, str]]:
        """게임 폴더에서 사용 가능한 언어 감지

        Args:
            game_path: 게임 루트 폴더

        Returns:
            언어 정보 리스트 [{'code': 'zh-Hans', 'name': '중국어 간체', 'files': [...]}]
        """
        languages = {}

        # 1. StreamingAssets 폴더에서 bundle 파일 검색
        for sa_folder in game_path.glob("*_Data/StreamingAssets"):
            if sa_folder.exists():
                for file in sa_folder.rglob("*"):
                    if file.is_file():
                        # Asset Bundle (확장자 없거나 .bundle) 또는 일반 파일
                        if not file.suffix or file.suffix in ['.bundle', '.txt', '.asset', '.bytes']:
                            lang_code = self._extract_language_from_filename(file.name)
                            if lang_code:
                                if lang_code not in languages:
                                    languages[lang_code] = {
                                        'code': lang_code,
                                        'name': self.LANGUAGE_CODES.get(lang_code, lang_code),
                                        'files': []
                                    }
                                if str(file) not in languages[lang_code]['files']:
                                    languages[lang_code]['files'].append(str(file))

        # 2. Naninovel 로컬라이제이션 폴더 검색 (추가)
        for loc_folder in game_path.glob("*_Data/StreamingAssets/Naninovel/Localization"):
            if loc_folder.exists() and loc_folder.is_dir():
                for file in loc_folder.rglob("*"):
                    if file.is_file():
                        lang_code = self._extract_language_from_filename(file.name)
                        if lang_code:
                            if lang_code not in languages:
                                languages[lang_code] = {
                                    'code': lang_code,
                                    'name': self.LANGUAGE_CODES.get(lang_code, lang_code),
                                    'files': []
                                }
                            if str(file) not in languages[lang_code]['files']:
                                languages[lang_code]['files'].append(str(file))

        return list(languages.values())

    def _extract_language_from_filename(self, filename: str) -> str:
        """파일명에서 언어 코드 추출

        Examples:
            - general-localization-zhhans-scripts-common_assets_all → zh-Hans
            - text-ja-JP.asset → ja-JP
            - localization_en.txt → en
        """
        # 패턴 1: zhhans, zhcn 등
        if 'zhhans' in filename.lower() or 'zh-hans' in filename.lower():
            return 'zh-Hans'
        if 'zhcn' in filename.lower() or 'zh-cn' in filename.lower():
            return 'zh-Hans'
        if 'zhhant' in filename.lower() or 'zh-hant' in filename.lower():
            return 'zh-Hant'
        if 'zhtw' in filename.lower() or 'zh-tw' in filename.lower():
            return 'zh-Hant'

        # 패턴 2: ja-JP, en-US 등 (하이픈 포함)
        match = re.search(r'-(ja|en|zh|ko)[-_]?([A-Z]{2})?', filename, re.IGNORECASE)
        if match:
            lang = match.group(1).lower()
            country = match.group(2).upper() if match.group(2) else None
            if country:
                return f"{lang}-{country}"
            return lang

        # 패턴 3: 단순 언어 코드 (ja, en, ko 등)
        match = re.search(r'[_-](ja|en|zh|ko)[_-]', filename, re.IGNORECASE)
        if match:
            return match.group(1).lower()

        return None

    def find_target_bundles(self, game_path: Path, language_code: str) -> List[Path]:
        """특정 언어의 Asset Bundle 파일 찾기

        Args:
            game_path: 게임 루트 폴더
            language_code: 대상 언어 코드 (예: 'zh-Hans')

        Returns:
            Asset Bundle 파일 경로 리스트
        """
        bundles = []

        # 언어 코드를 소문자로 변환
        lang_pattern = language_code.lower().replace('-', '')

        # StreamingAssets 폴더에서 검색
        for sa_folder in game_path.glob("*_Data/StreamingAssets"):
            if sa_folder.exists():
                for file in sa_folder.rglob("*"):
                    if file.is_file():
                        # Asset Bundle은 확장자가 없거나 .bundle 확장자를 가짐
                        if not file.suffix or file.suffix == '.bundle':
                            if lang_pattern in file.name.lower():
                                bundles.append(file)

        return bundles


# 사용 예시
if __name__ == "__main__":
    detector = GameLanguageDetector()

    # 테스트
    game_path = Path(r"C:\Your\Game\Path")

    languages = detector.detect_languages(game_path)

    print("감지된 언어:")
    for lang in languages:
        print(f"  - {lang['name']} ({lang['code']}): {len(lang['files'])}개 파일")
