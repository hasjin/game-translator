"""게임 번역기 GUI 메인 윈도우"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QTextEdit, QProgressBar, QComboBox, QMessageBox, QGroupBox, QCheckBox,
    QScrollArea, QSplitter, QFrame, QDialog, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap

# API 설정 다이얼로그 임포트
from gui.api_settings_dialog import APISettingsDialog


class ChapterSelectionDialog(QDialog):
    """챕터 선택 다이얼로그"""
    def __init__(self, chapter_patterns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("챕터 선택")
        self.setMinimumSize(800, 600)

        self.chapter_patterns = chapter_patterns
        self.checkboxes = {}

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 안내 메시지
        info_label = QLabel("번역할 챕터를 선택하세요 (선택 안 하면 전체 번역)")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 전체 선택/해제 버튼
        button_layout = QHBoxLayout()
        btn_select_all = QPushButton("전체 선택")
        btn_select_all.clicked.connect(self.select_all)
        button_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("전체 해제")
        btn_deselect_all.clicked.connect(self.deselect_all)
        button_layout.addWidget(btn_deselect_all)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 챕터 정렬
        def sort_chapter_key(chapter):
            """챕터 이름에서 숫자 추출하여 정렬"""
            import re
            match = re.search(r'act(\d+).*chapter(\d+)', chapter.lower())
            if match:
                return (int(match.group(1)), int(match.group(2)))
            match = re.search(r'chapter(\d+)', chapter.lower())
            if match:
                return (0, int(match.group(1)))
            match = re.search(r'ch(\d+)', chapter.lower())
            if match:
                return (0, int(match.group(1)))
            return (999, 999, chapter.lower())

        sorted_chapters = sorted(chapter_patterns.keys(), key=sort_chapter_key)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        # 그리드 레이아웃 (3열)
        grid_layout = QGridLayout()
        scroll_widget.setLayout(grid_layout)

        # 체크박스를 그리드로 배치
        columns = 3
        for i, chapter in enumerate(sorted_chapters):
            file_count = len(chapter_patterns[chapter])
            checkbox = QCheckBox(f"{chapter} ({file_count}개)")
            checkbox.setChecked(True)  # 기본 선택
            self.checkboxes[chapter] = checkbox

            row = i // columns
            col = i % columns
            grid_layout.addWidget(checkbox, row, col)

        # 확인/취소 버튼
        button_box = QHBoxLayout()
        button_box.addStretch()

        btn_ok = QPushButton("확인")
        btn_ok.setMinimumWidth(100)
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        button_box.addWidget(btn_ok)

        btn_cancel = QPushButton("취소")
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 8px;
                border-radius: 4px;
            }
        """)
        button_box.addWidget(btn_cancel)

        layout.addLayout(button_box)

    def select_all(self):
        """모든 챕터 선택"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        """모든 챕터 선택 해제"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def get_selected_chapters(self):
        """선택된 챕터 목록 반환"""
        selected = []
        for chapter, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected.append(chapter)
        return selected if selected else None


