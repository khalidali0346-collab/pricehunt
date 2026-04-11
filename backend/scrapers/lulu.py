"""Lulu Hypermarket UAE — Playwright-powered."""
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .browser import fetch_rendered
from .utils import parse_price

BASE = "https://www.luluhypermarket.com"


async def scrape(query: str) -> list[dict]:
    url = f"{BASE}/en-ae/search?q={quote_plus(query)}&sortBy=Price+ascending"
    html = await fetch_rendered(url, wait_selector="div.product-item, li.product-item, div[class*='product-card']")
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    for item in soup.select("div.product-item, li.product-item, div[class*='product-card']")[:20]:
        title_el = item.select_one("h2, h3, [class*='name'], [class*='title']")
        price_el = item.select_one("[class*='price'], span.price")
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
            "source": "Lulu Hypermarket", "source_type": "web", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE (online + in-store)", "shipping": "Home Delivery / In-store",
            "condition": "New", "currency": "AED",
        })
    return results
