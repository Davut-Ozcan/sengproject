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


# Singleton instance - tüm projede bu kullanılır
settings = Settings()

# Debug modunda ayarları yazdır
if settings.DEBUG:
    print("=" * 50)
    print("⚙️  UYGULAMA AYARLARI")
    print("=" * 50)
    print(f"DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"GEMINI_API_KEY: {'✅ Var' if settings.GEMINI_API_KEY else '❌ Yok'}")
    print(f"ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
    print("=" * 50)