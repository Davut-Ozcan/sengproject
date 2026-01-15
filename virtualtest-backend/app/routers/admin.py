from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_active_user
from app.models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

# Admin Yetki Kontrolü
def get_current_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have admin privileges"
        )
    return current_user

# 1. İstatistikleri Getir
@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    total_users = db.query(User).count()
    total_admins = db.query(User).filter(User.role == "Admin").count()
    active_users = db.query(User).filter(User.account_status == "Active").count()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "active_users": active_users,
        "tests_run": 0, 
        "ai_status": "Active"
    }

# 2. Tüm Kullanıcıları Listele
@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "account_status": u.account_status
        }
        for u in users
    ]