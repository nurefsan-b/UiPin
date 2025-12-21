from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, distinct, func
from typing import List, Optional
from datetime import datetime
import json
from pydantic import BaseModel
from websocket_manager import manager

# GERÇEK BAĞIMLILIKLAR
from database import get_db
from models import User, Message

# =========================================================================
# Pydantic Şemaları
# =========================================================================

class UserInMessageList(BaseModel):
    id: int
    username: str
    is_mutual_following: bool = False
    profile_picture: Optional[str] = None
    last_message_preview: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    sender_id: int
    content: str
    created_at: datetime
    is_mine: bool 

    class Config:
        from_attributes = True

# =========================================================================
# WebSocket Bağlantı Yöneticisi
# =========================================================================


router = APIRouter(prefix="/messages", tags=["Mesajlaşma (API & WS)"])

# =========================================================================
# WebSocket Endpoint'i (ANLIK İLETİŞİM)
# =========================================================================

@router.websocket("/ws/{sender_id}")
async def websocket_endpoint(websocket: WebSocket, sender_id: int, db: AsyncSession = Depends(get_db)):
    """WebSocket üzerinden anlık mesaj alıp gönderme."""
    await manager.connect(sender_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                receiver_id = int(message_data.get("receiver_id"))
                content = message_data.get("content")
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
            
            if receiver_id and content:
                new_message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
                db.add(new_message)
                await db.flush()  # Veritabanına yazılmasını sağla
                
                # ALICIYA GÖNDER
                response_to_receiver = json.dumps({
                    "type": "new_message",
                    "sender_id": sender_id,
                    "content": content,
                    "created_at": str(datetime.now())
                })
                await manager.send_personal_message(response_to_receiver, receiver_id)
                
                # GÖNDERENE ONAY GÖNDER
                response_to_sender = json.dumps({
                    "type": "sent_success"
                })
                await manager.send_personal_message(response_to_sender, sender_id)
                
    except WebSocketDisconnect:
        manager.disconnect(sender_id)
    except Exception as e:
        print(f"WS Hata: {e}")
        manager.disconnect(sender_id)

# =========================================================================
# REST API Endpoint'leri (Arayüz Verileri)
# =========================================================================

@router.get("/users/list", response_model=List[UserInMessageList])
async def get_messageable_users(db: AsyncSession = Depends(get_db), current_user_id: int = Query(...)):
    """Sadece geçmiş mesajlaşma olanları listeler."""
    
    # Mesajlaştığım kişilerin ID'lerini bul (Hem alıcı hem gönderici olarak)
    sent = await db.execute(select(distinct(Message.receiver_id)).where(Message.sender_id == current_user_id))
    received = await db.execute(select(distinct(Message.sender_id)).where(Message.receiver_id == current_user_id))
    
    contact_ids = set(sent.scalars().all()) | set(received.scalars().all())
    contact_ids.discard(current_user_id) # Kendimi listeden çıkar
    
    if not contact_ids:
        return []

    users = await db.execute(select(User).where(User.id.in_(contact_ids)))
    return [UserInMessageList(id=u.id, username=u.username, profile_picture=u.profile_picture) for u in users.scalars().all()]

@router.get("/users/search", response_model=List[UserInMessageList])
async def search_users(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    search_term = f"%{q}%"
    stmt = select(User).where(User.username.ilike(search_term)).limit(20)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [
        UserInMessageList(
            id=u.id, 
            username=u.username, 
            profile_picture=u.profile_picture
        ) for u in users
    ]

@router.get("/history/{target_user_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(target_user_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Query(...)):
    stmt = select(Message).where(
        or_(
            (Message.sender_id == current_user_id) & (Message.receiver_id == target_user_id),
            (Message.sender_id == target_user_id) & (Message.receiver_id == current_user_id)
        )
    ).order_by(Message.created_at.asc())
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return [
        ChatMessageResponse(
            sender_id=m.sender_id,
            content=m.content,
            created_at=m.created_at,
            is_mine=(m.sender_id == current_user_id)
        ) for m in messages
    ]