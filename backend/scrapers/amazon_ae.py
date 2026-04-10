"""Amazon.ae — UAE Amazon store."""
import httpx, json, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.amazon.ae"

async def scrape(query):
    url = f"{BASE}/s?k={quote_plus(query)}&s=price-asc-rank"
    h = get_headers(BASE)
    h["Accept-Language"] = "en-AE,en;q=0.9"
    h["Cookie"] = "i18n-prefs=AED; sp-cdn=\"L5Z9:AE\""
    results = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25, http2=True) as c:
            r = await c.get(url, headers=h)
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    for item in soup.select("div[data-component-type='s-search-result']")[:24]:
        try:
            title_el = item.select_one("h2 a span") or item.select_one("h2 span")
            pw = item.select_one("span.a-price-whole")
            pf = item.select_one("span.a-price-fraction")
            link_el = item.select_one("h2 a")
            img_el = item.select_one("img.s-image")
            rating_el = item.select_one("span.a-icon-alt")
            review_el = item.select_one("span.a-size-base.s-underline-text")
            badge_el = item.select_one("span.a-badge-text")

            if not title_el or not pw:
                continue

            frac = pf.get_text(strip=True) if pf else "00"
            price_str = pw.get_text(strip=True).replace(",","") + "." + frac
            price = parse_price(price_str)
            if not price:
                continue

            href = link_el.get("href","") if link_el else ""
            if href and not href.startswith("http"):
                href = BASE + href

            results.append(make_result(
                title=title_el.get_text(strip=True),
                price=price, price_text=f"AED {price:,.2f}",
                source="Amazon.ae", source_type="web", store_type="both",
                url=href, image=img_el.get("src","") if img_el else "",
                location="UAE — Fast Delivery",
                shipping="FREE delivery on eligible orders",
                condition=badge_el.get_text(strip=True) if badge_el else "New",
                rating=rating_el.get_text(strip=True) if rating_el else "",
            ))
        except Exception:
            continue
    return results
