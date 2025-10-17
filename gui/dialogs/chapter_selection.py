"""챕터 선택 다이얼로그"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt


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
