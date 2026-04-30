"""Microless UAE — electronics retailer with SSR HTML (WooCommerce/custom)."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

BASE = "https://www.microless.com"


async def scrape(query: str) -> list[dict]:
    url = f"{BASE}/search/?searchtext={quote_plus(query)}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20, http2=True) as client:
            r = await client.get(url, headers=get_headers(BASE))
            if r.status_code != 200:
                return []
            html = r.text
    except Exception:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    items = (
        soup.select("div.product-grid-item")
        or soup.select("li.product")
        or soup.select("div[class*='product-item']")
        or soup.select("div[class*='product-card']")
    )

    for item in items[:20]:
        title_el = (
            item.select_one("h2.woocommerce-loop-product__title")
            or item.select_one("[class*='product-name']")
            or item.select_one("[class*='product-title']")
            or item.select_one("h2, h3")
        )
        price_el = (
            item.select_one("span.price")
            or item.select_one("[class*='price']")
        )
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

        img_src = ""
        if img_el:
            img_src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")

        results.append({
            "title": title,
            "price": price,
            "price_text": f"AED {price:,.2f}",
            "source": "Microless",
            "source_type": "web",
            "url": href,
            "image": img_src,
            "location": "UAE",
            "shipping": "Delivery across UAE",
            "condition": "New",
            "currency": "AED",
        })

    return results
