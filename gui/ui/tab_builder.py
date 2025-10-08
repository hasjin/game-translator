"""UI 탭 생성을 위한 Mixin 클래스"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QComboBox, QCheckBox, QProgressBar, QTextEdit,
    QLineEdit, QTabWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class TabBuilderMixin:
    """MainWindow에서 사용할 UI 탭 생성 Mixin"""

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

        # 게임 적용 시 자동 백업 안내
        backup_label = QLabel("💾 게임 적용 시 원본 파일 자동 백업")
        backup_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        backup_label.setToolTip("게임에 번역을 적용할 때 원본 파일이 자동으로 백업됩니다")
        options_layout.addWidget(backup_label)

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
