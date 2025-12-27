# routers/pins.py
import shutil
import os
import json
from pathlib import Path
from typing import Annotated, List
from utils import save_image_file # En tepeye ekledik
from notification_service import create_notification

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from sqlalchemy.orm import selectinload
from starlette.templating import Jinja2Templates

from database import get_db
from models import Pin, User, CodeSnippet, Comment, pin_likes, Board, board_pins, Report
from routers.users import get_current_user
from routers.notifications import create_notification

#ELASTICSEARCH
try:
    from search import index_pin, delete_pin_from_es, search_pins
    ES_ACTIVE = True
except ImportError:
    ES_ACTIVE = False
    print("Elasticsearch modülü bulunamadı, arama çalışmayabilir.")

router = APIRouter(prefix="/pins", tags=["Pins"])
templates = Jinja2Templates(directory="templates")

class SnippetResponse(BaseModel):
    language: str
    content: str
    class Config:
        from_attributes = True

class PinResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    image_path: str
    owner_id: int 
    snippets: List[SnippetResponse] = []
    class Config:
        from_attributes = True

# 1. PIN OLUŞTURMA (CREATE)
@router.post("/", response_model=PinResponse)
async def create_pin(
    request: Request,
    title: Annotated[str, Form()], 
    image_file: Annotated[UploadFile, File()],
    description: Annotated[str | None, Form()] = None,
    snippets_json: Annotated[str | None, Form()] = None, 
    tag: Annotated[str, Form()] = "Genel", 
    db: AsyncSession = Depends(get_db) 
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Pin oluşturmak için giriş yapmalısınız.")
    
    db_image_path = await save_image_file(image_file, "images")
    
    db_pin = Pin(title=title, description=description, image_path=db_image_path, owner_id=int(user_id), tag=tag)
    db.add(db_pin)
    await db.commit()
    await db.refresh(db_pin)
    
    if snippets_json:
        try:
            snippets_data = json.loads(snippets_json)
            for item in snippets_data:
                new_snippet = CodeSnippet(language=item.get('lang', 'text'), content=item.get('code', ''), pin_id=db_pin.id)
                db.add(new_snippet)
            await db.commit()
        except: pass
    if ES_ACTIVE:
        await index_pin({
            "id": db_pin.id,
            "title": db_pin.title,
            "description": db_pin.description or "",
            "tag": db_pin.tag,
            "image_path": db_pin.image_path
        })

    stmt = select(Pin).options(selectinload(Pin.snippets)).where(Pin.id == db_pin.id)
    result = await db.execute(stmt)
    return result.scalars().first()

# 2. PIN SİLME
@router.delete("/{pin_id}")
async def delete_pin(
    pin_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Pin).where(Pin.id == pin_id))
    pin = result.scalars().first()

    if not pin or pin.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Yetkiniz yok")

    pin.is_deleted = True 

    if ES_ACTIVE:
        await delete_pin_from_es(pin_id)

    await db.commit()
    return {"message": "Pin çöp kutusuna taşındı (Soft Deleted)"}

#ARAMA ENDPOINT'İ
@router.get("/search")
async def search_handler(q: str):
    if not ES_ACTIVE: return []
    return await search_pins(q)

#DİĞER ENDPOINTLER 
@router.get("/", response_model=List[PinResponse])
async def get_all_pins(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pin).where(Pin.is_deleted == False).options(selectinload(Pin.owner), selectinload(Pin.snippets)).order_by(Pin.created_at.desc()).limit(50))
    return result.scalars().all()

@router.get("/api/my-pins")
async def get_my_pins(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Pin)
        .where(Pin.owner_id == current_user.id)
        .where(Pin.is_deleted == False)
        .order_by(Pin.created_at.desc())
    )
    return result.scalars().all()

@router.post("/{pin_id}/like")
async def like_pin(pin_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id: raise HTTPException(status_code=401)
    
    existing_like = (await db.execute(select(pin_likes).where((pin_likes.c.user_id == int(user_id)) & (pin_likes.c.pin_id == pin_id)))).first()
    pin = (await db.execute(select(Pin).where(Pin.id == pin_id))).scalars().first()

    if existing_like:
        await db.execute(delete(pin_likes).where((pin_likes.c.user_id == int(user_id)) & (pin_likes.c.pin_id == pin_id)))
        pin.like_count = max(0, pin.like_count - 1)
        liked = False
    else:
        await db.execute(insert(pin_likes).values(user_id=int(user_id), pin_id=pin_id))
        pin.like_count += 1
        liked = True
        if pin.owner_id != int(user_id):
            await create_notification(db, pin.owner_id, int(user_id), "liked", pin.id)
    
    await db.commit()
    return {"likes": pin.like_count, "liked": liked}

@router.post("/{pin_id}/comment")
async def add_comment(pin_id: int, request: Request, content: Annotated[str, Form()], db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id: raise HTTPException(status_code=401)
    
    db.add(Comment(content=content, pin_id=pin_id, user_id=int(user_id)))
    await db.commit()
    
    pin = (await db.execute(select(Pin).where(Pin.id == pin_id))).scalars().first()
    if pin.owner_id != int(user_id):
        await create_notification(db, pin.owner_id, int(user_id), "commented", pin.id)
    return {"message": "Yorum eklendi"}

@router.post("/save_to_board")
async def save_pin_to_specific_board(pin_id: Annotated[int, Form()], board_id: Annotated[int, Form()], request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(insert(board_pins).values(board_id=board_id, pin_id=pin_id))
        await db.commit()
        return {"message": "Kaydedildi"}
    except:
        await db.rollback()
        return {"message": "Hata"}

@router.post("/{pin_id}/report")
async def report_pin(pin_id: int, reason: Annotated[str, Form()], request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id: raise HTTPException(status_code=401)
    db.add(Report(reporter_id=int(user_id), pin_id=pin_id, reason=reason, status="pending"))
    await db.commit()
    return {"message": "Rapor iletildi."}