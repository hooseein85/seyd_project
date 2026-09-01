import asyncio
import json
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session
import hashlib

# ایمپورت‌های دیتابیس
from app.db.session import SessionLocal
from app.models.assessment import Assessment
from app.models.account import Account
from app.models.telegram_chat import TelegramChat
from app.models.content import Content
from app.models.policy import Policy
from app.models.violation import Violation 

# ایمپورت هوش مصنوعی
from app.services.analysis.llm.analyzer import analyze_with_llm, init_llm_analyzer
# ایمپورت موتورهای ریسک و اولویت
from app.services.analysis.risk.engine import get_severity_weight, calculate_risk_score
from app.services.analysis.priority.engine import calculate_account_history_score, calculate_priority_score

KAFKA_TOPIC = "assessment-created"
KAFKA_BROKER = "localhost:9092"

async def process_pipeline(payload: dict):
    """
    این تابع چرخه را مدیریت می‌کند (دیتابیس + هوش مصنوعی مستقیم)
    """
    assessment_id = payload.get("assessment_id")
    content_id = payload.get("content_id")
    
    # 1. گرفتن کلمات کلیدی از کافکا و پاکسازی فاصله‌های اضافه (Strip)
    matched_keywords_raw = payload.get("matched_keywords", [])
    matched_keywords = [kw.strip().lower() for kw in matched_keywords_raw if kw and kw.strip()]
    
    # 2. عملیات همگام دیتابیس (گرفتن دیتا)
    def fetch_data():
        db: Session = SessionLocal()
        try:
            assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
            if not assessment or assessment.status.lower() in ["clean", "violation_detected", "analyzing"]:
                return None, None, None, db
            
            assessment.status = "analyzing"
            db.commit()
            
            content = db.query(Content).filter(Content.id == content_id).first()
            active_policies = db.query(Policy).filter(Policy.status.ilike("ACTIVE")).all()
            
            return assessment, content, active_policies, db
        except Exception as e:
            db.rollback()
            return None, None, None, db

    assessment, content, active_policies, db = await asyncio.to_thread(fetch_data)
    
    if not assessment or not content:
        print(f"🛑 [STOP] Invalid Assessment/Content or already processed.")
        db.close()
        return

    print(f"✅ [DB] Status -> analyzing | Content: {content.body[:50]}...")

    # ---------------------------------------------------------
    # 3. فاز جدید: فیلتر کردن کاندیداها (Candidate Selection)
    # ---------------------------------------------------------
    print(f"🔑 [INPUT] Keywords from Kafka: {matched_keywords}")
    
    candidate_policies = []
    for pol in active_policies:
        pol_keywords_raw = getattr(pol, 'keywords', '') or ''
        # استخراج و پاکسازی کلمات کلیدیِ این قانون از دیتابیس
        pol_keywords = [k.strip().lower() for k in pol_keywords_raw.split(',') if k.strip()]
        
        # اگر اشتراکی بین کلمات کافکا و کلمات این قانون وجود داشت، کاندید می‌شود
        if set(matched_keywords).intersection(set(pol_keywords)):
            candidate_policies.append(pol)
    
    # لاگ کردن نتیجه کاندیداها برای بررسی در ترمینال
    if not candidate_policies:
        print(f"⚠️ [FILTER] No candidate policies matched. Falling back to ALL active policies.")
        candidate_policies = active_policies
    else:
        print("🎯 [FILTER] Matched Candidate Policies:")
        for p in candidate_policies:
            print(f"    - Code: {getattr(p, 'code', 'N/A')} | Title: {getattr(p, 'title', 'Unknown')}")
    # ---------------------------------------------------------

    # 4. تحلیل مستقیم با هوش مصنوعی (LLM) با سیستم تلاش مجدد
    max_retries = 3
    ai_result = None
    
    for attempt in range(1, max_retries + 1):
        print(f"🧠 [LLM] analyzing content directly... (Attempt {attempt}/{max_retries})")
        
        # ارسال کاندیداها به جای کل قوانین
        ai_result = await analyze_with_llm(content.body, candidate_policies, active_policies)
        
        if ai_result:
            break
            
        print(f"⚠️ [LLM] Analysis failed on attempt {attempt}.")
        if attempt < max_retries:
            print("⏳ Waiting 1 seconds before retrying...")

    if not ai_result:
        print("❌ [LLM] All 3 attempts failed. Status set to 'pending_retry'.")
        assessment.status = "pending_retry"
        db.commit()
        db.close()
        return
        
    print(f"🎯 [RESULT] Classification: {ai_result.get('classification')} | Reason: {ai_result.get('reason')}")

    # 5. محاسبه ریسک، اولویت و ذخیره نتیجه نهایی در دیتابیس
    if ai_result.get("classification") == "violation":
        assessment.status = "violation_detected"
        
        raw_policy_code = str(ai_result.get("policy_code", ""))
        clean_policy_code = raw_policy_code.replace("Code-", "").strip()
        
        violated_policy = None
        if clean_policy_code and clean_policy_code.lower() != "null":
            # جستجو در کل active_policies برای اطمینان از ذخیره دیتای صحیح
            violated_policy = next((p for p in active_policies if str(p.code) == clean_policy_code), None)
            
            if violated_policy:
                assessment.policy_id = violated_policy.id
                assessment.category = violated_policy.title
        
        # --- محاسبات ریسک و اولویت ---
        severity_str = getattr(violated_policy, 'severity', 'low') if violated_policy else 'low'
        severity_weight = get_severity_weight(severity_str)
        
        confidence = float(ai_result.get("confidence", 0.90))
        risk_score = calculate_risk_score(severity_weight, confidence)
        
        # محاسبه سابقه تخلفات اکانت از دیتابیس
        prev_violations_count = db.query(Violation).filter(Violation.account_id == content.account_id).count()
        account_history_score = calculate_account_history_score(prev_violations_count)
        
        # محاسبه اولویت نهایی
        priority_score = calculate_priority_score(severity_weight, account_history_score, risk_score)
        
        # ذخیره امتیازات در ارزیابی
        assessment.risk = risk_score
        assessment.priority_score = priority_score
        assessment.history_score = account_history_score
        assessment.previous_violations_count = prev_violations_count

        raw_fingerprint_data = f"{content.id}-{violated_policy.id if violated_policy else 'unknown'}"
        violation_fingerprint = hashlib.md5(raw_fingerprint_data.encode()).hexdigest()

        # بررسی وجود تخلف قبلی برای جلوگیری از خطای UniqueViolation
        existing_violation = db.query(Violation).filter(Violation.fingerprint == violation_fingerprint).first()
        
        if existing_violation:
            # در صورت وجود، فقط آرایه قوانین و ارزیابی را به‌روزرسانی کن
            existing_violation.matchedRules = ai_result.get("matchedRules", [])
            existing_violation.assessment_id = assessment.id
        else:
            # ساخت رکورد جدید تخلف در صورت نبودن در دیتابیس
            new_violation = Violation(
                assessment_id=assessment.id,
                content_id=content.id,
                account_id=content.account_id,
                policy_id=assessment.policy_id,
                fingerprint=violation_fingerprint,
                created_at=assessment.created_at,
                matchedRules=ai_result.get("matchedRules", [])
            )
            db.add(new_violation)

        assessment.matchedRules = ai_result.get("matchedRules", [])
        
    else:
        assessment.status = "clean"
        assessment.risk = 0.0
        assessment.priority_score = 0.0
        assessment.history_score = 0.0
    
    assessment.reason = ai_result.get("reason")
    
    raw_confidence = float(ai_result.get("confidence", 0.90))
    assessment.confidence_score = round(raw_confidence * 100, 2)
    assessment.analyser = "openai/gpt-oss-120b"
        
    db.commit()
    print(f"💾 [DB] Status: {assessment.status} | Risk: {getattr(assessment, 'risk', 0)} | Priority: {getattr(assessment, 'priority_score', 0)}")
    print("-" * 60)
    db.close()

async def consume_assessments():
    # روشن کردن مدیریت کلیدهای هوش مصنوعی
    await init_llm_analyzer()
    
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id="analysis-worker-group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    await consumer.start()
    print("🎧 [KAFKA] Consumer is listening for 'assessment.created' events...")
    
    try:
        async for msg in consumer:
            payload = msg.value
            
            # استخراج مستقیم assessment_id بر اساس ساختار پیام‌ها
            assessment_id = payload.get("assessment_id")
            
            if assessment_id:
                print(f"\n📥 [KAFKA] Job Received for Assessment: {assessment_id}")
                await process_pipeline(payload)
            else:
                print(f"⚠️ [KAFKA] Received invalid payload (missing assessment_id): {payload}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_assessments())