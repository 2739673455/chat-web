from cryptography.fernet import Fernet

from app.config.config import CFG

_fernet = Fernet(CFG.encryption_key.encode())  # 初始化加密器


def encrypt(plaintext: str | None) -> str | None:
    """加密明文字符串"""
    if not plaintext:
        return plaintext
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str | None) -> str | None:
    """解密密文字符串"""
    if not ciphertext:
        return ciphertext
    return _fernet.decrypt(ciphertext.encode()).decode()


if __name__ == "__main__":
    print(encrypt("sk-fff58ca453e4a4b01ef922a5e83a5d9a"))
