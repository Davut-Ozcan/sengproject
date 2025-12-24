# ============================================
# app/core/database.py - Database Connection
# ============================================
#
# Ne yapıyor?
# - PostgreSQL bağlantısını yönetir
# - SQLAlchemy async engine oluşturur
# - Session factory sağlar
#
# Kullanım:
#   from app.core.database import get_db, Base
# ============================================

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import settings


# ==========================================
# DATABASE ENGINE
# ==========================================

# Async engine oluştur
# pool_pre_ping: Bağlantı kopmuşsa yeniden bağlan
# echo: SQL sorgularını konsola yazdır (DEBUG modunda)
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Session factory
# expire_on_commit=False: Commit sonrası objeleri yeniden yükleme
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# ==========================================
# BASE MODEL
# ==========================================

class Base(DeclarativeBase):
    """
    Tüm modellerin miras alacağı base class.
    
    Kullanım:
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
    """
    pass


# ==========================================
# DEPENDENCY
# ==========================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Veritabanı session dependency.
    
    FastAPI endpoint'lerinde kullanılır:
    
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    'yield' kullanıyoruz çünkü:
    - İstek başında session açılır
    - İstek sonunda otomatik kapanır
    - Hata olursa rollback yapılır
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==========================================
# DATABASE UTILITIES
# ==========================================

async def create_tables():
    """
    Tüm tabloları oluşturur.
    
    Kullanım (main.py'de):
        @app.on_event("startup")
        async def startup():
            await create_tables()
    
    NOT: Production'da Alembic migration kullan!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database: Tablolar oluşturuldu")


async def drop_tables():
    """
    Tüm tabloları siler.
    
    ⚠️ DİKKAT: Tüm veri silinir!
    Sadece development/test için kullan.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("⚠️ Database: Tablolar silindi")