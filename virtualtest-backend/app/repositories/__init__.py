# ============================================
# app/repositories/__init__.py - Repository Exports
# ============================================

from app.repositories.user_repository import user_repository, UserRepository
from app.repositories.test_repository import test_repository, TestResultRepository

__all__ = [
    "user_repository",
    "test_repository",
    "UserRepository",
    "TestResultRepository",
]