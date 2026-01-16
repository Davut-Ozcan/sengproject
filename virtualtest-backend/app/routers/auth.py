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

responses={
    401: {"description": "Authentication error"},
    404: {"description": "Not found"},
}

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication error"},
        404: {"description": "Not found"},
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
    <!DOCTYPE html>
    <html>
    <head>
        <style>@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');</style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Plus Jakarta Sans', Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="{logo_url}" alt="ZenithAI" style="width: 50px; height: 50px; border-radius: 12px; vertical-align: middle;">
                <span style="font-size: 22px; font-weight: 800; color: #1e293b; margin-left: 10px; vertical-align: middle;">Zenith<span style="color: #2b57ff;">AI</span></span>
            </div>
            
            <div style="background: #ffffff; border-radius: 24px; padding: 40px; box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; text-align: center;">
                <h2 style="color: #1e293b; font-size: 24px; font-weight: 800; margin-bottom: 15px; margin-top: 0;">Verify Your Account</h2>
                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                    Welcome to ZenithAI! To complete your registration and access the assessment modules, please use the code below.
                </p>
                
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #bae6fd; border-radius: 16px; padding: 25px; margin-bottom: 30px; letter-spacing: 8px;">
                    <span style="font-family: monospace; font-size: 32px; font-weight: 800; color: #0284c7; display: block;">{otp}</span>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0;">
                    This code will expire in 10 minutes.<br>If you didn't request this, you can safely ignore this email.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #cbd5e1; font-size: 12px; font-weight: 500;">
                &copy; 2026 ZenithAI Assessment System
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="ZenithAI - Your Email Verification Code",
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")
    
    if user.account_status != "Active":
        raise HTTPException(status_code=403, detail=f"Account status: {user.account_status}")
    
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
    print("WARNING: Redis server not found!")
    # Redis yoksa kod patlamasın diye (Geliştirme amaçlı)
    class FakeRedis:
        def __init__(self): self.store = {}
        def setex(self, name, time, value): self.store[name] = value
        def get(self, name): return self.store.get(name)
        def delete(self, name): 
            if name in self.store: del self.store[name]
    r = FakeRedis()

# --- YARDIMCI FONKSİYONLAR ---
logo_url = "http://127.0.0.1:8000/static/logo.jpeg"

def generate_otp() -> str:
    """6 haneli rastgele kod üretir."""
    return str(random.randint(100000, 999999))

async def send_otp_email(email: str, otp: str):
    """Kayıt Doğrulama Maili (MAVI TEMA)"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');</style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Plus Jakarta Sans', Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="{logo_url}" alt="ZenithAI" style="width: 50px; height: 50px; border-radius: 12px; vertical-align: middle;">
                <span style="font-size: 22px; font-weight: 800; color: #1e293b; margin-left: 10px; vertical-align: middle;">Zenith<span style="color: #2b57ff;">AI</span></span>
            </div>
            
            <div style="background: #ffffff; border-radius: 24px; padding: 40px; box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; text-align: center;">
                <h2 style="color: #1e293b; font-size: 24px; font-weight: 800; margin-bottom: 15px; margin-top: 0;">Verify Your Account</h2>
                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                    Welcome to ZenithAI! To complete your registration and access the assessment modules, please use the code below.
                </p>
                
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #bae6fd; border-radius: 16px; padding: 25px; margin-bottom: 30px; letter-spacing: 8px;">
                    <span style="font-family: monospace; font-size: 32px; font-weight: 800; color: #0284c7; display: block;">{otp}</span>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0;">
                    This code will expire in 10 minutes.<br>If you didn't request this, you can safely ignore this email.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #cbd5e1; font-size: 12px; font-weight: 500;">
                &copy; 2026 ZenithAI Assessment System
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="ZenithAI Verification Code",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(settings.get_mail_config())
    await fm.send_message(message)

# --- ENDPOINTS ---

@router.post("/request-otp", summary="Step 1: Send Code")
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
        raise HTTPException(status_code=400, detail="Email address is already registered.")
    
    # 2. OTP Üretimi
    otp_code = generate_otp()
    
    # 3. Redis'e Kaydet (Cache)
    # Anahtar: "otp:user@mail.com" -> Değer: "123456" -> Süre: 600 saniye (10dk)
    try:
        r.setex(name=f"otp:{email}", time=600, value=otp_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Cache service error.")

    # 4. Mail Gönder
    background_tasks.add_task(send_otp_email, email, otp_code)
    
    return {"message": "Verification code sent.", "success": True}


@router.post("/verify-otp", summary="Step 2: Verify Code (Intermediate Step)")
async def verify_otp(email: str, code: str):
    """
    Sadece Redis'e bakar. Kod doğru mu ve süresi dolmamış mı?
    """
    # Redis'ten oku
    stored_code = r.get(f"otp:{email}")
    
    if not stored_code:
        # Kod yoksa ya hiç alınmamış ya da süresi dolup silinmiştir.
        raise HTTPException(status_code=400, detail="Code is invalid or has expired.")
    
    if stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid code entered.")
        
    return {"message": "Code verified.", "success": True}


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
        raise HTTPException(status_code=400, detail="Verification failed. Invalid code or timeout.")
    
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
        message="Account created successfully.",
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
    """Şifre Sıfırlama Maili (KIRMIZI TEMA)"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');</style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Plus Jakarta Sans', Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="{logo_url}" alt="ZenithAI" style="width: 50px; height: 50px; border-radius: 12px; vertical-align: middle;">
                <span style="font-size: 22px; font-weight: 800; color: #1e293b; margin-left: 10px; vertical-align: middle;">Zenith<span style="color: #2b57ff;">AI</span></span>
            </div>
            
            <div style="background: #ffffff; border-radius: 24px; padding: 40px; box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; text-align: center;">
                <div style="width: 50px; height: 50px; background: #fff1f2; color: #e11d48; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 20px;">
                    🔒
                </div>
                
                <h2 style="color: #1e293b; font-size: 24px; font-weight: 800; margin-bottom: 15px; margin-top: 0;">Password Reset</h2>
                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                    We received a request to reset your password. Enter the following code to proceed securely.
                </p>
                
                <div style="background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%); border: 1px solid #fecdd3; border-radius: 16px; padding: 25px; margin-bottom: 30px; letter-spacing: 8px;">
                    <span style="font-family: monospace; font-size: 32px; font-weight: 800; color: #e11d48; display: block;">{otp}</span>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0;">
                    If you didn't ask for this, please ignore this email.<br>Your account is safe.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #cbd5e1; font-size: 12px; font-weight: 500;">
                &copy; 2026 ZenithAI Assessment System
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="ZenithAI - Password Reset Code",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(settings.get_mail_config())
    await fm.send_message(message)

