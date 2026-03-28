"""Noon.com scraper — biggest MENA e-commerce platform."""
import httpx
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    # Noon has a search API endpoint
    url = f"https://www.noon.com/uae-en/search/?q={quote_plus(query)}&sortBy=price_asc"
    headers = get_headers("https://www.noon.com")
    headers["Accept-Language"] = "en-AE,en;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Try to extract from embedded JSON (Next.js __NEXT_DATA__)
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            hits = (
                data.get("props", {})
                .get("pageProps", {})
                .get("catalog", {})
                .get("hits", [])
            )
            for hit in hits[:20]:
                title = hit.get("name", "")
                price = hit.get("sale_price") or hit.get("price")
                sku = hit.get("sku", "")
                img = hit.get("image_keys", [""])[0]
                img_url = f"https://f.nooncdn.com/p/{img}?format=avif" if img else None
                brand = hit.get("brand", "")

                if not title or not price:
                    continue

                results.append({
                    "title": f"{brand} {title}".strip() if brand else title,
                    "price": float(price),
                    "price_text": f"AED {float(price):,.2f}",
                    "source": "Noon",
                    "source_type": "web",
                    "url": f"https://www.noon.com/uae-en/{sku}/",
                    "image": img_url,
                    "location": "UAE",
                    "shipping": "Noon Express",
                    "condition": "New",
                    "currency": "AED",
                })
            if results:
                return results
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # HTML fallback
    for item in soup.select("div[class*='productContainer']")[:20]:
        title_el = item.select_one("[class*='name']") or item.select_one("h3")
        price_el = item.select_one("[class*='price']") or item.select_one("strong")
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
            href = "https://www.noon.com" + href

        results.append({
            "title": title,
            "price": price,
            "price_text": f"AED {price:,.2f}",
            "source": "Noon",
            "source_type": "web",
            "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE",
            "shipping": "Noon Express",
            "condition": "New",
            "currency": "AED",
        })

    return results
