"""
RPG Maker 대사 추출 모듈

RPG Maker MV/MZ 게임에서 대사를 추출합니다.
"""
import json
from pathlib import Path
from typing import List, Dict, Any


class RPGMakerDialogueExtractor:
    """RPG Maker 대사 추출기"""

    def __init__(self, game_path: Path):
        """
        Args:
            game_path: 게임 폴더 경로
        """
        self.game_path = Path(game_path)
        self.data_folder = self.game_path / "data"
        self.dialogues = []

    def extract_all(self) -> List[Dict[str, Any]]:
        """모든 대사 추출"""
        print(f"📂 게임 폴더: {self.game_path}")
        print(f"📂 data 폴더: {self.data_folder}")

        if not self.data_folder.exists():
            print(f"❌ data 폴더를 찾을 수 없습니다: {self.data_folder}")
            return []

        # Map 파일에서 대사 추출 (MapInfos.json 제외)
        map_files = sorted(self.data_folder.glob("Map*.json"))
        map_files = [f for f in map_files if f.stem != 'MapInfos']  # MapInfos.json 제외
        print(f"\n🗺️  Map 파일: {len(map_files)}개 발견")

        for map_file in map_files:
            self._extract_from_map(map_file)

        # CommonEvents에서 대사 추출
        common_events_file = self.data_folder / "CommonEvents.json"
        if common_events_file.exists():
            self._extract_from_common_events(common_events_file)

        # System.json에서 시스템 메시지 추출
        system_file = self.data_folder / "System.json"
        if system_file.exists():
            self._extract_from_system(system_file)

        print(f"\n✅ 총 {len(self.dialogues)}개 대사 추출 완료")
        return self.dialogues

    def _extract_from_map(self, map_file: Path):
        """Map 파일에서 대사 추출"""
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            map_name = map_file.stem
            events = data.get('events', [])

            dialogue_count = 0

            for event in events:
                if not event or not isinstance(event, dict):
                    continue

                event_id = event.get('id', 0)
                event_name = event.get('name', '(이름 없음)')

                # 이벤트 페이지들
                pages = event.get('pages', [])

                for page_idx, page in enumerate(pages):
                    if not isinstance(page, dict):
                        continue

                    # 이벤트 명령들
                    commands = page.get('list', [])

                    for cmd_idx, cmd in enumerate(commands):
                        if not isinstance(cmd, dict):
                            continue

                        # 코드 401: 대사 (첫 줄)
                        # 코드 101: 대화 시작 (화자 정보)
                        code = cmd.get('code', 0)
                        parameters = cmd.get('parameters', [])

                        if code == 401 and parameters:
                            # 대사 텍스트
                            text = parameters[0] if parameters else ""

                            if text.strip():
                                dialogue_count += 1

                                # ID 생성 (고유 식별자)
                                dialogue_id = f"{map_name}_event_{event_id}_page_{page_idx}_line_{cmd_idx}"

                                self.dialogues.append({
                                    'id': dialogue_id,
                                    'file': f"{map_name}.json",
                                    'type': 'dialogue',
                                    'context': {
                                        'event_id': event_id,
                                        'event_name': event_name,
                                        'page': page_idx,
                                        'line': cmd_idx
                                    },
                                    'original': text,
                                    'translated': '',
                                    'speaker': '',
                                    'notes': ''
                                })

                        elif code == 102 and parameters:
                            # 선택지 (코드 102)
                            choices = parameters[0] if parameters else []
                            if isinstance(choices, list):
                                for choice_idx, choice_text in enumerate(choices):
                                    if choice_text.strip():
                                        dialogue_count += 1
                                        dialogue_id = f"{map_name}_event_{event_id}_page_{page_idx}_choice_{cmd_idx}_{choice_idx}"

                                        self.dialogues.append({
                                            'id': dialogue_id,
                                            'file': f"{map_name}.json",
                                            'type': 'choice',
                                            'context': {
                                                'event_id': event_id,
                                                'event_name': event_name,
                                                'page': page_idx,
                                                'line': cmd_idx,
                                                'choice_index': choice_idx
                                            },
                                            'original': choice_text,
                                            'translated': '',
                                            'speaker': '',
                                            'notes': '선택지'
                                        })

            if dialogue_count > 0:
                print(f"  • {map_name}: {dialogue_count}개 대사")

        except Exception as e:
            print(f"  ⚠️  {map_file.name} 처리 실패: {e}")

    def _extract_from_common_events(self, file_path: Path):
        """CommonEvents 파일에서 대사 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            dialogue_count = 0

            for event in data:
                if not event or not isinstance(event, dict):
                    continue

                event_id = event.get('id', 0)
                event_name = event.get('name', '(이름 없음)')

                commands = event.get('list', [])

                for cmd_idx, cmd in enumerate(commands):
                    if not isinstance(cmd, dict):
                        continue

                    code = cmd.get('code', 0)
                    parameters = cmd.get('parameters', [])

                    if code == 401 and parameters:
                        text = parameters[0] if parameters else ""

                        if text.strip():
                            dialogue_count += 1
                            dialogue_id = f"CommonEvents_event_{event_id}_line_{cmd_idx}"

                            self.dialogues.append({
                                'id': dialogue_id,
                                'file': 'CommonEvents.json',
                                'type': 'dialogue',
                                'context': {
                                    'event_id': event_id,
                                    'event_name': event_name,
                                    'line': cmd_idx
                                },
                                'original': text,
                                'translated': '',
                                'speaker': '',
                                'notes': 'Common Event'
                            })

            if dialogue_count > 0:
                print(f"  • CommonEvents: {dialogue_count}개 대사")

        except Exception as e:
            print(f"  ⚠️  CommonEvents 처리 실패: {e}")

    def _extract_from_system(self, file_path: Path):
        """System.json에서 시스템 메시지 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            dialogue_count = 0

            # 게임 타이틀
            game_title = data.get('gameTitle', '')
            if game_title and game_title.strip():
                dialogue_count += 1
                self.dialogues.append({
                    'id': 'System_gameTitle',
                    'file': 'System.json',
                    'type': 'system',
                    'context': {'field': 'gameTitle'},
                    'original': game_title,
                    'translated': '',
                    'speaker': '',
                    'notes': '게임 타이틀'
                })

            # 통화 단위
            currency_unit = data.get('currencyUnit', '')
            if currency_unit and currency_unit.strip():
                dialogue_count += 1
                self.dialogues.append({
                    'id': 'System_currencyUnit',
                    'file': 'System.json',
                    'type': 'system',
                    'context': {'field': 'currencyUnit'},
                    'original': currency_unit,
                    'translated': '',
                    'speaker': '',
                    'notes': '통화 단위'
                })

            if dialogue_count > 0:
                print(f"  • System: {dialogue_count}개 시스템 메시지")

        except Exception as e:
            print(f"  ⚠️  System 처리 실패: {e}")

    def to_json(self, output_path: Path):
        """JSON 파일로 저장 (GUI 호환 형식)"""
        if not self.dialogues:
            print("⚠️  추출된 대사가 없습니다.")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.dialogues, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 파일 저장 완료: {output_path}")
        print(f"   📊 {len(self.dialogues)}개 항목")
