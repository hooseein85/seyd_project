import re

def normalize_persian(text: str):
    """حروف عربی را به فارسی تبدیل کرده و فاصله‌های اضافی را پاک می‌کند"""
    if not text:
        return ""
    text = text.lower().replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return text

def find_candidate_policies(content_text: str, active_policies: list):
    candidate_policies = []
    normalized_text = normalize_persian(content_text)

    for policy in active_policies:
        if not policy.keywords:
            continue
            
        # هم ویرگول انگلیسی و هم فارسی را برای جدا کردن کلمات پشتیبانی می‌کند
        raw_keywords = re.split(r'[,،]', policy.keywords)
        keywords = [normalize_persian(k.strip()) for k in raw_keywords if k.strip()]
        
        matched_keywords = [kw for kw in keywords if kw in normalized_text]
        
        if matched_keywords:
            candidate_policies.append({
                "code": policy.code,
                "title": policy.title,
                "description": getattr(policy, 'description', ''),
                "prompt_description": getattr(policy, 'prompt_description', ''),
                "prompt_examples": getattr(policy, 'prompt_examples', ''),
                "matched_keywords": matched_keywords
            })
            
    return {
        "candidate_policies": candidate_policies
    }