import json
import re
from groq import AsyncGroq
# ایمپورت کلاس خودتان برای مدیریت کلیدها
from app.services.analysis.llm.api_key_manager import APIKeyManager

# همان کلیدهای تست خودتان
GROQ_API_KEYS = [
]

# ساخت یک نمونه سراسری (Global) از منیجر برای مدیریت وضعیت کلیدها در طول اجرای برنامه
key_manager = APIKeyManager(initial_keys=GROQ_API_KEYS)

async def init_llm_analyzer():
    """این تابع هنگام استارت خوردن Worker کافکا باید صدا زده شود"""
    await key_manager.setup_and_reset()
    print("🔑 [KEYS] API Key Manager Initialized.")

async def analyze_with_llm(content_text: str, active_policies: list):
    """
    این تابع محتوای خام را مستقیماً می‌گیرد، پالیسی‌ها را از آبجکت‌های دیتابیس داینامیک می‌سازد،
    پرامپت را می‌سازد و نتیجه را به فرمت JSON برمی‌گرداند.
    """
    
    # 1. ساخت متون داینامیک برای پرامپت از 3 فیلد دیتابیس (code, title, prompt_description)
    policies_text = ""
    for pol in active_policies:
        # چون active_policies آبجکت‌های SQLAlchemy هستند، از getattr استفاده می‌کنیم
        code = getattr(pol, 'code', '000')
        title = getattr(pol, 'title', 'Unknown')
        # اگر prompt_description خالی بود، از description استفاده کند
        prompt_desc = getattr(pol, 'prompt_description', getattr(pol, 'description', 'بدون توضیحات'))
        
        policies_text += f"- Code-{code}: {title} ({prompt_desc})\n"

    # اضافه کردن قانون پیش‌فرض برای حالت سالم
    policies_text += "- Code-000: فاقد تطابق (محتوای سالم یا نامرتبط)\n"

    # 2. پرامپت اصلی با تزریق داینامیک قوانین (توجه: آکولادهای JSON دوبرابر شده‌اند تا f-string پایتون ارور ندهد)
    system_prompt = f"""You are an expert forensic text classifier. Analyze the message for actionable criminal/security violations.

Tag Rules (Loaded Dynamically from Database):
{policies_text}

CRITICAL CONTEXT, ANTI-EVASION & CULTURAL SLURS RULES:
1. Masked Profanities: Users heavily mask profanities using dots, spaces, or abbreviations (e.g., "ک. کش", "ب.شرف"). You MUST decode these and treat them as direct insults.
2. Derogatory Metaphors & Nicknames: Users use culturally specific metaphors to mock death or insult groups/figures (e.g., using "کتلت" to mock death). These are STRICTLY considered direct insults (Code-105).
3. Sarcasm & Exaggeration (CRUCIAL): Users often use sarcasm, jokes, or extreme exaggerations in everyday banter (e.g., joking about destroying ships, military weapons, or hacking). You MUST differentiate between a genuine security leak/threat and a sarcastic joke. If the text is a joke, irony, or sarcastic exaggeration, it is NOT a violation.

Decision Logic:
1. Identify author `stance`:
   - "promoting": Author is directly executing, inciting, or actively using masked insults/derogatory metaphors.
   - "reporting_or_critic": Author is reporting, condemning, or criticizing without endorsing.
   - "neutral": Routine conversation, jokes, sarcasm, and non-serious exaggerations.
2. If `stance` is "reporting_or_critic" or "neutral": classification MUST be "clean".
3. If `stance` is "promoting": classification MUST be "violation".

EXAMPLES:
User: "فقط اون سلاحی که ناو رو غرق میکرد رو لو نداد و رفت"
Assistant: {{"classification": "clean", "policy_code": null, "reason": "این جمله یک کنایه و اغراق طنزآمیز در مکالمات روزمره است و افشای واقعیِ اطلاعات حساس محسوب نمی‌شود.", "confidence": 0.99, "evidence": []}}

User: "فلانی در سخنرانی‌اش توهین زشتی کرد و باعث ناراحتی مردم شد."
Assistant: {{"classification": "clean", "policy_code": null, "reason": "گزارش توهین شخص دیگری است و نویسنده مستقیماً فحاشی نکرده است.", "confidence": 0.91, "evidence": []}}

User: "اخجون موشعلی 2 ماهه کتلت شده"
Assistant: {{"classification": "violation", "policy_code": "105", "reason": "استفاده از القاب توهین‌آمیز (موشعلی) و تمسخر مرگ اشخاص با واژه کنایه‌آمیز (کتلت).", "confidence": 0.98, "evidence": ["موشعلی", "کتلت شده"]}}

User: "یه مشت بسیجی رو کتلت کردیم"
Assistant: {{"classification": "violation", "policy_code": "105", "reason": "استفاده از واژه توهین‌آمیز و کنایه‌آمیز (کتلت کردیم) برای تمسخر و هتاکی.", "confidence": 0.96, "evidence": ["بسیجی رو کتلت کردیم"]}}

You MUST output ONLY a valid JSON object. No markdown, no text outside JSON.
Strict JSON Format:
{{
  "classification": "violation" or "clean",
  "policy_code": "The matching code number (or null if clean)",
  "reason": "دلیل منطقی به زبان فارسی",
  "confidence": 0.95,
  "evidence": ["جمله مشکوک از متن"]
}}"""

    # دریافت کلید آزاد از منیجر
    current_ai_key = await key_manager.get_free_key()
    if not current_ai_key:
        print("😴 [API KEYS] Exhausted. Cannot analyze at the moment.")
        return None 

    client = AsyncGroq(api_key=current_ai_key['api_key'])
    
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Input Message:\n\"\"\"\n{content_text}\n\"\"\""}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.0, 
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )
        
        # آزادسازی کلید پس از موفقیت
        await key_manager.release_key(current_ai_key['id'])
        
        raw_output = response.choices[0].message.content
        
        return json.loads(raw_output)
            
    except Exception as e: 
        error_msg = str(e)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            await key_manager.handle_rate_limit(current_ai_key['id'], error_msg)
        else:
            await key_manager.release_key(current_ai_key['id'])
            print(f"❌ [GROQ ERROR] {error_msg}")
        
        return None