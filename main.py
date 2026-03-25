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

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/134.0.0.0 Safari/537.36"
                ),
                locale="tr-TR",
                viewport={"width": 1440, "height": 2200},
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
                },
            )

            page = context.new_page()

            try:
                page.goto(url, timeout=90000, wait_until="domcontentloaded")
            except Exception:
                page.goto(url, timeout=90000)

            page.wait_for_timeout(5000)

            cookie_selectors = [
                "button:has-text('Kabul Et')",
                "button:has-text('Tümünü Kabul Et')",
                "button:has-text('Anladım')",
                "button:has-text('Tamam')",
                "[id*='accept']",
                "[class*='accept']",
            ]

            for sel in cookie_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.click(timeout=2000)
                        page.wait_for_timeout(1500)
                        break
                except Exception:
                    pass

            current_url = page.url

            try:
                body_text = page.locator("body").inner_text(timeout=8000)
            except Exception:
                body_text = ""

            if "/ilan/" not in current_url:
                raise Exception(f"İlan sayfasına gidilemedi. Açılan sayfa: {current_url}")

            if (
                "{{advertCity}}" in body_text
                or "{{advertYear}}" in body_text
                or "{{advertTitle}}" in body_text
                or "2. EL ARABA VİTRİN İLANLARI" in body_text
            ):
                raise Exception("İlan sayfası yerine anasayfa/şablon içerik geldi")

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

            if title == "-" or len(title) < 4:
                title_patterns = [
                    r"İlan Başlığı[:\s]*([^\n]+)",
                    r"\b((?:19|20)\d{2}[^\n]{5,})",
                ]
                title_from_text = extract_with_regex(title_patterns, body_text)
                if title_from_text:
                    title = title_from_text.strip()

            if title == "-" or len(title) < 4:
                slug = current_url.strip("/").split("/")[-1]
                title = slug.replace("-", " ").title()

            # PRICE
            price = None

            price_match = re.search(r"(\d[\d\.\, ]{2,})\s*TL", body_text, re.IGNORECASE)
            if price_match:
                price = clean_int(price_match.group(0))

            if not price:
                price_selectors = [
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
                            txt = loc.inner_text(timeout=4000).strip()
                            val = clean_int(txt)
                            if val and val > 10000:
                                price = val
                                break
                    except Exception:
                        pass

            if not price:
                raise Exception("Fiyat bilgisi bulunamadı")

            # DETAIL AREA
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
                r"\b(İstanbul|Ankara|İzmir|Bursa|Antalya|Adana|Konya|Gaziantep|Mersin|Kocaeli|Samsun|Kayseri|Eskişehir|Sakarya|Diyarbakır|Hatay|Aydın|Muğla|Balıkesir)\b",
            ]
            city_str = extract_with_regex(city_patterns, joined_details)
            if city_str:
                city = city_str.strip()

            context.close()
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
        reason = "Gerçek veri + geliştirilmiş parse"

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
                "commentary": "Gerçek veri + geliştirilmiş parse",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
