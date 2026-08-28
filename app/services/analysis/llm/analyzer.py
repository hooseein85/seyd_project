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

async def analyze_with_llm(content_text: str, candidate_policies: list, all_active_policies: list):
    """
    پرامپت را از کل قوانین می‌خواند، اما به LLM فقط کاندیداها را پاس می‌دهد.
    """
    if not candidate_policies:
        print("⚠️ [LLM] No candidate policies provided.")
        return None

    # 1. پیدا کردن پرامپت اختصاصی از بین قوانین کاندید شده
    raw_prompt = None
    for pol in candidate_policies:  # 🔴 باگ اینجا بود! قبلا all_active_policies بود
        p_text = getattr(pol, 'prompt', None)
        if p_text and len(p_text.strip()) > 10:
            raw_prompt = p_text
            break # پرامپت پیدا شد، از حلقه خارج شو
            
    if not raw_prompt:
        print("❌ [ERROR] No system prompt found for the candidate policies! Check database.")
        return None

    # 2. ساخت متون داینامیک فقط برای قوانین کاندید شده (کاهش توکن)
    policies_text = ""
    for pol in candidate_policies:
        code = getattr(pol, 'code', '000')
        title = getattr(pol, 'title', 'Unknown')
        prompt_desc = getattr(pol, 'prompt_description', getattr(pol, 'description', 'بدون توضیحات'))
        policies_text += f"- Code-{code}: {title} ({prompt_desc})\n"

    policies_text += "- Code-000: فاقد تطابق (محتوای سالم یا نامرتبط)\n"

    # 3. تزریق قوانین به پرامپت دیتابیس و اصلاح آکولادها
    system_prompt = raw_prompt.replace("{policies_text}", policies_text)
    system_prompt = system_prompt.replace("{{", "{").replace("}}", "}")

    # بقیه کدهای اتصال به Groq کاملاً مثل قبل است...
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