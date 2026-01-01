# ============================================
# app/schemas/auth.py - Authentication Şemaları
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Login ve Register işlemleri için şablonlar.
# JWT token döndürme formatı.
#
# Auth Akışı:
# -----------
# 1. Register: email + password → Hesap oluştur → Token döndür
# 2. Login: email + password → Doğrula → Token döndür
# 3. Her istek: Token gönder → Backend doğrular → İşlemi yap
# ============================================


from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ==========================================
# LOGIN SCHEMAS
# ==========================================

class LoginRequest(BaseModel):
    """
    Login isteği şeması.
    
    Kullanıcı giriş yaparken gönderdiği veri.
    
    Örnek İstek (POST /api/auth/login):
    {
        "email": "test@test.com",
        "password": "şifrem123"
    }
    """
    
    email: EmailStr = Field(
        ...,
        description="Kullanıcı email adresi"
    )
    
    password: str = Field(
        ...,
        min_length=1,  # Login'de uzunluk kontrolü gevşek
        description="Kullanıcı şifresi"
    )


class LoginResponse(BaseModel):
    """
    Login yanıtı şeması.
    
    Başarılı login sonrası döndürülen veri.
    
    Örnek Yanıt:
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "test@test.com",
            "role": "Student"
        }
    }
    """
    
    # JWT Token
    # Frontend bunu saklayacak ve her istekte gönderecek
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    
    # Token tipi (her zaman "bearer")
    # Authorization header'da kullanılır:
    # "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
    token_type: str = Field(
        default="bearer",
        description="Token tipi"
    )
    
    # Kullanıcı bilgileri (opsiyonel)
    # Frontend'in hemen kullanabilmesi için
    user_id: int
    email: str
    role: str
    full_name: Optional[str] = None


# ==========================================
# REGISTER SCHEMAS
# ==========================================

class RegisterRequest(BaseModel):
    """
    Kayıt isteği şeması.
    
    Yeni kullanıcı kaydı için gönderilen veri.
    
    Örnek İstek (POST /api/auth/register):
    {
        "email": "yeni@kullanici.com",
        "password": "güçlü_şifre_123",
        "full_name": "Yeni Kullanıcı"
    }
    """
    
    email: EmailStr = Field(
        ...,
        description="Email adresi (benzersiz olmalı)"
    )
    
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Şifre (minimum 6 karakter)"
    )
    
    # Şifre tekrarı (frontend'de eşleşme kontrolü için)
    password_confirm: Optional[str] = Field(
        None,
        description="Şifre tekrarı (opsiyonel)"
    )
    
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Tam ad"
    )


class RegisterResponse(BaseModel):
    """
    Kayıt yanıtı şeması.
    
    Başarılı kayıt sonrası döndürülen veri.
    
    Örnek Yanıt:
    {
        "message": "Kayıt başarılı",
        "user_id": 1,
        "email": "yeni@kullanici.com",
        "access_token": "eyJhbGciOiJIUzI1NiIs..."
    }
    """
    
    message: str = Field(
        default="Kayıt başarılı",
        description="Başarı mesajı"
    )
    
    user_id: int
    email: str
    
    # Kayıttan hemen sonra token ver (otomatik login)
    access_token: str
    token_type: str = "bearer"


# ==========================================
# TOKEN SCHEMAS
# ==========================================

class Token(BaseModel):
    """
    Sadece token döndüren şema.
    
    Token yenileme gibi işlemlerde kullanılır.
    """
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Token içindeki veri şeması.
    
    JWT decode edildiğinde çıkan payload.
    Backend içinde kullanılır.
    """
    
    # subject: Token'ın sahibi (genellikle user_id)
    sub: Optional[str] = None
    
    # Token'ın ne zaman oluşturulduğu
    exp: Optional[int] = None


# ==========================================
# PASSWORD SCHEMAS
# ==========================================

class PasswordChange(BaseModel):
    """
    Şifre değiştirme şeması.
    
    Kullanıcı kendi şifresini değiştirirken.
    
    Örnek (PUT /api/auth/password):
    {
        "current_password": "eski_şifre",
        "new_password": "yeni_güçlü_şifre",
        "new_password_confirm": "yeni_güçlü_şifre"
    }
    """
    
    current_password: str = Field(
        ...,
        description="Mevcut şifre"
    )
    
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Yeni şifre (min 6 karakter)"
    )
    
    new_password_confirm: str = Field(
        ...,
        description="Yeni şifre tekrarı"
    )


class PasswordReset(BaseModel):
    """
    Şifre sıfırlama isteği şeması.
    
    "Şifremi unuttum" butonu için.
    
    Örnek (POST /api/auth/forgot-password):
    {
        "email": "unutkan@kullanici.com"
    }
    """
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """
    Şifre sıfırlama onay şeması.
    
    Email'deki link tıklandığında.
    
    Örnek (POST /api/auth/reset-password):
    {
        "token": "abc123...",
        "new_password": "yeni_şifre_123"
    }
    """
    
    token: str = Field(
        ...,
        description="Email'deki sıfırlama token'ı"
    )
    
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100
    )


# ==========================================
# MESSAGE SCHEMAS (Genel yanıtlar)
# ==========================================

class MessageResponse(BaseModel):
    """
    Basit mesaj yanıtı.
    
    İşlem başarılı/başarısız mesajları için.
    
    Örnek:
    {
        "message": "İşlem başarılı",
        "success": true
    }
    """
    
    message: str
    success: bool = True