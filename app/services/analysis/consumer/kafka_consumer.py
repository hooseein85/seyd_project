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
    
    # 1. عملیات همگام دیتابیس (گرفتن دیتا)
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

    # 2. تحلیل مستقیم با هوش مصنوعی (LLM) با سیستم تلاش مجدد (Retry Mechanism)
    max_retries = 3
    ai_result = None
    
    for attempt in range(1, max_retries + 1):
        print(f"🧠 [LLM] analyzing content directly... (Attempt {attempt}/{max_retries})")
        ai_result = await analyze_with_llm(content.body, active_policies)
        
        if ai_result:
            break  # اگر موفق بود، از حلقه خارج شو و به کار ادامه بده
            
        print(f"⚠️ [LLM] Analysis failed on attempt {attempt}.")
        if attempt < max_retries:
            print("⏳ Waiting 1 seconds before retrying...")  # ۵ ثانیه استراحت قبل از تلاش بعدی

    if not ai_result:
        print("❌ [LLM] All 3 attempts failed. Status set to 'pending_retry'.")
        # به جای failed، وضعیت را می‌گذاریم pending_retry تا بعداً بتوانیم پیدایشان کنیم
        assessment.status = "pending_retry"
        db.commit()
        db.close()
        return
        
    print(f"🎯 [RESULT] Classification: {ai_result.get('classification')} | Reason: {ai_result.get('reason')}")

   # 3. محاسبه ریسک، اولویت و ذخیره نتیجه نهایی در دیتابیس
    if ai_result.get("classification") == "violation":
        assessment.status = "violation_detected"
        
        raw_policy_code = str(ai_result.get("policy_code", ""))
        clean_policy_code = raw_policy_code.replace("Code-", "").strip()
        
        violated_policy = None
        if clean_policy_code and clean_policy_code.lower() != "null":
            violated_policy = next((p for p in active_policies if str(p.code) == clean_policy_code), None)
            
            if violated_policy:
                assessment.policy_id = violated_policy.id
                assessment.category = violated_policy.title
        
        # --- محاسبات ریسک و اولویت فاز MVP ---
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

        # ساخت رکورد تخلف (Violation)
        new_violation = Violation(
            assessment_id=assessment.id,
            content_id=content.id,
            account_id=content.account_id,
            policy_id=assessment.policy_id,
            fingerprint=violation_fingerprint,
            created_at=assessment.created_at,
        )
        db.add(new_violation)
        
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