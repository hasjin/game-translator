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

    def detect_game_format(self, game_path: Path) -> Dict[str, any]:
        """게임 형식 감지 (Naninovel 여부 및 상세 구조 분석)

        Args:
            game_path: 게임 루트 폴더

        Returns:
            {
                'is_naninovel': bool,
                'has_streaming_assets': bool,
                'has_language_folders': bool,
                'has_chapter_structure': bool,
                'game_type': str,
                'message': str,
                'details': str
            }
        """
        print("[INFO] Detecting game format: " + str(game_path))

        result = {
            'is_naninovel': False,
            'has_streaming_assets': False,
            'has_language_folders': False,
            'has_chapter_structure': False,
            'game_type': 'unknown',
            'message': '',
            'details': ''
        }

        # RPG Maker 게임 먼저 확인 (Game.exe + data/ + js/)
        rpgmaker_markers = [
            game_path / "Game.exe",
            game_path / "data",
            game_path / "js"
        ]

        if all(marker.exists() for marker in rpgmaker_markers[:2]):  # Game.exe + data/
            print("[OK] RPG Maker game detected")
            result['game_type'] = 'rpgmaker'
            result['message'] = 'RPG Maker 게임 감지됨'
            result['details'] = self._analyze_rpgmaker_game(game_path)
            return result

        # StreamingAssets 폴더 확인
        streaming_assets_folders = list(game_path.glob("*_Data/StreamingAssets"))

        if not streaming_assets_folders:
            result['game_type'] = 'unity_generic'
            result['message'] = '이 게임은 Naninovel 형식이 아닙니다.'
            result['details'] = self._analyze_non_naninovel_game(game_path)
            return result

        result['has_streaming_assets'] = True

        # Naninovel 특정 파일/폴더 확인
        has_naninovel_markers = False
        naninovel_folder = None

        for sa_folder in streaming_assets_folders:
            # Naninovel 마커: Scripts 폴더, .nani 파일, Localization 폴더 등
            naninovel_paths = [
                sa_folder / "Naninovel",
                sa_folder / "Scripts",
            ]

            for path in naninovel_paths:
                if path.exists():
                    has_naninovel_markers = True
                    naninovel_folder = sa_folder
                    break

            # .nani 확장자 파일 검색
            if list(sa_folder.rglob("*.nani")):
                has_naninovel_markers = True
                naninovel_folder = sa_folder
                break

        if has_naninovel_markers:
            result['is_naninovel'] = True
            result['game_type'] = 'naninovel'

            # 언어 폴더 구조 확인
            result['has_language_folders'] = self._check_language_folders(naninovel_folder)

            # 챕터 구조 확인
            result['has_chapter_structure'] = self._check_chapter_structure(naninovel_folder)

            # 상세 메시지 생성
            result['message'] = 'Naninovel 게임 감지됨'
            result['details'] = self._generate_naninovel_details(result)
        else:
            result['game_type'] = 'unity_other'
            result['message'] = '이 게임은 Naninovel 형식이 아닙니다.'
            result['details'] = f'StreamingAssets 폴더는 있지만,\nNaninovel 스크립트 구조가 감지되지 않았습니다.\n\n{self._analyze_non_naninovel_game(game_path)}'

        return result

    def _check_language_folders(self, streaming_assets_folder: Path) -> bool:
        """언어별 폴더 구조가 있는지 확인"""
        if not streaming_assets_folder or not streaming_assets_folder.exists():
            return False

        # Localization 폴더 확인
        localization_folder = streaming_assets_folder / "Naninovel" / "Localization"
        if localization_folder.exists():
            # 언어 코드 폴더가 있는지 확인
            lang_folders = [f for f in localization_folder.iterdir() if f.is_dir()]
            if len(lang_folders) > 0:
                return True

        # 파일명에 언어 코드가 포함된 Bundle 파일 확인
        bundle_files = list(streaming_assets_folder.rglob("*"))
        lang_patterns = ['zh-hans', 'zh-cn', 'ja-jp', 'ja', 'en-us', 'en', 'ko-kr', 'ko']

        for file in bundle_files[:50]:  # 처음 50개만 확인
            filename_lower = file.name.lower()
            if any(pattern in filename_lower for pattern in lang_patterns):
                return True

        return False

    def _check_chapter_structure(self, streaming_assets_folder: Path) -> bool:
        """챕터별 파일 구조가 있는지 확인"""
        if not streaming_assets_folder or not streaming_assets_folder.exists():
            return False

        # Scripts 폴더 확인
        scripts_folder = streaming_assets_folder / "Naninovel" / "Scripts"
        if scripts_folder.exists():
            script_files = list(scripts_folder.glob("*"))
            # 여러 개의 스크립트 파일이 있으면 챕터 구조로 판단
            if len(script_files) > 1:
                return True

        # Bundle 파일에 챕터 패턴 확인 (Act, Chapter, Episode 등)
        bundle_files = list(streaming_assets_folder.rglob("*"))
        chapter_patterns = ['act', 'chapter', 'ch', 'episode', 'ep', 'scene']

        chapter_files = []
        for file in bundle_files[:100]:  # 처음 100개 확인
            filename_lower = file.name.lower()
            if any(pattern in filename_lower for pattern in chapter_patterns):
                chapter_files.append(file)

        return len(chapter_files) > 1

    def _analyze_rpgmaker_game(self, game_path: Path) -> str:
        """RPG Maker 게임 상세 분석"""
        details = []

        details.append("[OK] RPG Maker MV/MZ Game Translation Available")
        details.append("\n[Structure Analysis]")

        data_folder = game_path / "data"

        # Language detection
        from core.rpgmaker_language_detector import RPGMakerLanguageDetector
        lang_detector = RPGMakerLanguageDetector()
        lang_info = lang_detector.detect_language(game_path)

        details.append(f"  [O] Original Language: {lang_info['language']} ({lang_info['locale']})")
        if lang_info['game_title']:
            details.append(f"  [O] Game Title: {lang_info['game_title']}")
        if lang_info['currency']:
            details.append(f"  [O] Currency: {lang_info['currency']}")

        # Map file count
        map_files = list(data_folder.glob("Map*.json"))
        map_files = [f for f in map_files if f.stem != 'MapInfos']
        details.append(f"  [O] Map Files: {len(map_files)} files")

        # CommonEvents check
        if (data_folder / "CommonEvents.json").exists():
            details.append("  [O] CommonEvents.json found")

        # System.json check
        if (data_folder / "System.json").exists():
            details.append("  [O] System.json found")

        details.append("\n[Translation Method]")
        details.append("  1. Auto-extract dialogues from data/ folder")
        details.append("  2. AI translation (Claude/DeepL/Google Translate)")
        details.append("  3. Apply translated text to JSON files")
        details.append("  4. Auto-backup creation")

        details.append("\n[Notes]")
        details.append("  - Original data/ folder will be modified")
        details.append("  - Always backup before proceeding (auto-backed up)")
        details.append("  - Verify dialogues after applying translation")

        return '\n'.join(details)

    def _analyze_non_naninovel_game(self, game_path: Path) -> str:
        """비Naninovel 게임 상세 분석"""
        details = []

        details.append("[✅ 일반 Unity 게임 번역 가능]")
        details.append("\n[구조 분석]")

        # data.unity3d 단일 번들 확인
        has_single_bundle = False
        data_folders = list(game_path.glob("*_Data"))

        if data_folders:
            data_folder = data_folders[0]
            details.append(f"  - 데이터 폴더: {data_folder.name}")

            # 단일 번들 확인
            if (data_folder / "data.unity3d").exists():
                has_single_bundle = True
                details.append("  [O] 단일 번들 파일 (data.unity3d) 발견")
                details.append("      → UnityPy로 텍스트 추출 가능")

            # .resource 파일 확인
            resource_files = list(data_folder.glob("*.resource"))
            if resource_files:
                details.append(f"  [O] Resource 파일: {len(resource_files)}개 발견")
                details.append("      → Resource에서 텍스트 추출 가능")

            # 분할 .assets 파일 확인
            assets_files = list(data_folder.glob("*.assets"))
            if assets_files:
                details.append(f"  [O] Assets 파일: {len(assets_files)}개")
                details.append("      → UnityPy/AssetsTools.NET으로 추출 가능")

        details.append("\n[번역 방법]")
        if has_single_bundle:
            details.append("  1. UnityPy로 텍스트 자동 추출")
        else:
            details.append("  1. 분할 Assets에서 텍스트 자동 추출")
        details.append("  2. AI 번역 (Claude/DeepL/Google Translate)")
        details.append("  3. 번역된 텍스트를 게임 파일에 재적용")
        details.append("  4. 자동 백업 생성")

        details.append("\n[주의사항]")
        details.append("  - 언어 전환 구조가 없으므로 원본 파일 교체")
        details.append("  - 반드시 게임 백업 후 진행 (자동 백업됨)")
        details.append("  - 일부 게임은 IL2CPP로 컴파일되어 추출 불가능")

        return '\n'.join(details)

    def _generate_naninovel_details(self, result: dict) -> str:
        """Naninovel 게임 상세 정보 생성"""
        details = []

        details.append("[OK] Naninovel 게임 지원 가능")
        details.append("\n[구조 분석]")

        if result['has_language_folders']:
            details.append("  [O] 언어별 폴더 구조 있음")
            details.append("      → 언어별 번역 파일 생성 가능")
        else:
            details.append("  [X] 언어별 폴더 구조 없음")
            details.append("      → 기본 언어 파일을 통째로 교체해야 함")

        if result['has_chapter_structure']:
            details.append("  [O] 챕터별 파일 구조 있음")
            details.append("      → 챕터 선택 번역 가능")
        else:
            details.append("  [X] 챕터별 파일 구조 없음")
            details.append("      → 전체 스크립트를 한번에 처리")

        return '\n'.join(details)

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
