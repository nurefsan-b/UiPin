
import json
from sqlalchemy.ext.asyncio import AsyncSession
from models import Notification
from websocket_manager import manager  

async def create_notification(db: AsyncSession, recipient_id: int, actor_id: int, verb: str, pin_id: int = None):
    
    if recipient_id == actor_id:
        return

    
    new_notif = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        verb=verb,
        pin_id=pin_id
    )
    db.add(new_notif)
    await db.commit()
    await db.refresh(new_notif)
    
    # WebSocket ile Canlı Gönder (Eğer kullanıcı bağlıysa)
    payload = json.dumps({
        "type": "new_notification",
        "content": "Yeni bir etkileşim!", 
        "count": 1 
    })
    
    await manager.send_personal_message(payload, recipient_id)
