"""세션 관리 Mixin 클래스"""
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox
import json
import shutil


class SessionManagerMixin:
    """세션 저장/복원 기능을 제공하는 Mixin 클래스"""

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
            # 입력 경로 복원 및 게임 형식 검증
            game_path = None
            if session_data.get("last_input_path"):
                game_path = Path(session_data["last_input_path"])
                self.input_path.setText(session_data["last_input_path"])

            # 게임 형식 검증 (게임 경로가 있는 경우)
            if game_path and game_path.exists():
                from core.game_language_detector import GameLanguageDetector
                detector = GameLanguageDetector()
                format_info = detector.detect_game_format(game_path)

                if not format_info['is_naninovel']:
                    # 비Naninovel 게임 경고
                    warning_msg = (
                        f"⚠️ 이 프로젝트는 지원하지 않는 게임 형식입니다.\n\n"
                        f"{format_info['message']}\n\n"
                    )
                    if format_info.get('details'):
                        warning_msg += f"{format_info['details']}\n\n"
                    warning_msg += (
                        f"이 프로젝트를 삭제하고 세션을 정리하시겠습니까?\n\n"
                        f"• 예: 프로젝트 삭제 및 세션 정리\n"
                        f"• 아니오: 프로젝트 유지 (사용 불가)"
                    )

                    reply = QMessageBox.question(
                        self,
                        "지원하지 않는 게임 형식",
                        warning_msg,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        # 프로젝트 삭제
                        if project_path.exists():
                            shutil.rmtree(project_path)
                            print(f"🗑️ 프로젝트 삭제됨: {project_path}")

                        # 세션 파일 삭제
                        if session_file.exists():
                            session_file.unlink()
                            print("🗑️ 세션 파일 삭제됨")

                        QMessageBox.information(
                            self,
                            "정리 완료",
                            "프로젝트와 세션이 삭제되었습니다."
                        )
                        return
                    else:
                        # 세션만 삭제하고 종료
                        if session_file.exists():
                            session_file.unlink()
                        print("⚠️ 비Naninovel 프로젝트 - 세션만 삭제됨")
                        return

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
