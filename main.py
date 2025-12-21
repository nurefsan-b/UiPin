# main.py
from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

# Arama ve Veritabanı Fonksiyonları
from search import create_index
from database import create_tables, get_db
from models import Pin, User, Comment 

# Router Entegrasyonları
from routers import pins, users, boards, notifications, messages, profile, admin
from routers.users import get_current_user 

# --- LIFESPAN (YAŞAM DÖNGÜSÜ) AYARI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await create_index()
    print("🚀 Uygulama ve Elasticsearch başarıyla başlatıldı.")
    yield 
    print("🛑 Uygulama kapatılıyor...")

# --- FASTAPI UYGULAMASI TANIMLAMASI ---
app = FastAPI(
    title="Pinterest Klonu API",
    description="Python FastAPI ile Pin paylaşım uygulaması",
    version="0.1.0",
    lifespan=lifespan 
)

templates = Jinja2Templates(directory="templates")

# Session (Oturum) Ayarı
app.add_middleware(SessionMiddleware, secret_key="cok_gizli_anahtar_buraya")

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- ROUTER ENTEGRASYONLARI ---
app.include_router(pins.router)
app.include_router(users.router)
app.include_router(boards.router)
app.include_router(notifications.router)
app.include_router(messages.router)
app.include_router(profile.router)
app.include_router(admin.router)

# --- ANA SAYFA (FEED) ---
@app.get("/")
async def home(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    tag: str = None 
):
    # --- 1. GÜVENLİK KONTROLÜ (YENİ) ---
    # Eğer kullanıcı giriş yapmamışsa, direkt Login sayfasına yönlendir!
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/users/login", status_code=status.HTTP_302_FOUND)

    # --- 2. KULLANICI BİLGİSİNİ ÇEK ---
    current_user = None
    if user_id:
        u_res = await db.execute(select(User).where(User.id == int(user_id)))
        current_user = u_res.scalars().first()

    pins_for_template = []
    try:
        query = select(Pin).where(Pin.is_deleted == False).options(
            selectinload(Pin.owner), 
            selectinload(Pin.snippets),
            selectinload(Pin.comments).options(selectinload(Comment.user)) 
        ).order_by(Pin.created_at.desc())

        if tag:
            query = query.filter(Pin.tag == tag)

        result = await db.execute(query.limit(50))
        pins_data = result.scalars().all()
        
        for pin in pins_data:
            pin_dict = pin.__dict__
            pin_dict['owner_username'] = pin.owner.username if pin.owner else "Anonim"
            pin_dict['snippets'] = pin.snippets 
            pin_dict['comments'] = pin.comments
            pins_for_template.append(pin_dict)
            
    except Exception as e:
        print(f"Hata: {e}")
        
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "title": f"Keşfet: {tag}" if tag else "Ana Akış", 
            "pins": pins_for_template,
            "current_user": current_user,
            "active_tag": tag
        }
    )

# --- API: KULLANICI PİNLERİ ---
@app.get("/api/my-pins")
async def get_user_pins(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Pin)
            .filter(Pin.owner_id == current_user.id)
            .order_by(Pin.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        return {"error": str(e)}

