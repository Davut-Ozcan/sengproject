# ============================================
# app/schemas/test.py - Test/Assessment Şemaları
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Test oturumları ve modül puanları için şablonlar.
# 4 modül: Reading, Listening, Speaking, Writing
#
# Test Akışı:
# -----------
# 1. Öğrenci teste başlar → TestSession oluşur
# 2. Her modülü tamamlar → ModuleScore kaydedilir
# 3. 4 modül bitince → CEFR seviyesi hesaplanır
# 4. Sonuç gösterilir
# ============================================


from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==========================================
# ENUM'LAR (Sabit Değerler)
# ==========================================

class ModuleName(str, Enum):
    """
    Modül isimleri.
    
    Enum kullanarak sadece bu 4 değerin kabul edilmesini sağlıyoruz.
    Yanlış yazım hatalarını önler.
    """
    READING = "reading"
    LISTENING = "listening"
    SPEAKING = "speaking"
    WRITING = "writing"


class CEFRLevel(str, Enum):
    """
    CEFR Seviyeleri.
    
    Avrupa Ortak Dil Referans Çerçevesi.
    A1 (en düşük) → C2 (en yüksek)
    """
    A1 = "A1"  # Başlangıç
    A2 = "A2"  # Temel
    B1 = "B1"  # Orta-alt
    B2 = "B2"  # Orta-üst
    C1 = "C1"  # İleri
    C2 = "C2"  # Ustalaşmış


# ==========================================
# TEST SESSION SCHEMAS
# ==========================================

class TestSessionCreate(BaseModel):
    """
    Yeni test oturumu başlatma.
    
    Öğrenci "Teste Başla" dediğinde bu istek gönderilir.
    Genellikle boş body ile gelir (student_id token'dan alınır).
    
    Örnek İstek (POST /api/test/start):
    {}  // Boş, user token'dan belirlenir
    """
    pass  # Şimdilik ekstra alan yok


class TestSessionResponse(BaseModel):
    """
    Test oturumu yanıtı.
    
    Test durumu ve puanları gösterir.
    
    Örnek Yanıt:
    {
        "id": 1,
        "student_id": 5,
        "start_date": "2025-01-01T10:00:00Z",
        "is_completed": false,
        "completed_modules": ["reading", "listening"],
        "remaining_modules": ["speaking", "writing"]
    }
    """
    
    id: int
    student_id: int
    start_date: datetime
    completion_date: Optional[datetime] = None
    is_completed: bool = False
    overall_cefr_level: Optional[str] = None
    overall_score: Optional[float] = None
    
    # Hangi modüller tamamlandı?
    completed_modules: List[str] = []
    remaining_modules: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class ModuleScoreResponse(BaseModel):
    """
    Modül puanı yanıtı.
    
    Örnek:
    {
        "id": 1,
        "module_name": "reading",
        "score": 75.5,
        "cefr_level": "B2",
        "test_date": "2025-01-01T10:30:00Z"
    }
    """
    
    id: int
    module_name: str
    score: float
    cefr_level: Optional[str] = None
    test_date: datetime
    duration_seconds: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class TestSessionDetail(TestSessionResponse):
    """
    Detaylı test oturumu (puanlarla birlikte).
    
    Test sonuç sayfasında kullanılır.
    """
    
    # Her modülün puanı
    module_scores: List["ModuleScoreResponse"] = []


# ==========================================
# MODULE SCORE SCHEMAS
# ==========================================

class ModuleScoreCreate(BaseModel):
    """
    Modül puanı oluşturma (internal kullanım).
    
    AI değerlendirmesinden sonra backend tarafından oluşturulur.
    """
    
    session_id: int
    module_name: ModuleName
    score: float = Field(..., ge=0, le=100)  # 0-100 arası
    cefr_level: Optional[str] = None
    user_answer: Optional[str] = None
    ai_feedback: Optional[str] = None
    duration_seconds: Optional[int] = None


class ModuleScoreDetail(ModuleScoreResponse):
    """
    Detaylı modül puanı (feedback ile).
    
    Sonuç sayfasında detaylı analiz için.
    """
    
    user_answer: Optional[str] = None
    ai_feedback: Optional[Dict[str, Any]] = None


# ==========================================
# MODULE SUBMISSION SCHEMAS (Cevap Gönderme)
# ==========================================

