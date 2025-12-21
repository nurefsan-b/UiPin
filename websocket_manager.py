# app/websocket_manager.py
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Aktif bağlantıları tutan sözlük: {user_id: websocket}
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"Bağlantı başarılı: Kullanıcı {user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"Bağlantı kesildi: Kullanıcı {user_id}")

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)
        else:
            print(f"Bilgi: Kullanıcı {user_id} çevrimdışı, mesaj sadece DB'ye kaydedildi.")

manager = ConnectionManager()