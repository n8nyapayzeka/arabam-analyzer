from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import re
from arabam_scraper import ArabamScraper  # önceki dosyanızın adı
import time

app = FastAPI(title="Arabam Fırsat Analiz API", version="1.0")

class AnalyzeRequest(BaseModel):
    ilan_url: str

def extract_listing_id(url: str):
    match = re.search(r'/ilan/(\d+)', url)
    return match.group(1) if match else None

async def scrape_single_listing(url: str):
    """Tek ilan detay sayfasını scrape eder (ileride genişletebilirsin)"""
    # Şimdilik temel bilgiler için mevcut scraper'ı kullanıyoruz, 
    # gerçekte detay sayfası için ayrı logic ekleyebiliriz.
    scraper = ArabamScraper(category="otomobil", min_price=0, max_price=100000000, max_pages=1)
    # Not: Tek ilan için yeni bir metod eklemen önerilir. Şimdilik placeholder.
    await asyncio.sleep(1)  # simülasyon
    return {
        "url": url,
        "brand": "Örnek Marka",
        "model": "Örnek Model",
        "year": 2023,
        "mileage": 45000,
        "price": 1250000,
        "location": "İstanbul",
        "fuel": "Benzin",
        "transmission": "Otomatik"
    }

async def get_market_comparison(ilan_data: dict):
    """Piyasa kıyaslaması (aynı marka/model/yıl için ortalama fiyat)"""
    scraper = ArabamScraper(
        category="otomobil",
        min_price=ilan_data["price"] - 300000,
        max_price=ilan_data["price"] + 300000,
        max_pages=3
    )
    # Gerçekte scrape çalıştırıp ortalama hesapla
    await asyncio.sleep(2)
    return {
        "average_price": 1380000,
        "min_price": 1190000,
        "max_price": 1550000,
        "count": 87,
        "same_km_range_avg": 1420000
    }

def calculate_opportunity_score(ilan: dict, market: dict) -> int:
    price_diff_percent = ((market["average_price"] - ilan["price"]) / market["average_price"]) * 100
    score = int(50 + price_diff_percent * 1.8)  # temel formül
    if ilan["mileage"] < 60000:
        score += 15
    score = max(0, min(100, score))
    return score

def generate_explanation(ilan: dict, market: dict, score: int) -> str:
    diff = market["average_price"] - ilan["price"]
    if score > 75:
        return f"Harika fırsat! Piyasanın %{int((diff/market['average_price'])*100)} altında. ALMAYI DÜŞÜN!"
    elif score > 50:
        return f"Ortalamanın altında. Değerlendirebilirsin."
    else:
        return f"Piyasa ortalamasının üzerinde. Acele etme."

@app.post("/analyze")
async def analyze_car(request: AnalyzeRequest):
    try:
        ilan_data = await scrape_single_listing(request.ilan_url)
        market_data = await get_market_comparison(ilan_data)
        score = calculate_opportunity_score(ilan_data, market_data)
        
        recommendation = "🚀 AL!" if score > 75 else "🤔 BEKLE" if score > 50 else "❌ KAÇIRMA"

        return {
            "success": True,
            "ilan": ilan_data,
            "piyasa": market_data,
            "firsat_skoru": score,
            "oner_i": recommendation,
            "aciklama": generate_explanation(ilan_data, market_data, score),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
async def root():
    return {"message": "Arabam Fırsat Analiz API çalışıyor! /analyze endpoint'ini kullan."}
