"""Jumbo Electronics UAE — leading electronics retailer."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.jumbo.ae/catalogsearch/result/?q={quote_plus(query)}&product_list_order=price"
    headers = get_headers("https://www.jumbo.ae")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    for item in soup.select("li.product-item, div.product-item")[:20]:
        title_el = (
            item.select_one("a.product-item-link")
            or item.select_one("[class*='product-name']")
            or item.select_one("h2, h3")
        )
        price_el = item.select_one("span.price") or item.select_one("[class*='price']")
        link_el = item.select_one("a.product-item-link") or item.select_one("a")
        img_el = item.select_one("img.product-image-photo") or item.select_one("img")

        if not title_el or not price_el:
            continue
        title = title_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True)
        price = parse_price(price_text)
        if not price:
            continue
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.jumbo.ae" + href
        results.append({
            "title": title, "price": price, "price_text": f"AED {price:,.2f}",
            "source": "Jumbo Electronics", "source_type": "web", "url": href,
            "image": img_el.get("src", "") or img_el.get("data-src", "") if img_el else None,
            "location": "UAE (online + in-store)", "shipping": "Home Delivery / In-store",
            "condition": "New", "currency": "AED",
        })
    return results
