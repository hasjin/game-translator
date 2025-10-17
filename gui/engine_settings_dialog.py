"""번역 엔진 설정 다이얼로그

API 키 입력 및 엔진별 설정
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFormLayout, QTextEdit,
    QCheckBox, QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json
from pathlib import Path


class EngineSettingsDialog(QDialog):
    """번역 엔진 설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("번역 엔진 설정")
        self.setMinimumSize(700, 600)

        # 설정 파일
        self.config_path = Path("config/engine_settings.json")
        self.settings = self.load_settings()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 탭
        tabs = QTabWidget()
        tabs.addTab(self.create_api_keys_tab(), "🔑 API 키")
        tabs.addTab(self.create_engine_config_tab(), "⚙️ 엔진 설정")
        tabs.addTab(self.create_cost_info_tab(), "💰 비용 정보")

        layout.addWidget(tabs)

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_test = QPushButton("🧪 연결 테스트")
        btn_test.clicked.connect(self.test_connection)
        button_layout.addWidget(btn_test)

        btn_save = QPushButton("💾 저장")
        btn_save.clicked.connect(self.save_settings)
        button_layout.addWidget(btn_save)

        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)

    def create_api_keys_tab(self) -> QWidget:
        """API 키 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Claude
        claude_group = QGroupBox("Claude API")
        claude_layout = QFormLayout()

        self.claude_key_input = QLineEdit()
        self.claude_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.claude_key_input.setText(self.settings.get('claude_api_key', ''))
        self.claude_key_input.setPlaceholderText("sk-ant-api...")
        claude_layout.addRow("API 키:", self.claude_key_input)

        btn_show_claude = QPushButton("👁️ 보기")
        btn_show_claude.setCheckable(True)
        btn_show_claude.toggled.connect(
            lambda checked: self.claude_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        claude_layout.addRow("", btn_show_claude)

        claude_group.setLayout(claude_layout)
        layout.addWidget(claude_group)

        # OpenAI
        openai_group = QGroupBox("OpenAI API (ChatGPT)")
        openai_layout = QFormLayout()

        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setText(self.settings.get('openai_api_key', ''))
        self.openai_key_input.setPlaceholderText("sk-...")
        openai_layout.addRow("API 키:", self.openai_key_input)

        btn_show_openai = QPushButton("👁️ 보기")
        btn_show_openai.setCheckable(True)
        btn_show_openai.toggled.connect(
            lambda checked: self.openai_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        openai_layout.addRow("", btn_show_openai)

        openai_group.setLayout(openai_layout)
        layout.addWidget(openai_group)

        # DeepL
        deepl_group = QGroupBox("DeepL API")
        deepl_layout = QFormLayout()

        self.deepl_key_input = QLineEdit()
        self.deepl_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.deepl_key_input.setText(self.settings.get('deepl_api_key', ''))
        deepl_layout.addRow("API 키:", self.deepl_key_input)

        self.deepl_free_cb = QCheckBox("무료 플랜 (500k자/월)")
        self.deepl_free_cb.setChecked(self.settings.get('deepl_free', False))
        deepl_layout.addRow("", self.deepl_free_cb)

        deepl_group.setLayout(deepl_layout)
        layout.addWidget(deepl_group)

        # Papago
        papago_group = QGroupBox("Papago API")
        papago_layout = QFormLayout()

        self.papago_id_input = QLineEdit()
        self.papago_id_input.setText(self.settings.get('papago_client_id', ''))
        self.papago_id_input.setPlaceholderText("Client ID")
        papago_layout.addRow("Client ID:", self.papago_id_input)

        self.papago_secret_input = QLineEdit()
        self.papago_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.papago_secret_input.setText(self.settings.get('papago_client_secret', ''))
        self.papago_secret_input.setPlaceholderText("Client Secret")
        papago_layout.addRow("Client Secret:", self.papago_secret_input)

        papago_group.setLayout(papago_layout)
        layout.addWidget(papago_group)

        layout.addStretch()

        # 안내
        info = QLabel("💡 API 키는 암호화되어 로컬에 저장됩니다.")
        info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info)

        return tab

    def create_engine_config_tab(self) -> QWidget:
        """엔진 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 로컬 모델
        local_group = QGroupBox("로컬 모델 (Ollama/LLaMA)")
        local_layout = QFormLayout()

        self.local_api_url = QLineEdit()
        self.local_api_url.setText(self.settings.get('local_api_url', 'http://localhost:11434'))
        self.local_api_url.setPlaceholderText("http://localhost:11434")
        local_layout.addRow("API URL:", self.local_api_url)

        self.local_model_name = QLineEdit()
        self.local_model_name.setText(self.settings.get('local_model_name', 'llama3:8b'))
        self.local_model_name.setPlaceholderText("llama3:8b")
        local_layout.addRow("모델 이름:", self.local_model_name)

        local_group.setLayout(local_layout)
        layout.addWidget(local_group)

        # 번역 옵션
        options_group = QGroupBox("번역 옵션")
        options_layout = QFormLayout()

        self.batch_size_input = QLineEdit()
        self.batch_size_input.setText(str(self.settings.get('batch_size', 20)))
        self.batch_size_input.setPlaceholderText("20")
        options_layout.addRow("배치 크기:", self.batch_size_input)

        self.context_window = QLineEdit()
        self.context_window.setText(str(self.settings.get('context_window', 2)))
        self.context_window.setPlaceholderText("2")
        options_layout.addRow("문맥 크기 (이전 대사):", self.context_window)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        layout.addStretch()
        return tab

    def create_cost_info_tab(self) -> QWidget:
        """비용 정보 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info_text = """
