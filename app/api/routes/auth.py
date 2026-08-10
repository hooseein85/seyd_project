from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.user import Token, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # نکته: OAuth2PasswordRequestForm باعث می‌شود دکمه لاگین در Swagger فعال شود!
    
    # ۱. پیدا کردن کاربر با یوزرنیم
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="نام کاربری یا رمز عبور اشتباه است")
    
    # ۲. مقایسه رمز عبور وارد شده با هش دیتابیس
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="نام کاربری یا رمز عبور اشتباه است")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="حساب کاربری شما غیرفعال شده است")
    
    # ۳. ساخت توکن برای کاربر تایید شده
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """این API اطلاعات کاربری که توکن معتبر دارد را برمی‌گرداند"""
    return current_user