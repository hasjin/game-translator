"""압축 해제 Worker 스레드"""
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from utils.archive_extractor import ArchiveExtractor


class ExtractionWorker(QThread):
    """압축 파일 해제를 백그라운드에서 수행하는 Worker"""

    # 시그널
    progress = pyqtSignal(int, int)  # (current, total)
    finished = pyqtSignal(str)  # 완료 (해제된 폴더 경로)
    error = pyqtSignal(str)  # 오류 메시지

    def __init__(self, archive_path: str, extract_to: str = None):
        super().__init__()
        self.archive_path = Path(archive_path)
        self.extract_to = Path(extract_to) if extract_to else None

    def run(self):
        """Worker 실행"""
        try:
            # 압축 해제
            result_path = ArchiveExtractor.extract(
                self.archive_path,
                self.extract_to,
                progress_callback=self._on_progress
            )

            # 완료 시그널 전송
            self.finished.emit(str(result_path))

        except Exception as e:
            # 오류 시그널 전송
            self.error.emit(str(e))

    def _on_progress(self, current: int, total: int):
        """진행상황 콜백"""
        self.progress.emit(current, total)
