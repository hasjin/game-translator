"""Excel 관련 핸들러 Mixin"""
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from datetime import datetime
import traceback


class ExcelHandlerMixin:
    """Excel 내보내기/가져오기 기능을 제공하는 Mixin 클래스"""

    def load_translation_for_review(self):
        """번역 결과를 검수 뷰어에 로드"""
        print(f"🔍 load_translation_for_review() 호출됨")

        # 번역 결과 경로 확인
        reload_path = None

        if self.preview_output_path and self.preview_output_path.exists():
            reload_path = self.preview_output_path
        elif self.last_translation_output:
            reload_path = Path(self.last_translation_output)
            if not reload_path.exists():
                reload_path = None
        elif self.current_project:
            reload_path = self.current_project / "preview"
            if not reload_path.exists():
                reload_path = None

        if reload_path:
            print(f"📂 번역 결과 로드 중: {reload_path}")
            self._reload_translation_entries_from_path(reload_path)
        else:
            QMessageBox.warning(
                self,
                "경고",
                "번역 결과를 찾을 수 없습니다!\n\n먼저 번역을 실행하세요."
            )
            return

        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "번역 엔트리가 비어있습니다!"
            )
            return

        # 뷰어에 로드
        self.translation_viewer.load_entries(self.translation_entries)
        self.btn_export_excel.setEnabled(True)

        QMessageBox.information(
            self,
            "완료",
            f"✅ 번역 결과 로드 완료!\n\n"
            f"총 {len(self.translation_entries)}개 항목"
        )

    def import_excel_to_viewer(self):
        """Excel 파일을 가져와서 뷰어에 변경사항 표시"""
        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "먼저 번역 결과를 로드하세요!"
            )
            return

        # Excel 파일 선택
        default_path = ""
        if self.current_project:
            default_path = str(self.current_project)

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Excel 열기",
            default_path,
            "Excel Files (*.xlsx)"
        )

        if not filename:
            return

        try:
            from core.excel_manager import ExcelManager

            # Excel 가져오기
            manager = ExcelManager()
            updated_entries, conflicts = manager.import_from_excel(
                filename,
                self.translation_entries
            )

            # 수정된 항목 추출
            modified_map = {}
            for idx, entry in enumerate(updated_entries):
                if isinstance(entry, dict):
                    if entry.get('status') == 'modified':
                        modified_text = entry.get('translated', '')
                        if modified_text:
                            modified_map[idx] = modified_text
                elif hasattr(entry, 'status') and entry.status == 'modified':
                    modified_text = getattr(entry, 'modified_translation',
                                          getattr(entry, 'translation', ''))
                    if modified_text:
                        modified_map[idx] = modified_text

            # 뷰어에 수정사항 적용
            self.translation_viewer.apply_modified_entries(modified_map)

            QMessageBox.information(
                self,
                "완료",
                f"✅ Excel 파일 로드 완료!\n\n"
                f"수정된 항목: {len(modified_map)}개\n\n"
                f"뷰어에서 변경사항을 확인하고 '수정 사항 저장'을 클릭하세요."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"Excel 가져오기 실패:\n{str(e)}\n\n{traceback.format_exc()}"
            )

    def save_viewer_modifications(self):
        """뷰어의 수정사항을 파일에 저장"""
        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "번역 결과가 없습니다!"
            )
            return

        # 뷰어에서 수정된 항목 가져오기
        modified_map = self.translation_viewer.get_modified_entries()

        if not modified_map:
            QMessageBox.information(
                self,
                "알림",
                "수정된 항목이 없습니다."
            )
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "수정 사항 저장",
            f"✏️ 수정된 항목: {len(modified_map)}개\n\n"
            f"번역 파일에 수정 사항을 저장하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # translation_entries에 수정사항 반영
            for idx, modified_text in modified_map.items():
                if idx < len(self.translation_entries):
                    entry = self.translation_entries[idx]

                    if isinstance(entry, dict):
                        entry['translated'] = modified_text
                        entry['status'] = 'modified'
                    elif hasattr(entry, 'translation'):
                        entry.translation = modified_text
                        entry.modified_translation = modified_text
                        entry.status = 'modified'

            # 파일에 저장
            if self.last_translation_output:
                output_dir = Path(self.last_translation_output)

                # JSON 파일 확인
                json_file = output_dir / "extracted_translated.json"
                if json_file.exists():
                    self._save_modified_to_json(modified_map, json_file)
                else:
                    # TXT 파일 업데이트
                    from core.excel_manager import ExcelManager
                    manager = ExcelManager()
                    manager.apply_to_files(self.translation_entries, output_dir)

                # translation_entries.json 저장
                self._save_translation_entries()

                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ 수정 사항이 저장되었습니다!\n\n"
                    f"✏️ 수정된 항목: {len(modified_map)}개\n"
                    f"📁 출력 폴더: {output_dir}\n\n"
                    f"이제 '게임에 적용하기'를 눌러주세요."
                )
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "출력 폴더를 찾을 수 없습니다."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"저장 실패:\n{str(e)}\n\n{traceback.format_exc()}"
            )

    def _save_modified_to_json(self, modified_map, json_file: Path):
        """수정사항을 JSON 파일에 저장"""
        import json

        # JSON 파일 로드
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modified_count = 0

        # RPG Maker 형식 (list) vs Unity 형식 (dict with entries) 구분
        if isinstance(data, list):
            # RPG Maker 형식: 인덱스로 직접 접근
            for idx, modified_text in modified_map.items():
                if idx < len(data):
                    data[idx]['translated'] = modified_text
                    modified_count += 1
        elif isinstance(data, dict) and 'entries' in data:
            # Unity 형식: entries에서 찾기
            entries = data.get('entries', [])
            for idx, modified_text in modified_map.items():
                if idx < len(entries):
                    entries[idx]['translated'] = modified_text
                    modified_count += 1

        # JSON 파일 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 파일 업데이트 완료: {modified_count}개 항목 수정됨")


    def export_excel(self):
        """번역 결과를 Excel로 내보내기"""
        print(f"🔍 export_excel() 호출됨")
        print(f"   current_project: {self.current_project}")
        print(f"   preview_output_path: {self.preview_output_path}")
        print(f"   last_translation_output: {self.last_translation_output}")
        print(f"   translation_entries 수: {len(self.translation_entries) if self.translation_entries else 0}")

        # 실제 번역 출력 경로에서 최신 번역 결과를 다시 로드
        # 우선순위: preview_output_path > last_translation_output > current_project/preview
        reload_path = None

        if self.preview_output_path and self.preview_output_path.exists():
            reload_path = self.preview_output_path
            print(f"📂 사용할 경로 (preview_output_path): {reload_path}")
        elif self.last_translation_output:
            reload_path = Path(self.last_translation_output)
            if reload_path.exists():
                print(f"📂 사용할 경로 (last_translation_output): {reload_path}")
            else:
                reload_path = None
        elif self.current_project:
            reload_path = self.current_project / "preview"
            if reload_path.exists():
                print(f"📂 사용할 경로 (current_project/preview): {reload_path}")
            else:
                reload_path = None

        if reload_path:
            print(f"📂 번역 결과 다시 로드 중: {reload_path}")
            self._reload_translation_entries_from_path(reload_path)
            print(f"   재로드 후 엔트리 수: {len(self.translation_entries) if self.translation_entries else 0}")

        if not self.translation_entries:
            print(f"❌ translation_entries가 비어있습니다")
            QMessageBox.warning(
                self,
                "경고",
                "번역 결과가 없습니다!\n\n먼저 번역을 실행하거나, 이전 번역 결과를 로드하세요."
            )
            return

        # 기본 저장 위치: 프로젝트 폴더
        # 파일명 형식: [프로젝트명]_translation_review_YYYYMMDD_HHMMSS.xlsx
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        project_name = "translation"
        if self.current_project:
            project_name = self.current_project.name

        default_filename = f"{project_name}_translation_review_{timestamp}.xlsx"

        if self.current_project:
            default_filename = str(self.current_project / default_filename)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Excel 저장",
            default_filename,
            "Excel Files (*.xlsx)"
        )

        if filename:
            try:
                from core.excel_manager import ExcelManager

                # Excel 내보내기
                manager = ExcelManager()
                manager.export_to_excel(self.translation_entries, filename)

                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ Excel 내보내기 완료!\n\n"
                    f"📁 {filename}\n\n"
                    f"📊 총 {len(self.translation_entries)}개 항목\n\n"
                    f"💡 사용 방법:\n"
                    f"1. Excel에서 '원문'과 'AI 번역' 확인\n"
                    f"2. 수정이 필요한 경우 '수정본' 컬럼에 입력\n"
                    f"3. 저장 후 '수정된 Excel 가져오기' 클릭"
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "오류",
                    f"Excel 저장 실패:\n{str(e)}\n\n{traceback.format_exc()}"
                )

    def import_excel(self):
        """수정된 Excel 파일을 가져와서 번역 파일에 반영"""
        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "원본 번역 결과가 없습니다!\n\n먼저 번역을 실행하거나 Excel을 내보내기하세요."
            )
            return

        # 기본 열기 위치: 프로젝트 폴더
        default_path = ""
        if self.current_project:
            default_path = str(self.current_project)

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Excel 열기",
            default_path,
            "Excel Files (*.xlsx)"
        )

        if not filename:
            return

        try:
            from core.excel_manager import ExcelManager

            # Excel 가져오기
            manager = ExcelManager()
            updated_entries, conflicts = manager.import_from_excel(
                filename,
                self.translation_entries
            )

            # 수정된 항목 개수 계산 (dict와 TranslationEntry 모두 처리)
            modified_count = 0
            for e in updated_entries:
                if isinstance(e, dict):
                    if e.get('status') == 'modified':
                        modified_count += 1
                elif hasattr(e, 'status') and e.status == 'modified':
                    modified_count += 1

            if modified_count == 0:
                QMessageBox.information(
                    self,
                    "알림",
                    f"✅ Excel 파일을 확인했습니다.\n\n"
                    f"수정된 항목이 없습니다.\n\n"
                    f"💡 '수정본' 컬럼에 수정 내용을 입력하세요."
                )
                return

            # 사용자 확인
            reply = QMessageBox.question(
                self,
                "수정 사항 반영",
                f"📊 Excel 가져오기 완료\n\n"
                f"✏️ 수정된 항목: {modified_count}개\n"
                f"⚠️ 충돌: {len(conflicts)}개\n\n"
                f"번역 파일에 수정 사항을 반영하시겠습니까?\n\n"
                f"대상 폴더: {self.last_translation_output or '미리보기 폴더'}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # 파일에 적용
            if self.last_translation_output:
                output_dir = Path(self.last_translation_output)

                # JSON 파일 확인 (일반 Unity 게임)
                json_file = output_dir / "extracted_translated.json"
                if json_file.exists():
                    # JSON 파일 업데이트
                    self._apply_excel_to_json(updated_entries, json_file)
                else:
                    # TXT 파일 업데이트 (Naninovel)
                    manager.apply_to_files(updated_entries, output_dir)

                # 번역 엔트리 업데이트
                self.translation_entries = updated_entries

                # JSON 저장
                self._save_translation_entries()

                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ 수정 사항이 반영되었습니다!\n\n"
                    f"✏️ 수정된 항목: {modified_count}개\n"
                    f"📁 출력 폴더: {output_dir}\n\n"
                    f"이제 '게임에 적용하기'를 눌러주세요."
                )
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "출력 폴더를 찾을 수 없습니다.\n먼저 번역을 실행하세요."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"Excel 가져오기 실패:\n{str(e)}\n\n{traceback.format_exc()}"
            )

    def _reload_translation_entries_from_path(self, output_dir: Path):
        """지정된 경로에서 번역 엔트리를 다시 로드"""
        # 기존 엔트리 초기화
        self.translation_entries = []

        # 1. JSON 파일 확인 (일반 Unity 게임 + RPG Maker)
        json_file = output_dir / "extracted_translated.json"
        if json_file.exists():
            print(f"📂 JSON 파일에서 로드: {json_file}")
            try:
                import json
                from core.excel_manager import TranslationEntry

                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # JSON 형식 판별
                if isinstance(data, list):
                    # RPG Maker 형식 (리스트)
                    for entry in data:
                        self.translation_entries.append(TranslationEntry.from_dict(entry))
                    print(f"✅ {len(self.translation_entries)}개 번역 엔트리 로드 완료 (RPG Maker JSON)")
                elif isinstance(data, dict) and 'entries' in data:
                    # Unity 형식 (dict with entries)
                    entries = data.get('entries', [])
                    for entry in entries:
                        self.translation_entries.append({
                            'file': entry['context'].get('file', 'unknown'),
                            'original': entry['text'],
                            'translated': entry.get('translated', ''),
                            'context': entry['context']
                        })
                    print(f"✅ {len(self.translation_entries)}개 번역 엔트리 로드 완료 (Unity JSON)")
                else:
                    print(f"⚠️ 알 수 없는 JSON 형식: {type(data)}")

                return
            except Exception as e:
                import traceback
                print(f"⚠️ JSON 로드 실패: {str(e)}")
                print(traceback.format_exc())

        # 2. TXT 파일 로드 (Naninovel 게임)
        txt_files = list(output_dir.glob("*.txt"))

        from core.excel_manager import TranslationEntry

        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 일본어 주석에서 원문 추출 및 한국어 번역 매칭
                for idx, line in enumerate(lines):
                    stripped = line.strip()

                    # 주석(일본어 원문) 발견
                    if stripped.startswith(';') and not stripped.startswith('; >') and not stripped.startswith('; 日本語'):
                        japanese_text = stripped[1:].strip()  # '; ' 제거

                        if japanese_text:
                            # 다음 라인에서 한국어 번역 찾기
                            korean_idx = idx + 1
                            while korean_idx < len(lines):
                                korean_line = lines[korean_idx].strip()
                                # 빈 줄이나 주석/메타데이터가 아니면 한국어 번역
                                if korean_line and not korean_line.startswith('#') and not korean_line.startswith(';'):
                                    entry = TranslationEntry(
                                        file_path=str(txt_file),
                                        line_number=korean_idx + 1,
                                        japanese=japanese_text,
                                        translation=korean_line
                                    )
                                    self.translation_entries.append(entry)
                                    break
                                korean_idx += 1

            except Exception as e:
                print(f"⚠️ 파일 로드 실패: {txt_file.name} - {str(e)}")

        print(f"✅ {len(self.translation_entries)}개 번역 엔트리 로드 완료 (TXT)")

    def _apply_excel_to_json(self, updated_entries, json_file: Path):
        """Excel 수정사항을 JSON 파일에 반영 (일반 Unity 게임 또는 RPG Maker)"""
        import json

        # JSON 파일 로드
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 수정된 항목 매핑 (원문 -> 수정본)
        updates_map = {}
        for entry in updated_entries:
            if isinstance(entry, dict):
                # Unity 게임 (dict) 처리
                if entry.get('status') == 'modified' and entry.get('original'):
                    updates_map[entry['original']] = entry['translated']
            elif hasattr(entry, 'status') and entry.status == 'modified':
                # Naninovel (TranslationEntry) 처리
                original = entry.japanese if hasattr(entry, 'japanese') else ''
                modified = entry.modified_translation if hasattr(entry, 'modified_translation') and entry.modified_translation else entry.translation
                if original:
                    updates_map[original] = modified

        # JSON entries 업데이트
        modified_count = 0

        # RPG Maker 형식 (list) vs Unity 형식 (dict with entries) 구분
        if isinstance(data, list):
            # RPG Maker 형식: list of entries
            for entry in data:
                original_text = entry.get('original', '')
                if original_text in updates_map:
                    entry['translated'] = updates_map[original_text]
                    modified_count += 1
        elif isinstance(data, dict) and 'entries' in data:
            # Unity 형식: dict with entries key
            for entry in data.get('entries', []):
                original_text = entry.get('text', '')
                if original_text in updates_map:
                    entry['translated'] = updates_map[original_text]
                    modified_count += 1
        else:
            print(f"⚠️ 알 수 없는 JSON 형식: {json_file}")
            return

        # JSON 파일 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 파일 업데이트 완료: {modified_count}개 항목 수정됨")


    def apply_translation_to_game(self):
        """번역을 실제 게임에 적용"""
        if not self.translation_entries:
            QMessageBox.warning(
                self,
                "경고",
                "번역 결과가 없습니다!\n\n먼저 번역을 실행하세요."
            )
            return

        if not self.last_translation_output:
            QMessageBox.warning(
                self,
                "경고",
                "출력 폴더를 찾을 수 없습니다."
            )
            return

        # 게임 경로 확인
        game_path = None
        if self.current_project:
            # settings.json에서 game_path 읽기
            settings_file = self.current_project / "settings.json"
            if settings_file.exists():
                try:
                    import json
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    game_path = Path(settings.get('input_dir', ''))
                except:
                    pass

        if not game_path or not game_path.exists():
            QMessageBox.warning(
                self,
                "경고",
                "게임 경로를 찾을 수 없습니다.\n\n프로젝트 설정을 확인하세요."
            )
            return

        # 게임 타입 먼저 감지
        from core.game_language_detector import GameLanguageDetector
        detector = GameLanguageDetector()
        game_info = detector.detect_game_format(game_path)
        game_type = game_info.get('game_type', 'unknown')

        # RPG Maker인 경우 모드 선택 및 언어 정보 표시
        rpg_mode = 'replace'  # 기본값
        if game_type == 'rpgmaker':
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QDialogButtonBox
            from core.rpgmaker_language_detector import RPGMakerLanguageDetector

            # 언어 정보 감지
            rpg_detector = RPGMakerLanguageDetector()
            lang_info = rpg_detector.detect_language(game_path)

            mode_dialog = QDialog(self)
            mode_dialog.setWindowTitle("RPG Maker Translation Application")
            layout = QVBoxLayout()

            # 언어 정보 표시
            lang_label = QLabel(
                f"[O] Original Language: {lang_info['language']} ({lang_info['locale']})\n"
                f"[O] Target Language: Korean (ko)\n"
            )
            lang_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; background: #ecf0f1; border-radius: 4px;")
            layout.addWidget(lang_label)

            layout.addWidget(QLabel("\nHow to apply translation?\n"))

            replace_radio = QRadioButton("Replace Original (Simple, Recommended)")
            replace_radio.setChecked(True)
            replace_info = QLabel(
                "  [O] Direct modification of data/ folder\n"
                "  [O] No plugin required\n"
                "  [O] Game executable immediately\n"
                "  [O] Auto-backup created\n"
                "  [X] Cannot switch languages"
            )
            replace_info.setStyleSheet("color: #555; padding-left: 20px;")

            multilang_radio = QRadioButton("Multilingual Folder (Advanced)")
            multilang_info = QLabel(
                "  [O] Keep original data/ folder\n"
                "  [O] Support multiple languages\n"
                "  [O] Can switch languages\n"
                "  [X] Multilingual plugin required\n"
                "  [X] Folder structure: data_languages/ko/"
            )
            multilang_info.setStyleSheet("color: #555; padding-left: 20px;")

            layout.addWidget(replace_radio)
            layout.addWidget(replace_info)
            layout.addWidget(QLabel(""))
            layout.addWidget(multilang_radio)
            layout.addWidget(multilang_info)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(mode_dialog.accept)
            buttons.rejected.connect(mode_dialog.reject)
            layout.addWidget(buttons)

            mode_dialog.setLayout(layout)

            if mode_dialog.exec() == QDialog.DialogCode.Accepted:
                rpg_mode = 'replace' if replace_radio.isChecked() else 'multilang'
            else:
                return  # Canceled

        # 사용자 확인
        confirm_msg = f"⚠️ 게임 파일을 수정합니다!\n\n"
        confirm_msg += f"📁 게임 경로: {game_path}\n"
        confirm_msg += f"📊 번역 항목: {len(self.translation_entries)}개\n"

        if game_type == 'rpgmaker':
            if rpg_mode == 'replace':
                confirm_msg += f"\n💾 모드: 원본 교체\n"
                confirm_msg += f"📂 수정 위치: data/ 폴더\n"
            else:
                confirm_msg += f"\n💾 모드: 다국어 폴더\n"
                confirm_msg += f"📂 생성 위치: data_languages/ko/\n"

        confirm_msg += f"\n자동 백업이 생성됩니다.\n"
        confirm_msg += f"계속하시겠습니까?"

        reply = QMessageBox.question(
            self,
            "게임에 적용",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from core.bundle_packer import BundlePacker
            from core.game_language_detector import GameLanguageDetector

            # 게임 타입 감지
            detector = GameLanguageDetector()
            game_info = detector.detect_game_format(game_path)
            game_type = game_info.get('game_type', 'unknown')

            print(f"🎮 게임 타입: {game_type}")

            # BundlePacker 사용 (자동으로 RPG Maker/Unity 분기 처리)
            packer = BundlePacker()

            # RPG Maker는 list 형식, Unity는 dict 형식
            if game_type == 'rpgmaker':
                # translation_entries를 그대로 전달 (list 형식)
                # rpg_mode는 위에서 선택됨
                success = packer.apply_translations(
                    game_path=game_path,
                    target_language='ko',  # 한국어
                    translated_files=self.translation_entries,
                    create_backup=True,
                    rpg_mode=rpg_mode  # 'replace' or 'multilang'
                )
            else:
                # Unity: 번역 파일 경로 딕셔너리 생성
                output_dir = Path(self.last_translation_output)
                translated_files = {}

                # JSON 파일 확인
                json_file = output_dir / "extracted_translated.json"
                if json_file.exists():
                    # JSON 파일에서 번역된 텍스트 로드
                    import json
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Unity 형식으로 변환
                    if isinstance(data, dict) and 'entries' in data:
                        for entry in data.get('entries', []):
                            file_name = entry['context'].get('file', 'unknown')
                            if file_name not in translated_files:
                                translated_files[file_name] = str(output_dir / f"{file_name}.txt")

                target_language = getattr(self, 'last_target_language', 'zh-Hans')
                success = packer.apply_translations(
                    game_path=game_path,
                    target_language=target_language,
                    translated_files=translated_files,
                    create_backup=True
                )

            if success:
                backup_msg = ""
                if packer.backup_dir:
                    backup_msg = f"\n💾 백업 위치: {packer.backup_dir}"

                QMessageBox.information(
                    self,
                    "완료",
                    f"✅ 게임에 번역 적용 완료!\n\n"
                    f"🎮 게임을 실행하여 번역을 확인하세요.{backup_msg}\n\n"
                    f"💡 문제가 있으면 백업 폴더에서 복원할 수 있습니다."
                )
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    "번역 적용 중 오류가 발생했습니다.\n\n로그를 확인하세요."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"게임 적용 실패:\n{str(e)}\n\n{traceback.format_exc()}"
            )

