from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Annotated
from pydantic import BaseModel

from app.core.database import get_db
from app.models import User
from app.routers.auth import get_current_user, CurrentUser


# --- Response Modelleri ---
class AdminStatsResponse(BaseModel):
    total_users: int
    total_admins: int
    active_users: int
    ai_status: str


class AdminUserListResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    account_status: str


router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    responses={404: {"description": "Not found"}},
)


# --- Yetki Kontrolü ---
def check_admin_privileges(user: User):
    if user.role != "admin":  # Rol kontrolü (büyük/küçük harfe dikkat et, veritabanında nasılsa öyle olmalı)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için Admin yetkisi gerekiyor."
        )


# 1. İstatistikleri Getir
@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
        current_user: CurrentUser,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    check_admin_privileges(current_user)

    # Async sorgular
    total_users = await db.scalar(select(func.count(User.id)))
    total_admins = await db.scalar(select(func.count(User.id)).where(User.role == "admin"))

    # Şimdilik aktif kullanıcı mantığı yoksa toplamı dönelim
    active_users = total_users

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "active_users": active_users,
        "ai_status": "Active"
    }


# 2. Tüm Kullanıcıları Listele
@router.get("/users", response_model=List[AdminUserListResponse])
async def get_all_users(
        current_user: CurrentUser,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    check_admin_privileges(current_user)

    # Async sorgu
    result = await db.execute(select(User).order_by(User.id.desc()).limit(100))
    users = result.scalars().all()

    # Listeyi dön
    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "account_status": "Active"  # DB'de kolon yoksa varsayılan
        })
    return user_list