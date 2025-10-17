"""
게임 형식 자동 감지 유틸리티
"""
from pathlib import Path
from typing import Dict, Optional


class GameDetector:
    """게임 형식 자동 감지"""

    @staticmethod
    def detect_game_type(game_path: Path) -> Dict[str, any]:
        """
        게임 폴더를 분석하여 게임 형식 감지

        Args:
            game_path: 게임 폴더 경로

        Returns:
            게임 정보 딕셔너리
            {
                'type': 'rpgmaker_mv' | 'rpgmaker_mz' | 'rpgmaker_vx' | 'unity_naninovel' | 'unity_general' | 'unknown',
                'version': 버전 정보,
                'engine': 엔진 이름,
                'confidence': 신뢰도 (0.0 ~ 1.0),
                'details': 상세 정보
            }
        """
        game_path = Path(game_path)

        if not game_path.exists() or not game_path.is_dir():
            return {
                'type': 'unknown',
                'engine': '알 수 없음',
                'confidence': 0.0,
                'details': '유효하지 않은 경로'
            }

        # 1. RPG Maker 감지
        rpg_result = GameDetector._detect_rpgmaker(game_path)
        if rpg_result['confidence'] > 0.8:
            return rpg_result

        # 2. Unity 게임 감지
        unity_result = GameDetector._detect_unity(game_path)
        if unity_result['confidence'] > 0.5:
            return unity_result

        # 3. 기타 게임 엔진
        other_result = GameDetector._detect_other(game_path)
        if other_result['confidence'] > 0.5:
            return other_result

        # 감지 실패
        return {
            'type': 'unknown',
            'engine': '알 수 없음',
            'confidence': 0.0,
            'details': '지원하지 않는 게임 형식입니다.'
        }

    @staticmethod
    def _detect_rpgmaker(game_path: Path) -> Dict:
        """RPG Maker 게임 감지"""
        confidence = 0.0
        details = []
        version = None
        type_name = 'unknown'

        # data 폴더 확인
        data_folder = game_path / 'data'
        if not data_folder.exists():
            return {
                'type': type_name,
                'engine': 'RPG Maker',
                'version': version,
                'confidence': 0.0,
                'details': 'data 폴더 없음'
            }

        confidence += 0.3
        details.append('✓ data/ 폴더 발견')

        # JSON 파일 확인 (MV/MZ)
        json_files = list(data_folder.glob('*.json'))
        if json_files:
            confidence += 0.3
            details.append(f'✓ JSON 파일 {len(json_files)}개 발견')

            # 특정 JSON 파일로 버전 판별
            key_files = ['System.json', 'Actors.json', 'Map001.json']
            found_keys = [f.name for f in json_files if f.name in key_files]

            if found_keys:
                confidence += 0.2
                details.append(f'✓ 핵심 파일: {", ".join(found_keys[:3])}')

            # js 폴더로 MV/MZ 구분
            js_folder = game_path / 'js'
            if js_folder.exists():
                if (js_folder / 'rmmz_core.js').exists():
                    version = 'MZ'
                    type_name = 'rpgmaker_mz'
                    confidence += 0.2
                    details.append('✓ RPG Maker MZ 확인 (rmmz_core.js)')
                elif (js_folder / 'rpg_core.js').exists():
                    version = 'MV'
                    type_name = 'rpgmaker_mv'
                    confidence += 0.2
                    details.append('✓ RPG Maker MV 확인 (rpg_core.js)')
                else:
                    version = 'MV/MZ'
                    type_name = 'rpgmaker_mv'

        # rvdata2 파일 확인 (VX Ace)
        rvdata2_files = list(data_folder.glob('*.rvdata2'))
        if rvdata2_files:
            confidence = 0.9
            version = 'VX Ace'
            type_name = 'rpgmaker_vx_ace'
            details = [
                '✓ RPG Maker VX Ace 확인',
                f'✓ rvdata2 파일 {len(rvdata2_files)}개 발견'
            ]

        # rvdata 파일 확인 (VX)
        rvdata_files = list(data_folder.glob('*.rvdata'))
        if rvdata_files:
            confidence = 0.9
            version = 'VX'
            type_name = 'rpgmaker_vx'
            details = [
                '✓ RPG Maker VX 확인',
                f'✓ rvdata 파일 {len(rvdata_files)}개 발견'
            ]

        # 실행 파일 확인
        exe_files = list(game_path.glob('*.exe'))
        if exe_files:
            details.append(f'✓ 실행 파일: {exe_files[0].name}')

        return {
            'type': type_name,
            'engine': 'RPG Maker',
            'version': version,
            'confidence': confidence,
            'details': '\n'.join(details)
        }

    @staticmethod
    def _detect_unity(game_path: Path) -> Dict:
        """Unity 게임 감지"""
        confidence = 0.0
        details = []
        game_type = 'unknown'
        version = None

        # *_Data 폴더 확인
        data_folders = list(game_path.glob('*_Data'))
        if not data_folders:
            return {
                'type': game_type,
                'engine': 'Unity',
                'version': version,
                'confidence': 0.0,
                'details': 'Unity _Data 폴더 없음'
            }

        confidence += 0.4
        data_folder = data_folders[0]
        game_name = data_folder.name.replace('_Data', '')
        details.append(f'✓ Unity 게임 확인: {game_name}')

        # StreamingAssets 확인
        streaming_assets = data_folder / 'StreamingAssets'
        if streaming_assets.exists():
            confidence += 0.2
            details.append('✓ StreamingAssets 폴더 발견')

            # Naninovel 감지
            naninovel_folder = streaming_assets / 'Naninovel'
            if naninovel_folder.exists():
                confidence = 0.95
                game_type = 'unity_naninovel'
                version = 'Naninovel'
                details.append('✓ Naninovel 엔진 감지')

                # 스크립트 파일 확인
                script_files = list(naninovel_folder.glob('**/*.nani')) + \
                               list(naninovel_folder.glob('**/*.txt'))
                if script_files:
                    details.append(f'✓ 스크립트 파일 {len(script_files)}개 발견')

            # 번들 파일 확인
            bundle_files = list(streaming_assets.glob('**/*.bundle'))
            if bundle_files and game_type == 'unknown':
                confidence += 0.2
                details.append(f'✓ Asset Bundle {len(bundle_files)}개 발견')

        # Asset Bundle 파일 확인 (일반 Unity)
        if game_type == 'unknown':
            all_bundles = list(game_path.glob('**/*.bundle'))
            if all_bundles:
                game_type = 'unity_general'
                version = 'Asset Bundle'
                confidence += 0.3
                details.append(f'✓ 일반 Unity 게임 (Asset Bundle)')

        # Managed 폴더 확인
        managed_folder = data_folder / 'Managed'
        if managed_folder.exists():
            confidence += 0.1
            details.append('✓ Managed DLL 폴더 발견')

        # globalgamemanagers 확인
        if (data_folder / 'globalgamemanagers').exists():
            confidence += 0.1

        if game_type == 'unknown' and confidence > 0.4:
            game_type = 'unity_general'
            version = 'General'

        return {
            'type': game_type,
            'engine': 'Unity',
            'version': version,
            'confidence': confidence,
            'details': '\n'.join(details)
        }

    @staticmethod
    def _detect_other(game_path: Path) -> Dict:
        """기타 게임 엔진 감지"""
        confidence = 0.0
        details = []
        game_type = 'unknown'
        engine = '알 수 없음'

        # Ren'Py
        if (game_path / 'renpy').exists():
            return {
                'type': 'renpy',
                'engine': "Ren'Py",
                'version': None,
                'confidence': 0.9,
                'details': "✓ Ren'Py 비주얼 노벨 엔진"
            }

        # Wolf RPG
        if (game_path / 'Game.exe').exists() and (game_path / 'Data').exists():
            data_files = list((game_path / 'Data').glob('*.wolf'))
            if data_files:
                return {
                    'type': 'wolf_rpg',
                    'engine': 'WOLF RPG Editor',
                    'version': None,
                    'confidence': 0.9,
                    'details': f'✓ WOLF RPG Editor\n✓ .wolf 파일 {len(data_files)}개'
                }

        # Kirikiri/TyranoScript
        if list(game_path.glob('*.xp3')):
            return {
                'type': 'kirikiri',
                'engine': 'Kirikiri',
                'version': None,
                'confidence': 0.85,
                'details': '✓ Kirikiri 엔진 (.xp3)'
            }

        return {
            'type': game_type,
            'engine': engine,
            'version': None,
            'confidence': confidence,
            'details': '\n'.join(details) if details else '지원하지 않는 형식'
        }

    @staticmethod
    def get_display_text(game_info: Dict) -> str:
        """
        게임 정보를 사용자 친화적인 텍스트로 변환

        Args:
            game_info: detect_game_type()의 반환값

        Returns:
            표시용 텍스트
        """
        engine = game_info.get('engine', '알 수 없음')
        version = game_info.get('version')
        confidence = game_info.get('confidence', 0.0)
        details = game_info.get('details', '')

        # 게임 타입별 한글 이름
        type_names = {
            'rpgmaker_mv': 'RPG Maker MV',
            'rpgmaker_mz': 'RPG Maker MZ',
            'rpgmaker_vx_ace': 'RPG Maker VX Ace',
            'rpgmaker_vx': 'RPG Maker VX',
            'unity_naninovel': 'Unity (Naninovel)',
            'unity_general': 'Unity (일반)',
            'renpy': "Ren'Py",
            'wolf_rpg': 'WOLF RPG Editor',
            'kirikiri': 'Kirikiri',
            'unknown': '알 수 없음'
        }

        game_type = game_info.get('type', 'unknown')
        type_display = type_names.get(game_type, game_type)

        # 신뢰도 표시
        if confidence >= 0.9:
            confidence_text = '매우 높음'
            confidence_icon = '✅'
        elif confidence >= 0.7:
            confidence_text = '높음'
            confidence_icon = '✓'
        elif confidence >= 0.5:
            confidence_text = '보통'
            confidence_icon = '⚠️'
        else:
            confidence_text = '낮음'
            confidence_icon = '❌'

        text = f"{confidence_icon} 게임 형식: {type_display}\n"
        text += f"엔진: {engine}"

        if version:
            text += f" {version}"

        text += f"\n신뢰도: {confidence_text} ({confidence*100:.0f}%)"

        if details:
            text += f"\n\n상세 정보:\n{details}"

        return text
