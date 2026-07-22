from fastapi import FastAPI
from app.api.routes import policy
from app.db.session import engine
from app.db.base import Base

# ساخت جداول دیتابیس (برای MVP فعلی. بعداً از Alembic استفاده می‌کنیم)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelligence & Governance Platform API",
    description="Backend API for Investigation Workspace",
    version="1.0.0"
)

# ثبت روترها
app.include_router(policy.router)