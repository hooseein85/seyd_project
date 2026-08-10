from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

# تنظیمات امنیتی (در پروژه‌های واقعی این‌ها از فایل env. خوانده می‌شوند)
# اما فعلاً برای اینکه سریع بالا بیاییم همینجا تعریفشان می‌کنیم
SECRET_KEY = "Vali@asr123" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # توکن برای ۲۴ ساعت معتبر است

# راه‌اندازی سیستم هش کردن با الگوریتم bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """پسورد خام وارد شده توسط کاربر را با هشِ داخل دیتابیس مقایسه می‌کند"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """پسورد خام را می‌گیرد و یک رشته هش شده و غیرقابل برگشت تحویل می‌دهد"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """دیتای کاربر را می‌گیرد و یک توکن JWT برایش امضا می‌کند"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt