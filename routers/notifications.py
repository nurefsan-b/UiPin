# routers/notifications.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime
import json
from websocket_manager import manager
from database import get_db
from models import Notification, User, Pin
from routers.users import get_current_user
from notification_service import create_notification

# WebSocket yöneticisini çağırıyoruz (Anlık bildirim için)
from routers.messages import manager 

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# --- ŞEMA ---
class NotificationOut(BaseModel):
    id: int
    actor_username: str
    actor_avatar: str | None
    verb: str
    pin_title: str | None
    pin_id: int | None
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True


# --- ENDPOINT: BİLDİRİMLERİ GETİR ---
@router.get("/", response_model=list[NotificationOut])
async def get_notifications(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        return []
        
    result = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == current_user.id)
        .options(selectinload(Notification.actor), selectinload(Notification.pin))
        .order_by(desc(Notification.created_at))
        .limit(20)
    )
    
    notifs = result.scalars().all()
    
    # Pydantic formatına çevir
    response = []
    for n in notifs:
        response.append(NotificationOut(
            id=n.id,
            actor_username=n.actor.username,
            actor_avatar=n.actor.profile_picture,
            verb=n.verb,
            pin_id=n.pin_id,
            pin_title=n.pin.title if n.pin else "Pin",
            created_at=n.created_at,
            is_read=n.is_read
        ))
        
    return response

# --- ENDPOINT: OKUNDU OLARAK İŞARETLE ---
@router.post("/mark-read")
async def mark_read(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Basitçe hepsini okundu yapalım (Geliştirilebilir)
    # Burada update sorgusu yazılabilir ama şimdilik pas geçiyorum, liste açılınca okunmuş saysın.
    pass