"""Noon.com scraper — Playwright-powered for full JS rendering."""
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .browser import fetch_rendered
from .utils import parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.noon.com/uae-en/search/?q={quote_plus(query)}&sortBy=price_asc"
    html = await fetch_rendered(
        url,
        wait_selector="[data-qa='product-block'], div[class*='productContainer'], div[class*='product-card']",
    )
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    # ── 1. __NEXT_DATA__ JSON (populated after hydration) ──
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            pp = data.get("props", {}).get("pageProps", {})
            hits = (
                pp.get("catalog", {}).get("hits")
                or pp.get("searchResults", {}).get("hits")
                or pp.get("initialState", {}).get("catalog", {}).get("hits")
                or pp.get("items")
                or pp.get("hits")
                or []
            )
            for h in hits[:20]:
                title = h.get("name", "") or h.get("title", "")
                brand = h.get("brand", "") or h.get("brand_name", "")
                if brand and not title.lower().startswith(brand.lower()):
                    title = f"{brand} {title}".strip()
                price = h.get("sale_price") or h.get("price") or h.get("current_price")
                if not title or price is None:
                    continue
                sku = h.get("sku", "") or h.get("id", "")
                img_keys = h.get("image_keys") or h.get("images") or []
                img_key = img_keys[0] if img_keys else h.get("thumbnail", "") or h.get("image", "")
                img_url = (
                    f"https://f.nooncdn.com/p/{img_key}?format=avif"
                    if img_key and not img_key.startswith("http") else img_key or None
                )
                results.append({
                    "title": title, "price": float(price),
                    "price_text": f"AED {float(price):,.2f}",
                    "source": "Noon", "source_type": "web",
                    "url": f"https://www.noon.com/uae-en/{sku}/",
                    "image": img_url, "location": "UAE",
                    "shipping": "Noon Express", "condition": "New", "currency": "AED",
                })
            if results:
                return results
        except Exception:
            pass

    # ── 2. HTML fallback ──
    for item in soup.select("[data-qa='product-block'], div[class*='productContainer'], div[class*='product-card']")[:20]:
        title_el = item.select_one("[class*='name']") or item.select_one("h3") or item.select_one("h2")
        price_el = item.select_one("[class*='price']") or item.select_one("strong")
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
            href = "https://www.noon.com" + href
        results.append({
            "title": title, "price": price, "price_text": f"AED {price:,.2f}",
            "source": "Noon", "source_type": "web", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE", "shipping": "Noon Express", "condition": "New", "currency": "AED",
        })
    return results
