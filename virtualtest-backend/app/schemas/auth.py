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


from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


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
        description="User email address"
    )
    
    password: str = Field(
        ...,
        min_length=1,  # Login'de uzunluk kontrolü gevşek
        description="User password"
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
        description="Token type"
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
        description="Email address (must be unique)"
    )
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)"
    )
    
    # Şifre tekrarı (frontend'de eşleşme kontrolü için)
    password_confirm: str = Field(
        ..., 
        min_length=8,
        description="Must match password"
    )
    
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Tam ad"
    )


    # EMAIL VALIDATOR / EMAIL DOĞRULAYICI
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """
        Custom check for email format to provide descriptive error messages.
        Daha açıklayıcı hata mesajları sağlamak için özel email format kontrolü.
        """
        # Standard email pattern / Standart email deseni
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Check basic format / Temel formatı kontrol et
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format. Use hakancaglar@ankarbilim.edu.tr')
        
        # Check for empty spaces / Boşluk kontrolü
        if " " in v:
            raise ValueError('Email cannot contain spaces.')
            
        return v.lower() # Normalize to lowercase / Küçük harfe dönüştürerek standartlaştır


    # PASSWORD COMPLEXITY / ŞİFRE KARMAŞIKLIĞI
    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """
        Ensures the password meets complexity requirements (A-Z, a-z, 0-9, symbol).
        Şifrenin karmaşıklık kurallarına uygunluğunu denetler (A-Z, a-z, 0-9, sembol).
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character.')
        return v

    # PASSWORD MATCH / ŞİFRE EŞLEŞMESİ
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """
        Validates that password_confirm matches the password field.
        password_confirm alanının password alanı ile aynı olduğunu doğrular.
        """
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match.')
        return v

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
        default="Registration successful",
        description="Success message"
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
    
    # Kullanıcı rolü (opsiyonel)
    role: Optional[str] = None

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
        description="Current password"
    )
    
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="New password (minimum 8 characters)"
    )
    
    new_password_confirm: str = Field(
        ...,
        description="New password confirmation"
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
        description="Reset token from email"
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