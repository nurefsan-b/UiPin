# --- YARDIMCI FONKSİYON: BİLDİRİM OLUŞTUR VE GÖNDER ---
# app/notification_service.py en tepesi:
import json
from sqlalchemy.ext.asyncio import AsyncSession
from models import Notification
from websocket_manager import manager  # 👈 Bu çok önemli!

async def create_notification(db: AsyncSession, recipient_id: int, actor_id: int, verb: str, pin_id: int = None):
    # Kendi kendine bildirim atmasını engelle
    if recipient_id == actor_id:
        return

    # Veritabanına Kaydet
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
    # Mesaj yapısını masonry.js'in anlayacağı şekilde ayarlıyoruz
    payload = json.dumps({
        "type": "new_notification",
        "content": "Yeni bir etkileşim!", # Frontend detayları çekecek
        "count": 1 # Sayaç arttırmak için
    })
    
    await manager.send_personal_message(payload, recipient_id)
