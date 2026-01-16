# ============================================
# app/core/config.py - Application Settings
# ============================================
#
# Ne yapıyor?
# - .env dosyasından ayarları okur
# - Tüm uygulama bu ayarları kullanır
#
# Kullanım:
#   from app.core.config import settings
#   print(settings.DATABASE_URL)
# ============================================

from pydantic_settings import BaseSettings
from typing import Optional, List
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    """
    Uygulama ayarları.
    
    .env dosyasından otomatik okur.
    Değişken isimleri büyük/küçük harf duyarsız.
    """
    
    # ==========================================
    # DATABASE
    # ==========================================
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password123@localhost:5432/virtuatest"
    
    # ==========================================
    # JWT AUTHENTICATION
    # ==========================================
    SECRET_KEY: str = "change-this-to-a-secure-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ==========================================
    # AI SERVICES
    # ==========================================
    GEMINI_API_KEY: Optional[str] = None

    # ==========================================
    # EMAIL SETTINGS (GMAIL SMTP) - YENİ EKLENDİ
    # ==========================================
    MAIL_USERNAME: str = "zenithai090@gmail.com"
    MAIL_PASSWORD: str = ""  # .env dosyasından uygulama şifresini okuyacak
    MAIL_FROM: str = "zenithai090@gmail.com"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_FROM_NAME: str = "ZenithAI Support"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    
    # ==========================================
    # APPLICATION
    # ==========================================
    DEBUG: bool = True
    PROJECT_NAME: str = "VirtuaTest API"
    API_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"
    
    # ==========================================
    # PYDANTIC CONFIG
    # ==========================================
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    
    def get_allowed_origins_list(self) -> List[str]:
        """
        ALLOWED_ORIGINS string'ini listeye çevirir.
        
        CORS ayarları için kullanılır.
        
        Kullanım:
            origins = settings.get_allowed_origins_list()
            # ["http://localhost:5500", "http://127.0.0.1:5500"]
        """
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    def get_mail_config(self) -> ConnectionConfig:
        """
        fastapi-mail için gerekli ConnectionConfig objesini oluşturur.
        """
        return ConnectionConfig(
            MAIL_USERNAME=self.MAIL_USERNAME,
            MAIL_PASSWORD=self.MAIL_PASSWORD,
            MAIL_FROM=self.MAIL_FROM,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            MAIL_STARTTLS=self.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.MAIL_SSL_TLS,
            USE_CREDENTIALS=self.USE_CREDENTIALS,
            VALIDATE_CERTS=self.VALIDATE_CERTS
        )



# Singleton instance - tüm projede bu kullanılır
settings = Settings()

# Debug modunda ayarları yazdır
if settings.DEBUG:
    print("=" * 50)
    print("⚙️ APPLICATION SETTINGS")
    print("=" * 50)
    print(f"DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"GEMINI_API_KEY: {'✅ Set' if settings.GEMINI_API_KEY else '❌ Missing'}")
    print(f"ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
    print("=" * 50)