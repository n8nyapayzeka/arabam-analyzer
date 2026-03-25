from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import re

app = FastAPI(title="Arabam Fırsat Botu API")

class AnalyzeRequest(BaseModel):
    ilan_url: str

@app.get("/")
async def home():
    return {"status": "✅ API ÇALIŞIYOR (Test Modu)", "platform": "Railway"}

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    await asyncio.sleep(1.2)  # biraz gerçekçi his versin

    # Basit URL parsing ile ilan numarasını al
    ilan_id = re.search(r'/ilan/(\d+)', request.ilan_url)
    ilan_id = ilan_id.group(1) if ilan_id else "Bilinmiyor"

    return {
        "success": True,
        "ilan": {
            "url": request.ilan_url,
            "ilan_id": ilan_id,
            "full_title": "Test Modu - İlan Analizi",
            "brand": "Test Marka",
            "model": "Test Model",
            "year": 2023,
            "mileage": 45000,
            "price": 1350000
        },
        "firsat_skoru": 79,
        "oner_i": "🚀 AL! İyi fırsat görünüyor",
        "aciklama": "Şu anda test modundayız. Gerçek scraping (Cloudflare bypass) yakında eklenecek.\n\nTelegram botu çalışıyor ✓",
        "note": "Railway ücretsiz planda Selenium çok zor çalıştığı için test moduna geçtik."
    }
