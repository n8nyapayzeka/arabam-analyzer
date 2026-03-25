from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

app = FastAPI(title="Arabam Analiz API")

class AnalyzeRequest(BaseModel):
    ilan_url: str

async def scrape_single_listing(url: str):
    if not url.startswith("https://www.arabam.com/ilan/"):
        raise ValueError("Geçersiz link")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        await asyncio.sleep(6)   # Cloudflare beklemesi

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Basit veri çekme
        title = soup.find('h1')
        full_title = title.get_text(strip=True) if title else "Bilinmiyor"

        price_text = re.sub(r'[^\d]', '', soup.find(string=re.compile(r'\d.*TL')) or "0")
        price = int(price_text) if price_text.isdigit() else 0

        data = {
            "url": url,
            "full_title": full_title,
            "price": price,
            "brand": full_title.split()[0] if full_title != "Bilinmiyor" else "Bilinmiyor",
            "model": " ".join(full_title.split()[1:]),
            "year": 2023,   # şimdilik sabit, sonra geliştireceğiz
            "mileage": 50000
        }
        return data

    finally:
        if driver:
            driver.quit()

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        ilan = await scrape_single_listing(request.ilan_url)
        return {
            "success": True,
            "ilan": ilan,
            "firsat_skoru": 65,
            "oner_i": "🤔 İYİ DEĞERLENDİR",
            "aciklama": "Test modunda çalışıyoruz. Tam analiz yakında gelecek."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def home():
    return {"status": "API canlı - Railway deploy başarılı"}
