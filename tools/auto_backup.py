"""자동 백업 시스템

번역 작업 중 자동으로 백업하여 데이터 손실 방지
"""
import shutil
from pathlib import Path
from datetime import datetime
import zipfile
import json
from typing import Optional, List
import schedule
import time
import threading


class AutoBackup:
    """자동 백업 관리자"""

    def __init__(
        self,
        source_dir: str,
        backup_dir: str = "backups",
        max_backups: int = 10
    ):
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups

        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, comment: str = "") -> str:
        """백업 생성

        Returns:
            백업 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name

        # ZIP 압축
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.source_dir)
                    zipf.write(file_path, arcname)

        # 메타데이터
        meta = {
            'timestamp': timestamp,
            'comment': comment,
            'file_count': len(list(self.source_dir.rglob('*'))),
            'size_mb': backup_path.stat().st_size / (1024 * 1024)
        }

        meta_path = self.backup_dir / f"backup_{timestamp}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

        print(f"✅ 백업 생성: {backup_path} ({meta['size_mb']:.2f}MB)")

        # 오래된 백업 삭제
        self.cleanup_old_backups()

        return str(backup_path)

    def restore_backup(self, backup_name: str):
        """백업 복원"""
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            print(f"❌ 백업 파일 없음: {backup_path}")
            return

        # 현재 파일 백업 (안전)
        safety_backup = self.create_backup(comment="복원 전 자동 백업")

        # 복원
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(self.source_dir)

        print(f"✅ 백업 복원 완료: {backup_name}")
        print(f"   안전 백업: {safety_backup}")

    def list_backups(self) -> List[Dict]:
        """백업 목록"""
        backups = []

        for backup_file in sorted(self.backup_dir.glob("backup_*.zip")):
            timestamp = backup_file.stem.replace("backup_", "")
            meta_file = self.backup_dir / f"backup_{timestamp}.json"

            meta = {}
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

            backups.append({
                'name': backup_file.name,
                'timestamp': timestamp,
                'size_mb': backup_file.stat().st_size / (1024 * 1024),
                'comment': meta.get('comment', ''),
                'file_count': meta.get('file_count', 0)
            })

        return backups

    def cleanup_old_backups(self):
        """오래된 백업 삭제"""
        backups = sorted(self.backup_dir.glob("backup_*.zip"))

        if len(backups) > self.max_backups:
            to_delete = backups[:-self.max_backups]
            for backup in to_delete:
                # ZIP 및 메타데이터 삭제
                backup.unlink()
                meta = backup.parent / f"{backup.stem}.json"
                if meta.exists():
                    meta.unlink()

            print(f"🗑️ 오래된 백업 {len(to_delete)}개 삭제됨")

    def auto_backup_daemon(self, interval_minutes: int = 30):
        """백업 데몬 (백그라운드 자동 백업)"""
        def backup_job():
            self.create_backup(comment=f"{interval_minutes}분 자동 백업")

        # 스케줄 설정
        schedule.every(interval_minutes).minutes.do(backup_job)

        # 백그라운드 실행
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)

        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()

        print(f"🕐 자동 백업 시작: {interval_minutes}분마다")


class ProgressCheckpoint:
    """진행 상황 체크포인트"""

    def __init__(self, checkpoint_file: str = "checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.data = self.load()

    def load(self) -> dict:
        """체크포인트 로드"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save(self, data: dict):
        """체크포인트 저장"""
        self.data.update(data)
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def save_progress(
        self,
        chapter: str,
        file_index: int,
        total_files: int,
        completed_dialogues: int
    ):
        """진행 상황 저장"""
        self.save({
            'chapter': chapter,
            'file_index': file_index,
            'total_files': total_files,
            'completed_dialogues': completed_dialogues,
            'timestamp': datetime.now().isoformat(),
            'resume_possible': True
        })

        print(f"📍 체크포인트 저장: {chapter} [{file_index}/{total_files}]")

    def can_resume(self) -> bool:
        """재개 가능 여부"""
        return self.data.get('resume_possible', False)

    def get_resume_point(self) -> dict:
        """재개 지점 정보"""
        return {
            'chapter': self.data.get('chapter'),
            'file_index': self.data.get('file_index', 0),
            'total_files': self.data.get('total_files', 0),
            'completed_dialogues': self.data.get('completed_dialogues', 0)
        }

    def clear(self):
        """체크포인트 클리어"""
        self.data = {}
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


class VersionControl:
    """간단한 버전 관리"""

    def __init__(self, versions_dir: str = "versions"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def create_version(
        self,
        file_path: str,
        version_name: str = "",
        comment: str = ""
    ):
        """파일 버전 생성"""
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"❌ 파일 없음: {file_path}")
            return

        # 버전 이름
        if not version_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_name = f"v_{timestamp}"

        # 버전 디렉토리
        version_dir = self.versions_dir / file_path.stem / version_name
        version_dir.mkdir(parents=True, exist_ok=True)

        # 파일 복사
        version_file = version_dir / file_path.name
        shutil.copy2(file_path, version_file)

        # 메타데이터
        meta = {
            'version_name': version_name,
            'original_path': str(file_path),
            'comment': comment,
            'timestamp': datetime.now().isoformat(),
            'size': file_path.stat().st_size
        }

        with open(version_dir / "meta.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

        print(f"📌 버전 생성: {version_name} - {comment}")

    def list_versions(self, file_name: str) -> List[Dict]:
        """파일 버전 목록"""
        file_versions_dir = self.versions_dir / Path(file_name).stem

        if not file_versions_dir.exists():
            return []

        versions = []
        for version_dir in sorted(file_versions_dir.iterdir()):
            if version_dir.is_dir():
                meta_file = version_dir / "meta.json"
                if meta_file.exists():
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        versions.append(json.load(f))

        return versions

    def restore_version(self, file_name: str, version_name: str):
        """버전 복원"""
        version_dir = self.versions_dir / Path(file_name).stem / version_name
        meta_file = version_dir / "meta.json"

        if not meta_file.exists():
            print(f"❌ 버전 없음: {version_name}")
            return

        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        original_path = Path(meta['original_path'])
        version_file = version_dir / original_path.name

        # 복원
        shutil.copy2(version_file, original_path)
        print(f"✅ 버전 복원: {version_name} → {original_path}")


# 사용 예시
if __name__ == "__main__":
    # 자동 백업
    backup = AutoBackup(
        source_dir="translation_work/extracted",
        max_backups=10
    )

    # 수동 백업
    backup.create_backup(comment="번역 시작 전")

    # 백업 목록
    for b in backup.list_backups():
        print(f"{b['name']}: {b['size_mb']:.2f}MB - {b['comment']}")

    # 자동 백업 시작 (30분마다)
    # backup.auto_backup_daemon(interval_minutes=30)

    # 체크포인트
    checkpoint = ProgressCheckpoint()
    checkpoint.save_progress(
        chapter="Act01_Ch01",
        file_index=10,
        total_files=44,
        completed_dialogues=500
    )

    # 재개
    if checkpoint.can_resume():
        resume_point = checkpoint.get_resume_point()
        print(f"📍 재개 가능: {resume_point}")
