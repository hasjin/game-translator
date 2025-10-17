"""백그라운드 번역 작업 워커"""
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal


class TranslationWorker(QThread):
    """백그라운드 번역 작업"""
    progress = pyqtSignal(int, str)  # (진행률, 메시지)
    finished = pyqtSignal(str, dict, list, int)  # (완료 메시지, 비용 정보, 번역 엔트리 리스트, 새로 번역한 파일 수)
    error = pyqtSignal(str)  # 오류 메시지

    def __init__(self, input_dir, output_dir, engine, source_lang, target_lang, selected_chapters=None, preview_mode=True, batch_size=1):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.engine = engine
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.selected_chapters = selected_chapters  # 선택된 챕터 리스트
        self.preview_mode = preview_mode  # 미리보기 모드 (임시 폴더에만 저장)
        self.batch_size = batch_size  # 배치 크기 (1, 10, 50, 100)
        self.total_tokens = {"input": 0, "output": 0}
        self.total_cost = 0.0
        self.translation_entries = []  # 번역 항목 리스트
        self.game_type = None  # 게임 타입 ('naninovel', 'unity_generic', 'unity_other')

    def _extract_from_bundles(self, bundle_files, output_path):
        """번들 파일에서 텍스트 추출 (선택된 챕터만)"""
        import UnityPy
        from pathlib import Path

        extracted_files = []

        print(f"Starting bundle extraction from {len(bundle_files)} bundles")
        print(f"Selected chapters: {self.selected_chapters}")

        # 선택된 챕터에 해당하는 번들만 필터링
        bundles_to_extract = []
        for bundle_file in bundle_files:
            if self.selected_chapters:
                full_path = str(bundle_file).lower()
                for chapter in self.selected_chapters:
                    if chapter.lower() in full_path:
                        bundles_to_extract.append(bundle_file)
                        print(f"  ✓ Bundle matched: {bundle_file.name} (chapter: {chapter})")
                        break
            else:
                bundles_to_extract.append(bundle_file)

        print(f"Bundles to extract: {len(bundles_to_extract)}")

        # 추출 폴더 생성
        extract_dir = output_path / "_extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        for bundle_file in bundles_to_extract:
            try:
                print(f"Processing bundle: {bundle_file.name}")
                env = UnityPy.load(str(bundle_file))

                text_assets_found = 0
                for obj in env.objects:
                    if obj.type.name == "TextAsset":
                        text_assets_found += 1
                        data = obj.read()

                        # 텍스트 데이터 추출
                        text_content = None
                        try:
                            # m_Script가 bytes인 경우
                            if isinstance(data.m_Script, bytes):
                                text_content = data.m_Script.decode('utf-8')
                            # m_Script가 문자열인 경우
                            elif isinstance(data.m_Script, str):
                                text_content = data.m_Script
                            # script 또는 text 속성 시도
                            elif hasattr(data, 'script'):
                                text_content = str(data.script)
                            elif hasattr(data, 'text'):
                                text_content = str(data.text)
                            else:
                                # 다른 인코딩 시도
                                text_content = data.m_Script.decode('utf-8-sig')
                        except Exception as decode_err:
                            print(f"  ⚠ Failed to decode {data.m_Name}: {type(data.m_Script)} - {str(decode_err)}")
                            continue

                        if not text_content:
                            print(f"  ⚠ Empty content for {data.m_Name}")
                            continue

                        # 파일명 생성 (번들명 기반)
                        bundle_name = bundle_file.stem.replace('.bundle', '')
                        output_file = extract_dir / f"{data.m_Name or bundle_name}.txt"

                        # 저장
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(text_content)

                        extracted_files.append(output_file)
                        print(f"  ✓ Extracted: {output_file.name}")

                print(f"  Found {text_assets_found} TextAssets in {bundle_file.name}")

            except Exception as e:
                print(f"  ✗ Failed to process bundle {bundle_file.name}: {str(e)}")
                continue

        print(f"Total extracted files: {len(extracted_files)}")
        return extracted_files

    def run(self):
        try:
            from core.translator import UniversalTranslator
            from core.game_language_detector import GameLanguageDetector
            from security.secure_storage import SecureStorage
            import os

            self.progress.emit(3, "게임 형식 감지 중...")

            # 게임 형식 감지
            input_path = Path(self.input_dir)
            detector = GameLanguageDetector()
            format_info = detector.detect_game_format(input_path)
            self.game_type = format_info.get('game_type', 'unknown')

            print(f"🎮 게임 형식: {self.game_type}")
            print(f"   - Naninovel: {format_info.get('is_naninovel', False)}")

            # RPG Maker 게임 처리
            if self.game_type == 'rpgmaker':
                self.progress.emit(5, "RPG Maker 게임 감지됨")
                return self._translate_rpgmaker_game()

            # 일반 Unity 게임 처리
            if self.game_type in ['unity_generic', 'unity_other']:
                self.progress.emit(5, "일반 Unity 게임 감지됨")
                return self._translate_general_unity_game()

            self.progress.emit(5, "API 키 확인 중...")

            # API 키 로드
            storage = SecureStorage()
            api_key = storage.get_api_key("claude")

            if not api_key and "Claude" in self.engine:
                self.error.emit("❌ Claude API 키가 설정되지 않았습니다!\n\n설정 → API 키 설정에서 API 키를 입력하세요.")
                return

            # API 키 환경변수로 설정
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key

            self.progress.emit(10, "파일 스캔 중...")

            # 파일 목록 가져오기
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 지원하는 파일 확장자
            files = []
            for ext in ['*.txt', '*.nani', '*.json', '*.csv']:
                found = list(input_path.glob(f"**/{ext}"))
                files.extend(found)
                if found:
                    print(f"Found {len(found)} {ext} files")

            # 번들 파일 확인 (게임 폴더인 경우)
            bundle_files = list(input_path.glob("**/*.bundle"))
            if bundle_files:
                print(f"Found {len(bundle_files)} bundle files")

            if not files and bundle_files:
                # 번들 파일에서 추출
                self.progress.emit(8, "Unity 번들 파일 감지됨, 추출 중...")

                try:
                    files = self._extract_from_bundles(bundle_files, output_path)
                    if not files:
                        self.error.emit("❌ 번들 파일에서 텍스트를 추출할 수 없습니다!")
                        return
                    self.progress.emit(10, f"{len(files)}개 파일 추출 완료")
                except Exception as e:
                    self.error.emit(f"❌ 번들 추출 실패: {str(e)}")
                    return

            # 챕터 필터링
            if self.selected_chapters:
                original_count = len(files)
                filtered_files = []
                for file_path in files:
                    file_name = file_path.name
                    full_path = str(file_path).lower()

                    # 이미 번역된 파일 제외
                    if any(x in file_name for x in ["_KOREAN", "_KO", "_CLAUDE"]):
                        continue

                    # 선택된 챕터에 속하는지 확인 (파일명 + 경로)
                    for chapter in self.selected_chapters:
                        chapter_lower = chapter.lower()
                        if chapter_lower in file_name.lower() or chapter_lower in full_path:
                            filtered_files.append(file_path)
                            print(f"  ✓ Matched: {file_path.name} (chapter: {chapter})")
                            break

                files = filtered_files
                print(f"Chapter filtering: {original_count} → {len(files)} files")

                # 필터링 후 파일이 없으면 경고
                if not files and bundle_files:
                    print(f"No text files matched chapters, trying bundles...")
                    self.progress.emit(8, "텍스트 파일 없음, Unity 번들에서 추출 시도...")
                    try:
                        files = self._extract_from_bundles(bundle_files, output_path)
                        if files:
                            print(f"Extracted {len(files)} files from bundles")
                            # 추출된 파일에 다시 챕터 필터링 적용
                            filtered_files = []
                            for file_path in files:
                                for chapter in self.selected_chapters:
                                    if chapter.lower() in str(file_path).lower():
                                        filtered_files.append(file_path)
                                        break
                            files = filtered_files
                            print(f"After filtering extracted files: {len(files)} files")
                    except Exception as e:
                        print(f"Bundle extraction failed: {str(e)}")

                self.progress.emit(12, f"챕터 필터링: {original_count}개 → {len(files)}개")
            else:
                # 챕터 선택 안 됨 - 이미 번역된 파일만 제외
                original_count = len(files)
                files = [f for f in files if not any(x in f.name for x in ["_KOREAN", "_KO", "_CLAUDE"])]
                print(f"Excluding translated files: {original_count} → {len(files)} files")

            if not files:
                print(f"ERROR: No files to translate in {input_path}")
                print(f"Total files found before filtering: {len(files)}")
                self.error.emit("❌ 번역할 파일을 찾을 수 없습니다!\n\n입력 폴더에 원본 파일이 있는지 확인하세요.\n이미 번역된 파일(_KOREAN, _KO, _CLAUDE)은 제외됩니다.")
                return

            self.progress.emit(15, f"{len(files)}개 파일 발견")

            # 번역기 초기화 (선택된 언어로)
            translator = UniversalTranslator(
                rules_file="config/translation_rules.yaml",
                glossary_file="config/glossary.yaml",
                source_lang=self.source_lang,
                target_lang=self.target_lang
            )

            self.progress.emit(20, "번역 시작...")

            print(f"🚀 번역 루프 시작")
            print(f"   번역할 파일 수: {len(files)}")
            print(f"   출력 경로: {output_path}")

            # 파일별 번역
            translated_count = 0
            skipped_count = 0

            for i, file_path in enumerate(files):
                progress_pct = 20 + int((i / len(files)) * 75)
                self.progress.emit(progress_pct, f"번역 중: {file_path.name} ({i+1}/{len(files)})")
                print(f"📄 처리 중: {file_path.name} ({i+1}/{len(files)})")

                try:
                    # 이미 번역된 파일이 있는지 확인 (출력 경로에 동일한 파일명이 존재하는지)
                    if "_extracted" in str(file_path):
                        parts = Path(file_path).parts
                        extracted_idx = parts.index("_extracted")
                        relative_parts = parts[extracted_idx + 1:]
                        relative_path = Path(*relative_parts) if relative_parts else Path(file_path.name)
                    else:
                        try:
                            relative_path = file_path.resolve().relative_to(input_path.resolve())
                        except ValueError:
                            relative_path = Path(file_path.name)

                    output_file = output_path / relative_path

                    # 출력 파일이 이미 존재하면 건너뛰기
                    if output_file.exists():
                        print(f"⏭️ 건너뛰기 (이미 번역됨): {file_path.name}")
                        skipped_count += 1

                        # 건너뛴 파일의 번역 엔트리도 로드 (Excel 내보내기용)
                        try:
                            with open(output_file, 'r', encoding='utf-8') as f:
                                translated_lines = f.readlines()

                            with open(file_path, 'r', encoding='utf-8') as f:
                                original_lines = f.readlines()

                            from core.excel_manager import TranslationEntry

                            # 일본어 주석에서 원문 추출
                            for idx, line in enumerate(original_lines):
                                stripped = line.strip()

                                # 주석(일본어 원문) 발견
                                if stripped.startswith(';') and not stripped.startswith('; >') and not stripped.startswith('; 日本語'):
                                    japanese_text = stripped[1:].strip()  # '; ' 제거

                                    if japanese_text:
                                        # 번역 파일의 대응하는 라인 찾기 (idx+1부터 시작)
                                        korean_idx = idx + 1
                                        while korean_idx < len(translated_lines):
                                            korean_line = translated_lines[korean_idx].strip()
                                            # 빈 줄이나 주석/메타데이터가 아니면 한국어 번역
                                            if korean_line and not korean_line.startswith('#') and not korean_line.startswith(';'):
                                                entry = TranslationEntry(
                                                    file_path=str(file_path),
                                                    line_number=korean_idx + 1,
                                                    japanese=japanese_text,
                                                    translation=korean_line
                                                )
                                                self.translation_entries.append(entry)
                                                break
                                            korean_idx += 1

                        except Exception as e:
                            print(f"⚠️ 건너뛴 파일 엔트리 로드 실패: {file_path.name} - {str(e)}")

                        continue

                    # 파일 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # 번역할 라인 수집 (주석의 일본어 원문 추출)
                    texts_to_translate = []  # 일본어 원문
                    line_indices = []  # 덮어쓸 중국어 라인 인덱스 (시작, 끝)
                    japanese_originals = []  # Excel용 일본어 원문

                    for idx, line in enumerate(lines):
                        stripped = line.strip()

                        # 주석(;로 시작)이면서 메타데이터가 아닌 경우 (일본어 원문)
                        if stripped.startswith(';') and not stripped.startswith('; >') and not stripped.startswith('; 日本語'):
                            # 주석 제거하고 일본어 원문만 추출
                            japanese_text = stripped[1:].strip()  # '; ' 제거

                            if japanese_text:  # 빈 주석이 아니면
                                # 다음 줄부터 시작해서 중국어 번역이 몇 줄인지 찾기
                                chinese_start = idx + 1
                                chinese_end = chinese_start

                                # 다음 #이나 ; 또는 빈 줄이 나올 때까지 중국어 라인 찾기
                                while chinese_end < len(lines):
                                    line_content = lines[chinese_end].strip()
                                    # 빈 줄이거나 #이나 ;로 시작하면 중단
                                    if not line_content or line_content.startswith('#') or line_content.startswith(';'):
                                        break
                                    chinese_end += 1

                                # 중국어 라인이 있으면 추가
                                if chinese_end > chinese_start:
                                    texts_to_translate.append(japanese_text)
                                    line_indices.append((chinese_start, chinese_end))  # (시작, 끝) 튜플
                                    japanese_originals.append(japanese_text)

                    if not texts_to_translate:
                        continue

                    # 배치 번역
                    translated_lines = []

                    if self.batch_size == 1:
                        # 개별 번역 (기존 방식)
                        for text in texts_to_translate:
                            translated = translator.translate(text)
                            translated_lines.append(translated)

                            # 토큰 정보 수집 (추정)
                            self.total_tokens["input"] += len(text) * 2
                            self.total_tokens["output"] += len(translated) * 2
                    else:
                        # 배치 번역 (10개, 50개, 100개씩)
                        for batch_start in range(0, len(texts_to_translate), self.batch_size):
                            batch = texts_to_translate[batch_start:batch_start + self.batch_size]
                            translated_batch = translator.translate_batch(batch)
                            translated_lines.extend(translated_batch)

                            # 토큰 정보 수집 (추정)
                            self.total_tokens["input"] += sum(len(t) * 2 for t in batch)
                            self.total_tokens["output"] += sum(len(t) * 2 for t in translated_batch)

                    # 번역 엔트리 생성 (Excel 내보내기용)
                    from core.excel_manager import TranslationEntry
                    for idx_range, original, translated in zip(line_indices, japanese_originals, translated_lines):
                        # idx_range는 (start, end) 튜플
                        chinese_start, chinese_end = idx_range
                        entry = TranslationEntry(
                            file_path=str(file_path),
                            line_number=chinese_start + 1,  # Excel에는 첫 번째 중국어 라인 번호 표시
                            japanese=original,
                            translation=translated
                        )
                        self.translation_entries.append(entry)

                    # 번역된 내용으로 중국어 라인 덮어쓰기
                    for idx_range, translated in zip(line_indices, translated_lines):
                        chinese_start, chinese_end = idx_range

                        # 첫 번째 중국어 라인을 한국어 번역으로 교체
                        lines[chinese_start] = translated + '\n'

                        # 나머지 중국어 라인들은 삭제 (빈 줄로 표시)
                        for i in range(chinese_start + 1, chinese_end):
                            lines[i] = ''

                    # 출력 파일 저장
                    # 번들 추출 파일인 경우 (_extracted 폴더 내)
                    if "_extracted" in str(file_path):
                        # _extracted 이후 경로만 사용
                        parts = Path(file_path).parts
                        extracted_idx = parts.index("_extracted")
                        relative_parts = parts[extracted_idx + 1:]
                        relative_path = Path(*relative_parts) if relative_parts else Path(file_path.name)
                    else:
                        # 일반 파일은 입력 폴더 기준 상대 경로
                        try:
                            relative_path = file_path.resolve().relative_to(input_path.resolve())
                        except ValueError:
                            # 상대 경로 계산 실패 시 파일명만 사용
                            relative_path = Path(file_path.name)

                    output_file = output_path / relative_path
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

                    translated_count += 1

                except Exception as e:
                    print(f"⚠️ 파일 번역 실패: {file_path.name} - {str(e)}")
                    continue

            # 비용 계산
            cost_info = self.calculate_cost()

            print(f"🎉 번역 루프 완료")
            print(f"   번역한 파일: {translated_count}개")
            print(f"   건너뛴 파일: {skipped_count}개")
            print(f"   총 파일: {len(files)}개")

            self.progress.emit(100, "번역 완료!")

            # 완료 메시지 생성
            total_files = len(files)
            if self.preview_mode:
                message = f"✅ 번역 완료 (미리보기)\n\n"
                message += f"📊 총 {total_files}개 파일:\n"
                message += f"   - ✅ 새로 번역: {translated_count}개\n"
                if skipped_count > 0:
                    message += f"   - ⏭️ 건너뛰기 (이미 번역됨): {skipped_count}개\n"
                message += f"\n📁 임시 폴더: {self.output_dir}\n\n"
                message += f"✅ 확인 후 '게임에 적용하기' 버튼을 눌러주세요."
            else:
                message = f"✅ 번역 완료\n\n"
                message += f"📊 총 {total_files}개 파일:\n"
                message += f"   - ✅ 새로 번역: {translated_count}개\n"
                if skipped_count > 0:
                    message += f"   - ⏭️ 건너뛰기 (이미 번역됨): {skipped_count}개\n"
                message += f"\n📁 출력: {self.output_dir}"

            self.finished.emit(message, cost_info, self.translation_entries, translated_count)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR: {error_detail}")
            self.error.emit(f"❌ 오류 발생:\n{str(e)}")

    def _find_patterns(self, texts: list, min_count: int = 5) -> dict:
        """반복 패턴 찾기 (숫자가 포함된 텍스트)"""
        import re
        from collections import defaultdict

        pattern_map = defaultdict(list)

        for text in texts:
            if re.search(r'\d+', text):  # 숫자 포함된 경우만
                pattern = re.sub(r'\d+', '{NUM}', text)
                numbers = re.findall(r'\d+', text)
                pattern_map[pattern].append({
                    'text': text,
                    'numbers': numbers
                })

        # min_count 이상만 필터링
        return {
            p: items for p, items in pattern_map.items()
            if len(items) >= min_count
        }

    def _load_dictionary(self, dict_path: str) -> dict:
        """사전 파일 로드"""
        import json
        from pathlib import Path

        path = Path(dict_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 사전 로드 실패: {dict_path} - {str(e)}")
                return {}
        return {}

    def calculate_cost(self):
        """API 사용 비용 계산"""
        cost_info = {
            "engine": self.engine,
            "input_tokens": self.total_tokens["input"],
            "output_tokens": self.total_tokens["output"],
            "total_cost": 0.0,
            "currency": "USD"
        }

        # 엔진별 가격 (per 1M tokens)
        pricing = {
            "Claude Haiku 3.5": {"input": 1.0, "output": 5.0},
            "Claude Sonnet 4": {"input": 3.0, "output": 15.0},
            "ChatGPT-4o": {"input": 2.5, "output": 10.0},
            "ChatGPT-4o-mini": {"input": 0.15, "output": 0.60},
        }

        for engine_key, prices in pricing.items():
            if engine_key in self.engine:
                input_cost = (self.total_tokens["input"] / 1_000_000) * prices["input"]
                output_cost = (self.total_tokens["output"] / 1_000_000) * prices["output"]
                cost_info["total_cost"] = input_cost + output_cost
                break

        return cost_info

    def _translate_general_unity_game(self):
        """일반 Unity 게임 번역 처리 (cli 도구 사용)"""
        try:
            from cli.extractor import UnityTextExtractor
            from core.translator import UniversalTranslator
            from security.secure_storage import SecureStorage
            import os

            input_path = Path(self.input_dir)
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 1. 텍스트 추출
            self.progress.emit(10, "Unity 게임에서 텍스트 추출 중...")
            print(f"📦 Extracting from: {input_path}")

            extractor = UnityTextExtractor(input_path)
            entries = extractor.extract()

            if not entries or len(entries) == 0:
                self.error.emit(
                    "❌ 번역 가능한 텍스트를 찾을 수 없습니다.\n\n"
                    "가능한 원인:\n"
                    "- 게임이 IL2CPP로 컴파일됨\n"
                    "- 텍스트가 암호화되어 있음\n"
                    "- 지원하지 않는 Unity 버전"
                )
                return

            self.progress.emit(20, f"{len(entries)}개 텍스트 항목 발견")
            print(f"✅ Found {len(entries)} translatable texts")

            # 2. API 키 확인
            self.progress.emit(25, "API 키 확인 중...")
            storage = SecureStorage()

            api_key = None
            if "Claude" in self.engine:
                api_key = storage.get_api_key("claude")
                if not api_key:
                    self.error.emit("❌ Claude API 키가 설정되지 않았습니다!")
                    return
                os.environ["ANTHROPIC_API_KEY"] = api_key

            # 3. 기존 번역 로드 (번역 메모리)
            existing_json = output_path / "extracted_translated.json"
            existing_translations = {}

            if existing_json.exists():
                self.progress.emit(28, "기존 번역 로드 중...")
                try:
                    import json
                    with open(existing_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    for entry_data in data.get('entries', []):
                        original_text = entry_data.get('text', '')
                        translated_text = entry_data.get('translated', '')
                        if original_text and translated_text:
                            existing_translations[original_text] = translated_text

                    print(f"✅ 기존 번역 {len(existing_translations)}개 로드됨")
                except Exception as e:
                    print(f"⚠️ 기존 번역 로드 실패: {str(e)}")

            # 4. 번역
            self.progress.emit(30, f"{len(entries)}개 항목 번역 시작...")

            translator = UniversalTranslator(
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                engine=self.engine
            )

            translated_count = 0
            skipped_count = 0

            for i, entry in enumerate(entries):
                try:
                    progress_pct = 30 + int((i / len(entries)) * 60)
                    self.progress.emit(progress_pct, f"번역 중... ({i+1}/{len(entries)})")

                    # 기존 번역 확인
                    if entry.text in existing_translations:
                        entry.translated = existing_translations[entry.text]
                        skipped_count += 1
                        continue

                    # 새로운 항목만 번역
                    translation = translator.translate(entry.text)
                    entry.translated = translation
                    translated_count += 1

                    # 토큰 및 비용 누적
                    if hasattr(translator, 'last_usage'):
                        usage = translator.last_usage
                        self.total_tokens["input"] += usage.get("input_tokens", 0)
                        self.total_tokens["output"] += usage.get("output_tokens", 0)

                    # 주기적으로 저장
                    if (i + 1) % 10 == 0:
                        extractor.entries = entries
                        extractor.save(output_path / "extracted_translated.json")

                except Exception as e:
                    print(f"⚠️ Translation error: {str(e)}")
                    continue

            # 4. 최종 저장
            self.progress.emit(90, "번역 결과 저장 중...")
            extractor.entries = entries
            extractor.save(output_path / "extracted_translated.json")

            # 5. translation_entries 생성 (Excel 내보내기용)
            self.progress.emit(88, "엑셀 데이터 생성 중...")
            translation_entries = []
            for entry in entries:
                if entry.translated:
                    translation_entries.append({
                        'file': entry.context.get('file', 'unknown'),
                        'original': entry.text,
                        'translated': entry.translated,
                        'context': entry.context
                    })

            # 6. 게임에 적용 (preview_mode가 아닌 경우)
            if not self.preview_mode:
                self.progress.emit(92, "게임 파일에 번역 적용 중...")

                from cli.patcher import UnityPatcher

                # 백업 생성 후 패치 적용
                patcher = UnityPatcher(input_path, backup=True)
                success = patcher.apply_patches(entries)

                if success:
                    apply_msg = "\n✅ 게임 파일에 번역이 적용되었습니다!"
                else:
                    apply_msg = "\n⚠️ 게임 파일 적용 중 일부 오류 발생"
            else:
                apply_msg = "\n💡 '게임에 적용하기' 버튼을 눌러 게임에 적용하세요."

            # 7. 비용 계산
            cost_info = self.calculate_cost()

            # 8. 완료 메시지
            completion_msg = (
                f"✅ 일반 Unity 게임 번역 완료!\n\n"
                f"📊 새로 번역: {translated_count}개\n"
                f"⏭️ 건너뛰기 (기존 번역): {skipped_count}개\n"
                f"📝 총 항목: {len(entries)}개\n"
                f"💰 비용: ${cost_info['total_cost']:.4f}\n\n"
                f"📁 저장 위치: {output_path}{apply_msg}"
            )

            self.progress.emit(100, "완료")
            self.finished.emit(completion_msg, cost_info, translation_entries, translated_count)

        except Exception as e:
            import traceback
            self.error.emit(f"❌ Unity 게임 번역 실패:\n{str(e)}\n\n{traceback.format_exc()}")

    def _translate_rpgmaker_game(self):
        """RPG Maker 게임 번역 처리"""
        try:
            from core.rpgmaker_extractor import RPGMakerDialogueExtractor
            from core.translator import UniversalTranslator
            from security.secure_storage import SecureStorage
            import os
            import json

            input_path = Path(self.input_dir)
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 1. 대사 추출
            self.progress.emit(10, "RPG Maker 대사 추출 중...")
            print(f"📦 RPG Maker 게임에서 대사 추출 중: {input_path}")

            extractor = RPGMakerDialogueExtractor(input_path)
            dialogues = extractor.extract_all()

            if not dialogues or len(dialogues) == 0:
                self.error.emit(
                    "❌ 번역 가능한 대사를 찾을 수 없습니다.\n\n"
                    "가능한 원인:\n"
                    "- data 폴더가 없거나 Map 파일이 없음\n"
                    "- JSON 파일 형식이 올바르지 않음"
                )
                return

            self.progress.emit(20, f"{len(dialogues)}개 대사 발견")
            print(f"✅ {len(dialogues)}개 대사 추출 완료")

            # 2. API 키 확인
            self.progress.emit(25, "API 키 확인 중...")
            storage = SecureStorage()

            api_key = None
            if "Claude" in self.engine:
                api_key = storage.get_api_key("claude")
                if not api_key:
                    self.error.emit("❌ Claude API 키가 설정되지 않았습니다!")
                    return
                os.environ["ANTHROPIC_API_KEY"] = api_key

            # 3. 기존 번역 로드 (번역 메모리)
            existing_json = output_path / "extracted_translated.json"
            existing_translations = {}

            if existing_json.exists():
                self.progress.emit(28, "기존 번역 로드 중...")
                try:
                    with open(existing_json, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)

                    for entry in existing_data:
                        original_text = entry.get('original', '')
                        translated_text = entry.get('translated', '')
                        if original_text and translated_text:
                            existing_translations[original_text] = translated_text

                    print(f"✅ 기존 번역 {len(existing_translations)}개 로드됨")
                except Exception as e:
                    print(f"⚠️ 기존 번역 로드 실패: {str(e)}")

            # 4. 번역
            self.progress.emit(30, f"{len(dialogues)}개 대사 번역 시작...")

            translator = UniversalTranslator(
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                engine=self.engine
            )

            translated_count = 0
            skipped_count = 0

            # 고유한 텍스트만 추출 (중복 제거)
            unique_texts = {}
            for dialogue in dialogues:
                text = dialogue['original']
                if text not in unique_texts:
                    unique_texts[text] = None

            print(f"📊 고유 대사: {len(unique_texts)}개 (전체 {len(dialogues)}개)")

            # 패턴 감지 (5회 이상 반복)
            self.progress.emit(30, "반복 패턴 감지 중...")
            patterns = self._find_patterns(list(unique_texts.keys()), min_count=5)
            pattern_hits = 0

            if patterns:
                print(f"🔍 {len(patterns)}개 패턴 발견 (5회 이상 반복)")
                # 패턴별 번역
                for pattern_template, items in patterns.items():
                    # 패턴 템플릿 번역 (예시 숫자 사용)
                    example_text = pattern_template.replace('{NUM}', '10')
                    pattern_translation = translator.translate(example_text)

                    # 숫자를 다시 플레이스홀더로 치환
                    import re
                    pattern_translation = re.sub(r'\d+', '{NUM}', pattern_translation)

                    # 모든 인스턴스에 적용
                    for item in items:
                        original_text = item['text']
                        numbers = item['numbers']

                        # 플레이스홀더를 실제 숫자로 치환
                        translated = pattern_translation
                        for num in numbers:
                            translated = translated.replace('{NUM}', num, 1)

                        unique_texts[original_text] = translated
                        pattern_hits += 1

                print(f"✅ 패턴 번역: {pattern_hits}개 (API 절감: {pattern_hits - len(patterns)}회)")
            else:
                print("ℹ️ 반복 패턴 없음")

            # 사전 로드
            dict_hits = 0
            proper_nouns_dict = self._load_dictionary("config/dicts/proper_nouns.json")
            speaker_dict = self._load_dictionary("config/dicts/speaker_names.json")
            interjection_dict = self._load_dictionary("config/dicts/interjections.json")

            print(f"📚 사전 로드 완료:")
            print(f"   - 고유명사: {len(proper_nouns_dict)}개")
            print(f"   - 화자명: {len(speaker_dict)}개")
            print(f"   - 감탄사: {len(interjection_dict)}개")

            # 사전 적용 (완전 일치 & 부분 치환)
            self.progress.emit(32, "사전 적용 중...")
            all_dicts = {**proper_nouns_dict, **speaker_dict, **interjection_dict}
            partial_dicts = {**proper_nouns_dict, **speaker_dict}  # 감탄사 제외

            texts_need_translation = {}
            for text in unique_texts.keys():
                # 0. 이미 패턴으로 번역된 항목 건너뛰기
                if unique_texts[text] is not None:
                    continue

                # 1. 완전 일치 체크 (모든 사전)
                if text in all_dicts:
                    unique_texts[text] = all_dicts[text]
                    dict_hits += 1
                    continue

                # 2. 부분 치환 (고유명사 + 화자명만)
                text_to_translate = text
                for jp, ko in partial_dicts.items():
                    if jp in text_to_translate and jp != text_to_translate:
                        text_to_translate = text_to_translate.replace(jp, ko)

                # 번역 필요 항목에 추가
                texts_need_translation[text] = text_to_translate

            print(f"📖 사전 적용: {dict_hits}개 (번역 필요: {len(texts_need_translation)}개)")

            # 배치 번역
            texts_list = list(texts_need_translation.items())  # (원본, 치환된 텍스트) 튜플 리스트
            for i in range(0, len(texts_list), self.batch_size):
                batch = texts_list[i:i+self.batch_size]

                # 진행 상황 업데이트
                progress_pct = 35 + int((i / len(texts_list)) * 55)
                self.progress.emit(progress_pct, f"번역 중... ({i}/{len(texts_list)})")

                # 배치 아이템 준비
                batch_originals = []  # 원본 텍스트
                batch_to_translate = []  # 번역할 텍스트 (부분 치환 적용됨)

                for original_text, text_to_translate in batch:
                    # 기존 번역 확인
                    if original_text in existing_translations:
                        unique_texts[original_text] = existing_translations[original_text]
                        skipped_count += 1
                    else:
                        batch_originals.append(original_text)
                        batch_to_translate.append(text_to_translate)

                # 새로운 항목만 번역
                if batch_to_translate:
                    # 성인 콘텐츠 검열 우회 (민감한 단어 있으면)
                    bypass_censorship = any(
                        any(term in text for term in ["おっぱい", "セックス", "ちんぽ", "まんこ", "精液"])
                        for text in batch_to_translate
                    )

                    if self.batch_size == 1 or len(batch_to_translate) == 1:
                        # 개별 번역
                        for original, to_translate in zip(batch_originals, batch_to_translate):
                            translation = translator.translate(to_translate)
                            unique_texts[original] = translation
                            translated_count += 1

                            # 토큰 및 비용 누적
                            if hasattr(translator, 'last_usage'):
                                usage = translator.last_usage
                                self.total_tokens["input"] += usage.get("input_tokens", 0)
                                self.total_tokens["output"] += usage.get("output_tokens", 0)
                    else:
                        # 배치 번역 (검열 우회 옵션 사용)
                        translations = translator.translate_batch(
                            batch_to_translate,
                            bypass_censorship=bypass_censorship
                        )
                        for original, translation in zip(batch_originals, translations):
                            unique_texts[original] = translation
                            translated_count += 1

                        # 토큰 및 비용 누적
                        if hasattr(translator, 'last_usage'):
                            usage = translator.last_usage
                            self.total_tokens["input"] += usage.get("input_tokens", 0)
                            self.total_tokens["output"] += usage.get("output_tokens", 0)

                # 주기적으로 저장 (50개마다)
                if (i + self.batch_size) % 50 == 0:
                    # 번역 적용
                    for dialogue in dialogues:
                        original = dialogue['original']
                        dialogue['translated'] = unique_texts.get(original, '')

                    # 임시 저장
                    temp_file = output_path / "extracted_translated.json"
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(dialogues, f, ensure_ascii=False, indent=2)
                    print(f"💾 중간 저장: {i + self.batch_size}/{len(texts_list)}")

            # 5. 번역 적용
            self.progress.emit(90, "번역 결과 적용 중...")
            for dialogue in dialogues:
                original = dialogue['original']
                dialogue['translated'] = unique_texts.get(original, '')

            # 6. 최종 저장
            self.progress.emit(95, "번역 결과 저장 중...")
            output_file = output_path / "extracted_translated.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dialogues, f, ensure_ascii=False, indent=2)

            print(f"✅ 번역 결과 저장 완료: {output_file}")
            print(f"✅ 번역 결과 저장: {len(dialogues)}개 항목")

            # 7. translation_entries 생성 (Excel 내보내기용)
            self.progress.emit(98, "엑셀 데이터 생성 중...")
            self.translation_entries = dialogues  # RPG Maker는 이미 적절한 형식

            # 8. 비용 계산
            cost_info = self.calculate_cost()

            # 9. 완료 메시지
            completion_msg = (
                f"✅ RPG Maker 게임 번역 완료!\n\n"
                f"📊 새로 번역: {translated_count}개\n"
                f"⏭️ 건너뛰기 (기존 번역): {skipped_count}개\n"
                f"📝 총 대사: {len(dialogues)}개\n"
                f"💰 비용: ${cost_info['total_cost']:.4f}\n\n"
                f"📁 저장 위치: {output_path}\n\n"
                f"💡 'Excel 내보내기'로 검수하거나 '게임에 적용하기'로 게임에 적용하세요."
            )

            self.progress.emit(100, "완료")
            self.finished.emit(completion_msg, cost_info, self.translation_entries, translated_count)

        except Exception as e:
            import traceback
            self.error.emit(f"❌ RPG Maker 게임 번역 실패:\n{str(e)}\n\n{traceback.format_exc()}")
