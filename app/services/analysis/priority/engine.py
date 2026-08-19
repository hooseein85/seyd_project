# app/services/analysis/priority/engine.py

def calculate_account_history_score(previous_violations_count: int) -> float:
    """
    تبدیل تعداد تخلفات قبلی کاربر به یک نمره بین ۰ تا ۱۰۰ برای فاز MVP.
    منطق ساده: هر تخلف قبلی ۲۰ امتیاز ریسک به سابقه کاربر اضافه می‌کند.
    """
    score = previous_violations_count * 20.0
    return min(score, 100.0)

def calculate_priority_score(severity_weight: int, account_history_score: float, risk_score: float) -> float:
    """
    محاسبه نمره اولویت بر اساس فرمول مصوب سند فاز ۱
    """
    # اعمال ضرایب فرمول
    w_violation = 0.4 * severity_weight
    w_history = 0.2 * account_history_score
    w_risk = 0.4 * risk_score
    
    priority = w_violation + w_history + w_risk
    
    # اطمینان از اینکه نمره نهایی از ۱۰۰ بیشتر نشود
    return round(min(priority, 100.0), 2)