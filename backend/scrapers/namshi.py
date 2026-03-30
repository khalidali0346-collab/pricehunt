"""Namshi UAE — fashion and lifestyle e-commerce."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    # Namshi has an internal API used by their frontend
    api_url = (
        f"https://www.namshi.com/api/catalog/search"
        f"?q={quote_plus(query)}&lang=en&country=AE&sortBy=price_asc&page=1&limit=20"
    )
    headers = get_headers("https://www.namshi.com")
    headers["Accept"] = "application/json"
    headers["X-Requested-With"] = "XMLHttpRequest"

    results = []

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(api_url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                products = (
                    data.get("products") or data.get("hits")
                    or data.get("data", {}).get("products", [])
                )
                for p in products[:20]:
                    title = p.get("name") or p.get("title", "")
                    price = p.get("price") or p.get("sale_price") or p.get("currentPrice")
                    img = p.get("image") or p.get("imageUrl", "")
                    slug = p.get("url") or p.get("slug", "")
                    if not title or not price:
                        continue
                    if not slug.startswith("http"):
                        slug = "https://www.namshi.com" + slug
                    results.append({
                        "title": title, "price": float(price),
                        "price_text": f"AED {float(price):,.2f}",
                        "source": "Namshi", "source_type": "web",
                        "url": slug, "image": img,
                        "location": "UAE", "shipping": "Free Delivery over AED 100",
                        "condition": "New", "currency": "AED",
                    })
                if results:
                    return results
    except Exception:
        pass

    # HTML fallback
    try:
        web_url = f"https://www.namshi.com/en-ae/search/?q={quote_plus(query)}&sortBy=price_asc"
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(web_url, headers=get_headers("https://www.namshi.com"))
            soup = BeautifulSoup(r.text, "lxml")
            script = soup.select_one("script#__NEXT_DATA__")
            if script:
                data = json.loads(script.string)
                prods = (
                    data.get("props", {}).get("pageProps", {})
                    .get("catalog", {}).get("products", [])
                )
                for p in prods[:20]:
                    title = p.get("name", "")
                    price = p.get("price") or p.get("salePrice")
                    if not title or not price:
                        continue
                    results.append({
                        "title": title, "price": float(price),
                        "price_text": f"AED {float(price):,.2f}",
                        "source": "Namshi", "source_type": "web",
                        "url": f"https://www.namshi.com/en-ae/{p.get('slug', '')}",
                        "image": p.get("image", ""), "location": "UAE",
                        "shipping": "Free Delivery over AED 100",
                        "condition": "New", "currency": "AED",
                    })
    except Exception:
        pass

    return results
