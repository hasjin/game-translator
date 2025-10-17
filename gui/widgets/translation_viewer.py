"""번역 검수 뷰어 위젯"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class TranslationViewerWidget(QWidget):
    """번역 검수를 위한 페이징 뷰어"""

    # 시그널 정의
    entry_modified = pyqtSignal(int, str)  # (index, modified_text)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []  # 전체 번역 엔트리
        self.filtered_entries = []  # 필터링된 엔트리
        self.current_page = 0
        self.items_per_page = 50
        self.modified_entries = {}  # {index: modified_text}

        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 검색 영역
        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("검색:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("원문 또는 번역문 검색...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input, stretch=3)

        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["전체", "원문만", "번역만", "수정본만"])
        self.search_type_combo.currentTextChanged.connect(self.on_search)
        search_layout.addWidget(self.search_type_combo, stretch=1)

        btn_clear = QPushButton("초기화")
        btn_clear.clicked.connect(self.clear_search)
        search_layout.addWidget(btn_clear)

        layout.addLayout(search_layout)

        # 필터 정보 라벨
        self.filter_label = QLabel("")
        self.filter_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.filter_label)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "번호", "파일", "원문", "AI 번역", "수정본"
        ])

        # 헤더 크기 조정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 번호
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 파일
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 원문
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # AI 번역
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 수정본
        self.table.setColumnWidth(0, 60)

        # 테이블 스타일
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        # 페이징 컨트롤
        paging_layout = QHBoxLayout()

        self.page_info_label = QLabel("0 / 0 페이지 (총 0개)")
        self.page_info_label.setFont(QFont("맑은 고딕", 10))
        paging_layout.addWidget(self.page_info_label)

        paging_layout.addStretch()

        self.btn_first = QPushButton("⏮ 처음")
        self.btn_first.clicked.connect(self.go_first_page)
        paging_layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("◀ 이전")
        self.btn_prev.clicked.connect(self.go_prev_page)
        paging_layout.addWidget(self.btn_prev)

        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("페이지")
        self.page_input.setMaximumWidth(60)
        self.page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_input.returnPressed.connect(self.go_to_page)
        paging_layout.addWidget(self.page_input)

        self.btn_next = QPushButton("다음 ▶")
        self.btn_next.clicked.connect(self.go_next_page)
        paging_layout.addWidget(self.btn_next)

        self.btn_last = QPushButton("마지막 ⏭")
        self.btn_last.clicked.connect(self.go_last_page)
        paging_layout.addWidget(self.btn_last)

        layout.addLayout(paging_layout)

        # 수정 사항 요약
        self.summary_label = QLabel("수정된 항목: 0개")
        self.summary_label.setStyleSheet(
            "padding: 10px; background: #e7f3ff; border-radius: 4px; color: #004085;"
        )
        layout.addWidget(self.summary_label)

    def load_entries(self, entries, modified_entries=None):
        """번역 엔트리 로드"""
        self.entries = entries
        self.filtered_entries = entries.copy()
        self.current_page = 0

        # 기존 수정 사항 로드
        if modified_entries:
            self.modified_entries = modified_entries.copy()
        else:
            self.modified_entries = {}

        self.update_view()

    def on_search(self):
        """검색 실행"""
        search_text = self.search_input.text().strip().lower()
        search_type = self.search_type_combo.currentText()

        if not search_text:
            self.filtered_entries = self.entries.copy()
            self.filter_label.setText("")
        else:
            self.filtered_entries = []

            for entry in self.entries:
                # 엔트리에서 텍스트 추출 (dict와 TranslationEntry 모두 지원)
                if isinstance(entry, dict):
                    original = entry.get('original', '').lower()
                    translated = entry.get('translated', '').lower()
                    file_name = entry.get('file', '').lower()
                else:
                    original = getattr(entry, 'japanese', getattr(entry, 'original', '')).lower()
                    translated = getattr(entry, 'translation', getattr(entry, 'translated', '')).lower()
                    file_name = getattr(entry, 'file_path', getattr(entry, 'file', '')).lower()

                # 수정본 확인
                idx = self.entries.index(entry)
                modified = self.modified_entries.get(idx, '').lower()

                # 검색 타입에 따라 필터링
                match = False
                if search_type == "전체":
                    match = (search_text in original or search_text in translated or
                            search_text in modified or search_text in file_name)
                elif search_type == "원문만":
                    match = search_text in original
                elif search_type == "번역만":
                    match = search_text in translated
                elif search_type == "수정본만":
                    match = search_text in modified

                if match:
                    self.filtered_entries.append(entry)

            self.filter_label.setText(
                f"🔍 검색 결과: {len(self.filtered_entries)}개 (전체 {len(self.entries)}개 중)"
            )

        self.current_page = 0
        self.update_view()

    def clear_search(self):
        """검색 초기화"""
        self.search_input.clear()
        self.search_type_combo.setCurrentIndex(0)

    def update_view(self):
        """현재 페이지 표시 업데이트"""
        total_items = len(self.filtered_entries)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)

        # 현재 페이지가 범위를 벗어나면 조정
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)

        # 페이지 정보 업데이트
        self.page_info_label.setText(
            f"{self.current_page + 1} / {total_pages} 페이지 (총 {total_items}개)"
        )
        self.page_input.setText(str(self.current_page + 1))

        # 버튼 활성화/비활성화
        self.btn_first.setEnabled(self.current_page > 0)
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < total_pages - 1)
        self.btn_last.setEnabled(self.current_page < total_pages - 1)

        # 테이블 업데이트
        self.update_table()

        # 수정 사항 요약 업데이트
        self.update_summary()

    def update_table(self):
        """테이블 내용 업데이트"""
        # 현재 페이지의 항목 가져오기
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.filtered_entries))
        page_entries = self.filtered_entries[start_idx:end_idx]

        # 테이블 행 수 설정
        self.table.setRowCount(len(page_entries))

        # 테이블 채우기
        for row, entry in enumerate(page_entries):
            # 전체 엔트리에서의 인덱스 찾기
            global_idx = self.entries.index(entry)

            # 데이터 추출 (dict와 TranslationEntry 모두 지원)
            if isinstance(entry, dict):
                original = entry.get('original', '')
                translated = entry.get('translated', '')
                file_name = entry.get('file', 'unknown')
            else:
                original = getattr(entry, 'japanese', getattr(entry, 'original', ''))
                translated = getattr(entry, 'translation', getattr(entry, 'translated', ''))
                file_name = getattr(entry, 'file_path', getattr(entry, 'file', 'unknown'))
                if hasattr(file_name, '__fspath__'):  # Path 객체인 경우
                    from pathlib import Path
                    file_name = Path(file_name).name

            # 수정본
            modified = self.modified_entries.get(global_idx, '')

            # 번호
            item_num = QTableWidgetItem(str(global_idx + 1))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_num)

            # 파일
            item_file = QTableWidgetItem(str(file_name))
            item_file.setFlags(item_file.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_file)

            # 원문
            item_original = QTableWidgetItem(original)
            item_original.setFlags(item_original.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_original)

            # AI 번역
            item_translated = QTableWidgetItem(translated)
            item_translated.setFlags(item_translated.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, item_translated)

            # 수정본 (편집 가능)
            item_modified = QTableWidgetItem(modified)
            item_modified.setFlags(item_modified.flags() | Qt.ItemFlag.ItemIsEditable)
            item_modified.setBackground(QColor(255, 255, 200))  # 노란색 배경

            # 수정된 항목이면 강조
            if modified:
                item_modified.setBackground(QColor(200, 255, 200))  # 연두색 배경
                item_modified.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))

            self.table.setItem(row, 4, item_modified)

        # 셀 편집 시그널 연결
        self.table.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, col):
        """셀 내용 변경 시"""
        if col != 4:  # 수정본 컬럼만 처리
            return

        # 전체 엔트리에서의 인덱스 계산
        start_idx = self.current_page * self.items_per_page
        entry = self.filtered_entries[start_idx + row]
        global_idx = self.entries.index(entry)

        # 수정본 내용 가져오기
        item = self.table.item(row, col)
        if item:
            modified_text = item.text().strip()

            # 수정본이 비어있지 않으면 저장
            if modified_text:
                self.modified_entries[global_idx] = modified_text
                # 셀 강조
                item.setBackground(QColor(200, 255, 200))
                item.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
            else:
                # 수정본이 비어있으면 제거
                if global_idx in self.modified_entries:
                    del self.modified_entries[global_idx]
                item.setBackground(QColor(255, 255, 200))
                item.setFont(QFont("맑은 고딕", 9))

            # 시그널 발송
            self.entry_modified.emit(global_idx, modified_text)

            # 요약 업데이트
            self.update_summary()

    def update_summary(self):
        """수정 사항 요약 업데이트"""
        count = len(self.modified_entries)
        self.summary_label.setText(f"수정된 항목: {count}개")

        if count > 0:
            self.summary_label.setStyleSheet(
                "padding: 10px; background: #d4edda; border-radius: 4px; color: #155724; font-weight: bold;"
            )
        else:
            self.summary_label.setStyleSheet(
                "padding: 10px; background: #e7f3ff; border-radius: 4px; color: #004085;"
            )

    def go_first_page(self):
        """첫 페이지로"""
        self.current_page = 0
        self.update_view()

    def go_prev_page(self):
        """이전 페이지"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_view()

    def go_next_page(self):
        """다음 페이지"""
        total_pages = max(1, (len(self.filtered_entries) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_view()

    def go_last_page(self):
        """마지막 페이지로"""
        total_pages = max(1, (len(self.filtered_entries) + self.items_per_page - 1) // self.items_per_page)
        self.current_page = total_pages - 1
        self.update_view()

    def go_to_page(self):
        """특정 페이지로 이동"""
        try:
            page_num = int(self.page_input.text()) - 1
            total_pages = max(1, (len(self.filtered_entries) + self.items_per_page - 1) // self.items_per_page)

            if 0 <= page_num < total_pages:
                self.current_page = page_num
                self.update_view()
            else:
                self.page_input.setText(str(self.current_page + 1))
        except ValueError:
            self.page_input.setText(str(self.current_page + 1))

    def get_modified_entries(self):
        """수정된 항목 반환"""
        return self.modified_entries.copy()

    def apply_modified_entries(self, modified_entries):
        """외부에서 수정된 항목 적용 (Excel 가져오기 등)"""
        self.modified_entries = modified_entries.copy()
        self.update_view()
