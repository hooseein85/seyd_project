# وزن‌های قابل تنظیم بر اساس Severity
# به املای دقیق شما (low, medium, high, critical) دقت شده است
SEVERITY_WEIGHTS = {
    "low": 25,
    "medium": 50,
    "high": 75,
    "critical": 100
}

def get_severity_weight(severity: str) -> int:
    """وزن پایه را بر اساس فیلد severity دیتابیس برمی‌گرداند"""
    # تبدیل به حروف کوچک برای جلوگیری از خطای case-sensitivity
    safe_severity = severity.lower().strip() if severity else "low"
    return SEVERITY_WEIGHTS.get(safe_severity, 25)

def calculate_risk_score(severity_weight: int, confidence_score: float) -> float:
    """
    محاسبه نمره ریسک در فاز MVP
    فرمول: وزن پایه تخلف × میزان اطمینان هوش مصنوعی
    """
    # اطمینان از اینکه confidence بین 0 و 1 است
    safe_confidence = max(0.0, min(float(confidence_score), 1.0))
    
    risk = severity_weight * safe_confidence
    return round(risk, 2)