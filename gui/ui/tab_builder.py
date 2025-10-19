"""UI 탭 생성을 위한 Mixin 클래스"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QComboBox, QCheckBox, QProgressBar, QTextEdit,
    QLineEdit, QTabWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from gui.widgets.translation_viewer import TranslationViewerWidget


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

        # 챕터 감지 버튼은 숨김 처리 (모든 게임에서 동일한 UX 제공)
        # btn_detect_chapters = QPushButton("📖 챕터 감지")
        # btn_detect_chapters.clicked.connect(self.detect_chapters)
        # input_layout.addWidget(btn_detect_chapters)

        layout.addWidget(input_group)

        # 챕터 선택 결과 표시 (숨김 처리 - 모든 게임에서 동일한 UX 제공)
        # self.chapter_info_label = QLabel("")
        # self.chapter_info_label.setStyleSheet("""
        #     QLabel {
        #         background-color: #f0f8ff;
        #         color: #000000;
        #         padding: 10px;
        #         border-radius: 5px;
        #         border: 2px solid #4a90e2;
        #     }
        # """)
        # self.chapter_info_label.setVisible(False)
        # layout.addWidget(self.chapter_info_label)

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

        # 게임 정보 표시 (자동 감지)
        self.game_info_label = QLabel("")
        self.game_info_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #ced4da;
            }
        """)
        self.game_info_label.setVisible(False)
        self.game_info_label.setWordWrap(True)
        layout.addWidget(self.game_info_label)

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

        # 게임 내 대체할 언어 선택 (Unity 전용 - RPG Maker는 숨김)
        self.replace_lang_group = QGroupBox("🔄 게임에 적용할 언어 (어떤 언어를 대체할지)")
        replace_layout = QVBoxLayout()
        self.replace_lang_group.setLayout(replace_layout)

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

        layout.addWidget(self.replace_lang_group)

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

        # 배치 크기 설정
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("배치 크기:"))
        self.batch_size_combo = QComboBox()
        self.batch_size_combo.addItems([
            "1개씩 (기존 방식)",
            "10개씩 묶어서",
            "50개씩 묶어서",
            "100개씩 묶어서"
        ])
        self.batch_size_combo.setCurrentIndex(0)
        self.batch_size_combo.setToolTip("한 번에 몇 개의 텍스트를 번역 API에 전송할지 설정합니다")
        batch_layout.addWidget(self.batch_size_combo)
        batch_layout.addStretch()
        options_layout.addLayout(batch_layout)

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
        # 번역 실행 버튼 라인
        translate_layout = QHBoxLayout()
        translate_layout.addWidget(btn_translate)
        layout.addLayout(translate_layout)

        # 적용 버튼 라인 (번역 + RPG Maker 전용)
        apply_layout = QHBoxLayout()

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
        apply_layout.addWidget(self.btn_apply, 2)  # 2배 너비

        # RPG Maker 전용: 플러그인 설치
        self.btn_install_plugin = QPushButton("🔌 플러그인 설치")
        self.btn_install_plugin.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        self.btn_install_plugin.setMinimumHeight(50)
        self.btn_install_plugin.clicked.connect(self.install_rpgmaker_plugin)
        self.btn_install_plugin.setVisible(False)  # 초기에는 숨김
        self.btn_install_plugin.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
        """)
        apply_layout.addWidget(self.btn_install_plugin, 1)  # 1배 너비

        # RPG Maker 전용: 패치 내보내기
        self.btn_export_patch = QPushButton("📦 패치 내보내기")
        self.btn_export_patch.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        self.btn_export_patch.setMinimumHeight(50)
        self.btn_export_patch.clicked.connect(self.export_translation_patch)
        self.btn_export_patch.setVisible(False)  # 초기에는 숨김
        self.btn_export_patch.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        apply_layout.addWidget(self.btn_export_patch, 1)  # 1배 너비

        layout.addLayout(apply_layout)

        return tab

    def create_excel_tab(self):
        """Excel 검수 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 제목
        title = QLabel("📊 번역 검수")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # 설명
        info = QLabel(
            "번역 결과를 확인하고 수정할 수 있습니다. 수정본 컬럼에서 직접 편집하거나 Excel로 내보내기/가져오기가 가능합니다."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # 버튼 영역
        button_layout = QHBoxLayout()

        btn_load = QPushButton("📂 번역 결과 불러오기")
        btn_load.clicked.connect(self.load_translation_for_review)
        btn_load.setMinimumHeight(40)
        button_layout.addWidget(btn_load)

        self.btn_export_excel = QPushButton("📤 Excel 내보내기")
        self.btn_export_excel.clicked.connect(self.export_excel)
        self.btn_export_excel.setMinimumHeight(40)
        self.btn_export_excel.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.btn_export_excel)

        btn_import = QPushButton("📥 수정본 Excel 가져오기")
        btn_import.clicked.connect(self.import_excel_to_viewer)
        btn_import.setMinimumHeight(40)
        button_layout.addWidget(btn_import)

        btn_save = QPushButton("💾 수정 사항 저장")
        btn_save.clicked.connect(self.save_viewer_modifications)
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(btn_save)

        layout.addLayout(button_layout)

        # 번역 뷰어 위젯
        self.translation_viewer = TranslationViewerWidget()
        layout.addWidget(self.translation_viewer)

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

        info_text = QLabel("번역 시 적용할 규칙을 설정합니다.")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        # 텍스트 에디터
        self.rules_editor = QTextEdit()
        self.rules_editor.setFont(QFont("Consolas", 10))
        layout.addWidget(self.rules_editor)

        # 버튼
        btn_layout = QHBoxLayout()

        btn_load_default = QPushButton("기본값 불러오기")
        btn_load_default.clicked.connect(self.load_default_rules)
        btn_layout.addWidget(btn_load_default)

        btn_load_file = QPushButton("📂 파일 불러오기")
        btn_load_file.clicked.connect(lambda: self._load_rules_from_file())
        btn_layout.addWidget(btn_load_file)

        btn_save = QPushButton("💾 저장")
        btn_save.clicked.connect(lambda: self.save_config_file("config/translation_rules.yaml", self.rules_editor))
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

        # 초기 로드 (examples 폴더의 실제 사용 규칙)
        self.load_config_file("config/translation_rules.yaml", self.rules_editor, fallback="examples/translation_rules.txt")

        return tab

    def _load_rules_from_file(self):
        """파일에서 규칙 불러오기"""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "규칙 파일 선택",
            "config/rules",
            "YAML Files (*.yaml *.yml);;Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.rules_editor.setPlainText(content)
                print(f"✅ 규칙 파일 로드: {file_path}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "파일 로드 실패", f"❌ 파일 로드 실패:\n{str(e)}")

    def create_glossary_editor(self):
        """용어집 에디터 - 4가지 사전 관리"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 설명
        info_label = QLabel(
            "번역 시 사용할 용어를 관리합니다. JSON 형식으로 저장됩니다.\n"
            "형식: {\"원문\": \"번역문\", ...}"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 사전 탭
        dict_tabs = QTabWidget()
        layout.addWidget(dict_tabs)

        # 1. 민감한 표현 치환 (API 규칙 회피)
        sensitive_tab = self._create_dict_editor(
            dict_name="sensitive_terms",
            title="🔒 민감한 표현 치환",
            description="AI 번역 API의 사용 규칙에 어긋날 수 있는 표현을 미리 치환합니다.\n"
                       "번역 전에 외국어를 완곡한 표현으로 바꾼 후 번역하고, 번역 후 다시 원하는 표현으로 복원합니다.",
            default_content=self._get_default_sensitive_terms()
        )
        dict_tabs.addTab(sensitive_tab, "🔒 민감 표현")

        # 2. 고유명사
        proper_nouns_tab = self._create_dict_editor(
            dict_name="proper_nouns",
            title="📖 고유명사",
            description="인명, 지명, 아이템명 등 고유명사를 관리합니다.",
            default_content=self._get_default_proper_nouns()
        )
        dict_tabs.addTab(proper_nouns_tab, "📖 고유명사")

        # 3. 화자명
        speaker_tab = self._create_dict_editor(
            dict_name="speaker_names",
            title="👤 화자명",
            description="대화창에 표시되는 화자(캐릭터) 이름을 관리합니다.",
            default_content=self._get_default_speaker_names()
        )
        dict_tabs.addTab(speaker_tab, "👤 화자명")

        # 4. 감탄사
        interjection_tab = self._create_dict_editor(
            dict_name="interjections",
            title="💬 감탄사",
            description="감탄사, 추임새 등을 관리합니다.",
            default_content=self._get_default_interjections()
        )
        dict_tabs.addTab(interjection_tab, "💬 감탄사")

        return tab

    def _create_dict_editor(self, dict_name, title, description, default_content):
        """개별 사전 에디터 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 제목 및 설명
        title_label = QLabel(title)
        title_label.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 5px; background: #f9f9f9; border-radius: 4px;")
        layout.addWidget(desc_label)

        # JSON 에디터
        editor = QTextEdit()
        editor.setFont(QFont("Consolas", 10))
        editor.setPlaceholderText('{\n  "원문": "번역문",\n  "例": "예시"\n}')
        layout.addWidget(editor)

        # 사전 에디터를 인스턴스 변수로 저장
        setattr(self, f"{dict_name}_editor", editor)

        # 버튼
        btn_layout = QHBoxLayout()

        btn_load_default = QPushButton("📋 기본값 불러오기")
        btn_load_default.clicked.connect(
            lambda: editor.setPlainText(default_content)
        )
        btn_layout.addWidget(btn_load_default)

        btn_load_file = QPushButton("📂 파일 불러오기")
        btn_load_file.clicked.connect(
            lambda: self._load_dict_from_file(editor)
        )
        btn_layout.addWidget(btn_load_file)

        btn_validate = QPushButton("✓ JSON 검증")
        btn_validate.clicked.connect(
            lambda: self._validate_json(editor)
        )
        btn_layout.addWidget(btn_validate)

        btn_save = QPushButton("💾 저장")
        btn_save.clicked.connect(
            lambda: self._save_dict_file(f"config/dicts/{dict_name}.json", editor)
        )
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

        # 초기 로드
        self._load_dict_file(f"config/dicts/{dict_name}.json", editor, default_content)

        return tab

    def _load_dict_file(self, filepath, editor, default_content):
        """사전 파일 로드"""
        from pathlib import Path
        import json

        file_path = Path(filepath)

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 보기 좋게 포맷팅
                    editor.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
            except Exception as e:
                editor.setPlainText(default_content)
                print(f"⚠️ 사전 파일 로드 실패: {e}")
        else:
            # 기본값 설정
            editor.setPlainText(default_content)

    def _save_dict_file(self, filepath, editor):
        """사전 파일 저장"""
        from pathlib import Path
        from PyQt6.QtWidgets import QMessageBox
        import json

        try:
            # JSON 검증
            content = editor.toPlainText()
            data = json.loads(content)

            # 파일 저장
            file_path = Path(filepath)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "저장 완료", f"✅ 저장 완료!\n\n{filepath}")
            print(f"✅ 사전 저장: {filepath}")

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON 오류", f"❌ JSON 형식이 올바르지 않습니다!\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"❌ 저장 실패:\n{str(e)}")

    def _validate_json(self, editor):
        """JSON 형식 검증"""
        from PyQt6.QtWidgets import QMessageBox
        import json

        try:
            content = editor.toPlainText()
            data = json.loads(content)
            QMessageBox.information(
                self,
                "검증 성공",
                f"✅ JSON 형식이 올바릅니다!\n\n총 {len(data)}개 항목"
            )
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "JSON 오류",
                f"❌ JSON 형식이 올바르지 않습니다!\n\n{str(e)}"
            )

    def _load_default_from_file(self, dict_name):
        """기본값 파일 로드"""
        from pathlib import Path
        import json

        default_file = Path(f"config/dicts/defaults/{dict_name}.json")

        if default_file.exists():
            try:
                with open(default_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ 기본값 파일 로드 실패: {e}")
                return json.dumps({}, ensure_ascii=False, indent=2)
        else:
            # 파일이 없으면 빈 JSON 반환
            return json.dumps({}, ensure_ascii=False, indent=2)

    def _get_default_sensitive_terms(self):
        """민감한 표현 기본값"""
        return self._load_default_from_file("sensitive_terms")

    def _get_default_proper_nouns(self):
        """고유명사 기본값"""
        return self._load_default_from_file("proper_nouns")

    def _get_default_speaker_names(self):
        """화자명 기본값"""
        return self._load_default_from_file("speaker_names")

    def _get_default_interjections(self):
        """감탄사 기본값"""
        return self._load_default_from_file("interjections")

    def _load_dict_from_file(self, editor):
        """파일에서 사전 불러오기"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "사전 파일 선택",
            "config/dicts",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 보기 좋게 포맷팅
                    editor.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
                print(f"✅ 사전 파일 로드: {file_path}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "JSON 오류", f"❌ JSON 형식이 올바르지 않습니다!\n\n{str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "파일 로드 실패", f"❌ 파일 로드 실패:\n{str(e)}")
