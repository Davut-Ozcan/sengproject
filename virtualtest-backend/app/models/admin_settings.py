# ============================================
# app/models/admin_settings.py - Admin Ayarları
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Excel'deki "AdminSettings" tablosunu tanımlıyor.
# Admin'in test parametrelerini değiştirmesini sağlar.
#
# Excel'deki AdminSettings Tablosu:
# ---------------------------------
# | Column Name          | Data Type  | Constraints    | Example                                    |
# |----------------------|------------|----------------|---------------------------------------------|
# | settingID            | INTEGER    | PRIMARY KEY    | 1                                           |
# | speakingTimeLimit    | INTEGER    | Not Null       | 180                                         |
# | testAttemptsLimit    | INTEGER    | Not Null       | 3                                           |
# | AIGenerationSettings | JSON/TEXT  | NULL           | {"difficulty": "B1", "topic_count": 3}      |
#
# Neden Bu Tablo Var?
# -------------------
# Admin, kodlamaya dokunmadan test parametrelerini değiştirebilsin.
# Örneğin: Speaking süresini 3 dakikadan 5 dakikaya çıkarma.
# ============================================


# SQLAlchemy tipleri
from sqlalchemy import Integer, String, Text, DateTime, JSON

# ORM araçları
from sqlalchemy.orm import Mapped, mapped_column

# SQL fonksiyonları
from sqlalchemy import func

# Python tipleri
from datetime import datetime
from typing import Optional, Dict, Any

# Base class
from app.core.database import Base


class AdminSettings(Base):
    """
    Admin ayarları modeli - admin_settings tablosu.
    
    Bu tablo genellikle tek satır içerir (global ayarlar).
    Birden fazla satır olabilir (farklı preset'ler için).
    
    Attributes:
        id: Ayar ID'si
        setting_name: Ayar seti adı (örn: "default", "exam_mode")
        speaking_time_limit: Speaking modülü süre limiti (saniye)
        writing_time_limit: Writing modülü süre limiti (saniye)
        reading_time_limit: Reading modülü süre limiti (saniye)
        listening_time_limit: Listening modülü süre limiti (saniye)
        test_attempts_limit: Maksimum test deneme hakkı
        ai_generation_settings: AI içerik üretim ayarları (JSON)
        is_active: Bu ayar seti aktif mi?
        created_at: Oluşturulma tarihi
        updated_at: Güncellenme tarihi
    
    Örnek Kullanım:
        settings = AdminSettings(
            setting_name="default",
            speaking_time_limit=180,
            test_attempts_limit=3
        )
    """
    
    # ==========================================
    # TABLO ADI
    # ==========================================
    
    __tablename__ = "admin_settings"
    
    
    # ==========================================
    # SÜTUNLAR
    # ==========================================
    
    # ---------- id ----------
    # Excel'deki: settingID INTEGER PRIMARY KEY
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    
    
    # ---------- setting_name ----------
    # Ayar seti adı (Excel'de yok ama kullanışlı)
    # Birden fazla ayar seti tutmak için
    # Örnek: "default", "exam_mode", "practice_mode"
    setting_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        default="default"
    )
    
    
    # ---------- speaking_time_limit ----------
    # Excel'deki: speakingTimeLimit INTEGER Not Null
    #
    # Speaking modülü için süre limiti (saniye cinsinden)
    # 180 saniye = 3 dakika
    speaking_time_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=180  # 3 dakika
    )
    
    
    # ---------- writing_time_limit ----------
    # Writing modülü için süre limiti (saniye)
    # 2400 saniye = 40 dakika
    writing_time_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2400  # 40 dakika
    )
    
    
    # ---------- reading_time_limit ----------
    # Reading modülü için süre limiti (saniye)
    # 1200 saniye = 20 dakika
    reading_time_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1200  # 20 dakika
    )
    
    
    # ---------- listening_time_limit ----------
    # Listening modülü için süre limiti (saniye)
    # 840 saniye = 14 dakika
    listening_time_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=840  # 14 dakika
    )
    
    
    # ---------- test_attempts_limit ----------
    # Excel'deki: testAttemptsLimit INTEGER Not Null
    #
    # Bir öğrencinin kaç kez test çözebileceği
    # 3 = Maksimum 3 deneme hakkı
    test_attempts_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3
    )
    
    
    # ---------- ai_generation_settings ----------
    # Excel'deki: AIGenerationSettings JSON/TEXT NULL
    #
    # AI içerik üretimi için ayarlar (JSON formatında)
    # Örnek: {"difficulty": "B1", "level_mix": "3", "topic_count": 3}
    #
    # JSON Nedir?
    # -----------
    # Yapılandırılmış veri formatı.
    # Python'daki dict'e benzer.
    # Database'de metin olarak saklanır, Python'da dict olarak kullanılır.
    #
    # Dict[str, Any] = Anahtarları string, değerleri herhangi tipte dict
    ai_generation_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,  # PostgreSQL native JSON desteği
        nullable=True,
        default=None
    )
    
    
    # ---------- is_active ----------
    # Bu ayar seti şu an aktif mi?
    # Birden fazla ayar seti varsa hangisi kullanılacak
    is_active: Mapped[bool] = mapped_column(
        Integer,  # SQLite boolean desteği için Integer
        nullable=False,
        default=True
    )
    
    
    # ---------- created_at ----------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    
    # ---------- updated_at ----------
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    
    
    # ==========================================
    # METODLAR
    # ==========================================
    
    def __repr__(self) -> str:
        """String temsili."""
        return f"<AdminSettings(id={self.id}, name='{self.setting_name}', active={self.is_active})>"
    
    
    def get_time_limit(self, module_name: str) -> int:
        """
        Belirtilen modül için süre limitini döndürür.
        
        Args:
            module_name: Modül adı (speaking, writing, reading, listening)
        
        Returns:
            int: Süre limiti (saniye)
        
        Örnek:
            limit = settings.get_time_limit("speaking")  # 180
        """
        limits = {
            "speaking": self.speaking_time_limit,
            "writing": self.writing_time_limit,
            "reading": self.reading_time_limit,
            "listening": self.listening_time_limit,
        }
        return limits.get(module_name.lower(), 0)
    
    
    def get_time_limit_minutes(self, module_name: str) -> float:
        """
        Süre limitini dakika olarak döndürür.
        
        Args:
            module_name: Modül adı
        
        Returns:
            float: Süre limiti (dakika)
        """
        seconds = self.get_time_limit(module_name)
        return seconds / 60