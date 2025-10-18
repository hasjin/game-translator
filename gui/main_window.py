"""게임 번역기 GUI 메인 윈도우"""
import sys
import json
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
from gui.dialogs.chapter_selection import ChapterSelectionDialog
from gui.workers.translation_worker import TranslationWorker
from gui.ui.tab_builder import TabBuilderMixin
from gui.managers.project_manager import ProjectManagerMixin
from gui.managers.session_manager import SessionManagerMixin
from gui.handlers.excel_handler import ExcelHandlerMixin
from gui.handlers.archive_handler import ArchiveHandlerMixin


class MainWindow(ArchiveHandlerMixin, ExcelHandlerMixin, SessionManagerMixin, ProjectManagerMixin, TabBuilderMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 게임 번역기 v0.1")
        self.setGeometry(100, 100, 1100, 800)

        # 설정 매니저
        from core.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()

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
        tabs.addTab(self.create_archive_tab(), "📦 압축 해제")
        tabs.addTab(self.create_settings_tab(), "⚙️ 설정")

        # 상태바
        self.statusBar().showMessage("준비")

        # 저장된 설정 로드
        self._load_settings()

        # 마지막 세션 복원
        self._restore_session()

    # 이벤트 핸들러
    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "게임 폴더 선택")
        if folder:
            self.input_path.setText(folder)

            # 게임 형식 자동 감지 및 표시
            self.detect_and_display_game_info(folder)

            # 게임 이름 자동 감지 및 프로젝트 생성/선택
            self.auto_create_or_select_project(folder)

            # RPG Maker인 경우 UI 조정
            self.adjust_ui_for_game_type(folder)

    def detect_and_display_game_info(self, folder_path):
        """게임 형식 자동 감지 및 표시"""
        from pathlib import Path
        from utils.game_detector import GameDetector

        folder = Path(folder_path)

        # 게임 형식 감지
        game_info = GameDetector.detect_game_type(folder)

        # 표시용 텍스트 생성
        display_text = GameDetector.get_display_text(game_info)

        # GUI에 표시 (게임 정보 레이블이 있으면)
        if hasattr(self, 'game_info_label'):
            self.game_info_label.setText(display_text)
            self.game_info_label.setVisible(True)

            # 신뢰도에 따라 스타일 변경
            confidence = game_info.get('confidence', 0.0)
            if confidence >= 0.7:
                # 높은 신뢰도 - 초록색
                self.game_info_label.setStyleSheet(
                    "padding: 10px; background: #d4edda; border-radius: 4px; color: #155724; border: 1px solid #c3e6cb;"
                )
            elif confidence >= 0.5:
                # 보통 신뢰도 - 노란색
                self.game_info_label.setStyleSheet(
                    "padding: 10px; background: #fff3cd; border-radius: 4px; color: #856404; border: 1px solid #ffeaa7;"
                )
            else:
                # 낮은 신뢰도 - 빨간색
                self.game_info_label.setStyleSheet(
                    "padding: 10px; background: #f8d7da; border-radius: 4px; color: #721c24; border: 1px solid #f5c6cb;"
                )

    def adjust_ui_for_game_type(self, folder_path):
        """게임 형식에 따라 UI 조정 (RPG Maker는 언어 감지 UI 숨김)"""
        from pathlib import Path
        from core.game_language_detector import GameLanguageDetector

        game_path = Path(folder_path)
        detector = GameLanguageDetector()
        format_info = detector.detect_game_format(game_path)
        game_type = format_info.get('game_type', 'unknown')

        if game_type == 'rpgmaker':
            # RPG Maker: 언어 감지 UI 숨기기
            if hasattr(self, 'replace_lang_group'):
                self.replace_lang_group.setVisible(False)
                print(f"[INFO] RPG Maker game detected - language detection UI hidden")
            else:
                print("[WARNING] replace_lang_group not found - UI element not created yet")

            # 원본 언어 자동 감지 및 표시
            from core.rpgmaker_language_detector import RPGMakerLanguageDetector
            rpg_detector = RPGMakerLanguageDetector()
            lang_info = rpg_detector.detect_language(game_path)

            # 게임 정보 레이블에 언어 정보 추가
            current_text = self.game_info_label.text()
            lang_text = (
                f"\n\n[O] Original Language: {lang_info['language']} ({lang_info['locale']})"
            )
            if lang_info.get('game_title'):
                lang_text += f"\n[O] Game Title: {lang_info['game_title']}"

            self.game_info_label.setText(current_text + lang_text)
            print(f"[INFO] Original language: {lang_info['language']} ({lang_info['locale']})")
        else:
            # Unity 등 다른 게임: 언어 감지 UI 표시
            if hasattr(self, 'replace_lang_group'):
                self.replace_lang_group.setVisible(True)
                print(f"[INFO] {game_type} game detected - language detection UI shown")
            else:
                print("[WARNING] replace_lang_group not found - UI element not created yet")

    def detect_chapters(self):
        """챕터 감지 및 UI 업데이트 (Naninovel 전용)"""
        input_dir = self.input_path.text()
        if not input_dir:
            QMessageBox.warning(self, "경고", "입력 폴더를 먼저 선택하세요!")
            return

        from pathlib import Path
        import re

        input_path = Path(input_dir)

        # 게임 형식 확인
        from core.game_language_detector import GameLanguageDetector
        detector = GameLanguageDetector()
        format_info = detector.detect_game_format(input_path)

        # Naninovel 게임이 아니면 챕터 선택 불가
        if not format_info['is_naninovel']:
            # 경고창 대신 화면에 표시 (game_info_label에 이미 표시됨)
            return

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
            # 챕터 감지가 지원되지 않는 게임 (RPG Maker, Unity 등)
            # 조용히 반환 (경고 메시지 없음)
            print(f"[INFO] No chapter structure found. Total {len(files_to_analyze)} files")
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

        # RPG Maker 게임인 경우 한국어 존재 여부 확인
        from core.game_language_detector import GameLanguageDetector
        game_path = Path(input_dir)
        detector = GameLanguageDetector()
        format_info = detector.detect_game_format(game_path)
        game_type = format_info.get('game_type', 'unknown')

        if game_type == 'rpgmaker':
            # 한국어가 이미 있는지 확인
            from core.rpgmaker_language_detector import RPGMakerLanguageDetector
            rpg_detector = RPGMakerLanguageDetector()
            multilang_info = rpg_detector.check_multilang_support(game_path)

            if 'ko' in multilang_info['available_languages']:
                # 한국어가 이미 존재하는 경우 확인
                reply = QMessageBox.question(
                    self,
                    "Korean translation already exists",
                    f"[!] Korean translation already exists in this game.\n\n"
                    f"Available languages: {', '.join(multilang_info['available_languages'])}\n\n"
                    f"Do you want to overwrite the existing Korean translation?\n\n"
                    f"[Yes] Overwrite existing Korean translation\n"
                    f"[No] Cancel translation",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply != QMessageBox.StandardButton.Yes:
                    print("[INFO] User cancelled translation - Korean already exists")
                    return

                print("[INFO] User confirmed overwriting existing Korean translation")

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
                "미리보기 번역을 시작하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 마지막 번역 경로 저장
        self.last_translation_input = input_dir
        self.last_translation_output = preview_dir

        # 배치 크기 가져오기
        batch_size_text = self.batch_size_combo.currentText()
        if "1개씩" in batch_size_text:
            batch_size = 1
        elif "10개씩" in batch_size_text:
            batch_size = 10
        elif "50개씩" in batch_size_text:
            batch_size = 50
        elif "100개씩" in batch_size_text:
            batch_size = 100
        else:
            batch_size = 1  # 기본값

        # 작업자 스레드 시작 (미리보기 모드)
        self.worker = TranslationWorker(
            input_dir, preview_dir, engine, source_lang, target_lang,
            selected_chapters, preview_mode=True, batch_size=batch_size
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

        # 상태 라벨 업데이트 (translation_status_label이 없어서 주석 처리)
        # if self.last_translation_output:
        #     status_text = (
        #         f"✅ 번역 완료 (미리보기)!\n\n"
        #         f"입력: {self.last_translation_input}\n"
        #         f"미리보기: {self.last_translation_output}\n"
        #         f"번역 항목: {len(translation_entries)}개\n\n"
        #     )
        #     if cost_info["total_cost"] > 0:
        #         status_text += f"{cost_message}\n\n"
        #     status_text += "✅ '게임에 적용하기' 버튼을 눌러 게임에 반영하세요.\n"
        #     status_text += "📊 Excel 탭에서 검수할 수 있습니다."
        #
        #     self.translation_status_label.setText(status_text)
        #     self.translation_status_label.setStyleSheet(
        #         "padding: 10px; background: #d4edda; border-radius: 4px; color: #155724;"
        #     )

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

            # 게임 타입 먼저 확인
            format_info = detector.detect_game_format(game_path)
            game_type = format_info.get('game_type', 'unknown')

            # 디버깅: StreamingAssets 폴더 확인
            print(f"[INFO] Game path: {game_path}")
            streaming_folders = list(game_path.glob("*_Data/StreamingAssets"))
            print(f"[INFO] StreamingAssets folders: {streaming_folders}")

            # RPG Maker 게임인 경우 특별 처리
            if game_type == 'rpgmaker':
                # 언어 정보 감지
                from core.rpgmaker_language_detector import RPGMakerLanguageDetector
                rpg_detector = RPGMakerLanguageDetector()
                lang_info = rpg_detector.detect_language(game_path)

                info_msg = "RPG Maker Game Translation\n\n"
                info_msg += f"[O] Original Language: {lang_info['language']} ({lang_info['locale']})\n"
                if lang_info['game_title']:
                    info_msg += f"[O] Game Title: {lang_info['game_title']}\n"
                info_msg += f"\nTranslation will be ADDED (not replaced)\n"
                info_msg += f"Target: Korean (ko) in data_languages/ko/\n\n"
                info_msg += "Folder Structure:\n"
                info_msg += "  - data_languages/original/ (original backup)\n"
                info_msg += "  - data_languages/ko/ (Korean)\n"
                info_msg += "  - data_languages/en/ (English)\n\n"
                info_msg += "You can switch languages with multilingual plugin."

                self.detected_lang_label.setText(info_msg)
                self.detected_lang_label.setVisible(True)

                # RPG Maker는 언어 선택 불필요
                return

            if streaming_folders:
                for folder in streaming_folders:
                    files = list(folder.rglob("*"))
                    print(f"  📁 {folder.name}: {len(files)}개 파일")
                    # 처음 5개 파일만 출력
                    for f in files[:5]:
                        if f.is_file():
                            print(f"    - {f.name} (확장자: {f.suffix or '없음'})")

            languages = detector.detect_languages(game_path)
            print(f"[INFO] Detected languages: {len(languages)}")

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

        # 게임 형식 감지
        from core.game_language_detector import GameLanguageDetector
        detector = GameLanguageDetector()
        format_info = detector.detect_game_format(game_path)
        game_type = format_info.get('game_type', 'unknown')

        # RPG Maker 게임 처리
        if game_type == 'rpgmaker':
            return self._apply_rpgmaker_translation(game_path)

        # 일반 Unity 게임 처리
        if game_type in ['unity_generic', 'unity_other']:
            return self._apply_general_unity_translation(game_path)

        # Naninovel 게임 처리 (기존 로직)

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
                print(f"[OK] Initial config file created: {file_path} (from {fallback_path})")
            except Exception as e:
                print(f"[WARNING] Failed to create initial config file: {e}")

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

    def _apply_general_unity_translation(self, game_path: Path):
        """일반 Unity 게임에 번역 적용"""
        # extracted_translated.json 파일 확인
        json_file = self.preview_output_path / "extracted_translated.json"
        if not json_file.exists():
            QMessageBox.warning(
                self,
                "경고",
                "번역 파일을 찾을 수 없습니다!\n\n"
                "먼저 번역을 완료하세요."
            )
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "게임에 적용",
            f"⚠️ 일반 Unity 게임에 번역을 적용합니다.\n\n"
            f"📁 게임 경로: {game_path}\n"
            f"📊 번역 파일: {json_file.name}\n"
            f"💾 자동 백업: 예 ([게임]_Data_backup)\n\n"
            f"⚠️ 주의: 원본 게임 파일이 교체됩니다!\n\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from cli.extractor import UnityTextExtractor
            from cli.patcher import UnityPatcher

            # 번역 파일 로드
            self.statusBar().showMessage("번역 파일 로드 중...")
            QApplication.processEvents()

            extractor = UnityTextExtractor.load(json_file)
            entries = extractor.entries

            # 번역된 항목만 필터링
            translated_entries = [e for e in entries if e.translated]

            if not translated_entries:
                QMessageBox.warning(
                    self,
                    "경고",
                    "번역된 항목이 없습니다!"
                )
                return

            # 패치 적용
            self.statusBar().showMessage(f"{len(translated_entries)}개 항목을 게임에 적용 중...")
            QApplication.processEvents()

            patcher = UnityPatcher(game_path, backup=True)
            success = patcher.apply_patches(translated_entries)

            if success:
                QMessageBox.information(
                    self,
                    "적용 완료",
                    f"✅ 번역이 게임에 적용되었습니다!\n\n"
                    f"📊 적용된 항목: {len(translated_entries)}개\n"
                    f"💾 백업 위치: {game_path.parent / f'{game_path.name}_backup'}\n\n"
                    f"게임을 실행하여 번역을 확인하세요!"
                )

                self.btn_apply.setEnabled(False)
                self.statusBar().showMessage("게임에 적용 완료!")
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "번역 적용 중 오류가 발생했습니다.\n\n"
                    "콘솔 로그를 확인하세요."
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

    def _apply_rpgmaker_translation(self, game_path: Path):
        """RPG Maker 게임에 번역 적용"""
        # translation_entries.json 파일 확인
        if not self.current_project:
            QMessageBox.warning(
                self,
                "경고",
                "프로젝트를 찾을 수 없습니다!\n\n"
                "먼저 번역을 완료하세요."
            )
            return

        entries_file = self.current_project / "translation_entries.json"
        if not entries_file.exists():
            QMessageBox.warning(
                self,
                "경고",
                "번역 파일을 찾을 수 없습니다!\n\n"
                "먼저 번역을 완료하세요."
            )
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "게임에 적용",
            f"⚠️ RPG Maker 게임에 번역을 적용합니다.\n\n"
            f"📁 게임 경로: {game_path}\n"
            f"📊 번역 항목: {len(self.translation_entries)}개\n"
            f"💾 자동 백업: 예 (data_languages/original/)\n\n"
            f"⚠️ 주의: 다국어 폴더 구조가 생성됩니다!\n"
            f"   - data_languages/original/ (원본 백업)\n"
            f"   - data_languages/ko/ (한국어)\n\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from core.rpgmaker_packer import RPGMakerPacker

            # 번역 파일 로드
            self.statusBar().showMessage("번역 파일 로드 중...")
            QApplication.processEvents()

            with open(entries_file, 'r', encoding='utf-8') as f:
                translated_data = json.load(f)

            # 번역된 항목만 필터링
            translated_entries = [e for e in translated_data if e.get('translated')]

            if not translated_entries:
                QMessageBox.warning(
                    self,
                    "경고",
                    "번역된 항목이 없습니다!"
                )
                return

            # 패치 적용
            self.statusBar().showMessage(f"{len(translated_entries)}개 항목을 게임에 적용 중...")
            QApplication.processEvents()

            packer = RPGMakerPacker()
            success = packer.apply_translations(
                game_path=game_path,
                translated_data=translated_entries,
                create_backup=True,
                target_language='ko',
                mode='multilang'  # 다국어 폴더 모드
            )

            if success:
                backup_path = game_path / "data_languages" / "original"
                QMessageBox.information(
                    self,
                    "적용 완료",
                    f"✅ 번역이 게임에 적용되었습니다!\n\n"
                    f"📊 적용된 항목: {len(translated_entries)}개\n"
                    f"💾 백업 위치: {backup_path}\n"
                    f"🌏 한국어 폴더: data_languages/ko/\n\n"
                    f"게임을 실행하여 번역을 확인하세요!\n\n"
                    f"※ 다국어 플러그인이 필요할 수 있습니다."
                )

                self.btn_apply.setEnabled(False)
                self.statusBar().showMessage("게임에 적용 완료!")
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "번역 적용 중 오류가 발생했습니다.\n\n"
                    "콘솔 로그를 확인하세요."
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

    def extract_glossary(self):
        QMessageBox.information(self, "알림", "용어집 자동 추출 기능은 곧 추가됩니다.")

    def _load_settings(self):
        """저장된 설정 로드"""
        settings = self.settings_manager.get_translation_settings()

        # 엔진 설정
        engine = settings.get('engine', 'Claude Haiku 3.5')
        index = self.engine_combo.findText(engine)
        if index >= 0:
            self.engine_combo.setCurrentIndex(index)

        # 소스 언어
        source_lang = settings.get('source_lang', '자동 감지')
        index = self.source_lang_combo.findText(source_lang)
        if index >= 0:
            self.source_lang_combo.setCurrentIndex(index)

        # 타겟 언어
        target_lang = settings.get('target_lang', '한국어')
        index = self.target_lang_combo.findText(target_lang)
        if index >= 0:
            self.target_lang_combo.setCurrentIndex(index)

        # 체크박스
        self.enable_tm.setChecked(settings.get('use_tm', True))
        self.enable_quality.setChecked(settings.get('use_quality', True))
        self.include_font_info.setChecked(settings.get('include_font', True))

        # 콤보박스 변경 시 설정 저장
        self.engine_combo.currentTextChanged.connect(self._save_current_settings)
        self.source_lang_combo.currentTextChanged.connect(self._save_current_settings)
        self.target_lang_combo.currentTextChanged.connect(self._save_current_settings)
        self.enable_tm.stateChanged.connect(self._save_current_settings)
        self.enable_quality.stateChanged.connect(self._save_current_settings)
        self.include_font_info.stateChanged.connect(self._save_current_settings)

    def _save_current_settings(self):
        """현재 설정 저장"""
        self.settings_manager.save_translation_settings(
            engine=self.engine_combo.currentText(),
            source_lang=self.source_lang_combo.currentText(),
            target_lang=self.target_lang_combo.currentText(),
            use_tm=self.enable_tm.isChecked(),
            use_quality=self.enable_quality.isChecked(),
            include_font=self.include_font_info.isChecked()
        )
        print("[OK] Settings saved")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 모던한 스타일

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
