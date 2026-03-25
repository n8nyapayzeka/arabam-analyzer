from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import re

app = FastAPI()

class AnalyzeRequest(BaseModel):
    ilan_url: str

def clean_int(text):
    try:
        return int(re.sub(r"[^\d]", "", text))
    except:
        return None

@app.get("/")
def root():
    return {"ok": True}

@app.get("/health")
def health():
    return {"ok": True}

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
            price = clean_int(price_text)

            # DETAYLAR
            details = page.locator("li").all_inner_texts()

            year = None
            km = None

            for d in details:
                if "Model Yılı" in d:
                    year = clean_int(d)
                if "Kilometre" in d:
                    km = clean_int(d)

            browser.close()

        # BASİT PİYASA MODELİ (ilk versiyon)
        if price:
            estimated_market = int(price * 1.08)
        else:
            estimated_market = 0

        delta = estimated_market - price if price else 0
        percent = round((delta / price) * 100, 2) if price else 0

        # SKOR
        firsat = 80 if delta > 0 else 40
        risk = 30 if delta > 0 else 60

        decision = "✅ ALINABİLİR" if delta > 0 else "❌ PAHALI"

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
                "city": "-",
                "fuel_type": "-",
                "transmission": "-"
            },
            "market": {
                "comp_count": 5,
                "min_price": int(price * 0.95),
                "median_price": estimated_market,
                "max_price": int(price * 1.15),
                "avg_km": km,
                "samples": [
                    "Algoritmik tahmin 1",
                    "Algoritmik tahmin 2",
                    "Algoritmik tahmin 3"
                ]
            },
            "scores": {
                "firsat_skoru": firsat,
                "risk_skoru": risk,
                "guven_skoru": 70,
                "likidite_skoru": 65,
                "decision_label": decision,
                "decision_reason": "İlk gerçek analiz versiyonu",
                "price_delta": delta,
                "price_delta_percent": percent,
                "negotiation_min": int(price * 0.97),
                "negotiation_max": int(price * 1.00)
            },
            "summary": {
                "title": title,
                "listing_price": price,
                "median_price": estimated_market,
                "difference": delta,
                "difference_percent": percent,
                "firsat_skoru": firsat,
                "risk_skoru": risk,
                "guven_skoru": 70,
                "likidite_skoru": 65,
                "decision_label": decision,
                "decision_reason": "İlk gerçek analiz versiyonu",
                "commentary": "Gerçek veri + algoritmik tahmin"
            }
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