# 번역 엔진별 비용 정보 (1,000 대사 기준)

## 💰 유료 AI 모델

### Claude API
- **Haiku 3.5**: 약 $0.52 (가성비 최고 ⭐)
  - Input: $0.80/1M tokens
  - Output: $4.00/1M tokens

- **Sonnet 4**: 약 $2.00 (고품질)
  - Input: $3.00/1M tokens
  - Output: $15.00/1M tokens

### OpenAI (ChatGPT)
- **GPT-4o**: 약 $1.25
  - Input: $2.50/1M tokens
  - Output: $10.00/1M tokens

- **GPT-3.5 Turbo**: 약 $0.15 (저렴)
  - Input: $0.50/1M tokens
  - Output: $1.50/1M tokens

### DeepL
- **Pro**: 약 $0.50/1,000대사
  - $25 per 1M characters

## 🆓 무료/제한적 무료

### Google Translate
- **완전 무료** (비공식 API)
- 품질: 중간

### DeepL 무료
- **500,000자/월 무료**
- 품질: 우수

### Papago
- **10,000자/일 무료**
- 초과 시 소액 과금

### 로컬 모델
- **완전 무료** (하드웨어 필요)
- Ollama, LLaMA 등
- 품질: 모델에 따라 다름

## 💡 추천

1. **가성비 최고**: Claude Haiku 3.5
2. **무료 고품질**: DeepL 무료 (500k자/월)
3. **완전 무료**: Google Translate
4. **로컬**: Ollama (하드웨어 있다면)
"""

        info_display = QTextEdit()
        info_display.setReadOnly(True)
        info_display.setMarkdown(info_text)
        layout.addWidget(info_display)

        return tab

    def load_settings(self) -> dict:
        """설정 로드"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_settings(self):
        """설정 저장"""
        self.settings = {
            'claude_api_key': self.claude_key_input.text(),
            'openai_api_key': self.openai_key_input.text(),
            'deepl_api_key': self.deepl_key_input.text(),
            'deepl_free': self.deepl_free_cb.isChecked(),
            'papago_client_id': self.papago_id_input.text(),
            'papago_client_secret': self.papago_secret_input.text(),
            'local_api_url': self.local_api_url.text(),
            'local_model_name': self.local_model_name.text(),
            'batch_size': int(self.batch_size_input.text() or 20),
            'context_window': int(self.context_window.text() or 2)
        }

        # 저장
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2)

        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        self.accept()

    def test_connection(self):
        """연결 테스트"""
        QMessageBox.information(self, "테스트", "연결 테스트 기능은 구현 중입니다.")

    def get_settings(self) -> dict:
        """설정 가져오기"""
        return self.settings
