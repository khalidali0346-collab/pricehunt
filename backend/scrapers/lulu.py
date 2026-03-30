"""Lulu Hypermarket UAE — largest hypermarket chain in the Gulf."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.luluhypermarket.com/en-ae/search?q={quote_plus(query)}&sortBy=Price+ascending"
    headers = get_headers("https://www.luluhypermarket.com")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Try embedded JSON first
    for script in soup.find_all("script", type="application/json"):
        try:
            data = json.loads(script.string or "")
            products = data.get("products") or data.get("items") or []
            for p in products[:20]:
                title = p.get("name") or p.get("title", "")
                price = p.get("price") or p.get("salePrice") or p.get("finalPrice")
                img = p.get("image") or p.get("imageUrl") or p.get("thumbnail", "")
                url_path = p.get("url") or p.get("pdpUrl", "")
                if not title or not price:
                    continue
                if not url_path.startswith("http"):
                    url_path = "https://www.luluhypermarket.com" + url_path
                results.append({
                    "title": title, "price": float(price),
                    "price_text": f"AED {float(price):,.2f}",
                    "source": "Lulu Hypermarket", "source_type": "web",
                    "url": url_path, "image": img,
                    "location": "UAE (online + in-store)",
                    "shipping": "Home Delivery / In-store", "condition": "New", "currency": "AED",
                })
            if results:
                return results
        except Exception:
            continue

    # HTML fallback
    for item in soup.select("div.product-item, li.product-item, div[class*='product-card']")[:20]:
        title_el = item.select_one("h2, h3, [class*='name'], [class*='title']")
        price_el = item.select_one("[class*='price'], span.price")
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
            href = "https://www.luluhypermarket.com" + href
        results.append({
            "title": title, "price": price, "price_text": f"AED {price:,.2f}",
            "source": "Lulu Hypermarket", "source_type": "web", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE (online + in-store)", "shipping": "Home Delivery / In-store",
            "condition": "New", "currency": "AED",
        })
    return results
