# routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from starlette.templating import Jinja2Templates
from typing import Annotated
import os
from pathlib import Path
from notification_service import create_notification
from sqlalchemy.orm import selectinload
from database import get_db
from models import User, Pin, Comment, Board, Report, CodeSnippet, pin_likes, board_pins
from routers.users import get_current_user

#BİLDİRİM FONKSİYONU
try:
    from routers.notifications import create_notification
except ImportError:
    from ..routers.notifications import create_notification

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

#GÜVENLİK KONTROLÜ
async def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Giriş yapın.")
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Bu sayfaya erişim yetkiniz yok.")
    return current_user

#1. DASHBOARD
@router.get("/")
async def admin_dashboard(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user_count = await db.scalar(select(func.count(User.id)))
    pin_count = await db.scalar(select(func.count(Pin.id)))
    comment_count = await db.scalar(select(func.count(Comment.id)))
    board_count = await db.scalar(select(func.count(Board.id)))

    users_res = await db.execute(select(User).order_by(User.created_at.desc()).limit(10))
    recent_users = users_res.scalars().all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "admin": admin,
        "stats": {"users": user_count, "pins": pin_count, "comments": comment_count, "boards": board_count},
        "recent_users": recent_users, "active_page": "admin"
    })

#2. PİN YÖNETİMİ
@router.get("/pins")
async def admin_pins(
    request: Request, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(Pin)
        .where(Pin.is_deleted == False)     
        .options(selectinload(Pin.owner))   
        .order_by(Pin.created_at.desc())
        .limit(50)
    )
    pins = result.scalars().all()
    
    return templates.TemplateResponse("admin/pins.html", {
        "request": request, "admin": admin, "pins": pins, "active_page": "admin_pins"
    })
#3. KULLANICI SİLME

@router.post("/users/delete/{user_id}")
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db), 
    admin: User = Depends(get_current_admin)
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Kendinizi silemezsiniz.")

    
    await db.execute(delete(pin_likes).where(pin_likes.c.user_id == user_id))
    
    await db.execute(delete(Comment).where(Comment.user_id == user_id))
    
    await db.execute(delete(Board).where(Board.owner_id == user_id))
    
    await db.execute(delete(Pin).where(Pin.owner_id == user_id))

    await db.execute(delete(User).where(User.id == user_id))
    
    await db.commit()
    return {"message": "Kullanıcı ve tüm verileri kalıcı olarak silindi."}

# 4.PIN SİLME
@router.post("/pins/delete/{pin_id}")
async def delete_pin(
    pin_id: int, 
    db: AsyncSession = Depends(get_db), 
    admin: User = Depends(get_current_admin)):

    pin_res = await db.execute(select(Pin).where(Pin.id == pin_id))
    pin = pin_res.scalars().first()
    
    if pin:
        owner_id = pin.owner_id
        pin.is_deleted = True 
        
        await create_notification(
            db=db,
            recipient_id=owner_id,
            actor_id=admin.id,
            verb="deleted_admin",
            pin_id=None
        )
        
        await db.commit()
    return {"message": "Pin soft delete ile silindi"}

#5. RAPORLARI GÖRÜNTÜLE 
@router.get("/reports")
async def admin_reports(
    request: Request, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(Report).where(Report.status == "pending")
        .options(selectinload(Report.pin), selectinload(Report.reporter))
        .order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return templates.TemplateResponse("admin/reports.html", {
        "request": request, "admin": admin, "reports": reports, "active_page": "admin_reports"
    })

#6.RAPOR İŞLEMİ
@router.post("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: int, 
    action: str = Form(...), 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalars().first()
    if not report: raise HTTPException(status_code=404, detail="Rapor bulunamadı")
    
    msg = "İşlem yapıldı."

    if action == "delete_pin":
        if report.pin_id:
            pin_id = report.pin_id
            pin_res = await db.execute(select(Pin).where(Pin.id == pin_id))
            pin = pin_res.scalars().first()

            if pin:
                owner_id = pin.owner_id
                pin.is_deleted = True  
                report.status = "resolved"
                
                verb_str = f"deleted_{report.reason}"
                
                await create_notification(
                    db=db,
                    recipient_id=owner_id, 
                    actor_id=admin.id,     
                    verb=verb_str,         
                    pin_id=None            
                )

                msg = "Pin soft delete ile silindi, rapor kapatıldı ve kullanıcıya bildirim gönderildi."

            await db.commit()
            return {"message": msg}
        
    elif action == "dismiss":
        report.status = "dismissed"
        msg = "Rapor reddedildi."
        await db.commit()
        
    else:
        raise HTTPException(status_code=400, detail="Geçersiz işlem")

    return {"message": msg}