class TranslationWorker(QThread):
    """백그라운드 번역 작업"""
    progress = pyqtSignal(int, str)  # (진행률, 메시지)
    finished = pyqtSignal(str, dict, list, int)  # (완료 메시지, 비용 정보, 번역 엔트리 리스트, 새로 번역한 파일 수)
    error = pyqtSignal(str)  # 오류 메시지

    def __init__(self, input_dir, output_dir, engine, source_lang, target_lang, selected_chapters=None, preview_mode=True):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.engine = engine
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.selected_chapters = selected_chapters  # 선택된 챕터 리스트
        self.preview_mode = preview_mode  # 미리보기 모드 (임시 폴더에만 저장)
        self.total_tokens = {"input": 0, "output": 0}
        self.total_cost = 0.0
        self.translation_entries = []  # 번역 항목 리스트

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
            from utils.secure_storage import SecureStorage
            import os

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
            input_path = Path(self.input_dir)
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

            # 기존 번역 엔트리 로드 (이어서 하기 위해)
            # 이미 self.translation_entries에 로드되어 있을 수 있음
            # 새로 추가되는 엔트리만 append 됨

            # 파일별 번역
            translated_count = 0
            skipped_count = 0

            for i, file_path in enumerate(files):
                progress_pct = 20 + int((i / len(files)) * 75)
                self.progress.emit(progress_pct, f"번역 중: {file_path.name} ({i+1}/{len(files)})")

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

                    # 배치 번역 (한 번에 10줄씩)
                    batch_size = 10
                    translated_lines = []

                    for batch_start in range(0, len(texts_to_translate), batch_size):
                        batch = texts_to_translate[batch_start:batch_start + batch_size]
                        translated_batch = translator.translate_batch(batch)
                        translated_lines.extend(translated_batch)

                        # 토큰 정보 수집 (추정)
                        self.total_tokens["input"] += sum(len(t) * 2 for t in batch)  # 대략적 추정
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 게임 번역기 v0.1")
        self.setGeometry(100, 100, 1100, 800)

        # 마지막 번역 결과 저장
        self.last_translation_output = None
        self.last_translation_input = None
        self.translation_entries = []  # 번역 엔트리 (Excel 내보내기용)
        self.preview_output_path = None  # 미리보기 출력 경로

        # 프로젝트 설정
        self.projects_dir = Path("projects")
        self.projects_dir.mkdir(exist_ok=True)
        self.current_project = None

        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 레이아웃
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # 제목
        title = QLabel("🎮 게임 번역기 v0.1")
        title.setFont(QFont("맑은 고딕", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("AI 기반 게임 텍스트 자동 번역 도구")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # 탭 위젯
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 탭 추가
        tabs.addTab(self.create_translation_tab(), "📝 번역")
        tabs.addTab(self.create_excel_tab(), "📊 Excel 검수")
        tabs.addTab(self.create_settings_tab(), "⚙️ 설정")

        # 상태바
        self.statusBar().showMessage("준비")

        # 마지막 세션 복원
        self._restore_session()

    def _save_session(self):
        """현재 세션 정보 저장"""
        session_file = Path("session.json")

        session_data = {
            "last_input_path": self.input_path.text(),
            "current_project": str(self.current_project) if self.current_project else None,
            "last_translation_input": self.last_translation_input,
            "last_translation_output": self.last_translation_output,
            "preview_output_path": str(self.preview_output_path) if self.preview_output_path else None,
            "selected_engine": self.engine_combo.currentText(),
            "source_lang": self.source_lang_combo.currentText(),
            "target_lang": self.target_lang_combo.currentText(),
        }

        try:
            import json
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            print("✅ 세션 저장 완료")
        except Exception as e:
            print(f"⚠️ 세션 저장 실패: {str(e)}")

    def _restore_session(self):
        """이전 세션 복원 (사용자 확인)"""
        session_file = Path("session.json")

        if not session_file.exists():
            return

        try:
            import json
            import shutil
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # 이전 프로젝트가 있는지 확인
            if not session_data.get("current_project"):
                return

            project_path = Path(session_data["current_project"])
            if not project_path.exists():
                return

            # 사용자에게 이전 작업 이어하기 확인
            reply = QMessageBox.question(
                self,
                "이전 작업 발견",
                f"이전에 작업하던 프로젝트가 있습니다.\n\n"
                f"📂 프로젝트: {project_path.name}\n"
                f"📁 경로: {session_data.get('last_input_path', 'N/A')}\n\n"
                f"이전 작업을 이어서 하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                # 이전 작업 안 함 - 세션 파일 삭제
                session_file.unlink()
                print("❌ 이전 세션 삭제됨")
                return

            # 작업 내용 유지 확인
            preview_dir = project_path / "preview"
            has_preview = preview_dir.exists() and any(preview_dir.iterdir())

            if has_preview:
                reply2 = QMessageBox.question(
                    self,
                    "작업 내용 유지",
                    f"이전 번역 작업 내용이 있습니다.\n\n"
                    f"📊 번역 파일: preview/ 폴더\n\n"
                    f"작업 내용을 유지하시겠습니까?\n\n"
                    f"• 예: 이전 작업 이어하기 (번역된 파일 건너뛰기)\n"
                    f"• 아니오: 처음부터 다시 번역 (preview/ 폴더 삭제)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply2 == QMessageBox.StandardButton.No:
                    # 임시 파일 삭제
                    if preview_dir.exists():
                        shutil.rmtree(preview_dir)
                        print("🗑️ preview/ 폴더 삭제됨")

                    # _extracted 폴더도 삭제
                    extracted_dir = project_path / "preview" / "_extracted"
                    if extracted_dir.exists():
                        shutil.rmtree(extracted_dir)
                        print("🗑️ _extracted/ 폴더 삭제됨")

                    QMessageBox.information(
                        self,
                        "임시 파일 삭제 완료",
                        "이전 번역 내용이 삭제되었습니다.\n처음부터 새로 번역합니다."
                    )

            # 세션 복원 진행
            # 입력 경로 복원
            if session_data.get("last_input_path"):
                self.input_path.setText(session_data["last_input_path"])

            # 프로젝트 복원
            self.current_project = project_path
            self.project_info_label.setText(f"📂 프로젝트: {project_path.name}")

            # 번역 결과 로드
            self._load_translation_entries()

            # 번역 출력 경로 복원
            if session_data.get("last_translation_output"):
                self.last_translation_output = session_data["last_translation_output"]
                self.last_translation_input = session_data.get("last_translation_input")

                # 적용 버튼 활성화 (미리보기 폴더가 있는 경우)
                if Path(self.last_translation_output).exists():
                    self.btn_apply.setEnabled(True)

            if session_data.get("preview_output_path"):
                self.preview_output_path = Path(session_data["preview_output_path"])

            # 엔진 설정 복원
            if session_data.get("selected_engine"):
                index = self.engine_combo.findText(session_data["selected_engine"])
                if index >= 0:
                    self.engine_combo.setCurrentIndex(index)

            if session_data.get("source_lang"):
                index = self.source_lang_combo.findText(session_data["source_lang"])
                if index >= 0:
                    self.source_lang_combo.setCurrentIndex(index)

            if session_data.get("target_lang"):
                index = self.target_lang_combo.findText(session_data["target_lang"])
                if index >= 0:
                    self.target_lang_combo.setCurrentIndex(index)

            print("✅ 이전 세션 복원 완료")

        except Exception as e:
            print(f"⚠️ 세션 복원 실패: {str(e)}")

    def closeEvent(self, event):
        """프로그램 종료 시 세션 저장"""
        self._save_session()
        event.accept()

    def create_translation_tab(self):
        """번역 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)


        # 입력 폴더
        input_group = QGroupBox("📂 입력 폴더 (원본 게임 스크립트)")
        input_layout = QHBoxLayout()
        input_group.setLayout(input_layout)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("게임 스크립트 폴더 선택...")
        self.input_path.setReadOnly(True)
        input_layout.addWidget(self.input_path)

        btn_input = QPushButton("찾아보기")
        btn_input.clicked.connect(self.select_input_folder)
        input_layout.addWidget(btn_input)

        btn_detect_chapters = QPushButton("📖 챕터 감지")
        btn_detect_chapters.clicked.connect(self.detect_chapters)
        input_layout.addWidget(btn_detect_chapters)

        layout.addWidget(input_group)

        # 챕터 선택 결과 표시
        self.chapter_info_label = QLabel("")
        self.chapter_info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                color: #000000;
                padding: 10px;
                border-radius: 5px;
                border: 2px solid #4a90e2;
            }
        """)
        self.chapter_info_label.setVisible(False)
        layout.addWidget(self.chapter_info_label)

        # 프로젝트 폴더 정보
        self.project_info_label = QLabel("프로젝트를 선택하거나 생성하세요")
        self.project_info_label.setStyleSheet("""
            QLabel {
                background-color: #fff8dc;
                color: #000000;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #daa520;
            }
        """)
        layout.addWidget(self.project_info_label)

        # 언어 설정
        lang_group = QGroupBox("🌐 언어 설정")
        lang_layout = QHBoxLayout()
        lang_group.setLayout(lang_layout)

        lang_layout.addWidget(QLabel("원본 언어:"))
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems([
            "자동 감지 (Auto Detect)",
            "일본어 (Japanese)",
            "영어 (English)",
            "중국어 간체 (Chinese Simplified)",
            "중국어 번체 (Chinese Traditional)",
            "한국어 (Korean)"
        ])
        self.source_lang_combo.setCurrentIndex(0)  # 기본값: 자동 감지
        lang_layout.addWidget(self.source_lang_combo)

        lang_layout.addWidget(QLabel("→"))

        lang_layout.addWidget(QLabel("대상 언어:"))
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems([
            "한국어 (Korean)",
            "영어 (English)",
            "일본어 (Japanese)",
            "중국어 간체 (Chinese Simplified)",
            "중국어 번체 (Chinese Traditional)"
        ])
        self.target_lang_combo.setCurrentIndex(0)  # 기본값: 한국어
        lang_layout.addWidget(self.target_lang_combo)

        lang_layout.addStretch()

        layout.addWidget(lang_group)

        # 게임 내 대체할 언어 선택
        replace_lang_group = QGroupBox("🔄 게임에 적용할 언어 (어떤 언어를 대체할지)")
        replace_layout = QVBoxLayout()
        replace_lang_group.setLayout(replace_layout)

        info_label = QLabel(
            "💡 번역한 파일을 게임 패키지의 어떤 언어로 교체할지 선택하세요.\n"
            "   예: 중국어를 한국어로 번역했다면, 게임의 중국어 파일을 한국어로 교체합니다."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        replace_layout.addWidget(info_label)

        replace_combo_layout = QHBoxLayout()
        replace_combo_layout.addWidget(QLabel("교체할 언어:"))
        self.replace_lang_combo = QComboBox()
        self.replace_lang_combo.addItems([
            "자동 감지 (게임 분석)",
            "중국어 간체 (zh-Hans)",
            "중국어 번체 (zh-Hant)",
            "일본어 (ja)",
            "영어 (en)",
            "한국어 (ko)"
        ])
        self.replace_lang_combo.setCurrentIndex(0)  # 기본값: 자동 감지
        replace_combo_layout.addWidget(self.replace_lang_combo)

        btn_detect_lang = QPushButton("🔍 게임 언어 감지")
        btn_detect_lang.clicked.connect(self.detect_game_languages)
        replace_combo_layout.addWidget(btn_detect_lang)

        replace_combo_layout.addStretch()
        replace_layout.addLayout(replace_combo_layout)

        # 감지된 언어 표시
        self.detected_lang_label = QLabel("")
        self.detected_lang_label.setWordWrap(True)
        self.detected_lang_label.setStyleSheet("""
            QLabel {
                background-color: #e8f4f8;
                color: #000;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #4a90e2;
            }
        """)
        self.detected_lang_label.setVisible(False)
        replace_layout.addWidget(self.detected_lang_label)

        layout.addWidget(replace_lang_group)

        # 번역 엔진 선택
        engine_group = QGroupBox("🤖 번역 엔진")
        engine_layout = QHBoxLayout()
        engine_group.setLayout(engine_layout)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems([
            "Claude Haiku 3.5 (가성비 최고) 💰",
            "Claude Sonnet 4 (고품질) ⭐",
            # "ChatGPT-4o",  # 미테스트
            "Google Translate (무료) 🆓",
            "DeepL",
            # "Papago",  # 미테스트
        ])
        engine_layout.addWidget(self.engine_combo)

        btn_api_settings = QPushButton("🔑 API 키 설정")
        btn_api_settings.clicked.connect(self.open_api_settings)
        engine_layout.addWidget(btn_api_settings)

        layout.addWidget(engine_group)

        # 번역 옵션
        options_group = QGroupBox("⚙️ 번역 옵션")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        self.enable_tm = QCheckBox("Translation Memory 사용 (비용 50-80% 절감)")
        self.enable_tm.setChecked(True)
        options_layout.addWidget(self.enable_tm)

        self.enable_backup = QCheckBox("자동 백업 활성화 (30분마다)")
        self.enable_backup.setChecked(True)
        options_layout.addWidget(self.enable_backup)

        self.enable_quality = QCheckBox("품질 검증 활성화")
        self.enable_quality.setChecked(True)
        options_layout.addWidget(self.enable_quality)

        self.include_font_info = QCheckBox("폰트 정보 포함 (한글 지원 폰트 추천)")
        self.include_font_info.setChecked(True)
        self.include_font_info.setToolTip("번역 결과에 한글 폰트 정보를 포함합니다")
        options_layout.addWidget(self.include_font_info)

        layout.addWidget(options_group)

        # 진행 상황
        progress_group = QGroupBox("📊 진행 상황")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("대기 중...")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

        # 번역 시작 버튼
        btn_translate = QPushButton("🚀 번역 시작 (미리보기)")
        btn_translate.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        btn_translate.setMinimumHeight(50)
        btn_translate.clicked.connect(self.start_translation)
        btn_translate.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(btn_translate)

        # 적용 버튼
        self.btn_apply = QPushButton("✅ 게임에 적용하기")
        self.btn_apply.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        self.btn_apply.setMinimumHeight(50)
        self.btn_apply.clicked.connect(self.apply_translation)
        self.btn_apply.setEnabled(False)  # 초기에는 비활성화
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        layout.addWidget(self.btn_apply)

        return tab

    def create_excel_tab(self):
        """Excel 검수 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 제목
        title = QLabel("📊 Excel 검수 워크플로우")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # 설명
        info = QLabel(
            "번역 완료 후, Excel로 내보내서 검수하고 수정된 내용을 다시 가져옵니다."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # 현재 번역 결과 표시
        status_group = QGroupBox("📁 현재 번역 결과")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)

        self.translation_status_label = QLabel("아직 번역을 진행하지 않았습니다.")
        self.translation_status_label.setWordWrap(True)
        self.translation_status_label.setStyleSheet("padding: 10px; background: #f8f9fa; border-radius: 4px;")
        status_layout.addWidget(self.translation_status_label)

        layout.addWidget(status_group)

        # Excel 내보내기
        export_group = QGroupBox("1️⃣ Excel 내보내기")
        export_layout = QVBoxLayout()
        export_group.setLayout(export_layout)

        export_layout.addWidget(QLabel("번역 결과를 Excel 파일로 내보냅니다."))

        self.btn_export_excel = QPushButton("📤 Excel 내보내기 (최근 번역 결과)")
        self.btn_export_excel.clicked.connect(self.export_excel)
        self.btn_export_excel.setMinimumHeight(40)
        self.btn_export_excel.setEnabled(False)  # 초기에는 비활성화
        export_layout.addWidget(self.btn_export_excel)

        layout.addWidget(export_group)

        # Excel 가져오기
        import_group = QGroupBox("2️⃣ 수정 후 가져오기")
        import_layout = QVBoxLayout()
        import_group.setLayout(import_layout)

        import_layout.addWidget(QLabel(
            "Excel에서 수정한 내용을 번역 파일에 자동 반영합니다.\n"
            "• '원문': 번역 대상 텍스트 (확인용)\n"
            "• 'AI 번역': Claude가 번역한 결과 (참고용)\n"
            "• '수정본': 이 컬럼에만 수정 내용 입력 (노란색)"
        ))

        btn_import = QPushButton("📥 수정된 Excel 가져오기")
        btn_import.clicked.connect(self.import_excel)
        btn_import.setMinimumHeight(40)
        import_layout.addWidget(btn_import)

        layout.addWidget(import_group)

        # 폰트 적용 가이드
        font_group = QGroupBox("3️⃣ 폰트 적용 (한글 지원)")
        font_layout = QVBoxLayout()
        font_group.setLayout(font_layout)

        font_layout.addWidget(QLabel(
            "한글로 번역한 후 게임에서 폰트가 깨지는 문제를 해결합니다."
        ))

        btn_font_guide = QPushButton("🔤 폰트 적용 가이드 보기")
        btn_font_guide.clicked.connect(self.show_font_guide)
        btn_font_guide.setMinimumHeight(40)
        font_layout.addWidget(btn_font_guide)

        btn_generate_font_info = QPushButton("📋 폰트 정보 파일 생성")
        btn_generate_font_info.clicked.connect(self.generate_font_info)
        btn_generate_font_info.setMinimumHeight(40)
        font_layout.addWidget(btn_generate_font_info)

        layout.addWidget(font_group)

        # 사용 팁
        tip_group = QGroupBox("💡 검수 워크플로우")
        tip_layout = QVBoxLayout()
        tip_group.setLayout(tip_layout)

        tip_text = QTextEdit()
        tip_text.setReadOnly(True)
        tip_text.setMaximumHeight(120)
        tip_text.setText(
            "1. 번역 탭에서 번역 완료 → 자동으로 경로 저장\n"
            "2. Excel 내보내기 → 검수자에게 전달\n"
            "3. 검수자가 Excel에서 '번역' 컬럼 수정\n"
            "4. 수정된 Excel 가져오기 → 번역 파일 자동 업데이트\n"
            "5. 폰트 정보 파일 생성 → 게임에 적용\n"
            "6. 게임 실행하여 한글이 정상적으로 표시되는지 확인"
        )
        tip_layout.addWidget(tip_text)

        layout.addWidget(tip_group)

        layout.addStretch()

        return tab


    def create_settings_tab(self):
        """설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 제목
        title = QLabel("⚙️ 번역 설정")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # 탭으로 구분
        settings_tabs = QTabWidget()
        layout.addWidget(settings_tabs)

        # 번역 규칙 탭
        rules_tab = self.create_rules_editor()
        settings_tabs.addTab(rules_tab, "📝 번역 규칙")

        # 용어집 탭
        glossary_tab = self.create_glossary_editor()
        settings_tabs.addTab(glossary_tab, "📚 용어집")

        return tab

    def create_rules_editor(self):
        """번역 규칙 에디터"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("번역 시 적용할 규칙을 설정합니다. (실제 프로젝트 예시 포함)"))

        # 텍스트 에디터
        self.rules_editor = QTextEdit()
        self.rules_editor.setFont(QFont("Consolas", 10))
        layout.addWidget(self.rules_editor)

        # 버튼
        btn_layout = QHBoxLayout()

        btn_load_default = QPushButton("기본값 불러오기")
        btn_load_default.clicked.connect(self.load_default_rules)
        btn_layout.addWidget(btn_load_default)

        btn_save = QPushButton("💾 저장")
        btn_save.clicked.connect(lambda: self.save_config_file("config/translation_rules.yaml", self.rules_editor))
        btn_layout.addWidget(btn_save)

        btn_open_external = QPushButton("외부 에디터로 열기")
        btn_open_external.clicked.connect(lambda: self.open_file("config/translation_rules.yaml"))
        btn_layout.addWidget(btn_open_external)

        layout.addLayout(btn_layout)

        # 초기 로드 (examples 폴더의 실제 사용 규칙)
        self.load_config_file("config/translation_rules.yaml", self.rules_editor, fallback="examples/translation_rules.txt")

        return tab

    def create_glossary_editor(self):
        """용어집 에디터"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("게임에 사용되는 고유명사, 인명, 용어를 관리합니다."))

        # 텍스트 에디터
        self.glossary_editor = QTextEdit()
        self.glossary_editor.setFont(QFont("Consolas", 10))
        layout.addWidget(self.glossary_editor)

        # 버튼
        btn_layout = QHBoxLayout()

        btn_load_default = QPushButton("기본값 불러오기")
        btn_load_default.clicked.connect(lambda: self.load_config_file("config/glossary_default.yaml", self.glossary_editor))
        btn_layout.addWidget(btn_load_default)

        btn_save = QPushButton("💾 저장")
        btn_save.clicked.connect(lambda: self.save_config_file("config/glossary.yaml", self.glossary_editor))
        btn_layout.addWidget(btn_save)

        btn_extract = QPushButton("자동 추출")
        btn_extract.clicked.connect(self.extract_glossary)
        btn_layout.addWidget(btn_extract)

        layout.addLayout(btn_layout)

        # 초기 로드 (examples 폴더의 실제 사용 용어집)
        self.load_config_file("config/glossary.yaml", self.glossary_editor, fallback="examples/glossary_example.json")

        return tab

    # 이벤트 핸들러
    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "게임 폴더 선택")
        if folder:
            # 게임 폴더 검증
            if not self.validate_game_folder(folder):
                return

            self.input_path.setText(folder)

            # 게임 이름 자동 감지 및 프로젝트 생성/선택
            self.auto_create_or_select_project(folder)

    def validate_game_folder(self, folder_path):
        """게임 폴더 유효성 검사"""
        from pathlib import Path

        folder = Path(folder_path)

        # 일반적인 게임 파일 확장자
        game_extensions = {'.txt', '.json', '.xlsx', '.csv', '.nani', '.ks', '.dat'}

        # 현재 폴더에서 게임 파일 검색
        current_game_files = [f for f in folder.glob('**/*') if f.suffix.lower() in game_extensions]

        # 하위 2단계까지 게임 폴더 검색
        potential_game_folders = []
        for subdir in folder.rglob('*'):
            if subdir.is_dir() and subdir.relative_to(folder).parts and len(subdir.relative_to(folder).parts) <= 2:
                game_files = [f for f in subdir.glob('*') if f.suffix.lower() in game_extensions]
                if game_files:
                    potential_game_folders.append((subdir, len(game_files)))

        # 현재 폴더에 게임 파일이 있으면 OK
        if current_game_files:
            return True

        # 게임 폴더가 없음
        if not potential_game_folders:
            QMessageBox.warning(
                self,
                "게임 폴더 없음",
                "선택한 폴더와 하위 폴더(2단계)에서 게임 파일을 찾을 수 없습니다.\n\n"
                "게임 스크립트 파일이 있는 폴더를 정확하게 선택해주세요.\n\n"
                f"지원 파일: {', '.join(game_extensions)}"
            )
            return False

        # 게임 폴더가 여러 개 발견됨
        if len(potential_game_folders) > 1:
            folder_list = "\n".join([f"  • {f.relative_to(folder)} ({count}개 파일)"
                                    for f, count in sorted(potential_game_folders, key=lambda x: x[1], reverse=True)[:5]])

            QMessageBox.warning(
                self,
                "여러 게임 폴더 발견",
                f"하위 폴더에서 {len(potential_game_folders)}개의 게임 폴더가 발견되었습니다.\n\n"
                f"발견된 폴더:\n{folder_list}\n\n"
                "게임 스크립트가 있는 정확한 폴더를 직접 선택해주세요."
            )
            return False

        # 게임 폴더가 1개만 발견됨 - 사용자에게 확인
        found_folder, file_count = potential_game_folders[0]
        reply = QMessageBox.question(
            self,
            "게임 폴더 확인",
            f"하위 폴더에서 게임 폴더를 찾았습니다:\n\n"
            f"  📁 {found_folder.relative_to(folder)}\n"
            f"  📄 {file_count}개 파일\n\n"
            f"이 폴더를 사용하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.input_path.setText(str(found_folder))
            return False  # 이미 경로를 설정했으므로 False 반환

        return False


    def auto_create_or_select_project(self, folder_path):
        """폴더에서 자동으로 게임 이름 감지하고 프로젝트 생성/선택"""
        from pathlib import Path
        import shutil

        folder = Path(folder_path)

        # 게임 이름 추출 시도
        game_name = None

        # 1. 실행 파일 찾기 (.exe)
        exe_files = list(folder.glob("*.exe"))
        if exe_files:
            game_name = exe_files[0].stem

        # 2. _Data 폴더에서 추출
        if not game_name:
            for data_folder in folder.glob("*_Data"):
                game_name = data_folder.name.replace("_Data", "")
                break

        # 3. 폴더명 사용
        if not game_name:
            game_name = folder.name

        # 특수문자 제거 및 정리
        import re
        game_name = re.sub(r'[<>:"/\\|?*]', '', game_name)
        game_name = game_name.strip()

        if not game_name:
            game_name = "Unnamed_Game"

        # 프로젝트가 이미 존재하는지 확인
        project_path = self.projects_dir / game_name

        if project_path.exists():
            # 이전 작업이 있음 - 사용자에게 물어보기
            reply = QMessageBox.question(
                self,
                "이전 작업 발견",
                f"'{game_name}'의 이전 작업이 있습니다.\n\n"
                f"이어서 하시겠습니까?\n\n"
                f"• 예: 이전 작업 이어하기\n"
                f"• 아니오: 임시파일 삭제하고 새로 시작",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                # 임시파일 정리
                extracted_dir = project_path / "extracted"
                translated_dir = project_path / "translated"

                if extracted_dir.exists():
                    shutil.rmtree(extracted_dir)
                    extracted_dir.mkdir()

                if translated_dir.exists():
                    shutil.rmtree(translated_dir)
                    translated_dir.mkdir()

                QMessageBox.information(
                    self,
                    "임시파일 정리 완료",
                    "임시파일이 삭제되었습니다. 새로 시작합니다."
                )

            # 프로젝트 선택
            self.current_project = project_path
            self.project_info_label.setText(f"📂 프로젝트: {game_name}")

            # 이전 번역 결과 로드
            self._load_translation_entries()
        else:
            # 새 프로젝트 생성
            self._create_project_folder(game_name, folder_path)
            self.current_project = self.projects_dir / game_name
            self.project_info_label.setText(f"📂 프로젝트: {game_name} (새로 생성)")

    def _save_translation_entries(self):
        """번역 결과를 JSON으로 저장"""
        if not self.current_project or not self.translation_entries:
            return

        import json
        entries_file = self.current_project / "translation_entries.json"

        # TranslationEntry를 딕셔너리로 변환
        entries_data = [entry.to_dict() for entry in self.translation_entries]

        with open(entries_file, 'w', encoding='utf-8') as f:
            json.dump(entries_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 번역 결과 저장: {len(self.translation_entries)}개 항목")

    def _add_cost_to_project(self, cost_info):
        """프로젝트에 비용/토큰 누적 기록"""
        if not self.current_project:
            return None

        import json
        from datetime import datetime

        cost_history_file = self.current_project / "cost_history.json"

        # 기존 비용 기록 로드
        if cost_history_file.exists():
            with open(cost_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "records": []
            }

        # 새 기록 추가
        record = {
            "timestamp": datetime.now().isoformat(),
            "engine": cost_info.get("engine", "Unknown"),
            "input_tokens": cost_info.get("input_tokens", 0),
            "output_tokens": cost_info.get("output_tokens", 0),
            "cost_usd": cost_info.get("total_cost", 0.0),
        }

        history["records"].append(record)

        # 누적값 갱신
        history["total_input_tokens"] += record["input_tokens"]
        history["total_output_tokens"] += record["output_tokens"]
        history["total_cost_usd"] += record["cost_usd"]

        # 저장
        with open(cost_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"💰 비용 기록 저장: ${record['cost_usd']:.4f} (누적: ${history['total_cost_usd']:.4f})")

        return history

    def _load_cost_history(self):
        """프로젝트 비용 기록 로드"""
        if not self.current_project:
            return None

        import json
        cost_history_file = self.current_project / "cost_history.json"

        if not cost_history_file.exists():
            return None

        try:
            with open(cost_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 비용 기록 로드 실패: {str(e)}")
            return None

    def _load_translation_entries(self):
        """이전 번역 결과를 JSON에서 로드"""
        if not self.current_project:
            return

        import json
        from core.excel_manager import TranslationEntry

        entries_file = self.current_project / "translation_entries.json"

        if not entries_file.exists():
            return

        try:
            with open(entries_file, 'r', encoding='utf-8') as f:
                entries_data = json.load(f)

            self.translation_entries = [
                TranslationEntry.from_dict(data) for data in entries_data
            ]

            print(f"✅ 이전 번역 결과 로드: {len(self.translation_entries)}개 항목")

            # Excel 버튼 활성화
            self.btn_export_excel.setEnabled(True)

        except Exception as e:
            print(f"⚠️ 번역 결과 로드 실패: {str(e)}")

    def _create_project_folder(self, project_name, input_folder=""):
        """프로젝트 폴더 생성"""
        project_path = self.projects_dir / project_name

        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "extracted").mkdir(exist_ok=True)
        (project_path / "translated").mkdir(exist_ok=True)
        (project_path / "config").mkdir(exist_ok=True)

        # 프로젝트 정보 저장
        import json
        project_info = {
            "name": project_name,
            "created": str(Path.cwd()),
            "input_folder": input_folder,
            "selected_chapters": []
        }

        with open(project_path / "project.json", 'w', encoding='utf-8') as f:
            json.dump(project_info, f, indent=2, ensure_ascii=False)



    def detect_chapters(self):
        """챕터 감지 및 UI 업데이트"""
        input_dir = self.input_path.text()
        if not input_dir:
            QMessageBox.warning(self, "경고", "입력 폴더를 먼저 선택하세요!")
            return

        from pathlib import Path
        import re

        input_path = Path(input_dir)

        # 1. 텍스트 파일 검색 (이미 추출된 경우)
        all_files = []
        for ext in ['*.txt', '*.nani', '*.json', '*.csv']:
            all_files.extend(list(input_path.glob(f"**/{ext}")))

        # 이미 번역된 파일 제외
        text_files = [f for f in all_files if not any(x in f.name for x in ["_KOREAN", "_KO", "_CLAUDE"])]

        # 2. Unity 번들 파일 검색 (게임 폴더인 경우)
        bundle_files = list(input_path.glob("**/*.bundle"))

        # 챕터 패턴 감지를 위한 파일 목록 결정
        # 번들 파일이 있으면 번들 우선 (게임 폴더)
        # 번들 없고 텍스트만 있으면 텍스트 사용 (추출된 폴더)
        if bundle_files:
            # 번들 파일명에서 챕터 추출 (게임 폴더)
            files_to_analyze = bundle_files
            file_type = "bundle"
        elif text_files:
            # 추출된 텍스트 파일 사용
            files_to_analyze = text_files
            file_type = "text"
        else:
            QMessageBox.information(
                self,
                "결과",
                "번역할 파일이나 게임 번들을 찾을 수 없습니다.\n\n"
                "• 추출된 스크립트 폴더 또는\n"
                "• Unity 게임 폴더를 선택하세요."
            )
            return

        # 챕터 패턴 감지
        chapter_patterns = {}

        # 다양한 챕터 패턴 지원
        patterns = [
            r'(act\d+_chapter\d+)',   # act01_chapter01 (폴더명, 대소문자 무시)
            r'(Act\d+_Chapter\d+)',  # Act01_Chapter01
            r'(Chapter\d+)',          # Chapter01
            r'(Ch\d+)',               # Ch01
            r'(chapter\d+)',          # chapter01
            r'(ch\d+)',               # ch01
            r'(第\d+章)',             # 第1章
            r'(챕터\d+)',             # 챕터01
        ]

        for file_path in files_to_analyze:
            # 파일명과 전체 경로 모두 확인 (폴더명에 챕터 정보가 있을 수 있음)
            file_name = file_path.name
            full_path_str = str(file_path).lower()
            matched = False

            for pattern in patterns:
                # 먼저 전체 경로에서 찾기 (폴더명 포함)
                match = re.search(pattern, full_path_str, re.IGNORECASE)
                if not match:
                    # 파일명에서도 찾기
                    match = re.search(pattern, file_name, re.IGNORECASE)

                if match:
                    chapter = match.group(1)

                    # 대소문자 통일 (Act01_Chapter01 형식으로)
                    if 'act' in chapter.lower() and 'chapter' in chapter.lower():
                        parts = chapter.lower().replace('act', 'Act').replace('chapter', 'Chapter').split('_')
                        if len(parts) == 2:
                            act_num = ''.join(filter(str.isdigit, parts[0]))
                            ch_num = ''.join(filter(str.isdigit, parts[1]))
                            chapter = f"Act{act_num.zfill(2)}_Chapter{ch_num.zfill(2)}"

                    if chapter not in chapter_patterns:
                        chapter_patterns[chapter] = []
                    chapter_patterns[chapter].append(file_path)
                    matched = True
                    break

        if not chapter_patterns:
            QMessageBox.information(
                self,
                "챕터 감지 실패",
                f"챕터 구분을 감지하지 못했습니다.\n\n"
                f"총 {len(files_to_analyze)}개 파일이 발견되었습니다.\n"
                f"챕터를 선택하지 않고 전체 번역을 진행하세요."
            )
            return

        # 챕터 선택 다이얼로그 표시
        dialog = ChapterSelectionDialog(chapter_patterns, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_chapters = dialog.get_selected_chapters()
            self.chapter_patterns = chapter_patterns  # 나중에 사용하기 위해 저장

            if self.selected_chapters:
                # 선택된 챕터의 파일 개수 계산
                total_files = sum(len(chapter_patterns[ch]) for ch in self.selected_chapters)

                # 화면에 선택 결과 표시
                chapter_list = "\n".join([f"• {ch} ({len(chapter_patterns[ch])}개 파일)" for ch in self.selected_chapters[:5]])
                if len(self.selected_chapters) > 5:
                    chapter_list += f"\n• ... 외 {len(self.selected_chapters)-5}개"

                self.chapter_info_label.setText(
                    f"📚 <b>챕터 선택됨</b><br>"
                    f"✅ {len(self.selected_chapters)}개 챕터 | 📁 {total_files}개 파일<br>"
                    f"<small>{chapter_list.replace(chr(10), '<br>')}</small>"
                )
                self.chapter_info_label.setVisible(True)
            else:
                # 선택 안 함 = 전체 번역
                self.chapter_info_label.setText(
                    f"📚 <b>전체 번역 모드</b><br>"
                    f"<small>모든 챕터가 번역됩니다</small>"
                )
                self.chapter_info_label.setVisible(True)
        else:
            # 취소됨
            self.selected_chapters = None
            self.chapter_info_label.setVisible(False)

    def get_selected_chapters(self):
        """선택된 챕터 목록 반환"""
        return getattr(self, 'selected_chapters', None)

    def _parse_language(self, lang_text):
        """콤보박스 텍스트를 간단한 언어 이름으로 변환"""
        lang_map = {
            "자동 감지 (Auto Detect)": "자동 감지",
            "일본어 (Japanese)": "일본어",
            "영어 (English)": "영어",
            "중국어 간체 (Chinese Simplified)": "중국어",
            "중국어 번체 (Chinese Traditional)": "중국어",
            "한국어 (Korean)": "한국어",
        }
        return lang_map.get(lang_text, lang_text)

    def open_api_settings(self):
        """API 키 설정 다이얼로그 열기"""
        dialog = APISettingsDialog(self)
        dialog.exec()

    def start_translation(self):
        if not self.current_project:
            QMessageBox.warning(self, "경고", "프로젝트를 먼저 선택하거나 생성하세요!")
            return

        input_dir = self.input_path.text()
        if not input_dir:
            QMessageBox.warning(self, "경고", "입력 폴더를 선택하세요!")
            return

        # 미리보기 모드: 프로젝트 폴더 내의 preview 폴더 사용
        preview_dir = str(self.current_project / "preview")
        self.preview_output_path = Path(preview_dir)

        engine = self.engine_combo.currentText()

        # 언어 콤보박스 텍스트를 간단한 언어 이름으로 변환
        source_lang_text = self.source_lang_combo.currentText()
        target_lang_text = self.target_lang_combo.currentText()

        source_lang = self._parse_language(source_lang_text)
        target_lang = self._parse_language(target_lang_text)

        # 선택된 챕터 가져오기
        selected_chapters = self.get_selected_chapters()

        # 챕터 선택 확인 메시지
        if selected_chapters:
            chapter_count = len(selected_chapters)
            reply = QMessageBox.question(
                self,
                "번역 시작 확인 (미리보기)",
                f"선택된 챕터: {chapter_count}개\n\n"
                f"{', '.join(selected_chapters[:5])}"
                f"{' ...' if len(selected_chapters) > 5 else ''}\n\n"
                f"미리보기 번역을 시작합니다.\n"
                f"확인 후 '게임에 적용하기' 버튼을 눌러주세요.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            # 전체 번역 확인
            reply = QMessageBox.question(
                self,
                "번역 시작 확인 (미리보기)",
                "전체 파일을 번역합니다.\n\n"
                "특정 챕터만 번역하려면 '챕터 감지' 버튼을 먼저 클릭하세요.\n\n"
                "미리보기 번역을 시작하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 마지막 번역 경로 저장
        self.last_translation_input = input_dir
        self.last_translation_output = preview_dir

        # 작업자 스레드 시작 (미리보기 모드)
        self.worker = TranslationWorker(
            input_dir, preview_dir, engine, source_lang, target_lang,
            selected_chapters, preview_mode=True
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.translation_finished)
        self.worker.error.connect(self.translation_error)
        self.worker.start()

        self.statusBar().showMessage("번역 진행 중 (미리보기)...")

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def translation_finished(self, message, cost_info, translation_entries, translated_count):
        # 번역 엔트리 저장
        self.translation_entries = translation_entries

        # JSON으로 자동 저장
        self._save_translation_entries()

        # 비용 기록 누적 저장 (실제로 새로 번역한 파일이 있는 경우만)
        cost_history = None
        if translated_count > 0:
            cost_history = self._add_cost_to_project(cost_info)
        else:
            print("💰 새로 번역한 파일이 없음 - 비용 기록 안 함")

        # Excel 버튼 활성화 (번역 결과가 있으므로)
        self.btn_export_excel.setEnabled(True)

        # 비용 정보 포맷팅 (누적 비용 포함)
        cost_message = self.format_cost_info(cost_info, cost_history)

        # 적용 버튼 활성화
        self.btn_apply.setEnabled(True)

        # 상태 라벨 업데이트
        if self.last_translation_output:
            status_text = (
                f"✅ 번역 완료 (미리보기)!\n\n"
                f"입력: {self.last_translation_input}\n"
                f"미리보기: {self.last_translation_output}\n"
                f"번역 항목: {len(translation_entries)}개\n\n"
            )
            if cost_info["total_cost"] > 0:
                status_text += f"{cost_message}\n\n"
            status_text += "✅ '게임에 적용하기' 버튼을 눌러 게임에 반영하세요.\n"
            status_text += "📊 Excel 탭에서 검수할 수 있습니다."

            self.translation_status_label.setText(status_text)
            self.translation_status_label.setStyleSheet(
                "padding: 10px; background: #d4edda; border-radius: 4px; color: #155724;"
            )

        # 완료 메시지 박스
        full_message = message
        if cost_info["total_cost"] > 0:
            full_message += f"\n\n{cost_message}"

        QMessageBox.information(self, "완료", full_message)
        self.statusBar().showMessage("번역 완료")
        self.progress_bar.setValue(0)
        self.progress_label.setText("대기 중...")

    def format_cost_info(self, cost_info, cost_history=None):
        """비용 정보를 사용자 친화적으로 포맷팅 (누적 비용 포함)"""
        if cost_info["total_cost"] == 0:
            message = "💰 비용: 무료 (Google Translate 또는 시뮬레이션)"
        else:
            input_tokens = cost_info["input_tokens"]
            output_tokens = cost_info["output_tokens"]
            total_cost = cost_info["total_cost"]

            # 한국 원화로 환산 (approximate, 1 USD = 1,300 KRW)
            cost_krw = total_cost * 1300

            message = (
                f"💰 이번 번역 비용:\n"
                f"  • 입력 토큰: {input_tokens:,}개\n"
                f"  • 출력 토큰: {output_tokens:,}개\n"
                f"  • 비용: ${total_cost:.4f} (약 {cost_krw:.0f}원)"
            )

        # 누적 비용 정보 추가
        if cost_history:
            total_accumulated = cost_history["total_cost_usd"]
            total_krw = total_accumulated * 1300
            total_in = cost_history["total_input_tokens"]
            total_out = cost_history["total_output_tokens"]

            message += (
                f"\n\n📊 프로젝트 누적 비용:\n"
                f"  • 총 입력 토큰: {total_in:,}개\n"
                f"  • 총 출력 토큰: {total_out:,}개\n"
                f"  • 총 비용: ${total_accumulated:.4f} (약 {total_krw:.0f}원)\n"
                f"  • 번역 횟수: {len(cost_history['records'])}회"
            )

        return message

    def translation_error(self, message):
        QMessageBox.critical(self, "오류", message)
        self.statusBar().showMessage("오류 발생")
        self.progress_bar.setValue(0)
        self.progress_label.setText("대기 중...")

    def detect_game_languages(self):
        """게임에서 사용 가능한 언어 자동 감지"""
        game_path = Path(self.input_path.text())

        if not game_path.exists():
            QMessageBox.warning(
                self,
                "경고",
                "먼저 게임 폴더를 선택하세요!"
            )
            return

        try:
            from core.game_language_detector import GameLanguageDetector

            detector = GameLanguageDetector()

            # 디버깅: StreamingAssets 폴더 확인
            print(f"🔍 게임 경로: {game_path}")
            streaming_folders = list(game_path.glob("*_Data/StreamingAssets"))
            print(f"🔍 StreamingAssets 폴더: {streaming_folders}")

            if streaming_folders:
                for folder in streaming_folders:
                    files = list(folder.rglob("*"))
                    print(f"  📁 {folder.name}: {len(files)}개 파일")
                    # 처음 5개 파일만 출력
                    for f in files[:5]:
                        if f.is_file():
                            print(f"    - {f.name} (확장자: {f.suffix or '없음'})")

            languages = detector.detect_languages(game_path)
            print(f"🔍 감지된 언어: {len(languages)}개")

            if not languages:
                error_msg = "❌ 게임에서 언어 파일을 찾을 수 없습니다.\n\n"
                if not streaming_folders:
                    error_msg += "StreamingAssets 폴더가 없습니다.\n"
                    error_msg += f"경로: {game_path}/*_Data/StreamingAssets"
                else:
                    error_msg += "언어 관련 파일을 찾을 수 없습니다.\n"
                    error_msg += "콘솔 출력을 확인해주세요."

                self.detected_lang_label.setText(error_msg)
                self.detected_lang_label.setVisible(True)
                return

            # 결과 표시
            lang_text = "🔍 감지된 언어:\n\n"
            for lang in languages:
                lang_text += f"  • {lang['name']} ({lang['code']}): {len(lang['files'])}개 파일\n"

            self.detected_lang_label.setText(lang_text)
            self.detected_lang_label.setVisible(True)

            # 첫 번째 언어를 자동 선택
            if languages:
                first_lang = languages[0]['code']
                for i in range(self.replace_lang_combo.count()):
                    if first_lang in self.replace_lang_combo.itemText(i):
                        self.replace_lang_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "오류",
                f"언어 감지 중 오류 발생:\n{str(e)}"
            )

    def apply_translation(self):
        """미리보기 번역을 게임 Asset Bundle에 적용"""
        if not self.preview_output_path or not self.preview_output_path.exists():
            QMessageBox.warning(
                self,
                "경고",
                "먼저 번역을 완료하세요!\n\n'번역 시작' 버튼을 눌러 번역을 실행한 후 다시 시도하세요."
            )
            return

        game_path = Path(self.input_path.text())
        if not game_path.exists():
            QMessageBox.warning(
                self,
                "경고",
                "게임 폴더를 선택하세요!"
            )
            return

        # 대체할 언어 코드 가져오기
        replace_lang_text = self.replace_lang_combo.currentText()

        if "자동 감지" in replace_lang_text:
            QMessageBox.warning(
                self,
                "경고",
                "먼저 '게임 언어 감지' 버튼을 눌러 대체할 언어를 선택하세요!"
            )
            return

        # 언어 코드 추출 (예: "중국어 간체 (zh-Hans)" -> "zh-Hans")
        import re
        match = re.search(r'\(([^)]+)\)', replace_lang_text)
        target_lang_code = match.group(1) if match else "zh-Hans"

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "게임에 적용",
            f"⚠️ 게임 Asset Bundle에 번역을 적용합니다.\n\n"
            f"📊 번역 항목: {len(self.translation_entries)}개\n"
            f"🔄 대체할 언어: {replace_lang_text}\n"
            f"💾 자동 백업: 예\n\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from core.bundle_packer import BundlePacker

            # 번역 파일 매핑 생성 (Bundle 내 파일명은 확장자 없음)
            translated_files = {}
            for file_path in self.preview_output_path.rglob("*.txt"):
                # .stem을 사용하여 확장자 제거
                translated_files[file_path.stem] = str(file_path)

            # Bundle 패커 초기화
            packer = BundlePacker()

            # 상태바에 진행 상황 표시
            self.statusBar().showMessage("Asset Bundle에 번역을 적용하는 중...")
            QApplication.processEvents()  # UI 업데이트

            # 번역 적용
            success = packer.apply_translations(
                game_path=game_path,
                target_language=target_lang_code,
                translated_files=translated_files,
                create_backup=True
            )

            if success:
                backup_info = f"백업 위치: {packer.backup_dir}" if packer.backup_dir else ""

                QMessageBox.information(
                    self,
                    "적용 완료",
                    f"✅ 번역이 게임에 적용되었습니다!\n\n"
                    f"📊 적용된 번역: {len(translated_files)}개 파일\n"
                    f"{backup_info}\n\n"
                    f"게임을 실행하여 번역을 확인하세요!"
                )

                self.btn_apply.setEnabled(False)
                self.statusBar().showMessage("게임에 적용 완료!")
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "번역을 적용할 수 없습니다.\n\n"
                    "대상 언어의 Asset Bundle을 찾을 수 없습니다."
                )

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR: {error_detail}")

            QMessageBox.critical(
                self,
                "오류",
                f"적용 중 오류 발생:\n{str(e)}\n\n"
                f"자세한 내용은 콘솔 창을 확인하세요."
            )

    def _reload_translation_entries_from_preview(self):
        """preview 폴더에서 번역 엔트리를 다시 로드"""
        preview_dir = self.current_project / "preview"

        # 기존 엔트리 초기화
        self.translation_entries = []

        # preview 폴더의 모든 .txt 파일 찾기
        txt_files = list(preview_dir.glob("*.txt"))

        from core.excel_manager import TranslationEntry

        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 일본어 주석에서 원문 추출 및 한국어 번역 매칭
                for idx, line in enumerate(lines):
                    stripped = line.strip()

                    # 주석(일본어 원문) 발견
                    if stripped.startswith(';') and not stripped.startswith('; >') and not stripped.startswith('; 日本語'):
                        japanese_text = stripped[1:].strip()  # '; ' 제거

                        if japanese_text:
                            # 다음 라인에서 한국어 번역 찾기
                            korean_idx = idx + 1
                            while korean_idx < len(lines):
                                korean_line = lines[korean_idx].strip()
                                # 빈 줄이나 주석/메타데이터가 아니면 한국어 번역
                                if korean_line and not korean_line.startswith('#') and not korean_line.startswith(';'):
                                    entry = TranslationEntry(
                                        file_path=str(txt_file),
                                        line_number=korean_idx + 1,
                                        japanese=japanese_text,
                                        translation=korean_line
                                    )
                                    self.translation_entries.append(entry)
                                    break
                                korean_idx += 1

            except Exception as e:
                print(f"⚠️ 파일 로드 실패: {txt_file.name} - {str(e)}")

        print(f"✅ {len(self.translation_entries)}개 번역 엔트리 로드 완료")

    def export_excel(self):
        """번역 결과를 Excel로 내보내기"""
        # preview 폴더에서 최신 번역 결과를 다시 로드
        if self.current_project:
            preview_dir = self.current_project / "preview"
            if preview_dir.exists():
                print("📂 preview 폴더에서 번역 결과 다시 로드 중...")
                self._reload_translation_entries_from_preview()

        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "번역 결과가 없습니다!\n\n먼저 번역을 실행하거나, 이전 번역 결과를 로드하세요."
            )
            return

        # 기본 저장 위치: 프로젝트 폴더
        # 파일명 형식: [프로젝트명]_translation_review_YYYYMMDD_HHMMSS.xlsx
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        project_name = "translation"
        if self.current_project:
            project_name = self.current_project.name

        default_filename = f"{project_name}_translation_review_{timestamp}.xlsx"

        if self.current_project:
            default_filename = str(self.current_project / default_filename)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Excel 저장",
            default_filename,
            "Excel Files (*.xlsx)"
        )

        if filename:
            try:
                from core.excel_manager import ExcelManager

                # Excel 내보내기
                manager = ExcelManager()
                manager.export_to_excel(self.translation_entries, filename)

                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ Excel 내보내기 완료!\n\n"
                    f"📁 {filename}\n\n"
                    f"📊 총 {len(self.translation_entries)}개 항목\n\n"
                    f"💡 사용 방법:\n"
                    f"1. Excel에서 '원문'과 'AI 번역' 확인\n"
                    f"2. 수정이 필요한 경우 '수정본' 컬럼에 입력\n"
                    f"3. 저장 후 '수정된 Excel 가져오기' 클릭"
                )

            except Exception as e:
                import traceback
                QMessageBox.critical(
                    self,
                    "오류",
                    f"Excel 저장 실패:\n{str(e)}\n\n{traceback.format_exc()}"
                )

    def import_excel(self):
        """수정된 Excel 파일을 가져와서 번역 파일에 반영"""
        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "원본 번역 결과가 없습니다!\n\n먼저 번역을 실행하거나 Excel을 내보내기하세요."
            )
            return

        # 기본 열기 위치: 프로젝트 폴더
        default_path = ""
        if self.current_project:
            default_path = str(self.current_project)

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Excel 열기",
            default_path,
            "Excel Files (*.xlsx)"
        )

        if not filename:
            return

        try:
            from core.excel_manager import ExcelManager

            # Excel 가져오기
            manager = ExcelManager()
            updated_entries, conflicts = manager.import_from_excel(
                filename,
                self.translation_entries
            )

            # 수정된 항목 개수 계산
            modified_count = sum(1 for e in updated_entries if e.status == 'modified')

            if modified_count == 0:
                QMessageBox.information(
                    self,
                    "알림",
                    f"✅ Excel 파일을 확인했습니다.\n\n"
                    f"수정된 항목이 없습니다.\n\n"
                    f"💡 '수정본' 컬럼에 수정 내용을 입력하세요."
                )
                return

            # 사용자 확인
            reply = QMessageBox.question(
                self,
                "수정 사항 반영",
                f"📊 Excel 가져오기 완료\n\n"
                f"✏️ 수정된 항목: {modified_count}개\n"
                f"⚠️ 충돌: {len(conflicts)}개\n\n"
                f"번역 파일에 수정 사항을 반영하시겠습니까?\n\n"
                f"대상 폴더: {self.last_translation_output or '미리보기 폴더'}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # 파일에 적용
            if self.last_translation_output:
                output_dir = Path(self.last_translation_output)
                manager.apply_to_files(updated_entries, output_dir)

                # 번역 엔트리 업데이트
                self.translation_entries = updated_entries

                # JSON 저장
                self._save_translation_entries()

                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ 수정 사항이 반영되었습니다!\n\n"
                    f"✏️ 수정된 항목: {modified_count}개\n"
                    f"📁 출력 폴더: {output_dir}\n\n"
                    f"이제 '게임에 적용하기'를 눌러주세요."
                )
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "출력 폴더를 찾을 수 없습니다.\n먼저 번역을 실행하세요."
                )

        except Exception as e:
            import traceback
            QMessageBox.critical(
                self,
                "오류",
                f"Excel 가져오기 실패:\n{str(e)}\n\n{traceback.format_exc()}"
            )

    def show_font_guide(self):
        """폰트 적용 가이드 표시"""
        guide = """
<h2>🔤 한글 폰트 적용 가이드</h2>

<h3>왜 폰트가 필요한가?</h3>
<p>일본어 게임은 일본어 폰트만 포함하고 있어, 한글로 번역하면 폰트가 깨지거나 □□□로 표시됩니다.</p>

<h3>해결 방법</h3>

<h4>방법 1: 폰트 교체 (권장)</h4>
<ol>
<li><b>한글 지원 폰트 다운로드</b>
   <ul>
   <li>추천: <b>Noto Sans CJK KR</b> (무료, 구글 폰트)</li>
   <li>추천: <b>나눔고딕</b>, <b>맑은 고딕</b></li>
   <li>게임 분위기에 맞는 폰트 선택</li>
   </ul>
</li>

<li><b>게임 폰트 파일 찾기</b>
   <ul>
   <li>일반적 위치: <code>GameName_Data/Resources/Fonts/</code></li>
   <li>또는: <code>GameName_Data/StreamingAssets/Fonts/</code></li>
   <li>확장자: <code>.ttf</code>, <code>.otf</code></li>
   </ul>
</li>

<li><b>폰트 백업 및 교체</b>
   <ul>
   <li>원본 폰트 파일을 <code>.backup</code>으로 백업</li>
   <li>한글 폰트를 같은 이름으로 복사</li>
   <li>파일명을 정확하게 맞춰야 함</li>
   </ul>
</li>

<li><b>게임 실행 및 확인</b></li>
</ol>

<h4>방법 2: TextMeshPro 폰트 에셋 생성 (Unity 게임)</h4>
<ol>
<li><b>Unity Editor 설치</b> (게임과 같은 버전)</li>
<li><b>TextMeshPro 폰트 에셋 생성</b>
   <ul>
   <li>Window → TextMeshPro → Font Asset Creator</li>
   <li>한글 유니코드 범위 추가 (AC00-D7AF)</li>
   </ul>
</li>
<li><b>에셋 교체</b></li>
</ol>

<h4>방법 3: BepInEx 플러그인</h4>
<ol>
<li><b>BepInEx 설치</b></li>
<li><b>폰트 교체 플러그인 작성</b> (C#)</li>
<li>런타임에 폰트 동적 로드</li>
</ol>

<h3>📋 폰트 정보 파일</h3>
<p>아래 버튼으로 <code>font_info.txt</code> 파일을 생성하면 게임에 필요한 폰트 정보를 확인할 수 있습니다.</p>

<h3>💡 팁</h3>
<ul>
<li>폰트 크기가 너무 크면 게임 로딩이 느려질 수 있음</li>
<li>필요한 글자만 포함하는 서브셋 폰트 사용 권장</li>
<li>라이선스 확인 필수 (상업적 사용 가능 여부)</li>
</ul>
"""

        msg = QMessageBox(self)
        msg.setWindowTitle("폰트 적용 가이드")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet("QLabel{min-width: 600px; min-height: 400px;}")
        msg.exec()

    def generate_font_info(self):
        """폰트 정보 파일 생성"""
        if not self.last_translation_output:
            QMessageBox.warning(
                self,
                "경고",
                "먼저 번역을 완료하세요!\n\n번역 결과가 있어야 폰트 정보를 생성할 수 있습니다."
            )
            return

        try:
            # 폰트 정보 파일 생성
            output_path = Path(self.last_translation_output)
            font_info_path = output_path / "font_info.txt"

            font_info = f"""# 게임 한글 폰트 정보
# 생성일: {Path(__file__).parent.parent}

## 권장 폰트

### 1. Noto Sans CJK KR (무료, 추천)
- 다운로드: https://fonts.google.com/noto/specimen/Noto+Sans+KR
- 라이선스: SIL Open Font License (상업적 사용 가능)
- 특징: 한중일 통합 폰트, 게임에 적합

### 2. 나눔고딕 (무료)
- 다운로드: https://hangeul.naver.com/font
- 라이선스: SIL Open Font License
- 특징: 한글 전용, 깔끔한 디자인

### 3. 맑은 고딕 (Windows 내장)
- 위치: C:\\Windows\\Fonts\\malgun.ttf
- 라이선스: Windows에서만 사용 가능
- 특징: 시스템 폰트, 안정적

## 폰트 적용 방법

1. 게임 폰트 폴더 찾기
   - 일반적 위치: [게임 폴더]_Data/Resources/Fonts/
   - 또는: [게임 폴더]_Data/StreamingAssets/Fonts/

2. 원본 폰트 백업
   - 원본 폰트 파일을 .backup 확장자로 백업

3. 한글 폰트 복사
   - 다운로드한 한글 폰트를 원본과 같은 이름으로 복사

4. 게임 실행 및 확인

## 문제 해결

- 폰트가 여전히 깨진다면: TextMeshPro 에셋 교체 필요
- 폰트 크기가 너무 크다면: 서브셋 폰트 생성 권장
- Unity 게임이라면: BepInEx 플러그인 사용 고려

## 번역 정보

- 번역 엔진: {self.engine_combo.currentText()}
- 원본 언어: {self.source_lang_combo.currentText()}
- 대상 언어: {self.target_lang_combo.currentText()}
- 출력 폴더: {self.last_translation_output}
"""

            with open(font_info_path, 'w', encoding='utf-8') as f:
                f.write(font_info)

            QMessageBox.information(
                self,
                "완료",
                f"✅ 폰트 정보 파일 생성 완료!\n\n"
                f"{font_info_path}\n\n"
                f"이 파일을 참고하여 게임에 한글 폰트를 적용하세요."
            )

            # 파일 열기
            import os
            os.startfile(font_info_path)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"폰트 정보 파일 생성 실패:\n{str(e)}")

    def load_default_rules(self):
        """원본 언어에 맞는 기본 번역 규칙 불러오기"""
        # 현재 선택된 원본 언어 확인
        source_lang_text = self.source_lang_combo.currentText()

        # 언어 코드 매핑
        lang_map = {
            "자동 감지 (Auto Detect)": "ja",
            "일본어 (Japanese)": "ja",
            "영어 (English)": "en",
            "중국어 간체 (Chinese Simplified)": "zh",
            "중국어 번체 (Chinese Traditional)": "zh",
        }

        lang_code = lang_map.get(source_lang_text, "ja")
        default_file = f"config/translation_rules_{lang_code}_ko.yaml"

        # 기본값 파일 불러오기
        self.load_config_file(default_file, self.rules_editor)

        QMessageBox.information(self, "완료", f"✅ 기본값 불러오기 완료!\n\n언어: {source_lang_text}\n파일: {default_file}")

    def load_config_file(self, filepath, text_edit, fallback=None):
        """설정 파일 로드 (없으면 예제 파일에서 자동 생성)"""
        import shutil

        file_path = Path(filepath)
        fallback_path = Path(fallback) if fallback else None

        # 설정 파일이 없고 fallback이 있으면
        if not file_path.exists() and fallback_path and fallback_path.exists():
            try:
                # config 폴더 생성
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # fallback 파일을 복사하여 설정 파일 생성
                shutil.copy2(fallback_path, file_path)
                print(f"✅ 초기 설정 파일 생성: {file_path} (from {fallback_path})")
            except Exception as e:
                print(f"⚠️ 초기 설정 파일 생성 실패: {e}")

        # 파일 읽기
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_edit.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "경고", f"파일 읽기 실패:\n{str(e)}")
        else:
            text_edit.setText("# 설정 파일을 여기에 작성하세요")

    def save_config_file(self, filepath, text_edit):
        """설정 파일 저장"""
        try:
            file_path = Path(filepath)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_edit.toPlainText())

            QMessageBox.information(self, "완료", f"✅ 저장 완료!\n\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{str(e)}")

    def open_file(self, filepath):
        """외부 에디터로 파일 열기"""
        import os
        full_path = Path(filepath)

        # 파일이 없으면 생성
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write("# 설정 파일\n")

        try:
            os.startfile(full_path)
        except:
            QMessageBox.warning(self, "경고", f"파일을 열 수 없습니다:\n{filepath}")

    def extract_glossary(self):
        QMessageBox.information(self, "알림", "용어집 자동 추출 기능은 곧 추가됩니다.")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 모던한 스타일

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
