"""압축 해제 핸들러 Mixin"""
from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit,
    QGroupBox, QWidget
)
from PyQt6.QtCore import Qt
from pathlib import Path
from gui.workers.extraction_worker import ExtractionWorker
from utils.archive_extractor import ArchiveExtractor


class ArchiveHandlerMixin:
    """압축 해제 기능을 GUI에 추가하는 Mixin"""

    def create_archive_tab(self):
        """압축 해제 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 제목
        title = QLabel("📦 압축 파일 해제")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(
            "ZIP, RAR 파일을 일본어/한글 파일명을 보존하며 안전하게 해제합니다.\n"
            "게임 파일의 압축을 해제한 후 번역 작업을 시작하세요."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # 파일 선택 그룹
        file_group = QGroupBox("압축 파일 선택")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)

        # 파일 경로 입력
        path_layout = QHBoxLayout()
        self.archive_path_input = QLineEdit()
        self.archive_path_input.setPlaceholderText("압축 파일 경로 (ZIP, RAR)")
        self.archive_path_input.setReadOnly(True)
        path_layout.addWidget(self.archive_path_input)

        select_btn = QPushButton("📁 파일 선택")
        select_btn.clicked.connect(self.select_archive_file)
        path_layout.addWidget(select_btn)

        file_layout.addLayout(path_layout)

        # 파일 정보
        self.archive_info_label = QLabel("")
        self.archive_info_label.setStyleSheet("color: #666; font-size: 12px;")
        file_layout.addWidget(self.archive_info_label)

        layout.addWidget(file_group)

        # 해제 옵션 그룹
        options_group = QGroupBox("압축 해제 옵션")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        # 출력 폴더
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("출력 폴더:"))

        self.extract_output_input = QLineEdit()
        self.extract_output_input.setPlaceholderText("기본: 압축 파일과 같은 폴더")
        output_layout.addWidget(self.extract_output_input)

        output_btn = QPushButton("📁 선택")
        output_btn.clicked.connect(self.select_extract_output)
        output_layout.addWidget(output_btn)

        options_layout.addLayout(output_layout)

        layout.addWidget(options_group)

        # 실행 버튼
        extract_btn = QPushButton("🚀 압축 해제 시작")
        extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        extract_btn.clicked.connect(self.start_extraction)
        layout.addWidget(extract_btn)
        self.extract_btn = extract_btn

        # 진행상황
        progress_group = QGroupBox("진행 상황")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)

        self.extract_progress_bar = QProgressBar()
        self.extract_progress_bar.setValue(0)
        progress_layout.addWidget(self.extract_progress_bar)

        self.extract_status_label = QLabel("대기 중...")
        progress_layout.addWidget(self.extract_status_label)

        layout.addWidget(progress_group)

        # 로그
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.extract_log = QTextEdit()
        self.extract_log.setReadOnly(True)
        self.extract_log.setMaximumHeight(150)
        log_layout.addWidget(self.extract_log)

        layout.addWidget(log_group)

        # 스페이서
        layout.addStretch()

        return tab

    def select_archive_file(self):
        """압축 파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "압축 파일 선택",
            "",
            "압축 파일 (*.zip *.rar);;ZIP 파일 (*.zip);;RAR 파일 (*.rar);;모든 파일 (*.*)"
        )

        if file_path:
            self.archive_path_input.setText(file_path)
            self._update_archive_info(file_path)
            self._add_extract_log(f"파일 선택: {Path(file_path).name}")

    def select_extract_output(self):
        """압축 해제 출력 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "압축 해제 폴더 선택"
        )

        if folder:
            self.extract_output_input.setText(folder)
            self._add_extract_log(f"출력 폴더: {folder}")

    def _update_archive_info(self, file_path: str):
        """압축 파일 정보 업데이트"""
        try:
            info = ArchiveExtractor.get_archive_info(Path(file_path))

            size_mb = info['size'] / (1024 * 1024)
            info_text = f"크기: {size_mb:.1f} MB | 포맷: {info['format']}"

            if 'file_count' in info and info['file_count'] is not None:
                info_text += f" | 파일 수: {info['file_count']}개"

            if not info['supported']:
                info_text += " | ⚠️ 지원하지 않는 포맷"

            self.archive_info_label.setText(info_text)

        except Exception as e:
            self.archive_info_label.setText(f"⚠️ 정보 조회 실패: {e}")

    def start_extraction(self):
        """압축 해제 시작"""
        archive_path = self.archive_path_input.text().strip()

        if not archive_path:
            QMessageBox.warning(self, "경고", "압축 파일을 선택해주세요.")
            return

        if not Path(archive_path).exists():
            QMessageBox.warning(self, "경고", "선택한 파일이 존재하지 않습니다.")
            return

        # 출력 폴더
        extract_to = self.extract_output_input.text().strip() or None

        # UI 업데이트
        self.extract_btn.setEnabled(False)
        self.extract_progress_bar.setValue(0)
        self.extract_status_label.setText("압축 해제 중...")
        self._add_extract_log(f"\n=== 압축 해제 시작 ===")
        self._add_extract_log(f"파일: {archive_path}")

        # Worker 생성 및 실행
        self.extraction_worker = ExtractionWorker(archive_path, extract_to)
        self.extraction_worker.progress.connect(self._on_extraction_progress)
        self.extraction_worker.finished.connect(self._on_extraction_finished)
        self.extraction_worker.error.connect(self._on_extraction_error)
        self.extraction_worker.start()

    def _on_extraction_progress(self, current: int, total: int):
        """압축 해제 진행상황 업데이트"""
        if total > 0:
            progress = int((current / total) * 100)
            self.extract_progress_bar.setValue(progress)
            self.extract_status_label.setText(f"압축 해제 중... ({current}/{total} 파일)")

    def _on_extraction_finished(self, result_path: str):
        """압축 해제 완료"""
        self.extract_progress_bar.setValue(100)
        self.extract_status_label.setText("✅ 완료!")
        self._add_extract_log(f"✅ 압축 해제 완료!")
        self._add_extract_log(f"📁 출력 폴더: {result_path}")

        # UI 복원
        self.extract_btn.setEnabled(True)

        # 완료 메시지
        QMessageBox.information(
            self,
            "완료",
            f"압축 해제가 완료되었습니다.\n\n출력 폴더:\n{result_path}"
        )

    def _on_extraction_error(self, error_msg: str):
        """압축 해제 오류"""
        self.extract_status_label.setText("❌ 오류 발생")
        self._add_extract_log(f"❌ 오류: {error_msg}")

        # UI 복원
        self.extract_btn.setEnabled(True)

        # 오류 메시지
        QMessageBox.critical(
            self,
            "오류",
            f"압축 해제 중 오류가 발생했습니다:\n\n{error_msg}"
        )

    def _add_extract_log(self, message: str):
        """로그 추가"""
        self.extract_log.append(message)
        # 자동 스크롤
        self.extract_log.verticalScrollBar().setValue(
            self.extract_log.verticalScrollBar().maximum()
        )
