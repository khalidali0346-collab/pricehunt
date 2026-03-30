"""Virgin Megastore UAE — electronics, gaming, entertainment."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.virginmegastore.ae/en/search?q={quote_plus(query)}&sort=price-asc"
    headers = get_headers("https://www.virginmegastore.ae")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Next.js data
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            products = (
                data.get("props", {}).get("pageProps", {})
                .get("searchResults", {}).get("hits", [])
                or data.get("props", {}).get("pageProps", {})
                .get("products", {}).get("hits", [])
            )
            for p in products[:20]:
                title = p.get("name", "") or p.get("title", "")
                price = p.get("price", {}).get("AED") or p.get("price") or p.get("salePrice")
                img = p.get("image", "") or p.get("thumbnail", "")
                sku = p.get("sku", "") or p.get("objectID", "")
                if not title or not price:
                    continue
                results.append({
                    "title": title, "price": float(price),
                    "price_text": f"AED {float(price):,.2f}",
                    "source": "Virgin Megastore", "source_type": "web",
                    "url": f"https://www.virginmegastore.ae/en/product/{sku}",
                    "image": img, "location": "UAE (online + in-store)",
                    "shipping": "Home Delivery / In-store", "condition": "New", "currency": "AED",
                })
            if results:
                return results
        except Exception:
            pass

    # HTML fallback
    for item in soup.select("div[class*='product'], li[class*='product']")[:20]:
        title_el = item.select_one("h2, h3, [class*='name'], [class*='title']")
        price_el = item.select_one("[class*='price']")
        link_el = item.select_one("a")
        img_el = item.select_one("img")
        if not title_el or not price_el:
            continue
        title = title_el.get_text(strip=True)
        price = parse_price(price_el.get_text(strip=True))
        if not price:
            continue
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.virginmegastore.ae" + href
        results.append({
            "title": title, "price": price, "price_text": f"AED {price:,.2f}",
            "source": "Virgin Megastore", "source_type": "web", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE (online + in-store)", "shipping": "Home Delivery / In-store",
            "condition": "New", "currency": "AED",
        })
    return results
