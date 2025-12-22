from locust import HttpUser, task, between
import os

# Test sırasında kullanılacak görselin yolu
IMAGE_PATH = "static/images/test_image.jpg"

class UiPinUser(HttpUser):
    # Kullanıcılar her işlem arasında 1 ile 5 saniye beklesin (Gerçekçi davranış)
    wait_time = between(1, 5)

    # 1. TEST BAŞLAMADAN ÖNCE GİRİŞ YAP
    def on_start(self):
        # NOT: Veritabanında bu bilgilere sahip bir kullanıcı olduğundan emin ol!
        # Yoksa oluştur: username="locust_user", password="password123"
        response = self.client.post("/users/login", data={
            "username": "nurefsan_bozkurt",  # Buraya geçerli bir kullanıcı adı yaz
            "password": "NurefsanBozkurt"   # Buraya o kullanıcının şifresini yaz
        })
        
        if response.status_code == 200:
            print("✅ Giriş Başarılı!")
        else:
            print("❌ Giriş Başarısız! Lütfen kullanıcı bilgilerini kontrol et.")

    # 2. ANA SAYFAYI GÖRÜNTÜLE (En sık yapılan işlem - Ağırlık: 3)
    @task(3)
    def view_homepage(self):
        self.client.get("/")

    # 3. ARAMA YAP (Orta sıklıkta - Ağırlık: 2)
    @task(2)
    def search_pins(self):
        # Rastgele kelimelerle arama simülasyonu
        queries = ["UI", "CSS", "Python", "Web", "Design"]
        q = random.choice(queries)
        self.client.get(f"/pins/search?q={q}")

    # 4. PROFİLE BAK (Düşük sıklıkta - Ağırlık: 1)
    @task(1)
    def view_profile(self):
        self.client.get("/profile/")

    # 5. PIN YÜKLEME (En ağır işlem - Ağırlık: 1)
    @task(1)
    def create_pin(self):
        # Dosya var mı kontrol et
        if not os.path.exists(IMAGE_PATH):
            print(f"⚠️ Uyarı: {IMAGE_PATH} bulunamadı, yükleme testi atlanıyor.")
            return

        # Multipart form data gönderimi
        with open(IMAGE_PATH, "rb") as image_file:
            files = {
                "image_file": ("static/images/test_image.jpg", image_file, "image/jpeg")
            }
            data = {
                "title": "Locust Load Test Pin",
                "description": "Bu pin otomatik performans testi sırasında oluşturuldu.",
                "tag": "Other"
            }
            
            # POST isteği at
            self.client.post("/pins/", data=data, files=files)

import random