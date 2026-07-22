# ساخت محیط مجازی
python -m venv venv

# فعال‌سازی محیط مجازی (برای ویندوز)
.\venv\Scripts\activate
# اگر روی Arch Linux هستی: source venv/bin/activate

# نصب تمام نیازمندی‌ها
pip install -r requirements.txt


#gitignore content

# Environments
.env
.env.*
venv/
env/
.venv/

# Python cache
__pycache__/
*.py[cod]
*$py.class

# IDE
.vscode/
.idea/