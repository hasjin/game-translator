"""프로젝트 관리 기능 Mixin"""
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox
import json
import re
import shutil
from datetime import datetime


class ProjectManagerMixin:
    """프로젝트 생성, 선택, 번역 결과 저장/로드, 비용 관리 기능을 제공하는 Mixin 클래스"""

    def auto_create_or_select_project(self, folder_path):
        """폴더에서 자동으로 게임 이름 감지하고 프로젝트 생성/선택"""
        from core.game_language_detector import GameLanguageDetector

        folder = Path(folder_path)

        # 게임 형식 감지
        detector = GameLanguageDetector()
        format_info = detector.detect_game_format(folder)
        game_type = format_info.get('game_type', 'unknown')

        # 지원하지 않는 게임 형식 체크
        if game_type == 'unknown':
            detailed_message = f"{format_info['message']}\n\n"
            if format_info.get('details'):
                detailed_message += f"{format_info['details']}\n\n"
            detailed_message += "이 게임은 현재 지원하지 않는 형식입니다.\n"
            detailed_message += "Naninovel 또는 일반 Unity 게임만 지원합니다."

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("지원하지 않는 게임 형식")
            msg_box.setText(detailed_message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            return

        # 일반 Unity 게임 안내 메시지
        if game_type in ['unity_generic', 'unity_other']:
            info_message = f"{format_info['message']}\n\n"
            if format_info.get('details'):
                info_message += f"{format_info['details']}\n\n"
            info_message += "프로젝트를 생성하고 번역을 진행할 수 있습니다."

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("일반 Unity 게임 감지")
            msg_box.setText(info_message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            # return 하지 않고 계속 진행

        # Naninovel 게임이지만 특수한 구조일 경우 안내
        if format_info['is_naninovel']:
            warnings = []
            if not format_info.get('has_language_folders'):
                warnings.append("⚠️  언어별 폴더 구조가 없습니다.\n   → 기본 언어를 통째로 교체하는 방식으로 진행됩니다.")
            if not format_info.get('has_chapter_structure'):
                warnings.append("⚠️  챕터별 구조가 없습니다.\n   → 전체 스크립트를 한번에 처리합니다.")

            if warnings:
                info_message = f"{format_info['message']}\n\n"
                if format_info.get('details'):
                    info_message += f"{format_info['details']}\n\n"
                info_message += "진행하시겠습니까?"

                reply = QMessageBox.question(
                    self,
                    "게임 구조 확인",
                    info_message,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    return

        # 게임 이름 추출 시도
        game_name = None

        # 1. 실행 파일 찾기 (.exe)
        exe_files = list(folder.glob("*.exe"))
        if exe_files:
            game_name = exe_files[0].stem

        # 2. _Data 폴더에서 추출
        if not game_name:
            for data_folder in folder.glob("*_Data"):
                game_name = data_folder.name.replace("_Data", "")
                break

        # 3. 폴더명 사용
        if not game_name:
            game_name = folder.name

        # 특수문자 제거 및 정리
        game_name = re.sub(r'[<>:"/\\|?*]', '', game_name)
        game_name = game_name.strip()

        if not game_name:
            game_name = "Unnamed_Game"

        # 프로젝트가 이미 존재하는지 확인
        project_path = self.projects_dir / game_name

        if project_path.exists():
            # 이전 작업이 있음 - 사용자에게 물어보기
            reply = QMessageBox.question(
                self,
                "이전 작업 발견",
                f"'{game_name}'의 이전 작업이 있습니다.\n\n"
                f"이어서 하시겠습니까?\n\n"
                f"• 예: 이전 작업 이어하기\n"
                f"• 아니오: 임시파일 삭제하고 새로 시작",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                # 임시파일 정리
                extracted_dir = project_path / "extracted"
                translated_dir = project_path / "translated"

                if extracted_dir.exists():
                    shutil.rmtree(extracted_dir)
                    extracted_dir.mkdir()

                if translated_dir.exists():
                    shutil.rmtree(translated_dir)
                    translated_dir.mkdir()

                QMessageBox.information(
                    self,
                    "임시파일 정리 완료",
                    "임시파일이 삭제되었습니다. 새로 시작합니다."
                )

            # 프로젝트 선택
            self.current_project = project_path
            self.project_info_label.setText(f"📂 프로젝트: {game_name}")

            # 이전 번역 결과 로드
            self._load_translation_entries()
        else:
            # 새 프로젝트 생성
            self._create_project_folder(game_name, folder_path)
            self.current_project = self.projects_dir / game_name
            self.project_info_label.setText(f"📂 프로젝트: {game_name} (새로 생성)")

    def _create_project_folder(self, project_name, input_folder=""):
        """프로젝트 폴더 생성"""
        project_path = self.projects_dir / project_name

        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "extracted").mkdir(exist_ok=True)
        (project_path / "translated").mkdir(exist_ok=True)
        (project_path / "config").mkdir(exist_ok=True)

        # 프로젝트 정보 저장
        project_info = {
            "name": project_name,
            "created": str(Path.cwd()),
            "input_folder": input_folder,
            "selected_chapters": []
        }

        with open(project_path / "project.json", 'w', encoding='utf-8') as f:
            json.dump(project_info, f, indent=2, ensure_ascii=False)

    def _save_translation_entries(self):
        """번역 결과를 JSON으로 저장"""
        if not self.current_project or not self.translation_entries:
            return

        entries_file = self.current_project / "translation_entries.json"

        # TranslationEntry 또는 dict를 처리
        entries_data = []
        for entry in self.translation_entries:
            if isinstance(entry, dict):
                # 이미 dict인 경우 (Unity 게임)
                entries_data.append(entry)
            else:
                # TranslationEntry 객체인 경우 (Naninovel)
                entries_data.append(entry.to_dict())

        with open(entries_file, 'w', encoding='utf-8') as f:
            json.dump(entries_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 번역 결과 저장: {len(self.translation_entries)}개 항목")

    def _load_translation_entries(self):
        """이전 번역 결과를 JSON에서 로드"""
        if not self.current_project:
            return

        from core.excel_manager import TranslationEntry

        entries_file = self.current_project / "translation_entries.json"

        if not entries_file.exists():
            return

        try:
            with open(entries_file, 'r', encoding='utf-8') as f:
                entries_data = json.load(f)

            self.translation_entries = [
                TranslationEntry.from_dict(data) for data in entries_data
            ]

            print(f"✅ 이전 번역 결과 로드: {len(self.translation_entries)}개 항목")

            # Excel 버튼 활성화
            self.btn_export_excel.setEnabled(True)

        except Exception as e:
            print(f"⚠️ 번역 결과 로드 실패: {str(e)}")

    def _add_cost_to_project(self, cost_info):
        """프로젝트에 비용/토큰 누적 기록"""
        if not self.current_project:
            return None

        cost_history_file = self.current_project / "cost_history.json"

        # 기존 비용 기록 로드
        if cost_history_file.exists():
            with open(cost_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "records": []
            }

        # 새 기록 추가
        record = {
            "timestamp": datetime.now().isoformat(),
            "engine": cost_info.get("engine", "Unknown"),
            "input_tokens": cost_info.get("input_tokens", 0),
            "output_tokens": cost_info.get("output_tokens", 0),
            "cost_usd": cost_info.get("total_cost", 0.0),
        }

        history["records"].append(record)

        # 누적값 갱신
        history["total_input_tokens"] += record["input_tokens"]
        history["total_output_tokens"] += record["output_tokens"]
        history["total_cost_usd"] += record["cost_usd"]

        # 저장
        with open(cost_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"💰 비용 기록 저장: ${record['cost_usd']:.4f} (누적: ${history['total_cost_usd']:.4f})")

        return history

    def _load_cost_history(self):
        """프로젝트 비용 기록 로드"""
        if not self.current_project:
            return None

        cost_history_file = self.current_project / "cost_history.json"

        if not cost_history_file.exists():
            return None

        try:
            with open(cost_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 비용 기록 로드 실패: {str(e)}")
            return None
