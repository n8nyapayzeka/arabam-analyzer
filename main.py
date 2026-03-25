from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse

app = FastAPI(title="Arabam Analyzer")


class AnalyzeRequest(BaseModel):
    ilan_url: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if "arabam.com" not in req.ilan_url:
        raise HTTPException(status_code=400, detail="Geçerli bir arabam.com linki gönder.")

    parsed = urlparse(req.ilan_url)
    slug = parsed.path.strip("/").split("/")[-1] if parsed.path else "ilan"

    title = slug.replace("-", " ").title() if slug else "Arabam İlanı"

    response = {
        "listing": {
            "ilan_url": req.ilan_url,
            "title": title,
            "brand": "Örnek Marka",
            "model": "Örnek Model",
            "year": 2021,
            "mileage_km": 82000,
            "price": 865000,
            "currency": "TL",
            "city": "İstanbul",
            "fuel_type": "Benzin",
            "transmission": "Otomatik"
        },
        "market": {
            "comp_count": 18,
            "min_price": 825000,
            "median_price": 910000,
            "max_price": 975000,
            "avg_km": 87000,
            "samples": [
                "Örnek Emsal 1 | 899.000 TL",
                "Örnek Emsal 2 | 915.000 TL",
                "Örnek Emsal 3 | 928.000 TL"
            ]
        },
        "scores": {
            "firsat_skoru": 78,
            "risk_skoru": 32,
            "guven_skoru": 68,
            "likidite_skoru": 74,
            "decision_label": "✅ ALINABİLİR",
            "decision_reason": "Test sürümü: n8n entegrasyon kontrolü başarılı.",
            "price_delta": -45000,
            "price_delta_percent": -4.95,
            "negotiation_min": 875000,
            "negotiation_max": 895000
        },
        "summary": {
            "title": title,
            "listing_price": 865000,
            "median_price": 910000,
            "difference": -45000,
            "difference_percent": -4.95,
            "firsat_skoru": 78,
            "risk_skoru": 32,
            "guven_skoru": 68,
            "likidite_skoru": 74,
            "decision_label": "✅ ALINABİLİR",
            "decision_reason": "Test sürümü: n8n entegrasyon kontrolü başarılı.",
            "commentary": "Bu cevap test amaçlıdır. n8n akışının response formatı kontrol ediliyor."
        }
    }

    return response
