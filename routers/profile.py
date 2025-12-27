# routers/profile.py
import os
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Annotated
from sqlalchemy.orm import selectinload
from sqlalchemy import select 
from utils import save_image_file
try:
    from database import get_db
    from auth import get_password_hash, verify_password
    from routers.users import get_current_user
    from models import User, Pin, Board 
except ImportError:
    from ..database import get_db
    from ..auth import get_password_hash, verify_password
    from ..routers.users import get_current_user
    from ..models import User, Pin, Board

router = APIRouter(prefix="/profile", tags=["Profile"])
templates = Jinja2Templates(directory="templates")

# 1. PROFİL GÖSTER (GET)
@router.get("/")
async def show_profile(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_current_user(request, db)
    except:
        return RedirectResponse(url="/", status_code=302)
        
    return templates.TemplateResponse("profile.html", {
    "request": request, 
    "user": user,
    "active_page": "profile"
})

# 2. PROFİL GÜNCELLE (POST)
@router.post("/update")
async def update_profile(
    request: Request,
    first_name: Annotated[str, Form()] = None,
    last_name: Annotated[str, Form()] = None,
    username: Annotated[str, Form()] = None,
    email: Annotated[str, Form()] = None,
    age: Annotated[str, Form()] = None, 
    gender: Annotated[str, Form()] = None,
    current_password: Annotated[str, Form()] = None,
    new_password: Annotated[str, Form()] = None,
    profile_picture: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
    except:
        return RedirectResponse(url="/", status_code=302)

    try:
        # BİLGİ GÜNCELLEME 
        if first_name: user.first_name = first_name
        if last_name: user.last_name = last_name
        if username: user.username = username
        if email: user.email = email
        if age and age.strip().isdigit(): user.age = int(age)
        if gender: user.gender = gender

        # RESİM YÜKLEME 
        if profile_picture and profile_picture.filename:
            try:
                saved_path = await save_image_file(profile_picture, "images")
                
                if saved_path:
                    user.profile_picture = saved_path
                
            except Exception as img_err:
                print(f"Resim Hatası: {img_err}") 
                return templates.TemplateResponse("profile.html", {
                    "request": request, 
                    "user": user, 
                    "error": f"Fotoğraf yüklenemedi: {str(img_err)}"
                })

        # ŞİFRE DEĞİŞTİRME
        if current_password and new_password:
            if verify_password(current_password, user.hashed_password):
                user.hashed_password = get_password_hash(new_password)
            else:
                 return templates.TemplateResponse("profile.html", {
                     "request": request, "user": user, "error": "Mevcut şifre yanlış!"
                 })

        await db.commit()
        await db.refresh(user)
        
        return templates.TemplateResponse("profile.html", {
            "request": request, 
            "user": user, 
            "message": "Profil başarıyla güncellendi!"
        })

    except IntegrityError:
        await db.rollback()
        return templates.TemplateResponse("profile.html", {
            "request": request, "user": user, "error": "Bu kullanıcı adı veya e-posta zaten kullanımda!"
        })
    except Exception as e:
        print(f"Genel Hata: {e}")
        return templates.TemplateResponse("profile.html", {
            "request": request, "user": user, "error": f"Bir hata oluştu: {str(e)}"
        })
    
@router.get("/{username}")
async def show_public_profile(
    username: str, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == username))
    profile_user = result.scalars().first()

    if not profile_user:
        return RedirectResponse(url="/")

    pins_res = await db.execute(
        select(Pin)
        .where(Pin.owner_id == profile_user.id)
        .where(Pin.is_deleted == False)
        .order_by(Pin.created_at.desc())
    )
    user_pins = pins_res.scalars().all()

    boards_res = await db.execute(
        select(Board)
        .where(Board.owner_id == profile_user.id)
        .options(selectinload(Board.pins)) 
    )
    user_boards = boards_res.scalars().all()

    current_user = None
    if request.session.get("user_id"):
        try:
            current_user = await get_current_user(request, db)
        except:
            pass

    return templates.TemplateResponse("public_profile.html", {
        "request": request,
        "profile_user": profile_user,
        "user_pins": user_pins,
        "user_boards": user_boards,
        "current_user": current_user,
        "active_page": ""
    })