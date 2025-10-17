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
        print(f"🔧 [project_manager] auto_create_or_select_project() 호출됨")
        print(f"   folder_path: {folder_path}")
        print(f"   호출 전 current_project: {self.current_project}")

        from core.game_language_detector import GameLanguageDetector

        folder = Path(folder_path)

        # 게임 형식 감지
        detector = GameLanguageDetector()
        format_info = detector.detect_game_format(folder)
        game_type = format_info.get('game_type', 'unknown')

        # 지원하지 않는 게임 형식 체크 - 팝업 대신 game_info_label에 표시
        # if game_type == 'unknown':
        #     detailed_message = f"{format_info['message']}\n\n"
        #     if format_info.get('details'):
        #         detailed_message += f"{format_info['details']}\n\n"
        #     detailed_message += "이 게임은 현재 지원하지 않는 형식입니다.\n"
        #     detailed_message += "Naninovel 또는 일반 Unity 게임만 지원합니다."
        #
        #     msg_box = QMessageBox(self)
        #     msg_box.setIcon(QMessageBox.Icon.Warning)
        #     msg_box.setWindowTitle("지원하지 않는 게임 형식")
        #     msg_box.setText(detailed_message)
        #     msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        #     msg_box.exec()
        #     return

        # 일반 Unity 게임 안내 메시지 - 팝업 대신 game_info_label에 표시
        # if game_type in ['unity_generic', 'unity_other']:
        #     info_message = f"{format_info['message']}\n\n"
        #     if format_info.get('details'):
        #         info_message += f"{format_info['details']}\n\n"
        #     info_message += "프로젝트를 생성하고 번역을 진행할 수 있습니다."
        #
        #     msg_box = QMessageBox(self)
        #     msg_box.setIcon(QMessageBox.Icon.Information)
        #     msg_box.setWindowTitle("일반 Unity 게임 감지")
        #     msg_box.setText(info_message)
        #     msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        #     msg_box.exec()
        #     # return 하지 않고 계속 진행

        # Naninovel 게임이지만 특수한 구조일 경우 안내 - 팝업 대신 game_info_label에 표시
        # if format_info['is_naninovel']:
        #     warnings = []
        #     if not format_info.get('has_language_folders'):
        #         warnings.append("⚠️  언어별 폴더 구조가 없습니다.\n   → 기본 언어를 통째로 교체하는 방식으로 진행됩니다.")
        #     if not format_info.get('has_chapter_structure'):
        #         warnings.append("⚠️  챕터별 구조가 없습니다.\n   → 전체 스크립트를 한번에 처리합니다.")
        #
        #     if warnings:
        #         info_message = f"{format_info['message']}\n\n"
        #         if format_info.get('details'):
        #             info_message += f"{format_info['details']}\n\n"
        #         info_message += "진행하시겠습니까?"
        #
        #         reply = QMessageBox.question(
        #             self,
        #             "게임 구조 확인",
        #             info_message,
        #             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        #         )
        #
        #         if reply == QMessageBox.StandardButton.No:
        #             return

        # 게임 이름 추출 시도
        game_name = None

        print(f"🔍 게임 이름 추출 시작")
        print(f"   폴더: {folder}")
        print(f"   폴더명: {folder.name}")

        # 1. 실행 파일 찾기 (.exe)
        exe_files = list(folder.glob("*.exe"))
        print(f"   exe 파일: {exe_files}")

        # 너무 일반적인 게임 이름 목록 (이런 경우 폴더명 사용)
        generic_names = ["game", "play", "start", "launcher", "application", "app", "main"]

        if exe_files:
            # Game.exe를 우선적으로 찾기 (RPG Maker 게임)
            game_exe = None
            for exe in exe_files:
                if exe.stem.lower() == "game":
                    game_exe = exe
                    break

            # Game.exe가 없으면 notification_helper 등을 제외한 첫 번째 exe 사용
            if not game_exe:
                excluded_names = ["notification_helper", "unitycrashhandler", "crashreporter"]
                for exe in exe_files:
                    if exe.stem.lower() not in excluded_names:
                        game_exe = exe
                        break

            # 그래도 없으면 첫 번째 exe 사용
            if not game_exe:
                game_exe = exe_files[0]

            exe_game_name = game_exe.stem
            print(f"   ✅ exe에서 추출: {exe_game_name} (from {game_exe.name})")

            # 이름이 너무 일반적이면 폴더명 사용
            if exe_game_name.lower() in generic_names:
                game_name = folder.name
                print(f"   ⚠️ '{exe_game_name}'은(는) 너무 일반적인 이름")
                print(f"   ✅ 폴더명 사용: {game_name}")
            else:
                game_name = exe_game_name

        # 2. _Data 폴더에서 추출
        if not game_name:
            data_folders = list(folder.glob("*_Data"))
            print(f"   _Data 폴더: {data_folders}")
            for data_folder in data_folders:
                game_name = data_folder.name.replace("_Data", "")
                print(f"   ✅ _Data에서 추출: {game_name}")
                break

        # 3. 폴더명 사용
        if not game_name:
            game_name = folder.name
            print(f"   ✅ 폴더명 사용: {game_name}")

        # 특수문자 제거 및 정리
        original_game_name = game_name
        game_name = re.sub(r'[<>:"/\\|?*]', '', game_name)
        game_name = game_name.strip()
        print(f"   특수문자 제거 전: {original_game_name}")
        print(f"   특수문자 제거 후: {game_name}")

        if not game_name:
            game_name = "Unnamed_Game"
            print(f"   ⚠️ 빈 이름, 기본값 사용: {game_name}")

        print(f"✅ 최종 게임 이름: {game_name}")

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
            print(f"🔧 [project_manager] current_project 설정 (기존 프로젝트)")
            print(f"   경로: {project_path}")
            self.current_project = project_path
            print(f"   설정 후: {self.current_project}")
            self.project_info_label.setText(f"📂 프로젝트: {game_name}")

            # 이전 번역 결과 로드
            self._load_translation_entries()
        else:
            # 새 프로젝트 생성
            self._create_project_folder(game_name, folder_path)
            print(f"🔧 [project_manager] current_project 설정 (새 프로젝트)")
            print(f"   경로: {self.projects_dir / game_name}")
            self.current_project = self.projects_dir / game_name
            print(f"   설정 후: {self.current_project}")
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
        print(f"🔍 _load_translation_entries() 호출됨")
        print(f"   current_project: {self.current_project}")

        if not self.current_project:
            print(f"❌ current_project가 None입니다")
            return

        from core.excel_manager import TranslationEntry

        # 1. translation_entries.json 시도
        entries_file = self.current_project / "translation_entries.json"
        print(f"📂 entries_file 확인: {entries_file}")
        print(f"   존재 여부: {entries_file.exists()}")

        # 2. preview/extracted_translated.json 시도 (RPG Maker 등)
        preview_file = self.current_project / "preview" / "extracted_translated.json"
        print(f"📂 preview_file 확인: {preview_file}")
        print(f"   존재 여부: {preview_file.exists()}")

        target_file = None
        if entries_file.exists():
            target_file = entries_file
            print(f"✅ entries_file 사용")
        elif preview_file.exists():
            target_file = preview_file
            print(f"✅ preview_file 사용")
        else:
            print(f"❌ 번역 결과 파일을 찾을 수 없습니다")
            return

        try:
            print(f"📖 파일 읽기 시작: {target_file}")
            with open(target_file, 'r', encoding='utf-8') as f:
                entries_data = json.load(f)

            print(f"📊 JSON 데이터 로드 완료: {len(entries_data)}개 항목")
            print(f"   데이터 타입: {type(entries_data)}")

            if entries_data:
                first_entry = entries_data[0]
                print(f"   첫 번째 엔트리 키: {first_entry.keys() if isinstance(first_entry, dict) else 'dict 아님'}")

            self.translation_entries = [
                TranslationEntry.from_dict(data) for data in entries_data
            ]

            print(f"✅ TranslationEntry 변환 완료: {len(self.translation_entries)}개")
            print(f"   self.translation_entries 타입: {type(self.translation_entries)}")
            print(f"   첫 엔트리 타입: {type(self.translation_entries[0]) if self.translation_entries else 'Empty'}")

            # Excel 버튼 활성화
            self.btn_export_excel.setEnabled(True)
            print(f"✅ Excel 버튼 활성화됨")

        except Exception as e:
            import traceback
            print(f"❌ 번역 결과 로드 실패: {str(e)}")
            print(traceback.format_exc())

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
