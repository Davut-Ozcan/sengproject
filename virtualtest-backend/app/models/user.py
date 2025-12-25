# ============================================
# app/models/user.py - Kullanıcı Modeli
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Excel'deki "User" tablosunu Python sınıfı olarak tanımlıyor.
# SQLAlchemy bu sınıfı okuyup PostgreSQL'de tablo oluşturuyor.
#
# Excel'deki User Tablosu:
# ------------------------
# | Column Name       | Data Type     | Constraints        |
# |-------------------|---------------|-------------------|
# | userID            | INTEGER       | PRIMARY KEY (PK)   |
# | email             | VARCHAR(255)  | Unique             |
# | passwordHash      | VARCHAR(255)  | Not Null           |
# | accountStatus     | VARCHAR(50)   | -                  |
# | verificationToken | VARCHAR(100)  | NULL               |
# | role              | VARCHAR(50)   | Not Null           |
# ============================================


# SQLAlchemy tipleri
# Integer: Tam sayı (1, 2, 3, ...)
# String: Metin ("hello", "test@test.com")
# DateTime: Tarih ve saat
# Boolean: True/False
from sqlalchemy import Integer, String, DateTime, Boolean

# Mapped: Tip belirtmek için (Python 3.9+)
# mapped_column: Sütun tanımlamak için
from sqlalchemy.orm import Mapped, mapped_column, relationship

# func: SQL fonksiyonları (NOW(), COUNT(), vs.)
from sqlalchemy import func

# datetime: Python tarih/saat tipi
from datetime import datetime

# Optional: None olabilir demek
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.test_session import TestSession

# Base: Tüm modellerin türediği ana sınıf
from app.core.database import Base


