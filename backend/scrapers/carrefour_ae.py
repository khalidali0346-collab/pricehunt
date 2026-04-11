"""Carrefour UAE scraper — Playwright-powered."""
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .browser import fetch_rendered
from .utils import parse_price

BASE = "https://www.carrefouruae.com"


async def scrape(query: str) -> list[dict]:
    url = f"{BASE}/mafuae/en/search?keyword={quote_plus(query)}&sortBy=price-asc"
    html = await fetch_rendered(
        url,
        wait_selector="div[class*='product-card'], div[class*='productCard'], div[class*='product-item']",
    )
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    # ── __NEXT_DATA__ ──
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            pp = data.get("props", {}).get("pageProps", {})
            products = (
                pp.get("initialData", {}).get("data", {}).get("products")
                or pp.get("products")
                or pp.get("catalog", {}).get("products")
                or pp.get("data", {}).get("products")
                or []
            )
            for p in products[:20]:
                title = p.get("name", "")
                pi = p.get("price", {})
                price = pi.get("sale") or pi.get("regular") or pi.get("value")
                img = p.get("image", {}).get("url", "") if isinstance(p.get("image"), dict) else p.get("image", "")
                slug = p.get("slug", "") or p.get("url", "")
                if not title or not price:
                    continue
                results.append({
                    "title": title, "price": float(price),
                    "price_text": f"AED {float(price):,.2f}",
                    "source": "Carrefour UAE", "source_type": "web",
                    "url": f"{BASE}/mafuae/en/{slug}" if slug else BASE,
                    "image": img, "location": "UAE (online + in-store)",
                    "shipping": "Home Delivery / Click & Collect", "condition": "New", "currency": "AED",
                })
            if results:
                return results
        except Exception:
            pass

    # ── HTML fallback ──
    for item in soup.select("div[class*='product-card'], div[class*='productCard']")[:20]:
        title_el = item.select_one("h2, h3, [class*='title'], [class*='name']")
        price_el = item.select_one("[class*='price']")
        link_el = item.select_one("a")
        img_el = item.select_one("img")
        if not title_el or not price_el:
            continue
        title = title_el.get_text(strip=True)
        price = parse_price(price_el.get_text(strip=True))
        if not title or not price:
            continue
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = BASE + href
        results.append({
            "title": title, "price": price, "price_text": f"AED {price:,.2f}",
            "source": "Carrefour UAE", "source_type": "web", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE (online + in-store)", "shipping": "Home Delivery / Click & Collect",
            "condition": "New", "currency": "AED",
        })
    return results
