from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Arabam Analyzer")

class AnalyzeRequest(BaseModel):
    ilan_url: str

@app.get("/")
async def home():
    return {
        "status": "✅ API ÇALIŞIYOR",
        "message": "Test modu aktif - n8n bağlantısı hazır"
    }

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    await asyncio.sleep(1)

    return {
        "success": True,
        "ilan_url": request.ilan_url,
        "firsat_skoru": 78,
        "oner_i": "🚀 AL! İyi bir fırsat",
        "aciklama": "Bu mesaj test modundan geliyor.\nGerçek scraping özelliği yakında eklenecek.\n\nŞu anda bot çalışıyor ✓",
        "test_notu": "Railway + Render sorunları nedeniyle basit modda çalışıyoruz"
    }
