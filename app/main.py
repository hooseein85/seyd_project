from fastapi import FastAPI ,Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.dependencies import get_current_user
from app.api.routes import policy, assessment, content, violation, dashboard, auth
from app.models.content import Content
from app.models.telegram_chat import TelegramChat
from app.models.account import Account
from app.models.violation import Violation
from app.models.user import User

app = FastAPI(
    title="Intelligence & Governance Platform API",
    description="Backend API for Investigation Workspace",
    version="1.0.0"
)

# اضافه کردن تنظیمات CORS برای ارتباط با فرانت‌اند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # در محیط پروداکشن باید آدرس دقیق فرانت‌اند جایگزین شود
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)

protected_lock = [Depends(get_current_user)]

app.include_router(policy.router, dependencies=protected_lock)
app.include_router(assessment.router, dependencies=protected_lock)
app.include_router(content.router, dependencies=protected_lock)
app.include_router(violation.router, dependencies=protected_lock)
app.include_router(dashboard.router, dependencies=protected_lock)
