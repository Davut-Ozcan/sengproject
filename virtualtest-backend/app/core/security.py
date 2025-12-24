# ============================================
# app/core/security.py - Security Utilities
# ============================================
#
# Ne yapıyor?
# - Şifre hashing (bcrypt)
# - JWT token oluşturma/doğrulama
#
# Kullanım:
#   from app.core.security import hash_password, verify_password
#   from app.core.security import create_access_token, decode_access_token
# ============================================

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings


# ==========================================
# PASSWORD HASHING
# ==========================================

# bcrypt context
# deprecated="auto": Eski hash'leri otomatik güncelle
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Şifreyi hashler.
    
    Kullanım:
        hashed = hash_password("mypassword123")
        # "$2b$12$..."
    
    Input:
        password: Düz metin şifre
    
    Output:
        str: Hashlenmiş şifre (bcrypt formatında)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Şifreyi doğrular.
    
    Kullanım:
        is_valid = verify_password("mypassword123", hashed_from_db)
        if is_valid:
            print("Şifre doğru!")
    
    Input:
        plain_password: Kullanıcının girdiği şifre
        hashed_password: Veritabanındaki hashlenmiş şifre
    
    Output:
        bool: Şifre doğru mu?
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# JWT TOKEN
# ==========================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    JWT access token oluşturur.
    
    Kullanım:
        token = create_access_token(
            data={"sub": "user@example.com", "user_id": 5}
        )
        # "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    Input:
        data: Token içine gömülecek veri
              "sub" (subject) genelde email veya user_id olur
        expires_delta: Token geçerlilik süresi (opsiyonel)
    
    Output:
        str: JWT token string
    """
    to_encode = data.copy()
    
    # Expire time hesapla
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Expire time'ı token'a ekle
    to_encode.update({"exp": expire})
    
    # Token oluştur
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT token'ı decode eder.
    
    Kullanım:
        payload = decode_access_token(token)
        if payload:
            user_email = payload.get("sub")
            user_id = payload.get("user_id")
        else:
            print("Token geçersiz!")
    
    Input:
        token: JWT token string
    
    Output:
        Dict: Token payload (data)
        None: Token geçersiz veya expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        print(f"⚠️ JWT Decode Error: {e}")
        return None

def verify_token(token: str) -> Optional[dict]:
    """
    JWT token'ı doğrular ve payload'ı döndürür.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Token payload (sub, exp, vs.) veya None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
    
    
def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Refresh token oluşturur (uzun süreli).
    
    Access token expire olunca bu token ile yeni access token alınır.
    
    Kullanım:
        refresh_token = create_refresh_token({"sub": "user@example.com"})
    
    Input:
        data: Token içine gömülecek veri
        expires_delta: Token geçerlilik süresi (varsayılan 7 gün)
    
    Output:
        str: JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Refresh token 7 gün geçerli
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


# ==========================================
# TOKEN VALIDATION HELPERS
# ==========================================

def is_token_expired(token: str) -> bool:
    """
    Token'ın expire olup olmadığını kontrol eder.
    
    Kullanım:
        if is_token_expired(token):
            print("Token süresi dolmuş!")
    """
    payload = decode_access_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.utcnow() > datetime.fromtimestamp(exp)


def get_token_subject(token: str) -> Optional[str]:
    """
    Token'dan subject (genelde email) alır.
    
    Kullanım:
        email = get_token_subject(token)
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return Nones