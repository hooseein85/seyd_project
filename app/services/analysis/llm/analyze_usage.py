import pandas as pd
import numpy as np

FILE_NAME = "token_usage_logs.csv"

def calculate_capacity():
    try:
        df = pd.read_csv(FILE_NAME)
    except FileNotFoundError:
        print(f"❌ فایل {FILE_NAME} هنوز ایجاد نشده است. بگذارید ورکر کافکا چند درخواست ثبت کند.")
        return

    total_requests = len(df)
    if total_requests == 0:
        print("فایل لاگ خالی است.")
        return

    avg_prompt = df['prompt_tokens'].mean()
    avg_completion = df['completion_tokens'].mean()
    avg_total = df['total_tokens'].mean()
    p95_total = np.percentile(df['total_tokens'], 95)

    print("=" * 55)
    print(f"📈 گزارش مصرف واقعی توکن (بر اساس {total_requests} درخواست)")
    print("=" * 55)
    print(f"• میانگین توکن ورودی (Prompt):    {avg_prompt:.1f}")
    print(f"• میانگین توکن خروجی (Completion): {avg_completion:.1f}")
    print(f"• میانگین توکن کل هر درخواست:      {avg_total:.1f}")
    print(f"• صدک ۹۵ام مصرف توکن (P95):       {p95_total:.1f}")
    print("=" * 55)

    # مقادیر لیمیت فرضی اکانت‌های رایگان (می‌توانید مطابق پنل Groq تنظیم کنید)
    # معمولا اکانت رایگان: TPD = 500,000 توکن در روز یا RPD = 14,400 ریکوئست
    DAILY_TOKEN_LIMIT_PER_KEY = 500_000 
    
    # ظرفیت پردازش هر کلید در روز
    req_per_key = DAILY_TOKEN_LIMIT_PER_KEY / avg_total

    print("🧮 برآورد تعداد کلیدهای لازم برای حجم‌های مختلف:")
    print(f"(فرض ظرفیت روزانه هر کلید: {int(req_per_key):,} درخواست بر اساس سقف توکن)\n")

    targets = [1_000, 5_000, 10_000, 25_000, 50_000]
    for target in targets:
        # با احتساب ۲۰٪ ضریب اطمینان برای اسپایک‌ها و خطاهای شبکه
        keys_needed = int(np.ceil((target / req_per_key) * 1.2))
        print(f"  - لود {target:,} درخواست در روز 👈  نیاز به حداقل {keys_needed} کلید فعال")
    print("=" * 55)

if __name__ == "__main__":
    calculate_capacity()