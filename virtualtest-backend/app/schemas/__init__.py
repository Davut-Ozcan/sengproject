# ============================================
# app/schemas/__init__.py - Schema Exports
# ============================================

# User schemas
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserProfile,
    UserStatusUpdate,
    UserRoleUpdate,
)

# Auth schemas
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    Token,
    TokenData,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    MessageResponse,
)

# Test schemas
from app.schemas.test import (
    ModuleName,
    CEFRLevel,
    TestSessionCreate,
    TestSessionResponse,
    TestSessionDetail,
    ModuleScoreCreate,
    ModuleScoreResponse,
    ModuleScoreDetail,
    ReadingSubmission,
    ListeningSubmission,
    SpeakingSubmission,
    WritingSubmission,
    ModuleResult,
    TestResult,
    Topic,
    TopicList,
    TestProgress,
    # YENİ EKLENENLER
    QuestionSchema,
    ReadingContentResponse,
    ListeningContentResponse,
    WritingContentResponse,
    SpeakingContentResponse,
    ModuleStartRequest,
    ModuleStartResponse,
    EvaluationRequest,
    EvaluationResponse,
)

__all__ = [
    # User
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "UserListResponse", "UserProfile", "UserStatusUpdate", "UserRoleUpdate",
    # Auth
    "LoginRequest", "LoginResponse", "RegisterRequest", "RegisterResponse",
    "Token", "TokenData", "PasswordChange", "PasswordReset",
    "PasswordResetConfirm", "MessageResponse",
     # Test
    "ModuleName", "CEFRLevel", "TestSessionCreate", "TestSessionResponse",
    "TestSessionDetail", "ModuleScoreCreate", "ModuleScoreResponse",
    "ModuleScoreDetail", "ReadingSubmission", "ListeningSubmission",
    "SpeakingSubmission", "WritingSubmission", "ModuleResult", "TestResult",
    "Topic", "TopicList", "TestProgress",
    # YENİ EKLENENLER
    "QuestionSchema", "ReadingContentResponse", "ListeningContentResponse",
    "WritingContentResponse", "SpeakingContentResponse", "ModuleStartRequest",
    "ModuleStartResponse", "EvaluationRequest", "EvaluationResponse",
]