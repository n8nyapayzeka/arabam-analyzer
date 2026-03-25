from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AnalyzeRequest(BaseModel):
    ilan_url: str

@app.get("/")
def root():
    return {"ok": True, "message": "root works"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return {
        "listing": {
            "ilan_url": req.ilan_url,
            "title": "Test İlanı",
            "brand": "Test",
            "model": "Model",
            "year": 2021,
            "mileage_km": 100000,
            "price": 800000,
            "currency": "TL",
            "city": "İstanbul",
            "fuel_type": "Benzin",
            "transmission": "Otomatik"
        },
        "market": {
            "comp_count": 3,
            "min_price": 780000,
            "median_price": 820000,
            "max_price": 850000,
            "avg_km": 95000,
            "samples": [
                "Test Emsal 1 | 780.000 TL",
                "Test Emsal 2 | 820.000 TL",
                "Test Emsal 3 | 850.000 TL"
            ]
        },
        "scores": {
            "firsat_skoru": 72,
            "risk_skoru": 35,
            "guven_skoru": 65,
            "likidite_skoru": 60,
            "decision_label": "✅ ALINABİLİR",
            "decision_reason": "Test cevap",
            "price_delta": -20000,
            "price_delta_percent": -2.44,
            "negotiation_min": 790000,
            "negotiation_max": 805000
        },
        "summary": {
            "title": "Test İlanı",
            "listing_price": 800000,
            "median_price": 820000,
            "difference": -20000,
            "difference_percent": -2.44,
            "firsat_skoru": 72,
            "risk_skoru": 35,
            "guven_skoru": 65,
            "likidite_skoru": 60,
            "decision_label": "✅ ALINABİLİR",
            "decision_reason": "Test cevap",
            "commentary": "Servis çalışıyor."
        }
    }
