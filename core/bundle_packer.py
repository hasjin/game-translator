"""Asset Bundle 패키징 및 교체"""
from pathlib import Path
from typing import Dict, List
import UnityPy
import shutil
from datetime import datetime


class BundlePacker:
    """번역 파일을 Asset Bundle에 다시 패키징"""

    def __init__(self):
        self.backup_dir = None

    def apply_translations(
        self,
        game_path: Path,
        target_language: str,
        translated_files: Dict[str, str],
        create_backup: bool = True,
        rpg_mode: str = 'replace'  # RPG Maker 전용: 'replace' or 'multilang'
    ):
        """번역을 게임에 적용

        Args:
            game_path: 게임 루트 폴더
            target_language: 대체할 언어 코드 (예: 'zh-Hans')
            translated_files: {원본파일명: 번역파일경로} 딕셔너리 또는 번역 데이터 리스트
            create_backup: 백업 생성 여부

        Returns:
            성공 여부
        """
        from core.game_language_detector import GameLanguageDetector

        detector = GameLanguageDetector()

        # 게임 타입 감지
        game_info = detector.detect_game_format(game_path)
        game_type = game_info.get('game_type', 'unknown')

        # RPG Maker 게임인 경우
        if game_type == 'rpgmaker':
            from core.rpgmaker_packer import RPGMakerPacker

            print("[INFO] RPG Maker 게임 감지됨 - RPGMakerPacker 사용")
            packer = RPGMakerPacker()

            # translated_files가 리스트인 경우 (RPG Maker 형식)
            if isinstance(translated_files, list):
                # target_language가 없으면 기본값 'ko' 사용
                lang_code = target_language if target_language else 'ko'
                return packer.apply_translations(
                    game_path=game_path,
                    translated_data=translated_files,
                    create_backup=create_backup,
                    target_language=lang_code,
                    mode=rpg_mode  # 'replace' or 'multilang'
                )
            else:
                print("[ERROR] RPG Maker는 리스트 형식의 번역 데이터가 필요합니다")
                return False

        # Unity 게임인 경우 (기존 로직)

        # 대상 언어의 Bundle 파일 찾기
        target_bundles = detector.find_target_bundles(game_path, target_language)

        if not target_bundles:
            print(f"[ERROR] {target_language} 언어의 Asset Bundle을 찾을 수 없습니다.")
            return False

        print(f"[INFO] 대상 Bundle: {len(target_bundles)}개")

        # 백업 생성
        if create_backup:
            self.backup_dir = self._create_backup(target_bundles)
            print(f"[BACKUP] 백업 생성: {self.backup_dir}")

        # 각 Bundle 파일 처리
        success_count = 0
        for bundle_path in target_bundles:
            try:
                if self._pack_bundle(bundle_path, translated_files):
                    success_count += 1
            except Exception as e:
                print(f"[WARNING] Bundle 처리 실패: {bundle_path.name} - {str(e)}")

        print(f"\n[SUCCESS] 완료: {success_count}/{len(target_bundles)}개 Bundle 적용")
        return success_count > 0

    def _create_backup(self, bundle_files: List[Path]) -> Path:
        """원본 파일 백업

        Args:
            bundle_files: 백업할 파일 리스트

        Returns:
            백업 폴더 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups") / f"bundle_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for bundle_file in bundle_files:
            # 상대 경로 유지하면서 백업
            relative_path = bundle_file.name
            backup_file = backup_dir / relative_path

            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundle_file, backup_file)

        return backup_dir

    def _pack_bundle(
        self,
        bundle_path: Path,
        translated_files: Dict[str, str]
    ) -> bool:
        """단일 Bundle에 번역 적용

        Args:
            bundle_path: Asset Bundle 파일 경로
            translated_files: {원본파일명: 번역파일경로} 딕셔너리

        Returns:
            성공 여부
        """
        try:
            # Bundle 로드
            env = UnityPy.load(str(bundle_path))

            modified = False
            asset_names = []

            # 모든 TextAsset 순회
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    data = obj.read()

                    # 파일명 매칭 (name 또는 m_Name 체크)
                    asset_name = None
                    if hasattr(data, 'name') and data.name:
                        asset_name = data.name
                    elif hasattr(data, 'm_Name') and data.m_Name:
                        asset_name = data.m_Name

                    if asset_name:
                        asset_names.append(asset_name)

                    if asset_name and asset_name in translated_files:
                        translated_path = Path(translated_files[asset_name])

                        if translated_path.exists():
                            # 번역 파일 읽기
                            with open(translated_path, 'r', encoding='utf-8') as f:
                                translated_content = f.read()

                            # TextAsset 데이터 교체 (문자열로 직접 할당)
                            data.m_Script = translated_content
                            data.save()
                            modified = True

                            print(f"  [OK] {asset_name} 적용")

            # 디버깅: 매칭되지 않은 경우
            if not modified and asset_names:
                print(f"  [INFO] Bundle 내 TextAsset: {', '.join(asset_names[:3])}...")
                print(f"  [INFO] 번역 파일 키 예시: {', '.join(list(translated_files.keys())[:3])}...")
                # 첫 번째 asset과 비슷한 키 찾기
                if asset_names:
                    first_asset = asset_names[0]
                    matching = [k for k in translated_files.keys() if first_asset in k or k in first_asset]
                    if matching:
                        print(f"  [MATCH] '{first_asset}'와 유사한 키: {matching[:3]}")

            # 수정된 경우 저장
            if modified:
                # 원본 파일에 덮어쓰기
                with open(bundle_path, 'wb') as f:
                    f.write(env.file.save())

                print(f"[SAVE] 저장: {bundle_path.name}")
                return True
            else:
                print(f"[INFO] 변경 사항 없음: {bundle_path.name}")
                return False

        except Exception as e:
            print(f"[ERROR] Bundle 처리 실패: {bundle_path.name}")
            print(f"   오류: {str(e)}")
            return False

    def restore_backup(self, backup_dir: Path, game_path: Path):
        """백업에서 복원

        Args:
            backup_dir: 백업 폴더
            game_path: 게임 폴더
        """
        if not backup_dir.exists():
            print(f"[ERROR] 백업 폴더가 없습니다: {backup_dir}")
            return False

        # 백업된 파일들을 원래 위치로 복사
        for backup_file in backup_dir.rglob("*"):
            if backup_file.is_file():
                # 원래 경로 찾기
                relative_path = backup_file.relative_to(backup_dir)

                # 게임 폴더에서 원본 위치 찾기 (간단하게 파일명으로 검색)
                for original in game_path.rglob(backup_file.name):
                    if original.is_file():
                        shutil.copy2(backup_file, original)
                        print(f"[OK] 복원: {original.name}")

        print("[SUCCESS] 백업 복원 완료")
        return True


# 사용 예시
if __name__ == "__main__":
    packer = BundlePacker()

    game_path = Path(r"C:\Your\Game\Path")

    # 번역 파일 매핑 예시 (확장자 제거된 파일명을 키로 사용)
    translated_files = {
        "Act01_Chapter01_Adv01": "projects/your_project/preview/Act01_Chapter01_Adv01.txt",
        "Act01_Chapter01_Adv02": "projects/your_project/preview/Act01_Chapter01_Adv02.txt",
    }

    # 중국어를 한국어로 교체
    packer.apply_translations(
        game_path=game_path,
        target_language="zh-Hans",
        translated_files=translated_files,
        create_backup=True
    )
