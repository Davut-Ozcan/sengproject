# ============================================
# app/routers/test.py - Test/Assessment Endpoints
# ============================================
#
# Bu dosya ne yapıyor?
# --------------------
# Test oturumu ve modül endpoint'lerini tanımlar.
# AI servisleriyle entegre çalışır.
#
# Endpoint'ler:
# -------------
# POST /api/test/start                → Yeni test başlat
# GET  /api/test/session/{id}         → Test durumunu görüntüle
# GET  /api/test/progress/{id}        → İlerleme durumu
# POST /api/test/module/start         → Modül başlat (AI içerik üretir)
# POST /api/test/module/submit        → Modül cevabı gönder (AI değerlendirir)
# GET  /api/test/result/{id}          → Test sonucunu görüntüle
# GET  /api/test/history              → Geçmiş testler
# ============================================


from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated, List, Optional
from datetime import datetime
import json

# Projemizin modülleri
from app.core.database import get_db
from app.models import User, TestSession, ModuleScore

# Schemas
from app.schemas.test import (
    TestSessionCreate,
    TestSessionResponse,
    TestSessionDetail,
    TestProgress,
    ModuleStartRequest,
    ModuleStartResponse,
    EvaluationRequest,
    EvaluationResponse,
    TestResult,
    ModuleResult,
    ModuleScoreResponse,
)
from app.schemas.auth import MessageResponse

# AI Servisleri
from app.services import ai_service, stt_service, tts_service

# Repository'ler
from app.repositories import test_repository

# Auth dependency
from app.routers.auth import get_current_user, CurrentUser


# ==========================================
# ROUTER OLUŞTURMA
# ==========================================

router = APIRouter(
    prefix="/test",
    tags=["Test & Assessment"],
    responses={
        401: {"description": "Kimlik doğrulama gerekli"},
        404: {"description": "Test bulunamadı"},
    }
)


# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================

def get_remaining_modules(completed: List[str]) -> List[str]:
    """Tamamlanmamış modülleri döndürür."""
    all_modules = ["reading", "listening", "speaking", "writing"]
    return [m for m in all_modules if m not in completed]


def get_next_module(completed: List[str]) -> Optional[str]:
    """Sıradaki modülü döndürür."""
    remaining = get_remaining_modules(completed)
    return remaining[0] if remaining else None


# ==========================================
# ENDPOINT: Test Başlat
# ==========================================

@router.post(
    "/start",
    response_model=TestSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni test başlat",
    description="Öğrenci için yeni bir test oturumu oluşturur."
)
async def start_test(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TestSessionResponse:
    """
    Yeni test oturumu başlatır.
    
    İşlem:
    1. Aktif (tamamlanmamış) test var mı kontrol et
    2. Varsa onu döndür, yoksa yeni oluştur
    """
    
    # Aktif test var mı?
    active_session = await test_repository.get_active_session(db, current_user.id)
    
    if active_session:
        # Zaten aktif test var, onu döndür
        completed = await test_repository.get_completed_modules(db, active_session.id)
        return TestSessionResponse(
            id=active_session.id,
            student_id=active_session.student_id,
            start_date=active_session.start_date,
            completion_date=active_session.completion_date,
            is_completed=active_session.is_completed,
            overall_cefr_level=active_session.overall_cefr_level,
            overall_score=active_session.overall_score,
            completed_modules=completed,
            remaining_modules=get_remaining_modules(completed)
        )
    
    # Yeni test oluştur
    new_session = await test_repository.create_session(db, current_user.id)
    
    if not new_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test oturumu oluşturulamadı"
        )
    
    return TestSessionResponse(
        id=new_session.id,
        student_id=new_session.student_id,
        start_date=new_session.start_date,
        is_completed=False,
        completed_modules=[],
        remaining_modules=["reading", "listening", "speaking", "writing"]
    )


# ==========================================
# ENDPOINT: Test Durumu
# ==========================================

