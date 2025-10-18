"""RPG Maker 번역 적용 모듈"""
import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class RPGMakerPacker:
    """번역을 RPG Maker 게임에 적용"""

    def __init__(self):
        self.backup_dir = None

    def apply_translations(
        self,
        game_path: Path,
        translated_data: List[Dict],
        create_backup: bool = True,
        target_language: str = 'ko',
        mode: str = 'multilang'  # 'multilang' or 'replace'
    ) -> bool:
        """번역을 RPG Maker 게임에 적용

        Args:
            game_path: 게임 루트 폴더
            translated_data: 번역 데이터 리스트 (rpgmaker_extractor 또는 Excel에서)
            create_backup: 백업 생성 여부
            target_language: 대상 언어 코드 (예: 'ko', 'en', 'zh')
            mode: 'multilang' = 다국어 폴더 생성, 'replace' = 원본 교체

        Returns:
            성공 여부
        """
        data_folder = game_path / "data"

        if not data_folder.exists():
            print(f"[ERROR] data 폴더를 찾을 수 없습니다: {data_folder}")
            return False

        # 모드에 따라 다르게 처리
        if mode == 'replace':
            # 원본 교체 모드: data/ 폴더 직접 수정
            print(f"[INFO] 원본 교체 모드: data/ 폴더 직접 수정")

            # 백업 생성
            if create_backup:
                self.backup_dir = self._create_backup(data_folder)
                print(f"[BACKUP] 백업 생성: {self.backup_dir}")

            target_folder = data_folder
        else:
            # 다국어 모드: data_languages/ko/ 폴더 생성
            lang_folder = game_path / "data_languages" / target_language
            lang_folder.mkdir(parents=True, exist_ok=True)

            print(f"[INFO] 다국어 폴더 모드: {lang_folder}")

            # 원본 data 폴더 백업 (첫 실행 시만)
            if create_backup and not (game_path / "data_languages" / "original").exists():
                self.backup_dir = self._create_backup(data_folder, game_path / "data_languages" / "original")
                print(f"[BACKUP] 원본 백업 생성: {self.backup_dir}")

            target_folder = lang_folder

        # 번역 데이터를 ID로 딕셔너리화
        translations_by_id = {item['id']: item for item in translated_data if 'id' in item}
        print(f"[INFO] 번역 항목: {len(translations_by_id)}개")

        # 파일별로 그룹화
        files_to_update = {}
        for item in translated_data:
            file_name = item.get('file', '')
            if file_name:
                if file_name not in files_to_update:
                    files_to_update[file_name] = []
                files_to_update[file_name].append(item)

        print(f"[INFO] 수정할 파일: {len(files_to_update)}개")

        # 각 파일 처리
        success_count = 0
        total_files = len(files_to_update)

        for file_name, items in files_to_update.items():
            source_file = data_folder / file_name
            target_file = target_folder / file_name

            if not source_file.exists():
                print(f"[WARNING] 원본 파일 없음: {file_name}")
                continue

            try:
                # 원본 파일 복사 (replace 모드에서는 백업만 됨)
                if mode == 'multilang':
                    shutil.copy2(source_file, target_file)

                # 파일 타입에 따라 번역 적용
                if file_name.startswith('Map') and file_name != 'MapInfos.json':
                    if self._apply_to_map(target_file, items):
                        success_count += 1
                elif file_name == 'CommonEvents.json':
                    if self._apply_to_common_events(target_file, items):
                        success_count += 1
                elif file_name == 'System.json':
                    if self._apply_to_system(target_file, items):
                        success_count += 1
                else:
                    print(f"[INFO] 지원하지 않는 파일 타입: {file_name}")

            except Exception as e:
                print(f"[ERROR] {file_name} 처리 실패: {e}")

        print(f"\n[SUCCESS] 완료: {success_count}/{total_files}개 파일 적용")
        print(f"[INFO] 번역 파일 위치: {target_folder}")

        if mode == 'replace':
            print(f"[WARNING] 원본 data/ 폴더가 수정되었습니다")
            print(f"[INFO] 백업에서 복원하려면: restore_backup() 호출")

        return success_count > 0

    def _create_backup(self, data_folder: Path, backup_location: Path = None) -> Path:
        """data 폴더 백업

        Args:
            data_folder: data 폴더 경로
            backup_location: 백업 위치 (None이면 backups/ 폴더 사용)

        Returns:
            백업 폴더 경로
        """
        if backup_location:
            # 지정된 위치에 백업 (다국어 폴더 내 original/)
            backup_dir = backup_location
            backup_dir.mkdir(parents=True, exist_ok=True)

            # data 폴더 내용을 original 폴더에 복사
            for item in data_folder.glob('*.json'):
                shutil.copy2(item, backup_dir / item.name)

            print(f"  [OK] 원본 {len(list(backup_dir.glob('*.json')))}개 파일 백업됨")
        else:
            # 기존 방식: backups/ 폴더에 타임스탬프로 백업
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("backups") / f"rpgmaker_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # data 폴더 전체 복사
            backup_data_folder = backup_dir / "data"
            shutil.copytree(data_folder, backup_data_folder)

            print(f"  [OK] {len(list(backup_data_folder.glob('*.json')))}개 파일 백업됨")
            backup_dir = backup_data_folder

        return backup_dir

    def _apply_to_map(self, map_file: Path, items: List[Dict]) -> bool:
        """Map 파일에 번역 적용

        Args:
            map_file: Map JSON 파일 경로
            items: 번역 항목 리스트

        Returns:
            성공 여부
        """
        try:
            # JSON 로드
            with open(map_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            modified = False

            # 각 번역 항목 처리
            for item in items:
                translated = item.get('translated', '').strip()
                if not translated:
                    continue

                context = item.get('context', {})
                event_id = context.get('event_id')
                page_idx = context.get('page')
                line_idx = context.get('line')
                item_type = item.get('type', 'dialogue')

                if event_id is None:
                    continue

                # 이벤트 찾기
                events = data.get('events', [])
                if event_id >= len(events) or not events[event_id]:
                    continue

                event = events[event_id]

                # 페이지 찾기
                pages = event.get('pages', [])
                if page_idx >= len(pages):
                    continue

                page = pages[page_idx]
                commands = page.get('list', [])

                # 선택지인 경우
                if item_type == 'choice':
                    choice_idx = context.get('choice_index')
                    if line_idx < len(commands):
                        cmd = commands[line_idx]
                        if cmd.get('code') == 102:
                            params = cmd.get('parameters', [])
                            if params and isinstance(params[0], list):
                                if choice_idx < len(params[0]):
                                    params[0][choice_idx] = translated
                                    modified = True

                # 대사인 경우
                elif item_type == 'dialogue':
                    if line_idx < len(commands):
                        cmd = commands[line_idx]
                        if cmd.get('code') == 401:
                            params = cmd.get('parameters', [])
                            if params:
                                params[0] = translated
                                modified = True

            # 저장
            if modified:
                with open(map_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  [OK] {map_file.name}: {len(items)}개 항목 적용")
                return True
            else:
                print(f"  [INFO] {map_file.name}: 변경 사항 없음")
                return False

        except Exception as e:
            print(f"  [ERROR] {map_file.name} 처리 실패: {e}")
            return False

    def _apply_to_common_events(self, file_path: Path, items: List[Dict]) -> bool:
        """CommonEvents에 번역 적용

        Args:
            file_path: CommonEvents.json 경로
            items: 번역 항목 리스트

        Returns:
            성공 여부
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            modified = False

            for item in items:
                translated = item.get('translated', '').strip()
                if not translated:
                    continue

                context = item.get('context', {})
                event_id = context.get('event_id')
                line_idx = context.get('line')

                if event_id is None or line_idx is None:
                    continue

                # 이벤트 찾기
                if event_id >= len(data) or not data[event_id]:
                    continue

                event = data[event_id]
                commands = event.get('list', [])

                if line_idx < len(commands):
                    cmd = commands[line_idx]
                    if cmd.get('code') == 401:
                        params = cmd.get('parameters', [])
                        if params:
                            params[0] = translated
                            modified = True

            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  [OK] CommonEvents.json: {len(items)}개 항목 적용")
                return True
            else:
                print(f"  [INFO] CommonEvents.json: 변경 사항 없음")
                return False

        except Exception as e:
            print(f"  [ERROR] CommonEvents.json 처리 실패: {e}")
            return False

    def _apply_to_system(self, file_path: Path, items: List[Dict]) -> bool:
        """System.json에 번역 적용

        Args:
            file_path: System.json 경로
            items: 번역 항목 리스트

        Returns:
            성공 여부
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            modified = False

            for item in items:
                translated = item.get('translated', '').strip()
                if not translated:
                    continue

                context = item.get('context', {})
                field = context.get('field')

                if field == 'gameTitle':
                    data['gameTitle'] = translated
                    modified = True
                elif field == 'currencyUnit':
                    data['currencyUnit'] = translated
                    modified = True

            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  [OK] System.json: {len(items)}개 항목 적용")
                return True
            else:
                print(f"  [INFO] System.json: 변경 사항 없음")
                return False

        except Exception as e:
            print(f"  [ERROR] System.json 처리 실패: {e}")
            return False

    def restore_backup(self, backup_dir: Path, game_path: Path) -> bool:
        """백업 복원

        Args:
            backup_dir: 백업 폴더
            game_path: 게임 폴더

        Returns:
            성공 여부
        """
        if not backup_dir.exists():
            print(f"[ERROR] 백업 폴더가 없습니다: {backup_dir}")
            return False

        backup_data_folder = backup_dir / "data"
        if not backup_data_folder.exists():
            print(f"[ERROR] 백업 data 폴더가 없습니다: {backup_data_folder}")
            return False

        target_data_folder = game_path / "data"

        # 기존 data 폴더 삭제
        if target_data_folder.exists():
            shutil.rmtree(target_data_folder)

        # 백업에서 복원
        shutil.copytree(backup_data_folder, target_data_folder)

        print("[SUCCESS] 백업 복원 완료")
        return True
