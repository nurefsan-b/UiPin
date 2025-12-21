# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from fastapi.responses import RedirectResponse
# 👇 BU SATIR EKLENDİ (HTML sayfalarını kullanabilmek için şart)
from fastapi.templating import Jinja2Templates 

try:
    from database import get_db
    from models import User, Board
    from auth import verify_password, get_password_hash
except ImportError:
    from ..database import get_db
    from ..models import User, Board
    from ..auth import verify_password, get_password_hash

# Router prefix'i "/users" olduğu için tüm adresler /users ile başlar
router = APIRouter(prefix="/users", tags=["Users"])

# 👇 BU AYAR EKLENDİ (HTML dosyalarının 'templates' klasöründe olduğunu belirtir)
templates = Jinja2Templates(directory="templates")

# --- MODELLER ---
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr 
    password: str
    gender: str | None = None
    age: int | None = None

class UserLogin(BaseModel):
    username: str
    password: str

# --- SESSION KONTROL FONKSİYONU ---
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Oturum açmanız gerekiyor.")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    
    return user

# --- LOGIN SAYFASI GÖSTERME (YENİ EKLENDİ) ---
# Adres: /users/login
@router.get("/login")
async def login_page(request: Request):
        
    # Değilse giriş ekranını aç (login_register.html templates klasöründe olmalı!)
    return templates.TemplateResponse("login_register.html", {"request": request})

# --- KAYIT OL (REGISTER) ---
@router.post("/register") 
async def create_user(
    request: Request,
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    gender: Annotated[str | None, Form()] = None,
    age: Annotated[int | None, Form()] = None,
    db: AsyncSession = Depends(get_db)
):
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Şifre en az 4 karakter olmalıdır.")
    
    result = await db.execute(select(User).where((User.username == username) | (User.email == email)))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Kullanıcı adı veya e-posta dolu.")
    
    hashed_pwd = get_password_hash(password)

    new_user = User(
        first_name=first_name, last_name=last_name, username=username,
        email=email, hashed_password=hashed_pwd, gender=gender, age=age, is_superuser=False 
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    default_board = Board(title="Favoriler", description="İlk panonuz", owner_id=new_user.id)
    db.add(default_board)
    await db.commit()
    
    return {"message": "Kayıt başarılı"}

# --- GİRİŞ YAP (LOGIN POST) ---
@router.post("/login")
async def login_user(
    request: Request,
    username: Annotated[str, Form()], 
    password: Annotated[str, Form()], 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı.")

    request.session["user_id"] = user.id

    return {"message": "Giriş başarılı"}

# --- ÇIKIŞ YAP (LOGOUT) ---
# Adres: /users/logout
@router.get("/logout") 
async def logout_user(request: Request):
    request.session.clear()
    # Çıkış yapınca /users/login sayfasına yönlendir
    return RedirectResponse(url="/users/login", status_code=302)