@router.get(
    "/session/{session_id}",
    response_model=TestSessionDetail,
    summary="Test oturumu detayı",
    description="Test oturumunun detaylı bilgilerini döndürür."
)
async def get_session(
    session_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TestSessionDetail:
    """Test oturumu detaylarını döndürür."""
    
    session = await test_repository.get_session(db, session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test oturumu bulunamadı"
        )
    
    # Yetki kontrolü
    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu teste erişim yetkiniz yok"
        )
    
    completed = await test_repository.get_completed_modules(db, session_id)
    scores = await test_repository.get_scores(db, current_user.id, session_id)
    
    # ModuleScoreResponse listesi oluştur
    module_scores = []
    for module_name, score_data in scores.items():
        module_scores.append(ModuleScoreResponse(
            id=0,  # Basitleştirme
            module_name=module_name,
            score=score_data.get("score", 0),
            cefr_level=score_data.get("cefr"),
            test_date=datetime.fromisoformat(score_data["completed_at"]) if score_data.get("completed_at") else datetime.utcnow()
        ))
    
    return TestSessionDetail(
        id=session.id,
        student_id=session.student_id,
        start_date=session.start_date,
        completion_date=session.completion_date,
        is_completed=session.is_completed,
        overall_cefr_level=session.overall_cefr_level,
        overall_score=session.overall_score,
        completed_modules=completed,
        remaining_modules=get_remaining_modules(completed),
        module_scores=module_scores
    )


# ==========================================
# ENDPOINT: İlerleme Durumu
# ==========================================

@router.get(
    "/progress/{session_id}",
    response_model=TestProgress,
    summary="Test ilerleme durumu",
    description="Testin ilerleme durumunu döndürür."
)
async def get_progress(
    session_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TestProgress:
    """Test ilerleme durumunu döndürür."""
    
    session = await test_repository.get_session(db, session_id)
    
    if not session or session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test oturumu bulunamadı"
        )
    
    completed = await test_repository.get_completed_modules(db, session_id)
    scores = await test_repository.get_scores(db, current_user.id, session_id)
    
    # Modül durumları
    modules = {}
    for module in ["reading", "listening", "speaking", "writing"]:
        if module in scores:
            modules[module] = {
                "completed": True,
                "score": scores[module].get("score"),
                "cefr": scores[module].get("cefr")
            }
        else:
            modules[module] = {
                "completed": False,
                "score": None,
                "cefr": None
            }
    
    completed_count = len(completed)
    
    return TestProgress(
        session_id=session_id,
        total_modules=4,
        completed_modules=completed_count,
        progress_percent=(completed_count / 4) * 100,
        current_module=get_next_module(completed),
        modules=modules
    )


# ==========================================
# ENDPOINT: Modül Başlat (AI İçerik Üretir)
# ==========================================

@router.post(
    "/module/start",
    response_model=ModuleStartResponse,
    summary="Modül başlat",
    description="Belirtilen modülü başlatır ve AI içerik üretir."
)
async def start_module(
    data: ModuleStartRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ModuleStartResponse:
    # Session kontrolü
    session = await test_repository.get_session(db, data.session_id)

    if not session or session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test oturumu bulunamadı"
        )

    if session.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu test zaten tamamlanmış"
        )

    # Modül zaten tamamlanmış mı?
    completed = await test_repository.get_completed_modules(db, data.session_id)
    module_name = data.module_name.value  # Enum'dan string'e

    if module_name in completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{module_name.capitalize()} modülü zaten tamamlanmış"
        )

    # CEFR seviyesi
    cefr_level = data.cefr_level or "B1"

    # AI'dan içerik üret
    level_string = f"{cefr_level}-{module_name.capitalize()}"
    content = await ai_service.generate_content(level_string)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İçerik üretilemedi"
        )

    # Listening için ses dosyası oluştur
    if module_name == "listening" and content.get("script"):
        audio_path = tts_service.convert_text_to_audio(
            text=content["script"],
            slow=(cefr_level in ["A1", "A2"])
        )
        if audio_path:
            filename = audio_path.replace("\\", "/").split("/")[-1]
            content["audio_url"] = f"/static/audio/{filename}"
        else:
            content["audio_url"] = None

    # HER MODÜL İÇİN DÖN
    return ModuleStartResponse(
        session_id=data.session_id,
        module_name=module_name,
        cefr_level=cefr_level,
        content=content
    )


# ==========================================
# ENDPOINT: Modül Cevap Gönder (AI Değerlendirir)
# ==========================================

