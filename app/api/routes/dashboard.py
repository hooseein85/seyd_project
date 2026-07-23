from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.dependencies import get_db
from app.models.violation import Violation
from app.models.account import Account
from app.models.telegram_chat import TelegramChat
from app.models.assessment import Assessment
from app.models.policy import Policy

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)):
    # ۱. شمارش کاربران و بسترها
    total_accounts = db.query(Account).count()
    total_groups = db.query(TelegramChat).count()
    
    # ۲. شمارش کلی تخلفات
    total_violations = db.query(Violation).count()
    
    # ۳. شمارش بر اساس وضعیت (Status)
    pending_reviews = db.query(Violation).filter(Violation.action_status == 'pending').count()
    approved_suggestions = db.query(Violation).filter(Violation.action_status == 'approved').count()
    rejected_suggestions = db.query(Violation).filter(Violation.action_status == 'rejected').count()
    
    # ۴. شمارش تخلفات بحرانی (نیازمند Join با جدول ارزیابی)
    critical_violations = db.query(Violation).join(
        Assessment, Violation.assessment_id == Assessment.id
    ).filter(Assessment.priority == 'critical').count()

    # خروجی نهایی به همراه حذف اعداد فِیک قبلی
    return [
        {"key": "total_users", "label": "تعداد کل کاربران", "value": total_accounts, "tone": "neutral"},
        # اگر در آینده فیلدی برای کاربران و گروه‌های "تحت پایش" اضافه کردید، می‌توانید آن را اینجا فیلتر کنید
        {"key": "monitored_users", "label": "کاربران تحت پایش", "value": 0, "tone": "success"}, 
        {"key": "total_groups", "label": "تعداد کل بسترهای تلگرام", "value": total_groups, "tone": "neutral"},
        {"key": "monitored_groups", "label": "بسترهای تحت پایش", "value": 0, "tone": "info"}, 
        
        {"key": "critical_violations", "label": "تخلفات بحرانی", "value": critical_violations, "tone": "critical"},
        {"key": "pending_reviews", "label": "در انتظار بررسی", "value": pending_reviews, "tone": "warning"},
        {"key": "today_violations", "label": "کل تخلفات (تا امروز)", "value": total_violations, "tone": "critical"},
        {"key": "avg_review_time", "label": "میانگین زمان بررسی", "value": 0, "hint": "ثانیه", "tone": "info"}, # این مورد نیاز به محاسبه تفاضل زمان دارد
        
        {"key": "approved_suggestions", "label": "اقدامات تایید شده", "value": approved_suggestions, "tone": "success"},
        {"key": "rejected_suggestions", "label": "اقدامات رد شده", "value": rejected_suggestions, "tone": "warning"},
    ]

# ... (متد get_policy_categories که در مرحله قبل نوشتیم اینجا باقی می‌ماند) ...
@router.get("/policy-categories")
def get_policy_categories(db: Session = Depends(get_db)):
    # یک کوئری Group By برای شمارش تخلفات بر اساس هر قانون
    results = db.query(
        Policy.title,
        Policy.code,
        func.count(Violation.id).label('total_count')
    ).join(
        Violation, Policy.id == Violation.policy_id
    ).group_by(
        Policy.title, Policy.code
    ).all()

    # یک لیست رنگ برای اینکه نمودار خوشگل بماند
    colors = ["#ef4444", "#f97316", "#3b82f6", "#eab308", "#8b5cf6", "#10b981", "#64748b"]
    
    categories = []
    for index, row in enumerate(results):
        categories.append({
            "code": row.code or f"P{index}",
            "title": row.title or "سایر",
            "count": row.total_count,
            "color": colors[index % len(colors)] # اختصاص رنگ به ترتیب
        })

    # اگر در دیتابیس هیچ تخلفی نبود، یک دیتای خالی بفرست که نمودار صفر شود
    if not categories:
        return [{"code": "0", "title": "بدون دیتا", "count": 1, "color": "#334155"}]

    return categories