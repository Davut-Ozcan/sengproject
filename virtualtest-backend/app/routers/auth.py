# ============================================
# app/routers/auth.py - Authentication Endpoints
# ============================================

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Annotated, Optional
import random
from datetime import datetime, timedelta
from app.models.verification import VerificationCode

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

# Gerekli importları eklemeyi unutma:
# from app.models.verification import VerificationCode

@router.post("/request-otp", summary="1. Adım: Kod Gönder")
async def request_otp(
    email: str, 
    background_tasks: BackgroundTasks, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Email kontrolü yapar, kodu DB'ye kaydeder ve mail gönderir."""
    # 1. Kullanıcı zaten var mı kontrolü
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")
    
    # 2. OTP Üretimi
    otp_code = generate_otp()
    
    # 3. Kodu Veritabanına Kaydet (Hafıza)
    # db.merge: Varsa günceller, yoksa yeni kayıt açar (Upsert)
    db_otp = VerificationCode(email=email, code=otp_code)
    await db.merge(db_otp) 
    await db.commit()

    # 4. Maili arka planda gönder
    background_tasks.add_task(send_otp_email, email, otp_code)
    return {"message": "Doğrulama kodu gönderildi.", "success": True}


@router.post("/verify-otp", summary="2. Adım: Kodu Doğrula (Ara Geçiş)")
async def verify_otp(
    email: str, 
    code: str, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Frontend'in 3. adıma geçmeden önce kodu sorguladığı yer."""
    result = await db.execute(select(VerificationCode).where(
        VerificationCode.email == email, 
        VerificationCode.code == code
    ))
    db_otp = result.scalar_one_or_none()
    
    if not db_otp:
        raise HTTPException(status_code=400, detail="Geçersiz kod.")
    
    if db_otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Kodun süresi dolmuş.")
        
    return {"message": "Kod onaylandı.", "success": True}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest, 
    otp_code: str, 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> RegisterResponse:
    """OTP doğrulaması yapar ve hesabı oluşturur."""
    
    # 1. Son Güvenlik Kontrolü: Kod hala geçerli mi?
    result = await db.execute(select(VerificationCode).where(
        VerificationCode.email == data.email, 
        VerificationCode.code == otp_code
    ))
    db_otp = result.scalar_one_or_none()
    
    if not db_otp or db_otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Doğrulama başarısız. Kod hatalı veya süresi dolmuş.")
    
    # 2. Kullanıcı Oluşturma
    hashed_password = hash_password(data.password)
    new_user = User(
        email=data.email,
        password_hash=hashed_password,
        full_name=data.full_name,
        role="Student",
        account_status="Active"
    )
    
    db.add(new_user)
    
    try:
        # 3. İşlemleri tamamla ve kullanılan kodu sil
        await db.delete(db_otp) 
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Kayıt sırasında bir hata oluştu.")

    access_token = create_access_token(data={"sub": str(new_user.id), "role": new_user.role})
    
    return RegisterResponse(
        message="Hesap doğrulandı ve oluşturuldu",
        user_id=new_user.id,
        email=new_user.email,
        access_token=access_token,
        token_type="bearer"
    )

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