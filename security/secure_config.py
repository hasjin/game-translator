"""암호화된 API 키 관리

Fernet 대칭 암호화 사용:
- 머신별 고유 키 생성 (UUID 기반)
- API 키 암호화 저장
- 외부에서 복호화 불가능
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import uuid


class SecureConfigManager:
    """암호화된 설정 관리자"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / ".api_keys.enc"
        self.salt_file = self.config_dir / ".salt"

        # 머신 고유 키 생성/로드
        self.cipher = self._get_cipher()

    def _get_machine_id(self) -> str:
        """머신 고유 ID 생성 (MAC 주소 기반)"""
        # MAC 주소만 사용 (고정값)
        mac = uuid.getnode()
        machine_id = f"translator-{mac}"
        return machine_id

    def _get_cipher(self) -> Fernet:
        """암호화 cipher 생성"""
        # Salt 로드 또는 생성
        if self.salt_file.exists():
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)

        # 머신 ID 기반 키 파생
        machine_id = self._get_machine_id()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return Fernet(key)

    def save_api_key(self, service: str, api_key: str):
        """API 키 암호화하여 저장

        Args:
            service: 서비스 이름 (claude, openai, deepl 등)
            api_key: API 키
        """
        # 기존 설정 로드
        config = self._load_config()

        # API 키 암호화
        encrypted = self.cipher.encrypt(api_key.encode())
        config[service] = encrypted.decode()

        # 저장
        self._save_config(config)

    def get_api_key(self, service: str) -> Optional[str]:
        """API 키 복호화하여 반환

        Args:
            service: 서비스 이름

        Returns:
            복호화된 API 키 또는 None
        """
        config = self._load_config()

        if service not in config:
            return None

        try:
            encrypted = config[service].encode()
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error for {service}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_masked_key(self, service: str) -> Optional[str]:
        """API 키를 마스킹하여 반환 (앞 4자, 뒤 4자만)

        Args:
            service: 서비스 이름

        Returns:
            마스킹된 키 (예: "sk-a...xyz")
        """
        api_key = self.get_api_key(service)
        if not api_key:
            return None

        if len(api_key) <= 8:
            return "*" * len(api_key)

        return f"{api_key[:4]}...{api_key[-4:]}"

    def delete_api_key(self, service: str):
        """API 키 삭제

        Args:
            service: 서비스 이름
        """
        config = self._load_config()
        if service in config:
            del config[service]
            self._save_config(config)

    def list_services(self) -> list:
        """저장된 서비스 목록 반환"""
        config = self._load_config()
        return list(config.keys())

    def has_api_key(self, service: str) -> bool:
        """API 키 존재 여부 확인"""
        return service in self._load_config()

    def _load_config(self) -> Dict:
        """암호화된 설정 파일 로드"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self, config: Dict):
        """설정 파일 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        # 파일 권한 설정 (Windows는 무시됨)
        try:
            os.chmod(self.config_file, 0o600)  # 소유자만 읽기/쓰기
        except:
            pass

    def export_for_backup(self, output_file: str, password: str):
        """백업용 내보내기 (비밀번호 보호)

        Args:
            output_file: 출력 파일 경로
            password: 백업 비밀번호
        """
        # 비밀번호 기반 암호화
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        backup_cipher = Fernet(key)

        # 모든 API 키 수집
        config = self._load_config()
        plaintext_keys = {}

        for service in config:
            api_key = self.get_api_key(service)
            if api_key:
                plaintext_keys[service] = api_key

        # 암호화
        data = json.dumps(plaintext_keys).encode()
        encrypted = backup_cipher.encrypt(data)

        # 저장 (salt + 암호화된 데이터)
        with open(output_file, 'wb') as f:
            f.write(salt)
            f.write(encrypted)

    def import_from_backup(self, backup_file: str, password: str):
        """백업에서 가져오기

        Args:
            backup_file: 백업 파일 경로
            password: 백업 비밀번호
        """
        with open(backup_file, 'rb') as f:
            salt = f.read(16)
            encrypted = f.read()

        # 비밀번호로 복호화
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        backup_cipher = Fernet(key)

        try:
            decrypted = backup_cipher.decrypt(encrypted)
            plaintext_keys = json.loads(decrypted.decode())

            # 각 키 저장
            for service, api_key in plaintext_keys.items():
                self.save_api_key(service, api_key)

            return True
        except Exception:
            return False


# 사용 예시
if __name__ == "__main__":
    manager = SecureConfigManager()

    # API 키 저장
    manager.save_api_key("claude", "sk-ant-api03-xxxxxxxxxxxx")
    manager.save_api_key("openai", "sk-proj-xxxxxxxxxxxx")

    # API 키 조회
    claude_key = manager.get_api_key("claude")
    print(f"Claude 키: {claude_key}")

    # 마스킹된 키 조회
    masked = manager.get_masked_key("claude")
    print(f"마스킹: {masked}")  # sk-a...xxxx

    # 저장된 서비스 목록
    print(f"저장된 서비스: {manager.list_services()}")

    # 백업
    manager.export_for_backup("api_keys_backup.enc", "my_secure_password")
    print("✅ 백업 완료")
