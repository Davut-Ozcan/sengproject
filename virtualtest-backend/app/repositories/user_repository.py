# ============================================
# app/repositories/user_repository.py - User Repository
# ============================================
#
# UML'deki Karşılığı: UserRepository
#
# Ne yapıyor?
# - Kullanıcı veritabanı işlemlerini yönetir
# - Router'lar bu sınıfı kullanır, direkt SQL yazmaz
#
# Metodlar (UML'den):
# - findByEmail(email): User bulur
# - create(user): Yeni kullanıcı oluşturur
# - updateStatus(userID, status): Durumu günceller
# ============================================

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

# Model import (henüz oluşturmadık, sonra ekleyeceğiz)
# from app.models import User


class UserRepository:
    """
    UML: UserRepository
    
    Kullanıcı veritabanı işlemleri.
    """
    
    async def find_by_email(
        self, 
        db: AsyncSession, 
        email: str
    ) -> Optional[any]:  # Optional[User] olacak
        """
        UML: +findByEmail(email: string): User
        
        Email ile kullanıcı bulur.
        
        Kullanım:
            user = await user_repository.find_by_email(db, "test@test.com")
            if user:
                print(user.email)
        
        Input:
            db: Veritabanı session
            email: Aranacak email
        
        Output:
            User objesi veya None
        """
        
        # Model import'u burada yapıyoruz (circular import önlemek için)
        from app.models import User
        
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    
    async def find_by_id(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[any]:
        """
        ID ile kullanıcı bulur.
        
        Kullanım:
            user = await user_repository.find_by_id(db, 5)
        """
        
        from app.models import User
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    
    async def create(
        self, 
        db: AsyncSession,
        email: str,
        hashed_password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "student"
    ) -> Optional[any]:
        """
        UML: +create(user: User): bool
        
        Yeni kullanıcı oluşturur.
        
        Kullanım:
            user = await user_repository.create(
                db, 
                email="test@test.com",
                hashed_password="$2b$12$...",
                first_name="Ali",
                last_name="Yılmaz"
            )
        
        Input:
            db: Veritabanı session
            email: Kullanıcı emaili
            hashed_password: Hashlenmiş şifre
            first_name: Ad (opsiyonel)
            last_name: Soyad (opsiyonel)
            role: "student" veya "admin"
        
        Output:
            Oluşturulan User objesi veya None (email zaten varsa)
        """
        
        from app.models import User
        
        try:
            new_user = User(
                email=email,
                password_hash=hashed_password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                status="active"
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print(f"✅ UserRepository: User created successfully ({email})")
            return new_user
            
        except IntegrityError:
            # Email zaten var
            await db.rollback()
            print(f"⚠️ UserRepository: Email already registered ({email})")
            return None
        except Exception as e:
            await db.rollback()
            print(f"❌ UserRepository Create Error: {e}")
            return None
    
    
    async def update_status(
        self, 
        db: AsyncSession, 
        user_id: int, 
        status: str
    ) -> bool:
        """
        UML: +updateStatus(userID: int, status: string): void
        
        Kullanıcı durumunu günceller.
        
        Kullanım:
            success = await user_repository.update_status(db, 5, "inactive")
        
        Input:
            db: Veritabanı session
            user_id: Kullanıcı ID
            status: Yeni durum ("active", "inactive", "suspended")
        
        Output:
            bool: Başarılı mı?
        """
        
        from app.models import User
        
        try:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(status=status)
            )
            await db.commit()
            
            print(f"✅ UserRepository: Status updated (ID:{user_id} -> {status})")
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"❌ UserRepository Update Error: {e}")
            return False
    
    
    async def get_all_students(
        self, 
        db: AsyncSession,
        limit: int = 100
    ) -> list:
        """
        Tüm öğrencileri listeler.
        
        Kullanım:
            students = await user_repository.get_all_students(db)
        """
        
        from app.models import User
        
        result = await db.execute(
            select(User)
            .where(User.role == "student")
            .limit(limit)
        )
        return result.scalars().all()


# Singleton instance
user_repository = UserRepository()