class ReadingSubmission(BaseModel):
    """
    Reading modülü cevap gönderimi.
    
    Örnek İstek (POST /api/test/reading):
    {
        "session_id": 1,
        "answers": [
            {"question_id": 1, "answer": "B"},
            {"question_id": 2, "answer": "C"},
            {"question_id": 3, "answer": "A"}
        ],
        "duration_seconds": 1150
    }
    """
    
    session_id: int
    
    # Cevaplar listesi
    answers: List[Dict[str, Any]] = Field(
        ...,
        description="Soru cevapları: [{'question_id': 1, 'answer': 'B'}, ...]"
    )
    
    # Modülü tamamlama süresi (saniye)
    duration_seconds: Optional[int] = None


class ListeningSubmission(BaseModel):
    """
    Listening modülü cevap gönderimi.
    
    Reading ile aynı format.
    """
    
    session_id: int
    answers: List[Dict[str, Any]]
    duration_seconds: Optional[int] = None


class SpeakingSubmission(BaseModel):
    """
    Speaking modülü gönderimi.
    
    Ses dosyası ayrı endpoint'te yüklenir.
    Bu şema metadata içindir.
    
    Örnek:
    {
        "session_id": 1,
        "topic_id": 2,
        "audio_file_path": "/uploads/audio_123.webm",
        "duration_seconds": 120
    }
    """
    
    session_id: int
    
    # Seçilen konu
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    
    # Ses dosyası yolu (backend tarafından doldurulur)
    audio_file_path: Optional[str] = None
    
    # Konuşma süresi
    duration_seconds: Optional[int] = None
    
    # Transcript (Speech-to-Text sonucu)
    transcript: Optional[str] = None


class WritingSubmission(BaseModel):
    """
    Writing modülü gönderimi.
    
    Örnek İstek (POST /api/test/writing):
    {
        "session_id": 1,
        "topic_id": 1,
        "essay_text": "In my opinion, global tourism...",
        "duration_seconds": 2100
    }
    """
    
    session_id: int
    
    # Seçilen konu
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    
    # Essay metni
    essay_text: str = Field(
        ...,
        min_length=50,  # Minimum 50 karakter
        max_length=5000,  # Maksimum 5000 karakter
        description="Essay metni (250-400 kelime önerilen)"
    )
    
    # Yazma süresi
    duration_seconds: Optional[int] = None


# ==========================================
# RESULT SCHEMAS (Sonuç Şemaları)
# ==========================================

class ModuleResult(BaseModel):
    """
    Tek modül sonucu.
    
    Değerlendirme sonrası dönen veri.
    """
    
    module_name: str
    score: float
    cefr_level: str
    feedback: Optional[str] = None
    
    # Detaylı puanlama (opsiyonel)
    details: Optional[Dict[str, Any]] = None


class TestResult(BaseModel):
    """
    Tam test sonucu.
    
    4 modül tamamlandığında dönen final sonuç.
    total.html sayfasında gösterilecek veri.
    
    Örnek:
    {
        "session_id": 1,
        "overall_score": 67.5,
        "overall_cefr_level": "B1",
        "module_results": [
            {"module_name": "reading", "score": 75, "cefr_level": "B2"},
            {"module_name": "listening", "score": 60, "cefr_level": "B1"},
            ...
        ],
        "recommendations": ["Focus on listening skills..."]
    }
    """
    
    session_id: int
    student_id: int
    
    # Genel sonuçlar
    overall_score: float
    overall_cefr_level: str
    
    # Modül bazlı sonuçlar
    module_results: List[ModuleResult]
    
    # Test süreleri
    start_date: datetime
    completion_date: datetime
    total_duration_minutes: float
    
    # AI önerileri
    recommendations: List[str] = []
    
    # CEFR açıklaması
    cefr_description: Optional[str] = None


# ==========================================
# TOPIC SCHEMAS (Konu Şemaları)
# ==========================================

class Topic(BaseModel):
    """
    Speaking/Writing konusu.
    
    Frontend'de konu seçimi için.
    """
    
    id: int
    name: str
    description: str
    module: str  # "speaking" veya "writing"
    difficulty: Optional[str] = None  # "B1", "B2", vs.


class TopicList(BaseModel):
    """
    Konu listesi yanıtı.
    """
    
    topics: List[Topic]
    module: str


# ==========================================
# PROGRESS SCHEMA (İlerleme Durumu)
# ==========================================

class TestProgress(BaseModel):
    """
    Test ilerleme durumu.
    
    Frontend'de ilerleme çubuğu için.
    
    Örnek:
    {
        "session_id": 1,
        "total_modules": 4,
        "completed_modules": 2,
        "progress_percent": 50,
        "current_module": "speaking",
        "modules": {
            "reading": {"completed": true, "score": 75},
            "listening": {"completed": true, "score": 80},
            "speaking": {"completed": false, "score": null},
            "writing": {"completed": false, "score": null}
        }
    }
    """
    
    session_id: int
    total_modules: int = 4
    completed_modules: int = 0
    progress_percent: float = 0
    current_module: Optional[str] = None
    
    modules: Dict[str, Dict[str, Any]] = {}

    # ==========================================
