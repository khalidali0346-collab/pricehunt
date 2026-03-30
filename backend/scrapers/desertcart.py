"""Desertcart UAE — ships international products to UAE."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.desertcart.ae/search?q={quote_plus(query)}&sort_by=price_asc"
    headers = get_headers("https://www.desertcart.ae")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    for item in soup.select("div[class*='product'], article[class*='product']")[:20]:
        title_el = item.select_one("h2, h3, [class*='title'], [class*='name']")
        price_el = item.select_one("[class*='price']")
        link_el = item.select_one("a")
        img_el = item.select_one("img")

        if not title_el or not price_el:
            continue
        title = title_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True)
        price = parse_price(price_text)
        if not price:
            continue
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.desertcart.ae" + href
        results.append({
            "title": title, "price": price, "price_text": f"AED {price:,.2f}",
            "source": "Desertcart", "source_type": "web", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE (ships internationally)", "shipping": "International Delivery",
            "condition": "New", "currency": "AED",
        })
    return results
