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
    system_prompt = f"""<ROLE>
You are an Enterprise Content Safety Classifier. Your mission is to evaluate input text against active security policies using strict binary decision boundaries. Flag ONLY severe, acute violations (Threshold = High). Output ONLY a valid single-line JSON.
</ROLE>

<SAFETY_TAXONOMY>
[Active Policies from Database]:
{policies_text}

[Target Entities (Red Line)]:
["موشعلی", "موشتبا", "عرزشی", "ارزشی", "بسیجی", "آخوند", "سپاه"] (including death metaphors like "کتلت").
</SAFETY_TAXONOMY>

<DECISION_BOUNDARIES>
[VIOLATION CRITERIA (Label: "violation") -> ALL conditions must be True (AND Logic)]:
1. Active Policy Match: The behavior matches a policy explicitly defined in <SAFETY_TAXONOMY>. If no active policy code matches, output "clean" with policy_code: null.
2. Target Intersection: The message directly attacks, threatens, or dehumanizes entities in [Target Entities].
3. Direct Stance: The author is PROMOTING, INCITING, or DIRECTLY EXECUTING severe masked/explicit profanity (e.g., "خار...صه", "ک.کش") or direct violent harm.

[CLEAN CRITERIA (Label: "clean") -> ANY of these conditions makes the result Clean]:
1. Inactive Policy: The behavior is offensive, but no active policy code exists in <SAFETY_TAXONOMY>.
2. Stance - Reporting/Quoting: Author is quoting news, analyzing, or condemning someone else's violation without endorsing it.
3. Stance - Harmless Banter: Everyday sarcasm, political satire, general complaints, or jokes without acute profanity.
4. Non-Target Conflict: Severe swearing or mutual fighting between ordinary citizens without targeting [Target Entities].
</DECISION_BOUNDARIES>

<NORMALIZATION_RULES>
Before classification, decode character extensions (e.g., "خاااار"), internal punctuation/spaces (e.g., "ب.شرف", "ک...ص"), and Persian/Arabic character variations.
</NORMALIZATION_RULES>

<CONFIDENCE_CALIBRATION>
Calculate the `confidence` score strictly based on evidence clarity:
- 0.90 - 1.00: EXPLICIT & UNAMBIGUOUS. Direct, raw words without masking or ambiguity.
- 0.75 - 0.89: OBFUSCATED / CONTEXTUAL. Masked slurs (dots, spaces, leetspeak) or slang requiring contextual decoding.
- 0.50 - 0.74: BORDERLINE / AMBIGUOUS. Sarcastic tone, unclear targets, or debatable intent.
- NEVER default all classifications to 0.95+. Calibrate accurately.
</CONFIDENCE_CALIBRATION>

<OUTPUT_SCHEMA>
{{
  "classification": "violation" | "clean",
  "policy_code": "CODE_STRING" | null,
  "reason": "دلیل بسیار کوتاه در حداکثر 15 کلمه به فارسی",
  "confidence": 0.0-1.0,
  "evidence": ["exact_violating_substrings"]
}}
</OUTPUT_SCHEMA>

<FEW_SHOT_BENCHMARKS>
Input: "این عرزشی‌های خارکصده رو باید به رگبار بست"
Output: {{"classification":"violation","policy_code":"105","reason":"فحاشی کاملاً صریح و تهدید مستقیم جانی","confidence":0.98,"evidence":["عرزشی‌های خارکصده","به رگبار بست"]}}

Input: "همین م.وش.ع.لی اگه زنده بود الان وضع این نبود"
Output: {{"classification":"violation","policy_code":"105","reason":"استفاده از لقب توهین‌آمیز با استتار نقطه‌ای","confidence":0.82,"evidence":["م.وش.ع.لی"]}}

Input: "عرزشی جان یکم کمتر ساندیس بزن برات خوب نیست"
Output: {{"classification":"clean","policy_code":null,"reason":"طعنه و کنایه سیاسی بدون رکاکت یا تهدید حاد","confidence":0.65,"evidence":[]}}

Input: "مرتیکه دزد بی شرف کیفمو زد"
Output: {{"classification":"clean","policy_code":null,"reason":"نزاع شخصی فاقد هدف حاکمیتی","confidence":0.95,"evidence":[]}}

Input: "خبرگزاری تسنیم نوشته فردی به مقدسات توهین کرده است"
Output: {{"classification":"clean","policy_code":null,"reason":"نقل‌قول و گزارشگری رسمی فاقد نیت هتاکی","confidence":0.99,"evidence":[]}}
</FEW_SHOT_BENCHMARKS>"""

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