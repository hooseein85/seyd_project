import json
import os
import csv
from datetime import datetime
import asyncio
from groq import AsyncGroq
from app.services.analysis.llm.api_key_manager import APIKeyManager

# فایل لاگ مصرف توکن
TOKEN_LOG_FILE = "token_usage_logs.csv"

# همان کلیدهای تست خودتان
GROQ_API_KEYS = [
    # کلیدهای شما اینجا قرار می‌گیرد
]

key_manager = APIKeyManager(initial_keys=GROQ_API_KEYS)

def _append_token_log(log_data: dict):
    """ذخیره امن و ترتیبی لاگ توکن‌ها در فایل CSV"""
    file_exists = os.path.isfile(TOKEN_LOG_FILE)
    headers = [
        "timestamp", 
        "model", 
        "candidate_count", 
        "content_length", 
        "prompt_tokens", 
        "completion_tokens", 
        "total_tokens", 
        "key_id"
    ]
    
    with open(TOKEN_LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_data)

async def init_llm_analyzer():
    """این تابع هنگام استارت خوردن Worker کافکا باید صدا زده شود"""
    await key_manager.setup_and_reset()
    print("🔑 [KEYS] API Key Manager Initialized.")

async def _evaluate_single_policy(content_text: str, policy, key_manager) -> dict | None:
    """
    ارزیابی محتوا با پرامپت اختصاصی یک قانون (ایزوله و مستقل) و لاگ توکن‌های همان قانون
    """
    prompt = getattr(policy, 'prompt', None)
    if not prompt or len(prompt.strip()) < 10:
        return None

    current_ai_key = await key_manager.get_free_key()
    if not current_ai_key:
        print("😴 [API KEYS] Exhausted. Cannot analyze at the moment.")
        return None

    client = AsyncGroq(api_key=current_ai_key['api_key'])

    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Input Message:\n\"\"\"\n{content_text}\n\"\"\""}
            ],
            model="openai/gpt-oss-120b", 
            temperature=0.0,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        
        # استخراج و ذخیره متادیتای مصرف توکن برای این ریکوئست خاص
        if hasattr(response, 'usage') and response.usage:
            usage_data = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "model": "openai/gpt-oss-120b",
                "candidate_count": 1,
                "content_length": len(content_text.split()), 
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "key_id": current_ai_key.get('id', 'unknown')
            }
            await asyncio.to_thread(_append_token_log, usage_data)
            print(f"📊 [USAGE - Policy {getattr(policy, 'code', '???')}] Prompt: {response.usage.prompt_tokens} | Output: {response.usage.completion_tokens} | Total: {response.usage.total_tokens}")
        
        await key_manager.release_key(current_ai_key['id'])
        raw_output = response.choices[0].message.content
        result = json.loads(raw_output)
        
        # ثبت دقیق کدی که ارزیابی شده برای جلوگیری از توهم LLM
        result['evaluated_code'] = str(getattr(policy, 'code', '000'))
        return result

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            await key_manager.handle_rate_limit(current_ai_key['id'], error_msg)
        else:
            await key_manager.release_key(current_ai_key['id'])
            print(f"❌ [GROQ ERROR on Policy {getattr(policy, 'code', '???')}]: {error_msg}")
        return None

async def analyze_with_llm(content_text: str, candidate_policies: list, all_active_policies: list = None):
    """
    اجرای موازی پرامپت‌ها و تجمیع تخلفات متناسب با ساختار فرانت‌اند
    """
    if not candidate_policies:
        print("⚠️ [LLM] No candidate policies provided.")
        return None

    # ۱. اجرای هم‌زمان (موازی) ارزیابی روی تمام قوانین کاندید شده
    tasks = [
        _evaluate_single_policy(content_text, pol, key_manager)
        for pol in candidate_policies
    ]
    results = await asyncio.gather(*tasks)

    valid_results = [r for r in results if r is not None]
    if not valid_results:
        return None

    # ۲. جداسازی خروجی‌هایی که تخلف تشخیص داده شده‌اند
    violations = [r for r in valid_results if r.get("classification") == "violation"]

    # ۳. پردازش و آماده‌سازی داده‌ها در صورت وجود تخلف
    if violations:
        matched_rules = []
        combined_reasons = []
        all_evidence = []
        
        for v in violations:
            code = v.get("evaluated_code", str(v.get("policy_code", "000")))
            
            # استخراج عنوان قانون از لیست کاندیداها برای فرانت‌اند
            policy_title = "عنوان نامشخص"
            for p in candidate_policies:
                if str(getattr(p, 'code', '')) == code:
                    policy_title = getattr(p, 'title', policy_title)
                    break
                    
            # ساختار دقیق برای رندر شدن در UI فرانت‌اند
            matched_rules.append({
                "code": code,
                "title": policy_title
            })
            
            combined_reasons.append(f"قانون {code}: {v.get('reason', '')}")
            
            # تجمیع شواهد بدون تکرار کلمات
            for ev in v.get("evidence", []):
                if ev not in all_evidence:
                    all_evidence.append(ev)
                    
        max_confidence = max([v.get("confidence", 0.0) for v in violations])
        
        # فرمت‌بندی دلیل
        if len(violations) == 1:
            final_reason = violations[0].get("reason", "")
        else:
            final_reason = " | ".join(combined_reasons)

        return {
            "classification": "violation",
            "matchedRules": matched_rules,  # تغذیه مستقیم آرایه برای فرانت‌اند
            "reason": final_reason,
            "confidence": max_confidence,
            "evidence": all_evidence,
            "policy_code": ", ".join([m["code"] for m in matched_rules])
        }

    # ۴. اگر هیچ تخلفی پیدا نشد، اولین نتیجه clean را برگردان
    return valid_results[0]