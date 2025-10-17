"""
압축 파일 추출 유틸리티
일본어/한글 파일명을 안전하게 보존하며 ZIP, RAR 파일을 해제합니다.
"""
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Callable


class ArchiveExtractor:
    """압축 파일 추출기"""

    SUPPORTED_FORMATS = ['.zip', '.rar']

    @staticmethod
    def is_supported(file_path: Path) -> bool:
        """지원하는 압축 포맷인지 확인"""
        return file_path.suffix.lower() in ArchiveExtractor.SUPPORTED_FORMATS

    @staticmethod
    def extract(
        archive_path: Path,
        extract_to: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        압축 파일을 안전하게 해제

        Args:
            archive_path: 압축 파일 경로
            extract_to: 압축 해제 대상 폴더 (None이면 압축파일과 같은 폴더에 생성)
            progress_callback: 진행상황 콜백 함수 (current, total)

        Returns:
            압축 해제된 폴더 경로

        Raises:
            FileNotFoundError: 파일을 찾을 수 없음
            ValueError: 지원하지 않는 포맷
            RuntimeError: 압축 해제 실패
        """
        archive_path = Path(archive_path)

        if not archive_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {archive_path}")

        if not ArchiveExtractor.is_supported(archive_path):
            raise ValueError(f"지원하지 않는 포맷입니다: {archive_path.suffix}")

        # 압축 해제 폴더 결정
        if extract_to is None:
            extract_to = archive_path.parent / archive_path.stem
        else:
            extract_to = Path(extract_to)

        extract_to.mkdir(parents=True, exist_ok=True)

        # 포맷에 따라 적절한 메서드 호출
        if archive_path.suffix.lower() == '.zip':
            return ArchiveExtractor._extract_zip(archive_path, extract_to, progress_callback)
        elif archive_path.suffix.lower() == '.rar':
            return ArchiveExtractor._extract_rar(archive_path, extract_to, progress_callback)
        else:
            raise ValueError(f"지원하지 않는 포맷입니다: {archive_path.suffix}")

    @staticmethod
    def _extract_zip(
        zip_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        ZIP 파일을 일본어 파일명 보존하며 해제

        Args:
            zip_path: ZIP 파일 경로
            extract_to: 압축 해제 대상 폴더
            progress_callback: 진행상황 콜백 함수

        Returns:
            압축 해제된 폴더 경로
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)

                for idx, file_info in enumerate(file_list):
                    try:
                        # 파일명 인코딩 처리
                        filename = file_info.filename

                        # Shift-JIS로 인코딩된 파일명 처리
                        try:
                            filename = filename.encode('cp437').decode('shift-jis')
                        except (UnicodeDecodeError, UnicodeEncodeError):
                            # 실패하면 원본 파일명 사용
                            pass

                        # 파일 추출
                        target_path = extract_to / filename
                        target_path.parent.mkdir(parents=True, exist_ok=True)

                        # 디렉토리가 아닌 경우만 내용 추출
                        if not file_info.is_dir():
                            with zip_ref.open(file_info) as source, \
                                 open(target_path, 'wb') as target:
                                target.write(source.read())

                        # 진행상황 콜백
                        if progress_callback:
                            progress_callback(idx + 1, total_files)

                    except Exception as e:
                        # 개별 파일 오류는 무시하고 계속 진행
                        print(f"파일 추출 실패: {file_info.filename} - {e}")
                        continue

            return extract_to

        except Exception as e:
            raise RuntimeError(f"ZIP 파일 압축 해제 실패: {e}")

    @staticmethod
    def _extract_rar(
        rar_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        RAR 파일을 해제 (unar 사용)

        Args:
            rar_path: RAR 파일 경로
            extract_to: 압축 해제 대상 폴더
            progress_callback: 진행상황 콜백 함수

        Returns:
            압축 해제된 폴더 경로
        """
        # 먼저 rarfile 라이브러리 시도
        try:
            import rarfile
            return ArchiveExtractor._extract_rar_with_rarfile(
                rar_path, extract_to, progress_callback
            )
        except ImportError:
            pass

        # rarfile이 없으면 시스템 명령어 시도
        return ArchiveExtractor._extract_rar_with_command(
            rar_path, extract_to, progress_callback
        )

    @staticmethod
    def _extract_rar_with_rarfile(
        rar_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """rarfile 라이브러리를 사용한 RAR 해제"""
        import rarfile

        try:
            with rarfile.RarFile(rar_path, 'r') as rar_ref:
                file_list = rar_ref.infolist()
                total_files = len(file_list)

                for idx, file_info in enumerate(file_list):
                    try:
                        rar_ref.extract(file_info, extract_to)

                        # 진행상황 콜백
                        if progress_callback:
                            progress_callback(idx + 1, total_files)

                    except Exception as e:
                        print(f"파일 추출 실패: {file_info.filename} - {e}")
                        continue

            return extract_to

        except Exception as e:
            raise RuntimeError(f"RAR 파일 압축 해제 실패: {e}")

    @staticmethod
    def _extract_rar_with_command(
        rar_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """시스템 명령어를 사용한 RAR 해제"""
        # Mac/Linux: unar (The Unarchiver CLI)
        # Windows: UnRAR.exe

        try:
            # unar 명령어 시도 (Mac)
            result = subprocess.run(
                ['unar', '-o', str(extract_to), str(rar_path)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # 진행상황 콜백 (전체 완료로 표시)
                if progress_callback:
                    progress_callback(1, 1)
                return extract_to
            else:
                raise RuntimeError(f"unar 실행 실패: {result.stderr}")

        except FileNotFoundError:
            # unar가 없으면 unrar 시도
            try:
                result = subprocess.run(
                    ['unrar', 'x', '-o+', str(rar_path), str(extract_to)],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    if progress_callback:
                        progress_callback(1, 1)
                    return extract_to
                else:
                    raise RuntimeError(f"unrar 실행 실패: {result.stderr}")

            except FileNotFoundError:
                raise RuntimeError(
                    "RAR 파일 압축 해제 도구를 찾을 수 없습니다.\n"
                    "Mac: brew install unar\n"
                    "또는 rarfile 라이브러리 설치: pip install rarfile"
                )

    @staticmethod
    def get_archive_info(archive_path: Path) -> dict:
        """
        압축 파일 정보 조회

        Args:
            archive_path: 압축 파일 경로

        Returns:
            압축 파일 정보 딕셔너리
        """
        archive_path = Path(archive_path)

        if not archive_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {archive_path}")

        info = {
            'path': archive_path,
            'name': archive_path.name,
            'size': archive_path.stat().st_size,
            'format': archive_path.suffix.lower(),
            'supported': ArchiveExtractor.is_supported(archive_path)
        }

        # 파일 개수 조회 (ZIP만)
        if archive_path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    info['file_count'] = len(zip_ref.namelist())
            except:
                info['file_count'] = None

        return info
