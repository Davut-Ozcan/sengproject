# ============================================
# app/repositories/test_repository.py - Test Result Repository
# ============================================
#
# UML'deki Karşılığı: TestResultRepository
#
# Ne yapıyor?
# - Test sonuçlarını veritabanına kaydeder
# - Modül puanlarını yönetir
# - Final CEFR seviyesini kaydeder
#
# Metodlar (UML'den):
# - saveScore(studentID, module, score): Modül puanı kaydeder
# - getScores(studentID): Tüm puanları getirir
# - saveFinalResult(studentID, level): Final sonucu kaydeder
# ============================================

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime


class TestResultRepository:
    """
    UML: TestResultRepository
    
    Test sonuçları veritabanı işlemleri.
    """
    
    async def create_session(
        self, 
        db: AsyncSession, 
        student_id: int
    ) -> Optional[any]:
        """
        Yeni test oturumu oluşturur.
        
        Kullanım:
            session = await test_repository.create_session(db, student_id=5)
        
        Input:
            db: Veritabanı session
            student_id: Öğrenci ID
        
        Output:
            TestSession objesi
        """
        
        from app.models import TestSession
        
        try:
            new_session = TestSession(
                student_id=student_id,
                start_date=datetime.utcnow(),
                is_completed=False
            )
            
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            
            print(f"✅ TestRepository: Oturum oluşturuldu (Student:{student_id})")
            return new_session
            
        except Exception as e:
            await db.rollback()
            print(f"❌ TestRepository Create Session Error: {e}")
            return None
    
    
    async def save_score(
        self, 
        db: AsyncSession,
        student_id: int,
        session_id: int,
        module: str,
        score: float,
        cefr_level: Optional[str] = None
    ) -> bool:
        """
        UML: +saveScore(studentID: int, module: string, score: float): void
        
        Modül puanını kaydeder.
        
        Kullanım:
            await test_repository.save_score(
                db,
                student_id=5,
                session_id=1,
                module="reading",
                score=85.5,
                cefr_level="B2"
            )
        
        Input:
            db: Veritabanı session
            student_id: Öğrenci ID
            session_id: Test oturumu ID
            module: "reading", "listening", "speaking", "writing"
            score: 0-100 arası puan
            cefr_level: Modül CEFR seviyesi (opsiyonel)
        
        Output:
            bool: Başarılı mı?
        """
        
        from app.models import ModuleScore
        
        try:
            new_score = ModuleScore(
                session_id=session_id,
                module_name=module.lower(),
                score=score,
                cefr_level=cefr_level,
                completed_at=datetime.utcnow()
            )
            
            db.add(new_score)
            await db.commit()
            
            print(f"✅ TestRepository: Puan kaydedildi ({module}: {score})")
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"❌ TestRepository Save Score Error: {e}")
            return False
    
    
    async def get_scores(
        self, 
        db: AsyncSession, 
        student_id: int,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        UML: +getScores(studentID: int): TestResult
        
        Öğrencinin puanlarını getirir.
        
        Kullanım:
            scores = await test_repository.get_scores(db, student_id=5)
            print(scores)
            # {
            #     "reading": {"score": 85, "cefr": "B2"},
            #     "listening": {"score": 75, "cefr": "B1"},
            #     ...
            # }
        
        Input:
            db: Veritabanı session
            student_id: Öğrenci ID
            session_id: Belirli oturum (opsiyonel)
        
        Output:
            Dict: Modül puanları
        """
        
        from app.models import TestSession, ModuleScore
        
        try:
            # Önce session bul
            query = select(TestSession).where(TestSession.student_id == student_id)
            
            if session_id:
                query = query.where(TestSession.id == session_id)
            else:
                # En son oturumu al
                query = query.order_by(TestSession.start_date.desc())
            
            result = await db.execute(query)
            session = result.scalar_one_or_none()
            
            if not session:
                return {}
            
            # Puanları al
            scores_result = await db.execute(
                select(ModuleScore).where(ModuleScore.session_id == session.id)
            )
            scores = scores_result.scalars().all()
            
            # Dict olarak düzenle
            result_dict = {}
            for score in scores:
                result_dict[score.module_name] = {
                    "score": score.score,
                    "cefr": score.cefr_level,
                    "completed_at": score.completed_at.isoformat() if score.completed_at else None
                }
            
            return result_dict
            
        except Exception as e:
            print(f"❌ TestRepository Get Scores Error: {e}")
            return {}
    
    
    async def save_final_result(
        self, 
        db: AsyncSession,
        student_id: int,
        session_id: int,
        overall_score: float,
        cefr_level: str
    ) -> bool:
        """
        UML: +saveFinalResult(studentID: int, level: string): void
        
        Final sonucu kaydeder ve oturumu tamamlar.
        
        Kullanım:
            await test_repository.save_final_result(
                db,
                student_id=5,
                session_id=1,
                overall_score=82.5,
                cefr_level="B2"
            )
        
        Input:
            db: Veritabanı session
            student_id: Öğrenci ID
            session_id: Test oturumu ID
            overall_score: Genel puan ortalaması
            cefr_level: Final CEFR seviyesi
        
        Output:
            bool: Başarılı mı?
        """
        
        from app.models import TestSession
        
        try:
            await db.execute(
                update(TestSession)
                .where(TestSession.id == session_id)
                .values(
                    is_completed=True,
                    completion_date=datetime.utcnow(),
                    overall_score=overall_score,
                    overall_cefr_level=cefr_level
                )
            )
            await db.commit()
            
            print(f"✅ TestRepository: Final sonuç kaydedildi ({cefr_level})")
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"❌ TestRepository Save Final Error: {e}")
            return False
    
    
    async def get_session(
        self, 
        db: AsyncSession, 
        session_id: int
    ) -> Optional[any]:
        """
        Test oturumunu getirir.
        
        Kullanım:
            session = await test_repository.get_session(db, session_id=1)
        """
        
        from app.models import TestSession
        
        result = await db.execute(
            select(TestSession).where(TestSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    
    async def get_active_session(
        self, 
        db: AsyncSession, 
        student_id: int
    ) -> Optional[any]:
        """
        Öğrencinin aktif (tamamlanmamış) oturumunu getirir.
        
        Kullanım:
            session = await test_repository.get_active_session(db, student_id=5)
        """
        
        from app.models import TestSession
        
        result = await db.execute(
            select(TestSession)
            .where(TestSession.student_id == student_id)
            .where(TestSession.is_completed == False)
            .order_by(TestSession.start_date.desc())
        )
        return result.scalar_one_or_none()
    
    
    async def get_completed_modules(
        self, 
        db: AsyncSession, 
        session_id: int
    ) -> List[str]:
        """
        Tamamlanan modülleri listeler.
        
        Kullanım:
            modules = await test_repository.get_completed_modules(db, session_id=1)
            # ["reading", "listening"]
        """
        
        from app.models import ModuleScore
        
        result = await db.execute(
            select(ModuleScore.module_name)
            .where(ModuleScore.session_id == session_id)
        )
        return [row[0] for row in result.fetchall()]
    
    
    async def get_student_history(
        self, 
        db: AsyncSession, 
        student_id: int,
        limit: int = 10
    ) -> List[any]:
        """
        Öğrencinin test geçmişini getirir.
        
        Kullanım:
            history = await test_repository.get_student_history(db, student_id=5)
        """
        
        from app.models import TestSession
        
        result = await db.execute(
            select(TestSession)
            .where(TestSession.student_id == student_id)
            .order_by(TestSession.start_date.desc())
            .limit(limit)
        )
        return result.scalars().all()


# Singleton instance
test_repository = TestResultRepository()