# --- ŞİFRE SIFIRLAMA ENDPOINTLERİ ---
# --- ŞİFRE SIFIRLAMA ENDPOINTLERİ (GÜNCELLENMİŞ) ---

@router.post("/forgot-password", summary="Forgot Password: Send Code")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Kullanıcı Kontrolü
    user = await db.execute(select(User).where(User.email == data.email))
    if not user.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found.")

    # 2. Kod Üret
    otp_code = generate_otp()
    
    # DEBUG: Terminale yazdıralım
    print(f"--- DEBUG: Reset Code Generated: {otp_code} (Mail: {data.email}) ---")

    # 3. Redis'e Kaydet (reset: prefix'i ile)
    try:
        # Kod string olarak kaydediliyor
        r.setex(name=f"reset:{data.email}", time=300, value=otp_code)
        
        # DEBUG: Kaydettikten sonra hemen okuyup kontrol edelim
        kontrol = r.get(f"reset:{data.email}")
        print(f"--- DEBUG: Written to Redis? Read Value: {kontrol} ---")
        
    except Exception as e:
        print(f"--- DEBUG ERROR: {e} ---")
        raise HTTPException(status_code=500, detail="Redis error.")

    # 4. Mail Gönder (Doğru fonksiyonu çağırdığından emin ol)
    background_tasks.add_task(send_reset_email, data.email, otp_code)
    
    return {"message": "Reset code sent", "success": True}


@router.post("/reset-password", summary="Save New Password")
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # DEBUG: Gelen veriyi görelim
    print(f"--- DEBUG: Password Reset Request ---")
    print(f"--- Received Email: {data.email}, Received Code: {data.code} ---")

    # 1. Redis Kontrolü
    stored_code = r.get(f"reset:{data.email}")
    print(f"--- DEBUG: Read Code from Redis: {stored_code} ---")
    
    # FakeRedis kullanıyorsan ve sunucu restart olduysa stored_code None gelir.
    if stored_code is None:
        print("--- ERROR: Code not found (Expired or Server Restarted) ---")
        raise HTTPException(status_code=400, detail="Code expired or server restarted. Please request a new code.")

    if stored_code != data.code:
        print(f"--- ERROR: Code mismatch. Expected:: {stored_code}, Got: {data.code} ---")
        raise HTTPException(status_code=400, detail="Invalid code entered.")
    
    # 2. Kullanıcıyı Bul ve Güncelle
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.commit()
    
    # Temizlik
    r.delete(f"reset:{data.email}")
    
    print("--- SUCCESS: Password updated ---")
    return {"message": "Password updated successfully", "success": True}
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
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
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
    return MessageResponse(message="Logout successful.", success=True)