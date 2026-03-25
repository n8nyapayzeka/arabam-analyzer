from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import re

app = FastAPI()

class AnalyzeRequest(BaseModel):
    ilan_url: str

def parse_price(text):
    try:
        return int(re.sub(r"[^\d]", "", text))
    except:
        return 0

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    url = req.ilan_url

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)

            page.wait_for_timeout(3000)

            # BAŞLIK
            title = page.locator("h1").first.inner_text()

            # FİYAT
            price_text = page.locator("text=TL").first.inner_text()
            price = parse_price(price_text)

            # DETAYLAR
            details = page.locator("li").all_inner_texts()

            year = None
            km = None
            fuel = None
            transmission = None
            city = None

            for d in details:
                if "Model Yılı" in d:
                    year = int(re.sub(r"[^\d]", "", d))
                if "Kilometre" in d:
                    km = int(re.sub(r"[^\d]", "", d))
                if "Yakıt Tipi" in d:
                    fuel = d.split(":")[-1].strip()
                if "Vites Tipi" in d:
                    transmission = d.split(":")[-1].strip()
                if "Şehir" in d:
                    city = d.split(":")[-1].strip()

            browser.close()

        # BASİT ANALİZ (SONRA GELİŞTİRECEĞİZ)
        median_price = int(price * 1.05)

        return {
            "listing": {
                "ilan_url": url,
                "title": title,
                "brand": title.split()[0] if title else "-",
                "model": title.split()[1] if title else "-",
                "year": year,
                "mileage_km": km,
                "price": price,
                "currency": "TL",
                "city": city,
                "fuel_type": fuel,
                "transmission": transmission
            },
            "market": {
                "comp_count": 5,
                "min_price": int(price * 0.95),
                "median_price": median_price,
                "max_price": int(price * 1.1),
                "avg_km": km,
                "samples": [
                    "Benzer ilan 1",
                    "Benzer ilan 2",
                    "Benzer ilan 3"
                ]
            },
            "scores": {
                "firsat_skoru": 70,
                "risk_skoru": 40,
                "guven_skoru": 60,
                "likidite_skoru": 65,
                "decision_label": "🟡 ORTA",
                "decision_reason": "İlk versiyon analiz",
                "price_delta": median_price - price,
                "price_delta_percent": round(((median_price - price)/price)*100,2),
                "negotiation_min": int(price * 0.97),
                "negotiation_max": int(price * 1.00)
            },
            "summary": {
                "title": title,
                "listing_price": price,
                "median_price": median_price,
                "difference": median_price - price,
                "difference_percent": round(((median_price - price)/price)*100,2),
                "firsat_skoru": 70,
                "risk_skoru": 40,
                "guven_skoru": 60,
                "likidite_skoru": 65,
                "decision_label": "🟡 ORTA",
                "decision_reason": "İlk versiyon analiz",
                "commentary": "Gerçek veri çekildi"
            }
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
