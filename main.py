"""Unity Game Translator - 메인 실행 파일"""

import sys
import argparse
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.core.config_manager import ConfigManager
from src.extractors.unity_extractor import UnityTextExtractor
from src.translators.translation_engine import TranslationManager
from src.patchers.game_patcher import GamePatcher


def cli_mode():
    """CLI 모드 실행"""
    parser = argparse.ArgumentParser(description="Unity Game Translator - CLI Mode")
    parser.add_argument('command', choices=['extract', 'translate', 'patch'], help='실행할 명령')
    parser.add_argument('--game-path', '-g', required=True, help='게임 경로')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--input', '-i', help='입력 파일 경로')
    parser.add_argument('--engine', '-e', default='google', help='번역 엔진 (google, deepl)')
    parser.add_argument('--lang', '-l', default='ko', help='번역 언어 코드')
    parser.add_argument('--no-backup', action='store_true', help='백업 생성 안 함')

    args = parser.parse_args()

    # 설정 로드
    config = ConfigManager()

    if args.command == 'extract':
        # 텍스트 추출
        print(f"게임에서 텍스트 추출 중: {args.game_path}")
        extractor = UnityTextExtractor(args.game_path)
        texts = extractor.extract_all_texts()

        output_file = args.output or "data/extracted_texts.json"
        extractor.save_extracted_texts(output_file)
        print(f"추출 완료: {len(texts)}개 텍스트 발견")

    elif args.command == 'translate':
        # 번역
        if not args.input:
            print("오류: --input 옵션이 필요합니다 (추출된 텍스트 JSON 파일)")
            return

        print(f"번역 시작: {args.input}")

        # 추출된 텍스트 로드
        import json
        with open(args.input, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)

        # 텍스트만 추출
        texts = list(extracted_data.keys())

        # 번역 엔진 초기화
        cache_file = config.get('translation.cache_file', 'data/translation_cache.json')
        api_key = config.get('translation.deepl_api_key', '')

        translator = TranslationManager(
            engine=args.engine,
            cache_file=cache_file,
            api_key=api_key
        )

        # 비동기 배치 번역
        async def translate_all():
            return await translator.translate_batch(texts, target_lang=args.lang)

        translations = asyncio.run(translate_all())

        # 결과 저장
        output_file = args.output or "data/translations.json"
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        # 캐시 저장
        translator.save_cache()

        print(f"번역 완료: {output_file}")

    elif args.command == 'patch':
        # 패치
        if not args.input:
            print("오류: --input 옵션이 필요합니다 (번역 결과 JSON 파일)")
            return

        print(f"게임 패치 적용 중: {args.game_path}")

        # 패처 초기화
        backup_dir = config.get('patching.backup_dir', 'data/backups')
        patcher = GamePatcher(args.game_path, backup_dir)

        # 번역 데이터 로드
        patcher.load_translations(args.input)

        # 패치 적용
        create_backup = not args.no_backup
        success = patcher.patch_game(create_backup=create_backup)

        if success:
            print("패치 완료!")
        else:
            print("패치 실패")


def gui_mode():
    """GUI 모드 실행"""
    from src.gui.main_window import run_gui
    run_gui()


def main():
    """메인 함수"""
    if len(sys.argv) > 1 and sys.argv[1] in ['extract', 'translate', 'patch']:
        # CLI 모드
        cli_mode()
    else:
        # GUI 모드
        gui_mode()


if __name__ == "__main__":
    main()
