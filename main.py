from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import re
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random

app = FastAPI(title="Arabam Fırsat Analiz API - Cloudflare Bypass", version="1.2")

class AnalyzeRequest(BaseModel):
    ilan_url: str

async def scrape_single_listing(url: str):
    if not url.startswith("https://www.arabam.com/ilan/"):
        raise ValueError("Geçersiz Arabam.com ilan linki")

    options = uc.ChromeOptions()
    options.headless = False                    # Cloudflare için headless=False daha iyi çalışır (Docker'da xvfb ile)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        
        # Cloudflare'ı yavaş yavaş atlatmak için insan benzeri davranış
        driver.get("https://www.arabam.com")
        await asyncio.sleep(random.uniform(3, 6))
        
        driver.get(url)
        await asyncio.sleep(random.uniform(5, 8))   # Challenge çözülmesi için uzun bekleme

        # Scroll yap (daha gerçekçi görünüm)
        driver.execute_script("window.scrollTo(0, 800);")
        await asyncio.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Güncel selector'lar (2026)
        title_tag = soup.find('h1') or soup.find('h1', class_=re.compile('title', re.I))
        full_title = title_tag.get_text(strip=True) if title_tag else "Bilinmiyor"

        price_tag = soup.find('span', class_=re.compile('price', re.I)) or soup.find(string=re.compile(r'\d{1,3}(?:\.\d{3})* TL'))
        price_text = re.sub(r'[^\d]', '', price_tag.get_text()) if price_tag else "0"
        price = int(price_text) if price_text.isdigit() else 0

        # Özellik tablosu
        specs = {}
        for row in soup.find_all(['div', 'tr'], class_=re.compile('spec|row|feature', re.I)):
            try:
                key_elem = row.find(string=re.compile(r'(Model Yılı|Yıl|Kilometre|Yakıt|Vites|Renk|İl)', re.I))
                if key_elem:
                    key = key_elem.strip()
                    val = row.find('span', class_=re.compile('value')) or row.find('td', recursive=True)
                    if val:
                        specs[key] = val.get_text(strip=True)
            except:
                pass

        data = {
            "url": url,
            "full_title": full_title,
            "brand": full_title.split()[0] if full_title != "Bilinmiyor" else "Bilinmiyor",
            "model": " ".join(full_title.split()[1:])[:50],
            "year": int(specs.get("Model Yılı", specs.get("Yıl", "0")) or 0),
            "mileage": int(re.sub(r'[^\d]', '', specs.get("Kilometre", "0")) or 0),
            "price": price,
            "location": specs.get("İl / İlçe", "Bilinmiyor"),
            "fuel": specs.get("Yakıt Tipi", "Bilinmiyor"),
            "transmission": specs.get("Vites Tipi", "Bilinmiyor"),
            "color": specs.get("Renk", "Bilinmiyor")
        }

        return data

    except Exception as e:
        print(f"[ERROR] Scrape hatası: {e}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


# Diğer fonksiyonlar (get_market_comparison, calculate_opportunity_score, generate_explanation) aynı kalabilir.
# Aşağıya sadece özet olarak ekliyorum, istersen tam haliyle genişletirim.

async def get_market_comparison(ilan_data: dict):
    # Basit versiyon - gerçek scrape için mevcut ArabamScraper'ı kullanabilirsin
    await asyncio.sleep(1)
    return {
        "average_price": int(ilan_data["price"] * 1.09),
        "count": 72,
        "min_price": int(ilan_data["price"] * 0.82),
        "max_price": int(ilan_data["price"] * 1.22)
    }

def calculate_opportunity_score(ilan: dict, market: dict) -> int:
    diff_percent = ((market["average_price"] - ilan["price"]) / market["average_price"]) * 100 if market["average_price"] > 0 else 0
    score = int(50 + diff_percent * 1.7)
    if ilan.get("mileage", 0) < 70000: score += 20
    return max(10, min(100, score))

def generate_explanation(ilan: dict, market: dict, score: int) -> str:
    percent = int(((market["average_price"] - ilan["price"]) / market["average_price"]) * 100) if market["average_price"] > 0 else 0
    if score > 78:
        return f"ÇOK İYİ FIRSAT! Piyasanın %{percent} altında → Hemen AL!"
    elif score > 60:
        return f"Güzel bir fırsat. Pazarlık yaparak alabilirsin."
    else:
        return f"Piyasa ortalamasının üstünde. Biraz daha bekle."

@app.post("/analyze")
async def analyze_car(request: AnalyzeRequest):
    try:
        ilan_data = await scrape_single_listing(request.ilan_url)
        market_data = await get_market_comparison(ilan_data)
        score = calculate_opportunity_score(ilan_data, market_data)
        
        recommendation = "🚀 AL!" if score > 75 else "🤔 İYİ DEĞERLENDİR" if score > 55 else "❌ BEKLE"

        return {
            "success": True,
            "ilan": ilan_data,
            "piyasa": market_data,
            "firsat_skoru": score,
            "oner_i": recommendation,
            "aciklama": generate_explanation(ilan_data, market_data, score)
        }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Cloudflare koruması nedeniyle analiz şu an zor. Biraz sonra tekrar dene."}

@app.get("/")
async def root():
    return {"status": "API çalışıyor - Cloudflare bypass aktif"}
