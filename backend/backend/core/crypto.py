from cryptography.fernet import Fernet
from django.conf import settings

# 1. 암호화 키를 settings에서 가져오거나 없으면 새로 생성
SECRET_KEY = getattr(settings, 'ENCRYPTION_KEY', None)
if not SECRET_KEY:
    SECRET_KEY = Fernet.generate_key()
    setattr(settings, 'ENCRYPTION_KEY', SECRET_KEY)
fernet = Fernet(SECRET_KEY)

# 2. 암호화 함수
def encrypt(text: str) -> str:
    """문자열 암호화"""
    if not text:
        return ''
    return fernet.encrypt(text.encode()).decode()

# 3. 복호화 함수
def decrypt(token: str) -> str:
    """문자열 복호화"""
    if not token:
        return ''
    return fernet.decrypt(token.encode()).decode()