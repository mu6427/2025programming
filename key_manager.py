"""
API 키 암호화/복호화 유틸리티
"""
import base64
import os

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("경고: cryptography 모듈이 설치되지 않았습니다. pip install cryptography를 실행하세요.")


def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
    """비밀번호로부터 암호화 키 생성"""
    if salt is None:
        salt = b'default_salt_change_in_production'  # 프로덕션에서는 랜덤 salt 사용
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_api_key(api_key: str, password: str = None) -> str:
    """API 키를 암호화"""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography 모듈이 필요합니다. 'pip install cryptography'를 실행하세요.")
    
    if password is None:
        # 환경 변수에서 비밀번호 가져오기
        password = os.getenv("ENCRYPTION_PASSWORD", "default_password_change_me")
    
    key = generate_key_from_password(password)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str, password: str = None) -> str:
    """암호화된 API 키를 복호화"""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography 모듈이 필요합니다. 'pip install cryptography'를 실행하세요.")
    
    if password is None:
        password = os.getenv("ENCRYPTION_PASSWORD", "default_password_change_me")
    
    key = generate_key_from_password(password)
    fernet = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  암호화: python key_manager.py encrypt <API_KEY>")
        print("  복호화: python key_manager.py decrypt <ENCRYPTED_KEY>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "encrypt":
        if len(sys.argv) < 3:
            print("API 키를 입력해주세요.")
            sys.exit(1)
        api_key = sys.argv[2]
        encrypted = encrypt_api_key(api_key)
        print(f"암호화된 키: {encrypted}")
        print("\n이 키를 .streamlit/secrets.toml에 다음과 같이 저장하세요:")
        print(f'OPENAI_API_KEY_ENCRYPTED = "{encrypted}"')
    
    elif command == "decrypt":
        if len(sys.argv) < 3:
            print("암호화된 키를 입력해주세요.")
            sys.exit(1)
        encrypted_key = sys.argv[2]
        try:
            decrypted = decrypt_api_key(encrypted_key)
            print(f"복호화된 키: {decrypted}")
        except Exception as e:
            print(f"복호화 실패: {e}")
    
    else:
        print(f"알 수 없는 명령: {command}")