# AI CONTENT SCHEMAS (AI İçerik Şemaları)
# ==========================================

class QuestionSchema(BaseModel):
    """
    AI'dan gelen soru formatı.
    
    Reading ve Listening modülleri için.
    
    Örnek:
    {
        "question_text": "What is the main idea?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "weight": 30
    }
    """
    
    question_text: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: int = Field(..., ge=0, le=3)  # 0-3 arası index
    weight: int = Field(default=25, ge=10, le=50)  # Zorluk puanı


class ReadingContentResponse(BaseModel):
    """
    Reading modülü AI içeriği.
    
    AI'ın ürettiği okuma metni ve sorular.
    
    Örnek:
    {
        "text": "The quick brown fox...",
        "questions": [...]
    }
    """
    
    text: str
    questions: List[QuestionSchema]


class ListeningContentResponse(BaseModel):
    """
    Listening modülü AI içeriği.
    
    AI'ın ürettiği script ve sorular.
    audio_url: TTS servisinin oluşturduğu ses dosyası.
    
    Örnek:
    {
        "script": "Hello, my name is Sarah...",
        "audio_url": "/static/audio/listening_abc123.mp3",
        "questions": [...]
    }
    """
    
    script: str
    audio_url: Optional[str] = None
    questions: List[QuestionSchema]


class WritingContentResponse(BaseModel):
    """
    Writing modülü AI içeriği.
    
    AI'ın ürettiği yazma konuları.
    
    Örnek:
    {
        "topics": [
            "Discuss the benefits of technology.",
            "Is tourism good for local economy?",
            "Describe a memorable event."
        ]
    }
    """
    
    topics: List[str] = Field(..., min_length=1, max_length=5)


class SpeakingContentResponse(BaseModel):
    """
    Speaking modülü AI içeriği.
    
    AI'ın ürettiği konuşma konuları.
    
    Örnek:
    {
        "topics": [
            "What are your hobbies?",
            "Describe your hometown.",
            "Do you prefer summer or winter?"
        ]
    }
    """
    
    topics: List[str] = Field(..., min_length=1, max_length=5)


class ModuleStartRequest(BaseModel):
    """
    Modül başlatma isteği.
    
    Örnek (POST /api/test/module/start):
    {
        "session_id": 1,
        "module_name": "reading",
        "cefr_level": "B1"
    }
    """
    
    session_id: int
    module_name: ModuleName
    cefr_level: Optional[str] = "B1"


class ModuleStartResponse(BaseModel):
    """
    Modül başlatma yanıtı.
    
    AI içeriği ile birlikte döner.
    
    Örnek (Reading):
    {
        "session_id": 1,
        "module_name": "reading",
        "content": {
            "text": "...",
            "questions": [...]
        }
    }
    """
    
    session_id: int
    module_name: str
    cefr_level: str
    content: Dict[str, Any]  # AI'dan gelen içerik


class EvaluationRequest(BaseModel):
    """
    Değerlendirme isteği.
    
    Reading/Listening için:
    {
        "session_id": 1,
        "module_name": "reading",
        "user_answers": [0, 1, 2],
        "correct_answers": [0, 1, 0],
        "weights": [30, 40, 30]
    }
    
    Writing/Speaking için:
    {
        "session_id": 1,
        "module_name": "writing",
        "topic": "Discuss technology benefits",
        "student_response": "In my opinion..."
    }
    """
    
    session_id: int
    module_name: ModuleName
    
    # Reading/Listening için
    user_answers: Optional[List[int]] = None
    correct_answers: Optional[List[int]] = None
    weights: Optional[List[int]] = None
    
    # Writing/Speaking için
    topic: Optional[str] = None
    student_response: Optional[str] = None
    
    # Süre
    duration_seconds: Optional[int] = None


class EvaluationResponse(BaseModel):
    """
    Değerlendirme yanıtı.
    
    Örnek:
    {
        "session_id": 1,
        "module_name": "reading",
        "score": 85.5,
        "cefr_level": "B2",
        "feedback": "Good job!",
        "is_test_completed": false,
        "next_module": "listening"
    }
    """
    
    session_id: int
    module_name: str
    score: float
    cefr_level: str
    feedback: Optional[str] = None
    
    # Test durumu
    is_test_completed: bool = False
    next_module: Optional[str] = None
    
    # Final sonuç (test tamamlandıysa)
    overall_score: Optional[float] = None
    overall_cefr_level: Optional[str] = None