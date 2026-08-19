import aiosqlite
import re
from datetime import datetime, timedelta

DB_NAME = 'api_keys_manager.db'

class APIKeyManager:
    def __init__(self, initial_keys=None):
        self.initial_keys = initial_keys or []

    async def setup_and_reset(self):
        now = datetime.utcnow()
        async with aiosqlite.connect(DB_NAME, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT UNIQUE,
                    status TEXT DEFAULT 'FREE',
                    limit_reached_at DATETIME,
                    available_at DATETIME
                )
            ''')
            
            # تزریق کلیدهای جدید از فایل کانفیگ
            for key in self.initial_keys:
                await db.execute(
                    "INSERT OR IGNORE INTO api_keys (api_key) VALUES (?)",
                    (key,)
                )
            
            # بیدار کردن کلیدهایی که زمان استراحتشان تمام شده است
            await db.execute('''
                UPDATE api_keys 
                SET status = 'FREE', 
                    limit_reached_at = NULL, 
                    available_at = NULL
                WHERE status = 'LIMITED' 
                  AND available_at IS NOT NULL 
                  AND available_at <= ?
            ''', (now,))
            
            await db.commit()
            print("🔑 [KEY MANAGER] API Keys database initialized and cooldowns updated.")

    async def get_free_key(self):
        now = datetime.utcnow()
        async with aiosqlite.connect(DB_NAME, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            db.row_factory = aiosqlite.Row
            
            # عملیات اتمیک برای جلوگیری از تداخل (Race Condition)
            cursor = await db.execute('''
                UPDATE api_keys 
                SET status = 'BUSY' 
                WHERE id = (
                    SELECT id FROM api_keys 
                    WHERE status = 'FREE' 
                       OR (status = 'LIMITED' AND available_at <= ?)
                    LIMIT 1
                )
                RETURNING *
            ''', (now,))
            
            key_data = await cursor.fetchone()
            if key_data:
                await db.commit()
                # نام کلید را برای امنیت ماسک می‌کنیم (فقط 8 کاراکتر آخر)
                masked_key = f"...{key_data['api_key'][-8:]}"
                print(f"⚡ [DISPATCH] API Key '{masked_key}' locked and ready for analysis.")
                return dict(key_data)
                
            return None

    def extract_wait_time(self, error_msg):
        """استخراج دقیق زمان خواب از متن ارور سرور"""
        # الگو برای پیدا کردن ساعت، دقیقه و ثانیه: "try again in 17m43.584s"
        match = re.search(r'try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?', error_msg)
        if match:
            hours = float(match.group(1) or 0)
            minutes = float(match.group(2) or 0)
            seconds = float(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 86400 # اگر فرمت ارور عوض شده بود، برای امنیت 24 ساعت می‌خوابانیم

    async def handle_rate_limit(self, key_id, error_msg):
        now = datetime.utcnow()
        wait_seconds = self.extract_wait_time(error_msg)
        avail_at = now + timedelta(seconds=wait_seconds)
        
        async with aiosqlite.connect(DB_NAME, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute('''
                UPDATE api_keys 
                SET status = 'LIMITED', limit_reached_at = ?, available_at = ? 
                WHERE id = ?
            ''', (now, avail_at, key_id))
            await db.commit()
            
        print(f"🛑 [RATE LIMIT] API Key sent to bed! Waking up in {wait_seconds:.0f} seconds.")

    async def release_key(self, key_id):
        async with aiosqlite.connect(DB_NAME, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("UPDATE api_keys SET status = 'FREE' WHERE id = ? AND status = 'BUSY'", (key_id,))
            await db.commit()