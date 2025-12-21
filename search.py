# search.py - GÜVENLİ VERSİYON
from elasticsearch import AsyncElasticsearch

# Elasticsearch bağlantısı
es = AsyncElasticsearch("http://localhost:9200")

INDEX_NAME = "pins"

async def create_index():
    """İndeks oluşturur, hata alırsan sessizce geçer."""
    try:
        # İndeks zaten varsa tekrar oluşturma
        if not await es.indices.exists(index=INDEX_NAME):
            await es.indices.create(index=INDEX_NAME, body={
                "mappings": {
                    "properties": {
                        "pin_id": {"type": "integer"},
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "tag": {"type": "keyword"},
                        "image_path": {"type": "keyword"}
                    }
                }
            })
            print("✅ Elasticsearch İndeksi (Kutusu) Oluşturuldu.")
        else:
            print("ℹ️ Elasticsearch İndeksi zaten var.")
    except Exception as e:
        print(f"⚠️ İndeks oluşturma hatası (Sunucu kapalı olabilir): {e}")

async def index_pin(pin_data: dict):
    """Pini kaydeder."""
    try:
        await es.index(index=INDEX_NAME, id=pin_data["id"], document={
            "pin_id": pin_data["id"],
            "title": pin_data["title"],
            "description": pin_data["description"],
            "tag": pin_data["tag"],
            "image_path": pin_data["image_path"]
        })
    except Exception as e:
        print(f"⚠️ Pin kaydedilemedi: {e}")

async def delete_pin_from_es(pin_id: int):
    """Pini siler."""
    try:
        await es.delete(index=INDEX_NAME, id=pin_id)
    except:
        pass

async def search_pins(query: str):
    """Arama yapar. Hata olursa boş liste döner, siteyi ÇÖKERTMEZ."""
    try:
        # 1. Önce sunucuya ping at
        if not await es.ping():
            print("⚠️ Elasticsearch sunucusuna ulaşılamıyor.")
            return []
            
        # 2. İndeks var mı kontrol et (Senin hatanı çözen kısım)
        if not await es.indices.exists(index=INDEX_NAME):
            print("⚠️ 'pins' indeksi bulunamadı. Oluşturulmaya çalışılıyor...")
            await create_index() # Bulamazsa o an oluşturmayı dene
            return [] # Yeni oluştuğu için içi boştur

        # 3. Arama yap
        resp = await es.search(index=INDEX_NAME, body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "description"],
                    "fuzziness": "AUTO"
                }
            }
        })
        return [hit["_source"] for hit in resp["hits"]["hits"]]
        
    except Exception as e:
        # Ne olursa olsun boş liste dön, 500 hatası verme
        print(f"⚠️ Arama sırasında hata oluştu: {e}")
        return []