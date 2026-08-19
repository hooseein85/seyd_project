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
    
    # ۱. گروه‌های تحت پایش (فعلاً برابر با کل بسترهای تلگرام)
    monitored_groups = db.query(TelegramChat).count()
    
    # ۲. محتوای بررسی‌شده (فعلاً صفر تا زمانی که سرویس پایشگر اضافه شود)
    checked_content = 0 
    
    # ۳. محتوای مشکوک (کل رکوردهای جدول ارزیابی)
    suspicious_content = db.query(Assessment).count()
    
    # ۵. صف ارزیابی (محتواهایی که وضعیتشان queued است)
    content_waiting_for_anlaysis = db.query(Assessment).filter(Assessment.status == 'queued').count()
    
    # ۴. محتوای ارزیابی‌شده (محتواهای مشکوک منهای آن‌هایی که در صف هستند)
    analyzed_content = suspicious_content - content_waiting_for_anlaysis
    
    # ۶. تخلفات شناسایی‌شده (کل تخلفات)
    detected_violation = db.query(Violation).count()
    
    # ۷. تخلفات بحرانی (تخلفاتی که اولویت ارزیابی آن‌ها بحرانی است)
    critical_violation = db.query(Violation).join(
        Assessment, Violation.assessment_id == Assessment.id
    ).filter(Assessment.priority_score >= 70).count()
    
    # ۸. اقدامات تأییدشده (وضعیت approved)
    confirmed_actions = db.query(Violation).filter(Violation.action_status == 'approved').count()
    
    # ۹. عدم اقدام‌ها (تخلفاتی که کارشناس برایشان "عدم اقدام" ثبت کرده است)
    no_actions = db.query(Violation).filter(Violation.expert_action == 'no_action').count()
    
    # ۱۰. محاسبه درصد تشخیص صحیح سیستم
    # الف) تعداد مواردی که نظر کارشناس با پیشنهاد پیش‌فرض قانون یکسان بوده است
    correct_count = db.query(Violation).join(
        Policy, Violation.policy_id == Policy.id
    ).filter(Violation.expert_action == Policy.default_recomned).count()
    
    # ب) کل مواردی که کارشناس روی آن‌ها اقدام انجام داده (خالی نیست)
    total_decided = db.query(Violation).filter(Violation.expert_action.isnot(None)).count()
    
    # ج) محاسبه درصد (اگر تصمیمی گرفته نشده بود، صفر برمی‌گرداند تا ارور ندهد)
    success_rate = round((correct_count / total_decided) * 100) if total_decided > 0 else 0

    return [
        {
            "key": "monitored_groups",
            "label": "گروه‌های تحت پایش",
            "value": monitored_groups,
            "tone": "info"
        },
        {
            "key": "checked_content",
            "label": "محتوای بررسی‌شده",
            "value": checked_content,
            "tone": "info"
        },
        {
            "key": "suspicious_content",
            "label": "محتوای مشکوک",
            "value": suspicious_content,
            "tone": "info"
        },
        {
            "key": "analyzed_content",
            "label": "محتوای ارزیابی‌شده",
            "value": analyzed_content,
            "tone": "info"
        },
        {
            "key": "content_waiting_for_anlaysis",
            "label": "صف ارزیابی",
            "value": content_waiting_for_anlaysis,
            "tone": "warning"
        },
        {
            "key": "detected_violation",
            "label": "تخلفات شناسایی‌شده",
            "value": detected_violation,
            "tone": "neutral"
        },
        {
            "key": "critical_violation",
            "label": "تخلفات بحرانی",
            "value": critical_violation,
            "tone": "critical"
        },
        {
            "key": "confirmed_actions",
            "label": "اقدامات تأییدشده",
            "value": confirmed_actions,
            "tone": "success"
        },
        {
            "key": "no_actions",
            "label": "عدم اقدام ها",
            "value": no_actions,
            "tone": "neutral"
        },
        {
            "key": "success_recomend_actions",
            "label": "تشخیص صحیح سیستم",
            "value": success_rate,
            "tone": "success",
            "hint": "%"
        }
    ]

# ... (ادامه کدها مثل get_policy_categories سر جایش بماند)
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

    # ۱. تعریف رنگ‌های ثابت و اختصاصی برای ۵ قانون اصلی
    specific_colors = {
        "102": "#ef4444",  # قرمز برای "فراخوان"
        "101": "#f97316",  # نارنجی برای "افشای اطلاعات حساس"
        "105": "#64748b",  # خاکستری برای "توهین"
        "103": "#0ea5e9",  # آبی روشن (Sky Blue) برای "درخواست فیلم" (کد را با دیتابیس هماهنگ کنید)
        "104": "#10b981",  # سبز (Emerald) برای "عضویت"
    }
    
    # ۲. رنگ‌های جایگزین برای قوانینی که کدهایشان در لیست بالا نیست (از ۱۰۶ به بعد)
    fallback_colors = ["#3b82f6", "#eab308", "#8b5cf6", "#ec4899"]
    
    categories = []
    for index, row in enumerate(results):
        # ۳. پیدا کردن رنگ اختصاصی، یا استفاده از رنگ‌های جایگزین در صورت نبودن کد
        assigned_color = specific_colors.get(row.code, fallback_colors[index % len(fallback_colors)])
        
        categories.append({
            "code": row.code or f"P{index}",
            "title": row.title or "سایر",
            "count": row.total_count,
            "color": assigned_color
        })

    # اگر در دیتابیس هیچ تخلفی نبود، یک دیتای خالی بفرست که نمودار صفر شود
    if not categories:
        return [{"code": "0", "title": "بدون دیتا", "count": 1, "color": "#334155"}]

    return categories