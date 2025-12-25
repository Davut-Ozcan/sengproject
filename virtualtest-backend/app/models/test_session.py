# ============================================
# app/models/test_session.py - Test Oturumu
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Excel'deki "StudentTestSession" tablosunu tanımlıyor.
# Öğrencinin bir test oturumunu temsil eder.
#
# Excel'deki StudentTestSession Tablosu:
# --------------------------------------
# | Column Name      | Data Type   | Constraints  | Example            |
# |------------------|-------------|--------------|---------------------|
# | sessionID        | INTEGER     | PRIMARY KEY  | S-001               |
# | studentID        | INTEGER     | Not Null     | 101                 |
# | startDate        | DATETIME    | Not Null     | 2025-12-07 15:00    |
# | completionDate   | DATETIME    | NULL         | 2025-12-08 17:30    |
# | overallCEFRLevel | VARCHAR(10) | NULL         | B2                  |
#
# Test Oturumu Akışı:
# -------------------
# 1. Öğrenci teste başlar → yeni session oluşur
# 2. 4 modülü tamamlar (Reading, Listening, Speaking, Writing)
# 3. AI puanları hesaplar → CEFR seviyesi belirlenir
# 4. Session tamamlanır
# ============================================


# SQLAlchemy tipleri
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean

# ORM araçları
from sqlalchemy.orm import Mapped, mapped_column, relationship

# SQL fonksiyonları
from sqlalchemy import func
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean
# Python tipleri
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

# Base class
from app.core.database import Base

# TYPE_CHECKING: Sadece tip kontrolü sırasında import et
# Circular import (döngüsel import) sorununu önler
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.module_score import ModuleScore


class TestSession(Base):
    """
    Test oturumu modeli - test_sessions tablosu.
    
    Her öğrencinin her test denemesi bir TestSession'dır.
    Bir öğrencinin birden fazla session'ı olabilir.
    
    Attributes:
        id: Oturum ID'si (Primary Key)
        student_id: Öğrenci ID'si (Foreign Key → users)
        start_date: Test başlangıç tarihi
        completion_date: Test bitiş tarihi (NULL = devam ediyor)
        overall_cefr_level: Final CEFR seviyesi (A1-C2)
        is_completed: Test tamamlandı mı?
        
    Relationships:
        student: Bu session'ın sahibi User
        module_scores: Bu session'daki modül puanları
    
    Örnek Kullanım:
        session = TestSession(
            student_id=1,
            start_date=datetime.now()
        )
    """
    
    # ==========================================
    # TABLO ADI
    # ==========================================
    
    __tablename__ = "test_sessions"
    
    
    # ==========================================
    # SÜTUNLAR
    # ==========================================
    
    # ---------- id ----------
    # Excel'deki: sessionID INTEGER PRIMARY KEY
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    
    
    # ---------- student_id ----------
    # Excel'deki: studentID INTEGER Not Null
    #
    # Foreign Key (Yabancı Anahtar):
    # Bu sütun users tablosundaki id'ye referans verir.
    # Bir session mutlaka bir user'a ait olmalı.
    #
    # ForeignKey("users.id"):
    # - "users" = referans verilen tablo
    # - "id" = referans verilen sütun
    #
    # ondelete="CASCADE":
    # User silinirse, onun session'ları da silinir
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),  # users.id'ye referans
        nullable=False,
        index=True  # Arama performansı için index
    )
    
    
    # ---------- start_date ----------
    # Excel'deki: startDate DATETIME Not Null
    #
    # Testin başladığı tarih/saat
    # Otomatik olarak şu anki zaman atanır
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    
    # ---------- completion_date ----------
    # Excel'deki: completionDate DATETIME NULL
    #
    # Testin tamamlandığı tarih/saat
    # NULL = test henüz devam ediyor
    # Değer varsa = test tamamlanmış
    completion_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    
    
    # ---------- overall_cefr_level ----------
    # Excel'deki: overallCEFRLevel VARCHAR(10) NULL
    #
    # CEFR Seviyeleri:
    # - A1: Başlangıç (Beginner)
    # - A2: Temel (Elementary)
    # - B1: Orta-alt (Intermediate)
    # - B2: Orta-üst (Upper-Intermediate)
    # - C1: İleri (Advanced)
    # - C2: Ustalaşmış (Proficient)
    #
    # NULL = henüz hesaplanmamış (test devam ediyor)
    overall_cefr_level: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        default=None
    )
    
    
    # ---------- is_completed ----------
    # Test tamamlandı mı? (Kolaylık için ekstra alan)
    # True = 4 modül de tamamlandı
    # False = test devam ediyor
    is_completed: Mapped[bool] = mapped_column(
    Boolean,  
    nullable=False,
    default=False
)
    
    
    # ---------- overall_score ----------
    # Ortalama puan (0-100)
    # 4 modülün ortalaması
    overall_score: Mapped[Optional[float]] = mapped_column(
        Integer,
        nullable=True,
        default=None
    )
    
    
    # ==========================================
    # İLİŞKİLER (RELATIONSHIPS)
    # ==========================================
    #
    # Relationship Nedir?
    # -------------------
    # İki tablo arasındaki bağlantıyı Python'da kullanmamızı sağlar.
    # SQL JOIN yazmadan ilişkili verilere erişebiliriz.
    #
    # Örnek:
    #   session = await get_session(id=1)
    #   print(session.student.email)  # JOIN yapmadan!
    #   print(session.module_scores)  # Tüm puanlar
    
    # ---------- student ----------
    # Bu session'ın sahibi olan kullanıcı
    #
    # back_populates: Çift yönlü ilişki
    # User tarafında da "test_sessions" ilişkisi olacak
    student: Mapped["User"] = relationship(
        "User",
        back_populates="test_sessions"
    )
    
    
    # ---------- module_scores ----------
    # Bu session'daki modül puanları (0-4 arası)
    #
    # List["ModuleScore"]: Birden fazla puan olabilir
    # cascade="all, delete-orphan": Session silinirse puanlar da silinir
    module_scores: Mapped[List["ModuleScore"]] = relationship(
        "ModuleScore",
        back_populates="test_session",
        cascade="all, delete-orphan"  # Session silinince puanlar da silinsin
    )
    
    
    # ==========================================
    # METODLAR
    # ==========================================
    
    def __repr__(self) -> str:
        """String temsili."""
        status = "completed" if self.is_completed else "in_progress"
        return f"<TestSession(id={self.id}, student_id={self.student_id}, status={status})>"
    
    
    def complete(self, cefr_level: str, overall_score: float) -> None:
        """
        Test oturumunu tamamla.
        
        Args:
            cefr_level: Hesaplanan CEFR seviyesi (A1-C2)
            overall_score: Ortalama puan (0-100)
        """
        self.is_completed = True
        self.completion_date = datetime.utcnow()
        self.overall_cefr_level = cefr_level
        self.overall_score = overall_score
    
    
    def get_duration_minutes(self) -> Optional[float]:
        """
        Test süresini dakika olarak hesaplar.
        
        Returns:
            float: Süre (dakika), test devam ediyorsa None
        """
        if not self.completion_date:
            return None
        
        duration = self.completion_date - self.start_date
        return duration.total_seconds() / 60