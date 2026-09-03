# وزن‌های قابل تنظیم بر اساس Severity
# به املای دقیق شما (low, medium, high, critical) دقت شده است
SEVERITY_WEIGHTS = {
    "low": 25,
    "medium": 50,
    "high": 75,
    "critical": 100
}

def get_policy_weight(policy) -> int:
    """استخراج وزن قانون با اولویت ستون دیتابیس"""
    if hasattr(policy, 'weight') and policy.weight is not None:
        return int(policy.weight)
    
    # در صورت تعریف نشدن وزن، مقدار پیش‌فرض بر اساس severity بازمی‌گردد
    safe_severity = getattr(policy, 'severity', 'medium')
    safe_severity = safe_severity.lower().strip() if safe_severity else "medium"
    return SEVERITY_WEIGHTS.get(safe_severity, 50)

def get_severity_weight(severity: str) -> int:
    """وزن پایه را بر اساس فیلد severity دیتابیس برمی‌گرداند"""
    # تبدیل به حروف کوچک برای جلوگیری از خطای case-sensitivity
    safe_severity = severity.lower().strip() if severity else "low"
    return SEVERITY_WEIGHTS.get(safe_severity, 25)

def calculate_risk_score(severity_weight: int, confidence_score: float) -> float:
    """محاسبه نمره ریسک بر اساس وزن قانون و اطمینان مدل"""
    safe_confidence = max(0.0, min(float(confidence_score), 1.0))
    risk = severity_weight * safe_confidence
    return round(risk, 2)