@router.post(
    "/module/submit",
    response_model=EvaluationResponse,
    summary="Modül cevabı gönder",
    description="Modül cevabını gönderir ve AI değerlendirir."
)
async def submit_module(
    data: EvaluationRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> EvaluationResponse:
    """
    Modül cevabını değerlendirir.
    
    İşlem:
    1. Session kontrolü
    2. AI değerlendirmesi
    3. Puanı kaydet
    4. Test tamamlandı mı kontrol
    """
    
    # Session kontrolü
    session = await test_repository.get_session(db, data.session_id)
    
    if not session or session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test oturumu bulunamadı"
        )
    
    module_name = data.module_name.value
    
    # AI değerlendirmesi için veri hazırla
    if module_name in ["reading", "listening"]:
        eval_data = {
            "type": module_name.capitalize(),
            "user_answers": data.user_answers,
            "correct_answers": data.correct_answers,
            "weights": data.weights
        }
    else:  # writing, speaking
        eval_data = {
            "type": module_name.capitalize(),
            "topic": data.topic,
            "student_response": data.student_response
        }
    
    # AI değerlendirmesi
    score = await ai_service.evaluate_response(json.dumps(eval_data))
    
    # CEFR seviyesi hesapla
    cefr_level = await ai_service.calculate_overall_cefr([score])
    
    # Puanı kaydet
    await test_repository.save_score(
        db=db,
        student_id=current_user.id,
        session_id=data.session_id,
        module=module_name,
        score=score,
        cefr_level=cefr_level
    )
    
    # Tamamlanan modülleri kontrol et
    completed = await test_repository.get_completed_modules(db, data.session_id)
    is_test_completed = len(completed) >= 4
    next_module = get_next_module(completed)
    
    # Test tamamlandıysa final sonucu hesapla
    overall_score = None
    overall_cefr = None
    
    if is_test_completed:
        scores_dict = await test_repository.get_scores(db, current_user.id, data.session_id)
        all_scores = [s["score"] for s in scores_dict.values()]
        overall_score = sum(all_scores) / len(all_scores)
        overall_cefr = await ai_service.calculate_overall_cefr(all_scores)
        
        # Final sonucu kaydet
        await test_repository.save_final_result(
            db=db,
            student_id=current_user.id,
            session_id=data.session_id,
            overall_score=overall_score,
            cefr_level=overall_cefr
        )
    
    return EvaluationResponse(
        session_id=data.session_id,
        module_name=module_name,
        score=score,
        cefr_level=cefr_level,
        is_test_completed=is_test_completed,
        next_module=next_module,
        overall_score=overall_score,
        overall_cefr_level=overall_cefr
    )


# ==========================================
# ENDPOINT: Speaking Ses Yükleme
# ==========================================

@router.post(
    "/module/speaking/upload",
    response_model=EvaluationResponse,
    summary="Speaking ses dosyası yükle",
    description="Speaking modülü için ses dosyası yükler ve değerlendirir."
)
async def upload_speaking(
    session_id: int,
    topic: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    audio: UploadFile = File(...)
) -> EvaluationResponse:
    """
    Speaking ses dosyasını yükler ve değerlendirir.
    
    İşlem:
    1. Ses dosyasını oku
    2. Speech-to-Text ile metne çevir
    3. AI ile değerlendir
    4. Puanı kaydet
    """
    
    # Session kontrolü
    session = await test_repository.get_session(db, session_id)
    
    if not session or session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test oturumu bulunamadı"
        )
    
    # Ses dosyasını oku
    audio_data = await audio.read()
    
    if not audio_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ses dosyası boş"
        )
    
    # Speech-to-Text
    transcript = await stt_service.transcribe(audio_data)
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ses tanınamadı. Lütfen tekrar deneyin."
        )
    
    # AI değerlendirmesi
    eval_data = {
        "type": "Speaking",
        "topic": topic,
        "student_response": transcript
    }
    
    score = await ai_service.evaluate_response(json.dumps(eval_data))
    cefr_level = await ai_service.calculate_overall_cefr([score])
    
    # Puanı kaydet
    await test_repository.save_score(
        db=db,
        student_id=current_user.id,
        session_id=session_id,
        module="speaking",
        score=score,
        cefr_level=cefr_level
    )
    
    # Tamamlanan modülleri kontrol et
    completed = await test_repository.get_completed_modules(db, session_id)
    is_test_completed = len(completed) >= 4
    next_module = get_next_module(completed)
    
    # Test tamamlandıysa
    overall_score = None
    overall_cefr = None
    
    if is_test_completed:
        scores_dict = await test_repository.get_scores(db, current_user.id, session_id)
        all_scores = [s["score"] for s in scores_dict.values()]
        overall_score = sum(all_scores) / len(all_scores)
        overall_cefr = await ai_service.calculate_overall_cefr(all_scores)
        
        await test_repository.save_final_result(
            db=db,
            student_id=current_user.id,
            session_id=session_id,
            overall_score=overall_score,
            cefr_level=overall_cefr
        )
    
    return EvaluationResponse(
        session_id=session_id,
        module_name="speaking",
        score=score,
        cefr_level=cefr_level,
        feedback=f"Transcript: {transcript[:100]}...",
        is_test_completed=is_test_completed,
        next_module=next_module,
        overall_score=overall_score,
        overall_cefr_level=overall_cefr
    )


