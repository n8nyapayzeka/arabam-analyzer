from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Arabam Analiz API - Test Modu")

class AnalyzeRequest(BaseModel):
    ilan_url: str

@app.get("/")
async def home():
    return {
        "status": "✅ API ÇALIŞIYOR",
        "message": "Railway deploy başarılı. Test modundasınız."
    }

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    # Test için sabit yanıt veriyoruz (gerçek scraping'i sonra ekleyeceğiz)
    await asyncio.sleep(1.5)  # biraz gerçekçi bekleme
    
    return {
        "success": True,
        "ilan": {
            "url": request.ilan_url,
            "full_title": "Test Modu - Skoda Octavia 1.5 TSI",
            "brand": "Skoda",
            "model": "Octavia",
            "year": 2023,
            "mileage": 45000,
            "price": 1285000,
            "location": "İstanbul"
        },
        "firsat_skoru": 82,
        "oner_i": "🚀 AL! Çok iyi fırsat",
        "aciklama": "Bu mesaj test modundan geliyor. Gerçek scraping yakında aktif olacak.",
        "note": "Railway'de Selenium şu an çok kaynak tükettiği için devre dışı."
    }
