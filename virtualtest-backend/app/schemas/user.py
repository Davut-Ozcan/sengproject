# ============================================
# app/schemas/user.py - User Şemaları
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# API'ye gelen ve giden verilerin formatını tanımlar.
# Pydantic ile veri doğrulama (validation) yapar.
#
# Schema vs Model Farkı:
# ----------------------
# Model (SQLAlchemy): Database tablosu - verinin nasıl SAKLANACAĞI
# Schema (Pydantic): API şablonu - verinin nasıl GÖNDERİLECEĞİ/ALINACAĞI
#
# Neden İkisi Farklı?
# -------------------
# 1. Güvenlik: password_hash API'de görünmemeli
# 2. Esneklik: API'de farklı alanlar gösterilebilir
# 3. Doğrulama: Email formatı, şifre uzunluğu kontrolü
#
# Örnek:
# - UserCreate: Kayıt olurken gönderilen veri (email, password)
# - UserResponse: API'nin döndürdüğü veri (id, email, role) - şifre YOK!
# ============================================


# Pydantic: Veri doğrulama kütüphanesi
# BaseModel: Tüm şemaların türediği ana sınıf
from pydantic import BaseModel

# EmailStr: Email formatı doğrulama ("x@y.com" formatında mı?)
# Field: Alan ayarları (min uzunluk, max uzunluk, vs.)
from pydantic import EmailStr, Field

# ConfigDict: Pydantic ayarları
from pydantic import ConfigDict

# Python tipleri
from datetime import datetime
from typing import Optional, List


# ==========================================
# BASE SCHEMA (Temel Şema)
# ==========================================

class UserBase(BaseModel):
    """
    User için temel alanlar.
    
    Diğer şemalar bundan türeyecek.
    Ortak alanları burada tanımlıyoruz (DRY prensibi).
    
    DRY = Don't Repeat Yourself (Kendini Tekrarlama)
    """
    
    # Email alanı
    # EmailStr: Otomatik format kontrolü yapar
    # "test" → Hata!
    # "test@test.com" → Geçerli!
    email: EmailStr


# ==========================================
# CREATE SCHEMA (Kayıt için)
# ==========================================

class UserCreate(UserBase):
    """
    Yeni kullanıcı oluşturma şeması.
    
    Kullanıcı KAYIT olurken bu şema kullanılır.
    Frontend'den gelen veri bu formatta olmalı.
    
    Örnek İstek (POST /api/auth/register):
    {
        "email": "test@test.com",
        "password": "güçlü_şifre_123",
        "full_name": "Ali Yılmaz"  // opsiyonel
    }
    """
    
    # Şifre alanı
    # Field(...): Zorunlu alan (... = required)
    # min_length=6: Minimum 6 karakter
    # max_length=100: Maksimum 100 karakter
    password: str = Field(
        ...,  # Zorunlu
        min_length=6,
        max_length=100,
        description="Kullanıcı şifresi (min 6 karakter)"
    )
    
    # Tam ad (opsiyonel)
    # None = varsayılan değer (gönderilmezse None olur)
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Kullanıcının tam adı"
    )


# ==========================================
# UPDATE SCHEMA (Güncelleme için)
# ==========================================

class UserUpdate(BaseModel):
    """
    Kullanıcı güncelleme şeması.
    
    Profil güncellerken kullanılır.
    Tüm alanlar opsiyonel (sadece değişenler gönderilir).
    
    Örnek İstek (PUT /api/users/me):
    {
        "full_name": "Yeni İsim"
    }
    """
    
    # Tüm alanlar Optional (opsiyonel)
    # Sadece gönderilenler güncellenir
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    
    # Şifre değiştirme (opsiyonel)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


# ==========================================
# RESPONSE SCHEMAS (API Yanıtları)
# ==========================================

class UserResponse(UserBase):
    """
    API'nin döndürdüğü kullanıcı verisi.
    
    ÖNEMLİ: password_hash ASLA burada yok!
    Kullanıcı verisi dönerken bu şema kullanılır.
    
    Örnek Yanıt (GET /api/users/me):
    {
        "id": 1,
        "email": "test@test.com",
        "full_name": "Ali Yılmaz",
        "role": "Student",
        "account_status": "Active",
        "created_at": "2025-01-01T10:00:00Z"
    }
    """
    
    # Database'den gelen alanlar
    id: int
    full_name: Optional[str] = None
    role: str
    account_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Pydantic ayarları
    # from_attributes=True: SQLAlchemy modelinden otomatik dönüşüm
    # Eski adı: orm_mode = True
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """
    Kullanıcı listesi yanıtı.
    
    Admin panelinde kullanıcı listesi için.
    
    Örnek Yanıt (GET /api/admin/users):
    {
        "users": [...],
        "total": 150,
        "page": 1,
        "per_page": 20
    }
    """
    
    users: List[UserResponse]
    total: int
    page: int = 1
    per_page: int = 20


# ==========================================
# PROFILE SCHEMA (Profil detayları)
# ==========================================

class UserProfile(UserResponse):
    """
    Detaylı kullanıcı profili.
    
    Kendi profilini görüntülerken ekstra bilgiler.
    UserResponse'u genişletiyor.
    """
    
    # Test istatistikleri (ileride doldurulacak)
    total_tests: int = 0
    completed_tests: int = 0
    average_score: Optional[float] = None
    best_cefr_level: Optional[str] = None


# ==========================================
# ADMIN SCHEMAS (Admin işlemleri)
# ==========================================

class UserStatusUpdate(BaseModel):
    """
    Admin tarafından kullanıcı durumu güncelleme.
    
    Örnek (PUT /api/admin/users/1/status):
    {
        "account_status": "Suspended"
    }
    """
    
    # Sadece belirli değerler kabul edilir
    account_status: str = Field(
        ...,
        description="Hesap durumu: Pending, Active, Suspended, Deleted"
    )


class UserRoleUpdate(BaseModel):
    """
    Admin tarafından kullanıcı rolü güncelleme.
    
    Örnek (PUT /api/admin/users/1/role):
    {
        "role": "Admin"
    }
    """
    
    role: str = Field(
        ...,
        description="Kullanıcı rolü: Student, Admin"
    )