# ==========================================
# ENDPOINT: Test Sonucu
# ==========================================

@router.get(
    "/result/{session_id}",
    response_model=TestResult,
    summary="Test sonucu",
    description="Tamamlanmış testin sonucunu döndürür."
)
async def get_result(
    session_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TestResult:
    """Test sonucunu döndürür."""
    
    session = await test_repository.get_session(db, session_id)
    
    if not session or session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test oturumu bulunamadı"
        )
    
    if not session.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test henüz tamamlanmamış"
        )
    
    # Puanları al
    scores = await test_repository.get_scores(db, current_user.id, session_id)
    
    # Modül sonuçları
    module_results = []
    for module_name, score_data in scores.items():
        module_results.append(ModuleResult(
            module_name=module_name,
            score=score_data.get("score", 0),
            cefr_level=score_data.get("cefr", "A1")
        ))
    
    # Süre hesapla
    duration = 0
    if session.completion_date and session.start_date:
        delta = session.completion_date - session.start_date
        duration = delta.total_seconds() / 60
    
    # CEFR açıklaması
    cefr_descriptions = {
        "A1": "Başlangıç - Temel ifadeleri anlayabilir",
        "A2": "Temel - Basit günlük konuları anlayabilir",
        "B1": "Orta-Alt - Ana noktaları anlayabilir",
        "B2": "Orta-Üst - Karmaşık metinleri anlayabilir",
        "C1": "İleri - Geniş kapsamlı metinleri anlayabilir",
        "C2": "Ustalaşmış - Her şeyi kolayca anlayabilir"
    }
    
    return TestResult(
        session_id=session_id,
        student_id=current_user.id,
        overall_score=session.overall_score or 0,
        overall_cefr_level=session.overall_cefr_level or "A1",
        module_results=module_results,
        start_date=session.start_date,
        completion_date=session.completion_date or datetime.utcnow(),
        total_duration_minutes=duration,
        cefr_description=cefr_descriptions.get(session.overall_cefr_level, "")
    )


# ==========================================
# ENDPOINT: Test Geçmişi
# ==========================================

@router.get(
    "/history",
    response_model=List[TestSessionResponse],
    summary="Test geçmişi",
    description="Kullanıcının tüm test geçmişini döndürür."
)
async def get_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 10
) -> List[TestSessionResponse]:
    """Kullanıcının test geçmişini döndürür."""
    
    sessions = await test_repository.get_student_history(db, current_user.id, limit)
    
    result = []
    for session in sessions:
        completed = await test_repository.get_completed_modules(db, session.id)
        
        result.append(TestSessionResponse(
            id=session.id,
            student_id=session.student_id,
            start_date=session.start_date,
            completion_date=session.completion_date,
            is_completed=session.is_completed,
            overall_cefr_level=session.overall_cefr_level,
            overall_score=session.overall_score,
            completed_modules=completed,
            remaining_modules=get_remaining_modules(completed)
        ))
    
    return result