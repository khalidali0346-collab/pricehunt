"""Sharaf DG UAE — Magento 2 store."""
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .browser import fetch_with_session, fetch_rendered
from .utils import parse_price

BASE = "https://www.sharafdg.com"


async def scrape(query: str) -> list[dict]:
    url = f"{BASE}/search?q={quote_plus(query)}&product_list_order=price"
    html = await fetch_with_session(url, BASE)
    if not html or "product-item" not in html:
        html = await fetch_rendered(url, wait_selector="li.product-item, div.product-item")
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    for item in soup.select("li.product-item, div.product-item, div[class*='product-card']")[:20]:
        title_el = (
            item.select_one("a.product-item-link")
            or item.select_one("[class*='product-name']")
            or item.select_one("h2, h3")
        )
        price_el = item.select_one("span.price") or item.select_one("[class*='price']")
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
            "source": "Sharaf DG", "source_type": "web", "url": href,
            "image": img_el.get("src") or img_el.get("data-src", "") if img_el else None,
            "location": "UAE (online + in-store)", "shipping": "Home Delivery / In-store",
            "condition": "New", "currency": "AED",
        })
    return results
