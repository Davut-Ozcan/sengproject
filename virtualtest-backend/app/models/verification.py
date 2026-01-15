from sqlalchemy import Column, String, DateTime
from app.core.database import Base
from datetime import datetime, timedelta

class VerificationCode(Base):
    __tablename__ = "verification_codes"
    
    email = Column(String, primary_key=True, index=True)
    code = Column(String, nullable=False)
    # DİKKAT: auth.py içindeki kodunla uyumlu olması için 'expires_at' yapıyoruz
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))