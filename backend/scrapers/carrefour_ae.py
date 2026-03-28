"""Carrefour UAE scraper — major physical + online retailer in UAE/MENA."""
import httpx
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.carrefouruae.com/mafuae/en/search?keyword={quote_plus(query)}&sortBy=price-asc"
    headers = get_headers("https://www.carrefouruae.com")
    headers["Accept-Language"] = "en-AE,en;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Try Next.js embedded JSON
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            products = (
                data.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("data", {})
                .get("products", [])
            )
            for p in products[:20]:
                title = p.get("name", "")
                price_info = p.get("price", {})
                price = price_info.get("sale") or price_info.get("regular")
                img = p.get("image", {}).get("url", "")
                slug = p.get("slug", "")

                if not title or not price:
                    continue

                results.append({
                    "title": title,
                    "price": float(price),
                    "price_text": f"AED {float(price):,.2f}",
                    "source": "Carrefour UAE",
                    "source_type": "web",
                    "url": f"https://www.carrefouruae.com/mafuae/en/{slug}",
                    "image": img,
                    "location": "UAE (online + in-store)",
                    "shipping": "Home Delivery / Click & Collect",
                    "condition": "New",
                    "currency": "AED",
                })
            if results:
                return results
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # HTML fallback
    for item in soup.select("div[class*='product-card'], div[class*='productCard']")[:20]:
        title_el = item.select_one("[class*='title'], [class*='name'], h3, h2")
        price_el = item.select_one("[class*='price'], [class*='Price']")
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
            href = "https://www.carrefouruae.com" + href

        results.append({
            "title": title,
            "price": price,
            "price_text": f"AED {price:,.2f}",
            "source": "Carrefour UAE",
            "source_type": "web",
            "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE (online + in-store)",
            "shipping": "Home Delivery / Click & Collect",
            "condition": "New",
            "currency": "AED",
        })

    return results
