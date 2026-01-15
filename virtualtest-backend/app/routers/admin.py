# =================================================================
# app/routers/admin.py - Admin Dashboard & System Management
# =================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Annotated, Optional # Optional eklendi
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models import User
from app.models.admin_settings import AdminSettings 
from app.routers.auth import get_current_user, CurrentUser

# --- Schemas ---

class AdminStatsResponse(BaseModel):
    total_users: int
    total_admins: int
    active_users: int
    ai_status: str

class ConfigUpdateSchema(BaseModel):
    reading_time_limit: int
    listening_time_limit: int
    writing_time_limit: int
    speaking_time_limit: int
    difficulty: str 

class AdminUserListResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    account_status: str

class UserCreateSchema(BaseModel):
    """FR8: Yeni kullanıcı ekleme şeması"""
    email: EmailStr
    password: str
    full_name: str
    role: str = "Student"

class UserUpdateSchema(BaseModel):
    """Admin'in kullanıcıyı düzenleme şeması"""
    full_name: Optional[str] = None
    role: Optional[str] = None
    account_status: Optional[str] = None

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
)

# --- Authorization ---

def check_admin_privileges(user: User):
    if user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )

# --- Endpoints ---

# 1. STATISTICS
@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    check_admin_privileges(current_user)
    total_users = await db.scalar(select(func.count(User.id)))
    total_admins = await db.scalar(select(func.count(User.id)).where(User.role == "Admin"))
    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "active_users": total_users,
        "ai_status": "Active"
    }

# 2. LIST USERS (FR8)
@router.get("/users", response_model=List[AdminUserListResponse])
async def get_all_users(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    check_admin_privileges(current_user)
    result = await db.execute(select(User).order_by(User.id.desc()))
    return result.scalars().all()

# 3. CREATE USER (FR8 - Add User Butonu İçin)
@router.post("/users", status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: UserCreateSchema,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    check_admin_privileges(current_user)
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        account_status="Active"
    )
    new_user.set_password(data.password) 
    db.add(new_user)
    await db.commit()
    return {"message": "User created successfully"}

# 4. UPDATE USER (Ad, Rol ve Durum Düzenleme)
@router.put("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    data: UserUpdateSchema,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    check_admin_privileges(current_user)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.full_name is not None: user.full_name = data.full_name
    if data.role is not None: user.role = data.role
    if data.account_status is not None: user.account_status = data.account_status
    
    await db.commit()
    return {"message": "User updated successfully"}

# 5. CONFIG FETCH (FR48, FR50 - 500 Hatasını Önleyen Versiyon)
@router.get("/config")
async def get_test_config(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    check_admin_privileges(current_user)
    result = await db.execute(select(AdminSettings).where(AdminSettings.is_active == True))
    config = result.scalar_one_or_none()
    
    if not config:
        # Eğer tabloda ayar yoksa çökme, varsayılanları dön
        return {
            "reading_time_limit": 1200, 
            "listening_time_limit": 840,
            "writing_time_limit": 2400,
            "speaking_time_limit": 180,
            "ai_generation_settings": {"difficulty": "B1"}
        }
    return config

# 6. CONFIG UPDATE
@router.put("/config")
async def update_test_config(data: ConfigUpdateSchema, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    check_admin_privileges(current_user)
    result = await db.execute(select(AdminSettings).where(AdminSettings.is_active == True))
    config = result.scalar_one_or_none()
    
    if config:
        config.reading_time_limit = data.reading_time_limit
        config.listening_time_limit = data.listening_time_limit
        config.writing_time_limit = data.writing_time_limit
        config.speaking_time_limit = data.speaking_time_limit
        config.ai_generation_settings = {"difficulty": data.difficulty}
        await db.commit()
        return {"message": "System parameters updated successfully"}
    
    raise HTTPException(status_code=404, detail="Settings record not found. Run SQL first.")