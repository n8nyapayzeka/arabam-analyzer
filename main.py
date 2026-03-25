from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import re

app = FastAPI()


class AnalyzeRequest(BaseModel):
    ilan_url: str


def clean_int(text):
    try:
        return int(re.sub(r"[^\d]", "", str(text)))
    except Exception:
        return None


def extract_with_regex(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip() if m.groups() else m.group(0).strip()
    return None


@app.get("/")
def root():
    return {"ok": True, "message": "root works"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    url = req.ilan_url.strip()

    if "arabam.com" not in url:
        raise HTTPException(status_code=400, detail="Geçerli bir arabam.com linki gönder.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/134.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 2200},
            )

            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            body_text = ""
            try:
                body_text = page.locator("body").inner_text(timeout=5000)
            except Exception:
                body_text = ""

            # TITLE
            title = "-"
            title_selectors = [
                "h1",
                "[class*='title'] h1",
                "[class*='product-title']",
                "title",
            ]

            for sel in title_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        txt = loc.inner_text(timeout=5000).strip()
                        if txt and len(txt) > 2:
                            title = txt
                            break
                except Exception:
                    pass

            if title == "-" and body_text:
                first_line = body_text.splitlines()[0].strip() if body_text.splitlines() else ""
                if first_line:
                    title = first_line

            # PRICE
            price = None
            price_text = None

            price_selectors = [
                "text=/[0-9\\., ]+\\s*TL/i",
                "[class*='price']",
                "[class*='listing-price']",
                "[class*='product-price']",
                "[data-testid*='price']",
                "xpath=//*[contains(text(),'TL')]",
            ]

            for sel in price_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        txt = loc.inner_text(timeout=5000).strip()
                        val = clean_int(txt)
                        if val and val > 10000:
                            price_text = txt
                            price = val
                            break
                except Exception:
                    pass

            if not price and body_text:
                m = re.search(r"(\d[\d\.\, ]{3,})\s*TL", body_text, re.IGNORECASE)
                if m:
                    price_text = m.group(0)
                    price = clean_int(price_text)

            if not price:
                raise Exception("Fiyat bilgisi bulunamadı")

            # DETAIL TEXTS
            detail_texts = []
            try:
                detail_texts = page.locator("li").all_inner_texts()
            except Exception:
                detail_texts = []

            joined_details = "\n".join(detail_texts) + "\n" + body_text

            # YEAR
            year = None
            year_patterns = [
                r"Model Yılı[:\s]*([12][09]\d{2}|20\d{2})",
                r"\b([12][09]\d{2}|20\d{2})\b",
            ]
            year_str = extract_with_regex(year_patterns, joined_details)
            if year_str:
                year = clean_int(year_str)

            # KM
            km = None
            km_patterns = [
                r"Kilometre[:\s]*([\d\.\, ]+)",
                r"KM[:\s]*([\d\.\, ]+)",
                r"(\d[\d\.\, ]{2,})\s*km\b",
            ]
            km_str = extract_with_regex(km_patterns, joined_details)
            if km_str:
                km = clean_int(km_str)

            # FUEL
            fuel = "-"
            fuel_patterns = [
                r"Yakıt Tipi[:\s]*([^\n]+)",
                r"Yakıt[:\s]*([^\n]+)",
            ]
            fuel_str = extract_with_regex(fuel_patterns, joined_details)
            if fuel_str:
                fuel = fuel_str.strip()

            # TRANSMISSION
            transmission = "-"
            transmission_patterns = [
                r"Vites Tipi[:\s]*([^\n]+)",
                r"Vites[:\s]*([^\n]+)",
            ]
            transmission_str = extract_with_regex(transmission_patterns, joined_details)
            if transmission_str:
                transmission = transmission_str.strip()

            # CITY
            city = "-"
            city_patterns = [
                r"Şehir[:\s]*([^\n]+)",
                r"İl[:\s]*([^\n]+)",
            ]
            city_str = extract_with_regex(city_patterns, joined_details)
            if city_str:
                city = city_str.strip()

            browser.close()

        # Basit ilk piyasa modeli
        estimated_market = int(price * 1.08)
        delta = estimated_market - price
        percent = round((delta / price) * 100, 2) if price else 0

        firsat = 80 if delta > 0 else 40
        risk = 30 if delta > 0 else 60
        guven = 70 if delta > 0 else 45
        likidite = 65

        decision = "✅ ALINABİLİR" if delta > 0 else "❌ PAHALI"
        reason = "İlk gerçek analiz versiyonu"

        title_parts = title.split()
        brand = title_parts[0] if len(title_parts) > 0 else "-"
        model = title_parts[1] if len(title_parts) > 1 else "-"

        return {
            "listing": {
                "ilan_url": url,
                "title": title,
                "brand": brand,
                "model": model,
                "year": year,
                "mileage_km": km,
                "price": price,
                "currency": "TL",
                "city": city,
                "fuel_type": fuel,
                "transmission": transmission,
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
                    "Algoritmik tahmin 3",
                ],
            },
            "scores": {
                "firsat_skoru": firsat,
                "risk_skoru": risk,
                "guven_skoru": guven,
                "likidite_skoru": likidite,
                "decision_label": decision,
                "decision_reason": reason,
                "price_delta": delta,
                "price_delta_percent": percent,
                "negotiation_min": int(price * 0.97),
                "negotiation_max": int(price * 1.00),
            },
            "summary": {
                "title": title,
                "listing_price": price,
                "median_price": estimated_market,
                "difference": delta,
                "difference_percent": percent,
                "firsat_skoru": firsat,
                "risk_skoru": risk,
                "guven_skoru": guven,
                "likidite_skoru": likidite,
                "decision_label": decision,
                "decision_reason": reason,
                "commentary": "Gerçek veri + algoritmik tahmin",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
