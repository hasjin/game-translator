"""Excel 관련 핸들러 Mixin"""
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from datetime import datetime
import traceback


class ExcelHandlerMixin:
    """Excel 내보내기/가져오기 기능을 제공하는 Mixin 클래스"""

    def export_excel(self):
        """번역 결과를 Excel로 내보내기"""
        # preview 폴더에서 최신 번역 결과를 다시 로드
        if self.current_project:
            preview_dir = self.current_project / "preview"
            if preview_dir.exists():
                print("📂 preview 폴더에서 번역 결과 다시 로드 중...")
                self._reload_translation_entries_from_preview()

        if not self.translation_entries:
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

            # 수정된 항목 개수 계산
            modified_count = sum(1 for e in updated_entries if e.status == 'modified')

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

    def _reload_translation_entries_from_preview(self):
        """preview 폴더에서 번역 엔트리를 다시 로드"""
        preview_dir = self.current_project / "preview"

        # 기존 엔트리 초기화
        self.translation_entries = []

        # 1. JSON 파일 확인 (일반 Unity 게임)
        json_file = preview_dir / "extracted_translated.json"
        if json_file.exists():
            print(f"📂 JSON 파일에서 로드: {json_file}")
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # JSON에서 entries 추출
                entries = data.get('entries', [])
                for entry in entries:
                    self.translation_entries.append({
                        'file': entry['context'].get('file', 'unknown'),
                        'original': entry['text'],
                        'translated': entry.get('translated', ''),
                        'context': entry['context']
                    })

                print(f"✅ {len(self.translation_entries)}개 번역 엔트리 로드 완료 (JSON)")
                return
            except Exception as e:
                print(f"⚠️ JSON 로드 실패: {str(e)}")

        # 2. TXT 파일 로드 (Naninovel 게임)
        txt_files = list(preview_dir.glob("*.txt"))

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
        """Excel 수정사항을 JSON 파일에 반영 (일반 Unity 게임)"""
        import json

        # JSON 파일 로드
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 수정된 항목 매핑 (원문 -> 수정본)
        updates_map = {}
        for entry in updated_entries:
            if hasattr(entry, 'status') and entry.status == 'modified':
                # TranslationEntry 객체인 경우
                original = entry.japanese if hasattr(entry, 'japanese') else entry.get('original', '')
                modified = entry.translation if hasattr(entry, 'translation') else entry.get('translated', '')
                updates_map[original] = modified
            elif isinstance(entry, dict) and entry.get('original'):
                # dict 타입인 경우
                updates_map[entry['original']] = entry['translated']

        # JSON entries 업데이트
        modified_count = 0
        for entry in data.get('entries', []):
            original_text = entry.get('text', '')
            if original_text in updates_map:
                entry['translated'] = updates_map[original_text]
                modified_count += 1

        # JSON 파일 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 파일 업데이트 완료: {modified_count}개 항목 수정됨")
