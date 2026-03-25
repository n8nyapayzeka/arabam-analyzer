from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Arabam Analyzer")

class AnalyzeRequest(BaseModel):
    ilan_url: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return {
        "success": True,
        "ilan_url": req.ilan_url,
        "message": "Servis çalışıyor. Şimdi gerçek Playwright scraping ve skor motoru eklenecek."
    }
