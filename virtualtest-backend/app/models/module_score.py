# ============================================
# app/models/module_score.py - Modül Puanları
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Excel'deki "ModuleScore" tablosunu tanımlıyor.
# Her modülün (Reading, Listening, Speaking, Writing) puanını saklar.
#
# Excel'deki ModuleScore Tablosu:
# -------------------------------
# | Column Name | Data Type   | Constraints         | Example    |
# |-------------|-------------|---------------------|------------|
# | scoreID     | INTEGER     | PRIMARY KEY         | 1          |
# | sessionID   | INTEGER     | FOREIGN KEY,Not Null| S-001      |
# | moduleName  | VARCHAR(50) | Not Null            | Speaking   |
# | score       | INTEGER     | Not Null            | 75         |
# | testDate    | DATETIME    | Not Null            | 2025-12-08 |
#
# İlişki:
# -------
# TestSession (1) ──────< ModuleScore (N)
# Bir test oturumunda 4 modül puanı olur
# ============================================


# SQLAlchemy tipleri
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text

# ORM araçları
from sqlalchemy.orm import Mapped, mapped_column, relationship

# SQL fonksiyonları
from sqlalchemy import func

# Python tipleri
from datetime import datetime
from typing import Optional, TYPE_CHECKING

# Base class
from app.core.database import Base

# TYPE_CHECKING: Circular import önleme
if TYPE_CHECKING:
    from app.models.test_session import TestSession


class ModuleScore(Base):
    """
    Modül puanı modeli - module_scores tablosu.
    
    Her test oturumunda 4 modül skoru olur:
    - Reading
    - Listening  
    - Speaking
    - Writing
    
    Attributes:
        id: Puan kaydı ID'si
        session_id: Test oturumu ID'si (Foreign Key)
        module_name: Modül adı (reading/listening/speaking/writing)
        score: Puan (0-100)
        cefr_level: Bu modül için CEFR seviyesi (A1-C2)
        test_date: Modülün tamamlandığı tarih
        ai_feedback: AI'dan gelen detaylı feedback (JSON)
        user_answer: Kullanıcının cevabı (essay, ses transcript, vs.)
        
    Relationships:
        test_session: Bu puanın ait olduğu test oturumu
    """
    
    # ==========================================
    # TABLO ADI
    # ==========================================
    
    __tablename__ = "module_scores"
    
    
    # ==========================================
    # SÜTUNLAR
    # ==========================================
    
    # ---------- id ----------
    # Excel'deki: scoreID INTEGER PRIMARY KEY
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    
    
    # ---------- session_id ----------
    # Excel'deki: sessionID INTEGER FOREIGN KEY, Not Null
    #
    # Bu puan hangi test oturumuna ait?
    # Foreign Key ile test_sessions tablosuna bağlı
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    
    # ---------- module_name ----------
    # Excel'deki: moduleName VARCHAR(50) Not Null
    #
    # Modül adı - 4 seçenek:
    # - "reading"
    # - "listening"
    # - "speaking"
    # - "writing"
    #
    # Küçük harf kullanıyoruz (tutarlılık için)
    module_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True  # Modüle göre filtreleme için
    )
    
    
    # ---------- score ----------
    # Excel'deki: score INTEGER Not Null
    #
    # Modül puanı (0-100 arası)
    # Float kullanıyoruz (örn: 85.5)
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    
    # ---------- cefr_level ----------
    # Bu modül için CEFR seviyesi
    # Her modül ayrı değerlendirilebilir
    # Örn: Reading B2, Speaking B1
    cefr_level: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )
    
    
    # ---------- test_date ----------
    # Excel'deki: testDate DATETIME Not Null
    #
    # Modülün tamamlandığı tarih/saat
    test_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    
     # ---------- user_answer ----------
    # Kullanıcının verdiği cevap
    user_answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    
    # ---------- content_json ----------
    # AI'ın ürettiği içerik (soru, metin, script)
    #
    # Reading: {"text": "...", "questions": [...]}
    # Listening: {"script": "...", "questions": [...]}
    # Writing/Speaking: {"topics": ["...", "...", "..."]}
    content_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
        # ---------- content_json ----------
    # AI'ın ürettiği içerik (soru, metin, script)
    #
    # Reading: {"text": "...", "questions": [...]}
    # Listening: {"script": "...", "questions": [...]}
    # Writing/Speaking: {"topics": ["...", "...", "..."]}
    content_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # ---------- ai_feedback ----------
    # AI'dan gelen detaylı geri bildirim
    #
    # Örnek JSON:
    # {
    #   "grammar_score": 85,
    #   "vocabulary_score": 78,
    #   "coherence_score": 82,
    #   "comments": "Good structure but..."
    # }
    ai_feedback: Mapped[Optional[str]] = mapped_column(
        Text,  # JSON string olarak saklanacak
        nullable=True
    )
    
    
    # ---------- duration_seconds ----------
    # Modülü tamamlama süresi (saniye)
    # Analiz için kullanışlı
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    
    # ==========================================
    # İLİŞKİLER (RELATIONSHIPS)
    # ==========================================
    
    # ---------- test_session ----------
    # Bu puanın ait olduğu test oturumu
    test_session: Mapped["TestSession"] = relationship(
        "TestSession",
        back_populates="module_scores"
    )
    
    
    # ==========================================
    # METODLAR
    # ==========================================
    
    def __repr__(self) -> str:
        """String temsili."""
        return f"<ModuleScore(id={self.id}, module='{self.module_name}', score={self.score})>"
    
    
    @staticmethod
    def score_to_cefr(score: float) -> str:
        """
        Puanı CEFR seviyesine çevirir.
        
        Dönüşüm tablosu:
        - 0-20: A1 (Başlangıç)
        - 21-40: A2 (Temel)
        - 41-60: B1 (Orta-alt)
        - 61-80: B2 (Orta-üst)
        - 81-90: C1 (İleri)
        - 91-100: C2 (Ustalaşmış)
        
        Args:
            score: Puan (0-100)
        
        Returns:
            str: CEFR seviyesi
        """
        if score <= 20:
            return "A1"
        elif score <= 40:
            return "A2"
        elif score <= 60:
            return "B1"
        elif score <= 80:
            return "B2"
        elif score <= 90:
            return "C1"
        else:
            return "C2"
    
    
    def get_feedback_dict(self) -> Optional[dict]:
        """
        AI feedback'i dict olarak döndürür.
        
        Returns:
            dict: Feedback verisi veya None
        """
        if not self.ai_feedback:
            return None
        
        import json
        try:
            return json.loads(self.ai_feedback)
        except json.JSONDecodeError:
            return None
    
    
    def set_feedback_dict(self, feedback: dict) -> None:
        """
        Feedback'i JSON string olarak kaydeder.
        
        Args:
            feedback: Feedback dict'i
        """
        import json
        self.ai_feedback = json.dumps(feedback, ensure_ascii=False)