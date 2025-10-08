"""API 키 설정 다이얼로그"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QWidget, QMessageBox,
    QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

# security 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.secure_storage import SecureStorage


class APISettingsDialog(QDialog):
    """API 키 설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 API 키 설정")
        self.setMinimumSize(600, 500)

        # 보안 저장소
        self.storage = SecureStorage()

        # 레이아웃
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 설명
        info = QLabel(
            "API 키는 암호화되어 안전하게 저장됩니다.\n"
            "머신별 고유 키로 암호화되어 외부에서 복호화할 수 없습니다."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # 탭
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 각 서비스별 탭
        tabs.addTab(self.create_service_tab("Claude"), "Claude")
        tabs.addTab(self.create_service_tab("OpenAI"), "ChatGPT")
        tabs.addTab(self.create_service_tab("DeepL"), "DeepL")
        tabs.addTab(self.create_service_tab("Papago"), "Papago")
        tabs.addTab(self.create_backup_tab(), "백업/복원")

        # 버튼
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

    def create_service_tab(self, service: str) -> QWidget:
        """서비스별 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 서비스 정보
        info_map = {
            "Claude": {
                "name": "Claude (Anthropic)",
                "url": "https://console.anthropic.com/settings/keys",
                "key_format": "sk-ant-api03-...",
                "help": "1. console.anthropic.com 접속\n"
                        "2. Settings → API Keys\n"
                        "3. Create Key 클릭\n"
                        "4. 생성된 키 복사"
            },
            "OpenAI": {
                "name": "ChatGPT (OpenAI)",
                "url": "https://platform.openai.com/api-keys",
                "key_format": "sk-proj-...",
                "help": "1. platform.openai.com 접속\n"
                        "2. API keys 메뉴\n"
                        "3. Create new secret key\n"
                        "4. 생성된 키 복사"
            },
            "DeepL": {
                "name": "DeepL",
                "url": "https://www.deepl.com/account/summary",
                "key_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx",
                "help": "1. deepl.com/account 접속\n"
                        "2. API 탭\n"
                        "3. Authentication Key 확인"
            },
            "Papago": {
                "name": "Papago (Naver)",
                "url": "https://developers.naver.com/apps",
                "key_format": "Client ID + Client Secret",
                "help": "1. developers.naver.com 접속\n"
                        "2. Application → 내 애플리케이션\n"
                        "3. Papago 번역 API 추가\n"
                        "4. Client ID, Secret 확인"
            }
        }

        info = info_map.get(service, {})

        # 서비스 이름
        name_label = QLabel(f"🔑 {info.get('name', service)}")
        name_label.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        layout.addWidget(name_label)

        # 도움말
        help_group = QGroupBox("📖 API 키 발급 방법")
        help_layout = QVBoxLayout()
        help_group.setLayout(help_layout)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(100)
        help_text.setText(info.get('help', ''))
        help_layout.addWidget(help_text)

        # URL 버튼
        btn_open = QPushButton(f"🌐 {info.get('url', '')}")
        btn_open.clicked.connect(lambda: self.open_url(info.get('url', '')))
        help_layout.addWidget(btn_open)

        layout.addWidget(help_group)

        # 현재 저장된 키 표시
        status_group = QGroupBox("📊 현재 상태")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)

        service_key = service.lower()
        if self.storage.has_api_key(service_key):
            masked = self.storage.get_masked_key(service_key)
            status_label = QLabel(f"✅ 저장됨: {masked}")
            status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_label = QLabel("❌ 저장되지 않음")
            status_label.setStyleSheet("color: red;")

        status_layout.addWidget(status_label)
        layout.addWidget(status_group)

        # API 키 입력
        key_group = QGroupBox("🔐 API 키 입력")
        key_layout = QVBoxLayout()
        key_group.setLayout(key_layout)

        key_layout.addWidget(QLabel(f"형식: {info.get('key_format', '')}"))

        api_key_input = QLineEdit()
        api_key_input.setPlaceholderText("API 키를 입력하세요...")
        api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # 비밀번호 모드
        key_layout.addWidget(api_key_input)

        # 표시/숨김 토글
        btn_toggle = QPushButton("👁️ 키 표시")
        btn_toggle.setCheckable(True)
        btn_toggle.toggled.connect(
            lambda checked: api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_layout.addWidget(btn_toggle)

        # 저장/삭제 버튼
        btn_layout = QHBoxLayout()
        key_layout.addLayout(btn_layout)

        btn_save = QPushButton("💾 저장")
        btn_save.clicked.connect(
            lambda: self.save_api_key(service_key, api_key_input.text(), status_label)
        )
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_layout.addWidget(btn_save)

        btn_delete = QPushButton("🗑️ 삭제")
        btn_delete.clicked.connect(
            lambda: self.delete_api_key(service_key, status_label)
        )
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        btn_layout.addWidget(btn_delete)

        btn_test = QPushButton("🧪 연결 테스트")
        btn_test.clicked.connect(lambda: self.test_connection(service_key))
        btn_layout.addWidget(btn_test)

        layout.addWidget(key_group)

        layout.addStretch()

        return tab

    def create_backup_tab(self) -> QWidget:
        """백업/복원 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("💾 API 키 백업 및 복원"))

        # 백업
        backup_group = QGroupBox("📤 백업")
        backup_layout = QVBoxLayout()
        backup_group.setLayout(backup_layout)

        backup_layout.addWidget(QLabel(
            "모든 API 키를 비밀번호로 보호된 파일로 백업합니다.\n"
            "다른 컴퓨터에서도 복원 가능합니다."
        ))

        backup_pw = QLineEdit()
        backup_pw.setPlaceholderText("백업 비밀번호 입력...")
        backup_pw.setEchoMode(QLineEdit.EchoMode.Password)
        backup_layout.addWidget(backup_pw)

        btn_backup = QPushButton("💾 백업 파일 생성")
        btn_backup.clicked.connect(lambda: self.export_backup(backup_pw.text()))
        backup_layout.addWidget(btn_backup)

        layout.addWidget(backup_group)

        # 복원
        restore_group = QGroupBox("📥 복원")
        restore_layout = QVBoxLayout()
        restore_group.setLayout(restore_layout)

        restore_layout.addWidget(QLabel(
            "백업 파일에서 API 키를 복원합니다."
        ))

        restore_pw = QLineEdit()
        restore_pw.setPlaceholderText("백업 비밀번호 입력...")
        restore_pw.setEchoMode(QLineEdit.EchoMode.Password)
        restore_layout.addWidget(restore_pw)

        btn_restore = QPushButton("📥 백업 파일 선택 및 복원")
        btn_restore.clicked.connect(lambda: self.import_backup(restore_pw.text()))
        restore_layout.addWidget(btn_restore)

        layout.addWidget(restore_group)

        layout.addStretch()

        return tab

    def save_api_key(self, service: str, api_key: str, status_label: QLabel):
        """API 키 저장"""
        if not api_key.strip():
            QMessageBox.warning(self, "경고", "API 키를 입력하세요!")
            return

        try:
            self.storage.save_api_key(service, api_key.strip())
            masked = self.storage.get_masked_key(service)

            status_label.setText(f"✅ 저장됨: {masked}")
            status_label.setStyleSheet("color: green; font-weight: bold;")

            QMessageBox.information(
                self,
                "완료",
                f"✅ API 키가 암호화되어 저장되었습니다.\n\n"
                f"저장된 키: {masked}"
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{str(e)}")

    def delete_api_key(self, service: str, status_label: QLabel):
        """API 키 삭제"""
        reply = QMessageBox.question(
            self,
            "확인",
            f"{service} API 키를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.storage.delete_api_key(service)
            status_label.setText("❌ 저장되지 않음")
            status_label.setStyleSheet("color: red;")
            QMessageBox.information(self, "완료", "API 키가 삭제되었습니다.")

    def test_connection(self, service: str):
        """연결 테스트"""
        api_key = self.storage.get_api_key(service)

        if not api_key:
            QMessageBox.warning(self, "경고", "저장된 API 키가 없습니다!")
            return

        QMessageBox.information(
            self,
            "연결 테스트",
            f"✅ API 키를 찾았습니다.\n\n"
            f"실제 API 호출 테스트는 번역 시 자동으로 수행됩니다."
        )

    def export_backup(self, password: str):
        """백업 내보내기"""
        if not password:
            QMessageBox.warning(self, "경고", "백업 비밀번호를 입력하세요!")
            return

        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "백업 파일 저장",
            "api_keys_backup.enc",
            "Encrypted Files (*.enc)"
        )

        if filename:
            try:
                self.storage.export_for_backup(filename, password)
                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ 백업 완료!\n\n{filename}\n\n"
                    f"이 파일과 비밀번호를 안전하게 보관하세요."
                )
            except Exception as e:
                QMessageBox.critical(self, "오류", f"백업 실패:\n{str(e)}")

    def import_backup(self, password: str):
        """백업 가져오기"""
        if not password:
            QMessageBox.warning(self, "경고", "백업 비밀번호를 입력하세요!")
            return

        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "백업 파일 선택",
            "",
            "Encrypted Files (*.enc)"
        )

        if filename:
            try:
                success = self.storage.import_from_backup(filename, password)

                if success:
                    QMessageBox.information(
                        self,
                        "완료",
                        "✅ 백업 복원 완료!\n\n"
                        "다이얼로그를 다시 열면 복원된 키를 확인할 수 있습니다."
                    )
                    self.accept()  # 다이얼로그 닫기
                else:
                    QMessageBox.critical(
                        self,
                        "오류",
                        "❌ 복원 실패!\n\n"
                        "비밀번호가 잘못되었거나 파일이 손상되었습니다."
                    )
            except Exception as e:
                QMessageBox.critical(self, "오류", f"복원 실패:\n{str(e)}")

    def open_url(self, url: str):
        """URL 열기"""
        import webbrowser
        webbrowser.open(url)


# 테스트
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = APISettingsDialog()
    dialog.exec()
