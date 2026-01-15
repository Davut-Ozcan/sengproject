# ============================================
# app/routers/auth.py - Authentication Endpoints
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Login ve Register API endpoint'lerini tanımlar.
# Frontend bu URL'lere istek atar.
#
# Endpoint'ler:
# -------------
# POST /api/auth/register  → Yeni hesap oluştur
# POST /api/auth/login     → Giriş yap, token al
# GET  /api/auth/me        → Mevcut kullanıcı bilgisi
# POST /api/auth/logout    → Çıkış (opsiyonel)
# ============================================


# FastAPI imports
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# SQLAlchemy imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Typing
from typing import Annotated

# Projemizin modülleri
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    MessageResponse,
)
from app.schemas.user import UserResponse


# ==========================================
# ROUTER OLUŞTURMA
# ==========================================
#
# APIRouter: Endpoint'leri gruplamak için kullanılır.
# prefix="/auth": Tüm URL'ler /auth ile başlar
# tags=["Auth"]: Swagger UI'da gruplama için

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Kimlik doğrulama hatası"},
        404: {"description": "Bulunamadı"},
    }
)


# ==========================================
# DEPENDENCY: Mevcut Kullanıcıyı Al
# ==========================================
#
# Bu fonksiyon token'dan kullanıcıyı çıkarır.
# Korumalı endpoint'lerde kullanılır.

from fastapi.security import OAuth2PasswordBearer

# OAuth2PasswordBearer: Token'ı header'dan alır
# tokenUrl: Login endpoint'i (Swagger için)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Token'dan mevcut kullanıcıyı çıkarır.
    
    Bu bir "dependency" fonksiyonudur.
    Korumalı endpoint'lerde şöyle kullanılır:
    
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    
    Args:
        token: JWT token (header'dan otomatik alınır)
        db: Database session
    
    Returns:
        User: Mevcut kullanıcı
    
    Raises:
        HTTPException: Token geçersizse 401 hatası
    """
    from app.core.security import verify_token
    
    # Token'ı doğrula
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token'dan user_id al
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token'da kullanıcı bilgisi yok",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Database'den kullanıcıyı bul
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Hesap aktif mi kontrol et
    if user.account_status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Hesap durumu: {user.account_status}. Giriş yapılamaz.",
        )
    
    return user


# Aktif kullanıcı için kısa yol (type alias)
CurrentUser = Annotated[User, Depends(get_current_user)]


# ==========================================
# ENDPOINT: Register (Kayıt)
# ==========================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı kaydı",
    description="Email ve şifre ile yeni hesap oluşturur."
)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> RegisterResponse:
    """
    Yeni kullanıcı kaydı.
    
    İşlem adımları:
    1. Email daha önce kullanılmış mı kontrol et
    2. Şifreyi hashle
    3. Kullanıcıyı database'e kaydet
    4. JWT token oluştur ve döndür
    
    Args:
        data: RegisterRequest (email, password, full_name)
        db: Database session
    
    Returns:
        RegisterResponse: user_id, email, access_token
    
    Raises:
        HTTPException 400: Email zaten kayıtlı
    """
    
    # 1. Email kontrolü
    existing_user = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı"
        )
    
    # 2. Şifre hashle
    hashed_password = hash_password(data.password)
    
    # 3. Yeni kullanıcı oluştur
    new_user = User(
        email=data.email,
        password_hash=hashed_password,
        full_name=data.full_name,
        role="Student",  # Varsayılan rol
        account_status="Active"  # Direkt aktif (email doğrulama sonra eklenebilir)
    )
    
    # Database'e ekle
    db.add(new_user)
    
    try:
        await db.commit()
        await db.refresh(new_user)  # ID'yi al
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kayıt sırasında hata oluştu"
        )
    
    # 4. Token oluştur
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return RegisterResponse(
        message="Kayıt başarılı",
        user_id=new_user.id,
        email=new_user.email,
        access_token=access_token,
        token_type="bearer"
    )


# ==========================================
# ENDPOINT: Login (Giriş)
# ==========================================

from fastapi.security import OAuth2PasswordRequestForm

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Kullanıcı girişi",
    description="Email ve şifre ile giriş yapar, JWT token döndürür."
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LoginResponse:
    """
    Kullanıcı girişi (OAuth2 uyumlu).
    """
    
    # form_data.username = email olarak kullanılıyor
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Kullanıcı yoksa veya şifre yanlışsa
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz email veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Hesap durumu kontrolü
    if user.account_status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Hesap durumu: {user.account_status}"
        )
    
    # Token oluştur
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )

# ==========================================
# ENDPOINT: Me (Mevcut Kullanıcı)
# ==========================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Mevcut kullanıcı bilgisi",
    description="Token'a göre giriş yapmış kullanıcının bilgilerini döndürür."
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """
    Mevcut kullanıcının bilgilerini döndürür.
    
    Bu endpoint korumalıdır.
    Header'da geçerli bir token olmalı:
    Authorization: Bearer <token>
    
    Args:
        current_user: Token'dan çıkarılan kullanıcı (otomatik)
    
    Returns:
        UserResponse: Kullanıcı bilgileri
    """
    return UserResponse.model_validate(current_user)


# ==========================================
# ENDPOINT: Logout (Çıkış) - Opsiyonel
# ==========================================

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Çıkış",
    description="Kullanıcı oturumunu sonlandırır."
)
async def logout(current_user: CurrentUser) -> MessageResponse:
    """
    Kullanıcı çıkışı.
    
    JWT stateless olduğu için sunucu tarafında
    yapılacak bir şey yok. Frontend token'ı siler.
    
    İleride token blacklist eklenebilir.
    
    Returns:
        MessageResponse: Başarı mesajı
    """
    # Not: JWT stateless, sunucuda session tutmuyoruz
    # Frontend token'ı localStorage'dan silmeli
    
    return MessageResponse(
        message="Çıkış başarılı",
        success=True
    )


# ==========================================
# ENDPOINT: Şifre Değiştirme
# ==========================================

from fastapi.security import OAuth2PasswordRequestForm

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Kullanıcı girişi",
    description="Email ve şifre ile giriş yapar, JWT token döndürür."
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LoginResponse:
    """
    Kullanıcı girişi.
    """
    
    # form_data.username = email olarak kullanılıyor
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz email veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.account_status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Hesap durumu: {user.account_status}"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )

# --- EKSİK OLAN PARÇA ---
# admin.py dosyasının çalışması için bu gereklidir.

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    if current_user.account_status != "Active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user