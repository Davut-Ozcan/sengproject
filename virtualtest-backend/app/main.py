# ============================================
# app/main.py - Ana Uygulama Dosyası
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# 1. FastAPI uygulamasını oluşturur
# 2. Tüm router'ları (auth, test) bağlar
# 3. CORS ayarlarını yapar
# 4. Database tablolarını oluşturur
# 5. Uygulama başlangıç/bitiş olaylarını yönetir
#
# Çalıştırmak için:
# -----------------
# uvicorn app.main:app --reload --port 8000
#
# Swagger UI:
# -----------
# http://localhost:8000/docs
# ============================================


# FastAPI imports
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Contextlib: Async context manager
from contextlib import asynccontextmanager

# Projemizin modülleri
from app.core.config import settings
from app.core.database import create_tables, engine

# Router'lar
from app.routers import auth_router, test_router
from app.routers import auth, test, admin

# ==========================================
# LIFESPAN (Uygulama Yaşam Döngüsü)
# ==========================================
#
# Lifespan Nedir?
# ---------------
# Uygulama başlarken ve kapanırken çalışacak kodları tanımlar.
# - Başlangıç: Database bağlantısı, tablolar oluşturma
# - Kapanış: Bağlantıları temizleme
#
# @asynccontextmanager: Async context manager oluşturur
# yield öncesi: Başlangıçta çalışır
# yield sonrası: Kapanışta çalışır

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yönetimi.
    
    Başlangıç işlemleri:
    - Database tablolarını oluştur
    - Bağlantıları kontrol et
    
    Kapanış işlemleri:
    - Engine'i kapat
    - Kaynakları temizle
    """
    # ===== BAŞLANGIÇ =====
    print("=" * 50)
    print("🚀 Starting VirtuaTest API...")
    print("=" * 50)
    
    # Database tablolarını oluştur
    try:
        await create_tables()
        print("✅ Database tables are ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("⚠️  Check if PostgreSQL is running!")
    
    print(f"📍 API Address: http://localhost:8000")
    print(f"📚 Swagger UI: http://localhost:8000/docs")
    print(f"📋 ReDoc: http://localhost:8000/redoc")
    print("=" * 50)
    
    # Uygulama çalışsın
    yield
    
    # ===== KAPANIŞ =====
    print("=" * 50)
    print("👋 Shutting down VirtuaTest API...")
    
    # Engine'i kapat
    await engine.dispose()
    
    print("✅ Connections cleaned up")
    print("=" * 50)


# ==========================================
# FASTAPI UYGULAMASI
# ==========================================

app = FastAPI(
    # Uygulama bilgileri (Swagger'da görünür)
    title=settings.PROJECT_NAME,
    description="""
    ## VirtuaTest - AI Powered English Level Assessment API
    
    Bu API, İngilizce seviye değerlendirmesi yapar.
    
    ### Modüller:
    - 📖 **Reading**: Okuma anlama
    - 🎧 **Listening**: Dinleme anlama
    - 🎤 **Speaking**: Konuşma (AI değerlendirmeli)
    - ✍️ **Writing**: Yazma (AI değerlendirmeli)
    
    ### CEFR Seviyeleri:
    - A1: Başlangıç
    - A2: Temel
    - B1: Orta-alt
    - B2: Orta-üst
    - C1: İleri
    - C2: Ustalaşmış
    
    ### Kimlik Doğrulama:
    JWT Bearer token kullanılır.
    Login yapıp aldığınız token'ı header'a ekleyin:
    `Authorization: Bearer <token>`
    """,
    version=settings.API_VERSION,
    
    # Swagger UI ayarları
    docs_url="/docs",           # Swagger UI adresi
    redoc_url="/redoc",         # ReDoc adresi
    openapi_url="/openapi.json", # OpenAPI şeması
    
    # Lifespan (başlangıç/kapanış)
    lifespan=lifespan,
    
    # Debug modu
    debug=settings.DEBUG,
)


# ==========================================
# CORS AYARLARI
# ==========================================
#
# CORS Nedir?
# -----------
# Cross-Origin Resource Sharing
# Farklı domain'lerden (frontend) API'ye erişim izni.
#
# Frontend localhost:5500'de, Backend localhost:8000'de
# CORS olmadan frontend backend'e istek atamaz!

app.add_middleware(
    CORSMiddleware,
    
    # İzin verilen origin'ler (frontend adresleri)
    allow_origins=settings.get_allowed_origins_list(),
    #allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],

    # Cookie göndermeye izin ver
    allow_credentials=True,
    
    # Tüm HTTP metodlarına izin ver (GET, POST, PUT, DELETE, vs.)
    allow_methods=["*"],
    
    # Tüm header'lara izin ver
    allow_headers=["*"],
)

# ==========================================
# STATIC DOSYALAR (Ses dosyaları için)
# ==========================================

from fastapi.staticfiles import StaticFiles
import os

# Static klasörünü oluştur
os.makedirs("static/audio", exist_ok=True)

# /static URL'i altında static klasörünü sun
app.mount("/static", StaticFiles(directory="static"), name="static")
# ==========================================
# HATA YÖNETİMİ (Exception Handlers)
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Validation hataları için özel handler.
    
    Pydantic validation hatalarını daha okunabilir formatta döndürür.
    """
    errors = []

    all_errors = exc.errors()

    specific_message = all_errors[0].get("msg") if all_errors else "Invalid data"

    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": specific_message,
            "errors": errors
        }
    )


# ==========================================
# ROUTER'LARI BAĞLA
# ==========================================
#
# include_router: Router'ı ana uygulamaya ekler
# prefix="/api": Tüm URL'ler /api ile başlar
#
# Sonuç:
# - /api/auth/login
# - /api/auth/register
# - /api/test/start
# - vs.

app.include_router(
    auth_router,
    prefix="/api"
)

app.include_router(
    test_router,
    prefix="/api"
)
# ✅ YENİ HALİ (Doğru)
app.include_router(
    admin.router,
    prefix="/api"  # <-- İşte bu eksikti!
)

# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get(
    "/",
    tags=["Root"],
    summary="API Statu",
    description="Checks if the API is running."
)
async def root():
    """
    API sağlık kontrolü.
    
    Returns:
        dict: API durumu ve versiyon bilgisi
    """
    return {
        "status": "online",
        "message": "Welcome to VirtuaTest API!",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "test": "/api/test"
        }
    }


@app.get(
    "/health",
    tags=["Root"],
    summary="Health Check",
    description="Checks API and database status."
)
async def health_check():
    """
    Detaylı sağlık kontrolü.
    
    Database bağlantısını da kontrol eder.
    """
    # Database kontrolü
    db_status = "unknown"
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "api": "online",
        "database": db_status,
        "version": settings.API_VERSION
    }


# ==========================================
# ÇALIŞTIRMA (Development için)
# ==========================================
#
# Bu kısım sadece doğrudan çalıştırıldığında çalışır:
# python app/main.py
#
# Production'da uvicorn kullanılır:
# uvicorn app.main:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",     # Uygulama yolu
        host="0.0.0.0",     # Tüm IP'lerden erişim
        port=8000,          # Port
        reload=True,        # Kod değişince yeniden başlat
        log_level="info"    # Log seviyesi
    )