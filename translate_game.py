"""
Unity 게임 번역 파이프라인
전체 프로세스 통합
"""
import argparse
from pathlib import Path
import json
import time
from cli.extractor import UnityTextExtractor
from cli.translator import get_engine
from cli.patcher import UnityPatcher


def extract_texts(game_path: Path, output_path: Path):
    """텍스트 추출"""
    print("\n" + "="*80)
    print("Step 1: Text Extraction")
    print("="*80)

    extractor = UnityTextExtractor(game_path)
    entries = extractor.extract()

    extractor.save(output_path)
    print(f"\nExtracted {len(entries)} translatable texts")

    return extractor


def translate_texts(input_path: Path, output_path: Path, engine_type: str = "google", api_key: str = None):
    """텍스트 번역"""
    print("\n" + "="*80)
    print("Step 2: Translation")
    print("="*80)

    # 추출된 텍스트 로드
    extractor = UnityTextExtractor.load(input_path)
    print(f"Loaded {len(extractor.entries)} entries")

    # 번역 엔진 초기화
    engine = get_engine(engine_type, api_key)
    print(f"Using translation engine: {engine_type}")

    # 번역 (배치 처리)
    texts_to_translate = [entry.text for entry in extractor.entries]
    print(f"Translating {len(texts_to_translate)} texts...")

    start_time = time.time()

    try:
        # 배치로 번역
        batch_size = 50
        all_translations = []

        for i in range(0, len(texts_to_translate), batch_size):
            batch = texts_to_translate[i:i+batch_size]
            print(f"  Translating batch {i//batch_size + 1}/{(len(texts_to_translate)-1)//batch_size + 1}...")

            translations = engine.translate_batch(batch, source_lang="en", target_lang="ko")
            all_translations.extend(translations)

            time.sleep(1)  # Rate limiting

        # 번역 결과 적용
        for entry, translation in zip(extractor.entries, all_translations):
            entry.translated = translation

        elapsed = time.time() - start_time
        print(f"\nTranslation completed in {elapsed:.1f} seconds")

        # 저장
        extractor.save(output_path)
        print(f"Saved translations to {output_path}")

        return extractor

    except Exception as e:
        print(f"Translation error: {e}")
        import traceback
        traceback.print_exc()
        return None


def apply_patches(game_path: Path, translations_path: Path, backup: bool = True):
    """패치 적용"""
    print("\n" + "="*80)
    print("Step 3: Apply Patches")
    print("="*80)

    # 번역 로드
    extractor = UnityTextExtractor.load(translations_path)
    print(f"Loaded {len(extractor.entries)} translations")

    # 번역된 항목만 필터링
    translated_entries = [e for e in extractor.entries if e.translated]
    print(f"Applying {len(translated_entries)} translated entries")

    # 패처 초기화
    patcher = UnityPatcher(game_path, backup=backup)

    # 패치 적용
    success = patcher.apply_patches(translated_entries)

    if success:
        print("\n✓ Patch applied successfully!")
    else:
        print("\n✗ Patch failed")

    return success


def full_pipeline(game_path: Path, output_dir: Path, engine_type: str = "google", api_key: str = None, backup: bool = True):
    """전체 파이프라인 실행"""
    print("\n" + "="*80)
    print(f"Unity Game Translation Pipeline")
    print(f"Game: {game_path}")
    print(f"Engine: {engine_type}")
    print("="*80)

    output_dir.mkdir(exist_ok=True, parents=True)

    # Step 1: Extract
    extracted_path = output_dir / "extracted.json"
    extractor = extract_texts(game_path, extracted_path)

    if len(extractor.entries) == 0:
        print("\n✗ No translatable texts found")
        return False

    # Step 2: Translate
    translated_path = output_dir / "translated.json"
    extractor = translate_texts(extracted_path, translated_path, engine_type, api_key)

    if extractor is None:
        print("\n✗ Translation failed")
        return False

    # Step 3: Patch
    success = apply_patches(game_path, translated_path, backup)

    return success


def main():
    parser = argparse.ArgumentParser(description="Unity Game Translator")
    parser.add_argument("command", choices=["extract", "translate", "patch", "full"], help="Command to execute")
    parser.add_argument("path", type=Path, help="Path to game Data folder or input file")
    parser.add_argument("--output", "-o", type=Path, default=Path("translations"), help="Output directory")
    parser.add_argument("--engine", "-e", choices=["google", "deepl", "mock"], default="google", help="Translation engine")
    parser.add_argument("--api-key", "-k", help="API key for DeepL")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--input", "-i", type=Path, help="Input file for patch command")

    args = parser.parse_args()

    if args.command == "extract":
        output_path = args.output / "extracted.json"
        extract_texts(args.path, output_path)

    elif args.command == "translate":
        output_path = args.output / "translated.json"
        translate_texts(args.path, output_path, args.engine, args.api_key)

    elif args.command == "patch":
        if not args.input:
            print("Error: --input required for patch command")
            return

        apply_patches(args.path, args.input, backup=not args.no_backup)

    elif args.command == "full":
        full_pipeline(args.path, args.output, args.engine, args.api_key, backup=not args.no_backup)


if __name__ == "__main__":
    main()
