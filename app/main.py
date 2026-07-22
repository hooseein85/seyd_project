from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import policy, assessment
from app.models.content import Content

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

app.include_router(policy.router)
app.include_router(assessment.router) # اضافه شدن روتر ارزیابی