class User(Base):
    """
    Kullanıcı modeli - users tablosu.
    
    Bu sınıf PostgreSQL'de "users" tablosuna karşılık gelir.
    Her bir User nesnesi tablodaki bir satıra (row) karşılık gelir.
    
    Attributes:
        id: Benzersiz kullanıcı ID'si (otomatik artan)
        email: E-posta adresi (benzersiz)
        password_hash: Hashlenmiş şifre
        account_status: Hesap durumu (Pending/Active/Suspended/Deleted)
        verification_token: E-posta doğrulama token'ı
        role: Kullanıcı rolü (Student/Admin)
        created_at: Hesap oluşturulma tarihi
        updated_at: Son güncelleme tarihi
    
    Örnek Kullanım:
        # Yeni kullanıcı oluştur
        user = User(
            email="test@test.com",
            password_hash="$2b$12$...",
            role="Student"
        )
        
        # Database'e ekle
        session.add(user)
        await session.commit()
    """
    
    # ==========================================
    # TABLO ADI
    # ==========================================
    # __tablename__: PostgreSQL'deki tablo adı
    # Küçük harf ve çoğul kullanmak best practice
    # User sınıfı → users tablosu
    
    __tablename__ = "users"
    
    
    # ==========================================
    # SÜTUNLAR (COLUMNS)
    # ==========================================
    #
    # Mapped[int] = Bu sütun integer tipinde
    # mapped_column(...) = Sütun ayarları
    #
    # primary_key=True → Bu sütun PRIMARY KEY
    # unique=True → Değerler benzersiz olmalı
    # nullable=False → NULL olamaz (zorunlu alan)
    # nullable=True → NULL olabilir (opsiyonel alan)
    # default=... → Varsayılan değer
    # server_default=... → Database seviyesinde varsayılan
    
    # ==========================================
    # İLİŞKİLER (RELATIONSHIPS)
    # ==========================================
    
    # Kullanıcının test oturumları (1-to-many)
    test_sessions: Mapped[List["TestSession"]] = relationship(
        "TestSession",
        back_populates="student",
        lazy="selectin"
    )
    # ---------- id (Primary Key) ----------
    # Excel'deki: userID INTEGER PRIMARY KEY
    #
    # Otomatik artan benzersiz ID
    # Her yeni kullanıcıda otomatik 1 artar: 1, 2, 3, ...
    id: Mapped[int] = mapped_column(
        Integer,           # Veri tipi: tam sayı
        primary_key=True,  # Bu sütun birincil anahtar
        autoincrement=True # Otomatik artan (1, 2, 3, ...)
    )
    
    
    # ---------- email ----------
    # Excel'deki: email VARCHAR(255) Unique
    #
    # Kullanıcının e-posta adresi
    # Benzersiz olmalı (aynı email ile iki hesap açılamaz)
    # index=True: Arama performansını artırır
    email: Mapped[str] = mapped_column(
        String(255),     # Maksimum 255 karakter
        unique=True,     # Benzersiz (aynı email 2 kez olamaz)
        nullable=False,  # Zorunlu alan (NULL olamaz)
        index=True       # Index ekle (arama hızlandırır)
    )
    
    
    # ---------- password_hash ----------
    # Excel'deki: passwordHash VARCHAR(255) Not Null
    #
    # Hashlenmiş şifre
    # DÜZ METİN ŞİFRE ASLA SAKLANMAZ!
    # bcrypt hash örneği: "$2b$12$LQv3c1yqBWVHxkd0..."
    password_hash: Mapped[str] = mapped_column(
        String(255),     # Hash uzunluğu için yeterli
        nullable=False   # Zorunlu alan
    )
    
    
    # ---------- account_status ----------
    # Excel'deki: accountStatus VARCHAR(50)
    # Olası değerler: 'Pending', 'Active', 'Suspended', 'Deleted'
    #
    # Hesap durumu:
    # - Pending: E-posta doğrulanmamış
    # - Active: Aktif hesap
    # - Suspended: Askıya alınmış
    # - Deleted: Silinmiş (soft delete)
    account_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Pending"  # Varsayılan: beklemede
    )
    
    
    # ---------- verification_token ----------
    # Excel'deki: verificationToken VARCHAR(100) NULL
    #
    # E-posta doğrulama için rastgele token
    # Kullanıcı kaydolunca oluşturulur
    # E-posta doğrulanınca NULL yapılır
    #
    # Optional[str] = string veya None olabilir
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True  # Opsiyonel alan (NULL olabilir)
    )
    
    
    # ---------- role ----------
    # Excel'deki: role VARCHAR(50) Not Null
    # Olası değerler: 'Student', 'Admin'
    #
    # Kullanıcı rolü:
    # - Student: Öğrenci (test çözebilir)
    # - Admin: Yönetici (ayarları değiştirebilir)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Student"  # Varsayılan: öğrenci
    )
    
    
    # ---------- full_name (Ekstra) ----------
    # Excel'de yok ama kullanışlı olacak
    #
    # Kullanıcının tam adı (opsiyonel)
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    
    # ---------- created_at ----------
    # Hesabın oluşturulma tarihi
    #
    # server_default=func.now(): Database seviyesinde NOW() çağırır
    # Bu sayede Python'dan tarih göndermesek bile DB otomatik ekler
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # Timezone bilgisi ile
        server_default=func.now(),  # Database'de NOW() kullan
        nullable=False
    )
    
    
    # ---------- updated_at ----------
    # Son güncelleme tarihi
    #
    # onupdate=func.now(): Her UPDATE'te otomatik güncellenir
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # UPDATE'te otomatik güncelle
        nullable=True
    )
    
    
    # ==========================================
    # METODLAR
    # ==========================================
    
    def __repr__(self) -> str:
        """
        Nesnenin string temsili.
        
        Debug yaparken kullanışlı:
        print(user)  # <User(id=1, email='test@test.com', role='Student')>
        """
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    
    def is_active(self) -> bool:
        """
        Hesap aktif mi kontrol eder.
        
        Returns:
            bool: Hesap aktifse True
        """
        return self.account_status == "Active"
    
    
    def is_admin(self) -> bool:
        """
        Kullanıcı admin mi kontrol eder.
        
        Returns:
            bool: Admin ise True
        """
        return self.role == "Admin"
    
    
    def is_student(self) -> bool:
        """
        Kullanıcı öğrenci mi kontrol eder.
        
        Returns:
            bool: Öğrenci ise True
        """
        return self.role == "Student"