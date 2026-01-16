# ============================================
# app/routers/auth.py - Authentication Endpoints
# ============================================

from pydantic import BaseModel, EmailStr
import redis
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Annotated, Optional
import random
from datetime import datetime, timedelta


# Mail ve Config
from fastapi_mail import FastMail, MessageSchema, MessageType
from app.core.config import settings

# Projemizin modülleri
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, verify_token
from app.models.user import User


from app.schemas.auth import (
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    MessageResponse,
)
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Kimlik doğrulama hatası"},
        404: {"description": "Bulunamadı"},
    }
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==========================================
# YARDIMCI FONKSİYONLAR (OTP & MAIL)
# ==========================================

def generate_otp() -> str:
    """6 haneli rastgele sayısal kod üretir."""
    return str(random.randint(100000, 999999))

async def send_otp_email(email: str, otp: str):
    """Gmail SMTP üzerinden doğrulama kodu gönderir."""
    html = f"""
    <div style="font-family: Arial; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #2b57ff;">ZenithAI Doğrulama Kodu</h2>
        <p>Hesabınızı doğrulamak için aşağıdaki 6 haneli kodu kullanabilirsiniz:</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1e293b; padding: 10px; background: #f8fafc; text-align: center;">
            {otp}
        </div>
        <p style="color: #64748b; font-size: 0.9rem;">Bu kod 10 dakika süreyle geçerlidir.</p>
    </div>
    """
    message = MessageSchema(
        subject="ZenithAI - Email Doğrulama Kodun",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    # Settings üzerinden mail konfigürasyonunu alıyoruz
    fm = FastMail(settings.get_mail_config()) 
    await fm.send_message(message)

# ==========================================
# DEPENDENCY: Mevcut Kullanıcıyı Al
# ==========================================

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Token'ı doğrular ve aktif kullanıcıyı döner."""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    
    if user.account_status != "Active":
        raise HTTPException(status_code=403, detail=f"Hesap durumu: {user.account_status}")
    
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

# ==========================================
# ENDPOINTS: Register Flow (OTP Destekli)
# ==========================================

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    otp_code: str  # Frontend buraya kodu ekleyip gönderecek

class RegisterResponse(BaseModel):
    message: str
    user_id: int
    email: str
    access_token: str
    token_type: str

# --- ROUTER AYARLARI ---
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- REDIS BAĞLANTISI ---
# Eğer bilgisayarında Redis kurulu değilse, geçici olarak burayı yorum satırı yap
# ve alttaki 'fake_redis' sözlüğünü kullan.
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping() # Bağlantı testi
except redis.ConnectionError:
    print("UYARI: Redis sunucusu bulunamadı! Lütfen Redis'i başlatın.")
    # Redis yoksa kod patlamasın diye (Geliştirme amaçlı)
    class FakeRedis:
        def __init__(self): self.store = {}
        def setex(self, name, time, value): self.store[name] = value
        def get(self, name): return self.store.get(name)
        def delete(self, name): 
            if name in self.store: del self.store[name]
    r = FakeRedis()

# --- YARDIMCI FONKSİYONLAR ---

def generate_otp() -> str:
    """6 haneli rastgele kod üretir."""
    return str(random.randint(100000, 999999))

async def send_otp_email(email: str, otp: str):
    """Kullanıcıya mail atar."""
    html = f"""
    <div style="font-family: Arial; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #2b57ff;">ZenithAI Doğrulama Kodu</h2>
        <p>Hesabınızı doğrulamak için aşağıdaki kodu kullanın:</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1e293b; background: #f8fafc; padding: 10px; text-align: center;">
            {otp}
        </div>
        <p>Kod 10 dakika geçerlidir.</p>
    </div>
    """
    message = MessageSchema(
        subject="ZenithAI Doğrulama Kodu",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(settings.get_mail_config())
    await fm.send_message(message)

# --- ENDPOINTS ---

@router.post("/request-otp", summary="1. Adım: Kod Gönder")
async def request_otp(
    email: str, 
    background_tasks: BackgroundTasks, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    1. Email veritabanında var mı bakar (User tablosu).
    2. Varsa hata verir.
    3. Yoksa OTP üretir, REDIS'e kaydeder (User yok, sadece Cache).
    4. Mail atar.
    """
    # 1. Kullanıcı Kontrolü (SQL)
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")
    
    # 2. OTP Üretimi
    otp_code = generate_otp()
    
    # 3. Redis'e Kaydet (Cache)
    # Anahtar: "otp:user@mail.com" -> Değer: "123456" -> Süre: 600 saniye (10dk)
    try:
        r.setex(name=f"otp:{email}", time=600, value=otp_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Önbellek servisi hatası.")

    # 4. Mail Gönder
    background_tasks.add_task(send_otp_email, email, otp_code)
    
    return {"message": "Doğrulama kodu gönderildi.", "success": True}


@router.post("/verify-otp", summary="2. Adım: Kodu Doğrula (Ara Geçiş)")
async def verify_otp(email: str, code: str):
    """
    Sadece Redis'e bakar. Kod doğru mu ve süresi dolmamış mı?
    """
    # Redis'ten oku
    stored_code = r.get(f"otp:{email}")
    
    if not stored_code:
        # Kod yoksa ya hiç alınmamış ya da süresi dolup silinmiştir.
        raise HTTPException(status_code=400, detail="Kod geçersiz veya süresi dolmuş.")
    
    if stored_code != code:
        raise HTTPException(status_code=400, detail="Hatalı kod girdiniz.")
        
    return {"message": "Kod onaylandı.", "success": True}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    1. Redis'ten kodu son kez kontrol eder.
    2. Her şey tamamsa Kullanıcıyı (User) SQL'e kaydeder.
    3. Redis'teki kodu siler.
    """
    
    # 1. Güvenlik Kontrolü (Redis)
    stored_code = r.get(f"otp:{data.email}")
    
    # Kodun süresi dolmuşsa veya eşleşmiyorsa
    if not stored_code or stored_code != data.otp_code:
        raise HTTPException(status_code=400, detail="Doğrulama başarısız. Kod hatalı veya zaman aşımı.")
    
    # 2. Kullanıcı Oluşturma (SQL İşlemleri)
    hashed_password = hash_password(data.password)
    new_user = User(
        email=data.email,
        password_hash=hashed_password,
        full_name=data.full_name,
        role="Student",
        account_status="Active"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 3. Temizlik: Kullanılan kodu Redis'ten sil
    r.delete(f"otp:{data.email}")

    # Token üret
    access_token = create_access_token(data={"sub": str(new_user.id), "role": new_user.role})
    
    return RegisterResponse(
        message="Hesap başarıyla oluşturuldu.",
        user_id=new_user.id,
        email=new_user.email,
        access_token=access_token,
        token_type="bearer"
    )

# --- MEVCUT ŞEMALARIN ALTINA EKLE ---

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# --- YARDIMCI FONKSİYON (Reset İçin Mail) ---
# --- YARDIMCI FONKSİYON (Reset İçin Mail - KIRMIZI TEMA) ---
async def send_reset_email(email: str, otp: str):
    html = f"""
    <div style="font-family: Arial; padding: 20px; border: 1px solid #e11d48; border-radius: 10px;">
        <h2 style="color: #e11d48;">Şifre Sıfırlama İsteği</h2>
        <p>Hesabınızın şifresini sıfırlamak için aşağıdaki kodu kullanın:</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1e293b; background: #fff1f2; padding: 10px; text-align: center;">
            {otp}
        </div>
        <p>Bu kodu siz istemediyseniz, lütfen dikkate almayın.</p>
    </div>
    """
    message = MessageSchema(
        subject="ZenithAI - Şifre Sıfırlama Kodu", # Başlığı değiştirdik
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(settings.get_mail_config())
    await fm.send_message(message)

# --- ŞİFRE SIFIRLAMA ENDPOINTLERİ ---
# --- ŞİFRE SIFIRLAMA ENDPOINTLERİ (GÜNCELLENMİŞ) ---

@router.post("/forgot-password", summary="Şifremi Unuttum: Kod Gönder")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Kullanıcı Kontrolü
    user = await db.execute(select(User).where(User.email == data.email))
    if not user.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    # 2. Kod Üret
    otp_code = generate_otp()
    
    # DEBUG: Terminale yazdıralım
    print(f"--- DEBUG: Reset Kodu Üretildi: {otp_code} (Mail: {data.email}) ---")

    # 3. Redis'e Kaydet (reset: prefix'i ile)
    try:
        # Kod string olarak kaydediliyor
        r.setex(name=f"reset:{data.email}", time=300, value=otp_code)
        
        # DEBUG: Kaydettikten sonra hemen okuyup kontrol edelim
        kontrol = r.get(f"reset:{data.email}")
        print(f"--- DEBUG: Redis'e Yazıldı mı? Okunan Değer: {kontrol} ---")
        
    except Exception as e:
        print(f"--- DEBUG HATASI: {e} ---")
        raise HTTPException(status_code=500, detail="Redis hatası.")

    # 4. Mail Gönder (Doğru fonksiyonu çağırdığından emin ol)
    background_tasks.add_task(send_reset_email, data.email, otp_code)
    
    return {"message": "Sıfırlama kodu gönderildi.", "success": True}


@router.post("/reset-password", summary="Yeni Şifreyi Kaydet")
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # DEBUG: Gelen veriyi görelim
    print(f"--- DEBUG: Şifre Sıfırlama İsteği ---")
    print(f"--- Gelen Email: {data.email}, Gelen Kod: {data.code} ---")

    # 1. Redis Kontrolü
    stored_code = r.get(f"reset:{data.email}")
    print(f"--- DEBUG: Redis'ten Okunan Kod: {stored_code} ---")
    
    # FakeRedis kullanıyorsan ve sunucu restart olduysa stored_code None gelir.
    if stored_code is None:
        print("--- HATA: Kod bulunamadı (Süre dolmuş veya Server Restart olmuş) ---")
        raise HTTPException(status_code=400, detail="Kodun süresi dolmuş veya sunucu yeniden başlatılmış. Lütfen tekrar kod isteyin.")

    if stored_code != data.code:
        print(f"--- HATA: Kod uyuşmazlığı. Beklenen: {stored_code}, Gelen: {data.code} ---")
        raise HTTPException(status_code=400, detail="Hatalı kod girdiniz.")
    
    # 2. Kullanıcıyı Bul ve Güncelle
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
        
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.commit()
    
    # Temizlik
    r.delete(f"reset:{data.email}")
    
    print("--- BAŞARILI: Şifre güncellendi ---")
    return {"message": "Şifreniz başarıyla güncellendi.", "success": True}
# ==========================================
# ENDPOINT: Login, Me, Logout
# ==========================================

@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LoginResponse:
    """OAuth2 uyumlu giriş endpoint'i."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)

@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: CurrentUser) -> MessageResponse:
    return MessageResponse(message="Çıkış başarılı", success=True)