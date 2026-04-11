"""Carrefour UAE scraper — tries REST API first, then Next.js, then HTML."""
import httpx
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

BASE = "https://www.carrefouruae.com"


async def scrape(query: str) -> list[dict]:
    headers = get_headers(BASE)
    headers["Accept-Language"] = "en-AE,en;q=0.9"
    results = []

    # ── 1. SAP Commerce Cloud OCC REST API ───────────────────────────
    api_urls = [
        f"{BASE}/occ/v2/mafuae/products/search?fields=FULL&query={quote_plus(query)}&pageSize=20&lang=en&curr=AED",
        f"{BASE}/rest/v2/mafuae/products/search?fields=DEFAULT&query={quote_plus(query)}&pageSize=20&lang=en&curr=AED",
        f"{BASE}/api/v1/product/search?q={quote_plus(query)}&sortBy=price_asc&pageSize=20&lang=en",
    ]
    for api_url in api_urls:
        try:
            api_headers = {**headers, "Accept": "application/json"}
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                r = await client.get(api_url, headers=api_headers)
                if r.status_code == 200:
                    data = r.json()
                    products = (
                        data.get("products")
                        or data.get("data", {}).get("products")
                        or []
                    )
                    for p in products[:20]:
                        title = p.get("name", "") or p.get("summary", "")
                        price_info = p.get("price", {})
                        price = (
                            price_info.get("value")
                            or price_info.get("sale")
                            or price_info.get("regular")
                        )
                        if not title or price is None:
                            continue
                        img = (p.get("images") or [{}])[0].get("url", "") or p.get("image", {}).get("url", "")
                        if img and not img.startswith("http"):
                            img = BASE + img
                        slug = p.get("url", "") or p.get("slug", "")
                        url = (BASE + slug) if slug and not slug.startswith("http") else slug or BASE
                        results.append({
                            "title": title,
                            "price": float(price),
                            "price_text": f"AED {float(price):,.2f}",
                            "source": "Carrefour UAE",
                            "source_type": "web",
                            "url": url,
                            "image": img,
                            "location": "UAE (online + in-store)",
                            "shipping": "Home Delivery / Click & Collect",
                            "condition": "New",
                            "currency": "AED",
                        })
                    if results:
                        return results
        except Exception:
            pass

    # ── 2. Search page – Next.js __NEXT_DATA__ ────────────────────────
    page_urls = [
        f"{BASE}/mafuae/en/search?keyword={quote_plus(query)}&sortBy=price-asc",
        f"{BASE}/en-ae/search?q={quote_plus(query)}&sortBy=price_asc",
    ]
    for page_url in page_urls:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
                r = await client.get(page_url, headers=headers)
                if r.status_code != 200:
                    continue
            soup = BeautifulSoup(r.text, "lxml")
            script = soup.select_one("script#__NEXT_DATA__")
            if script:
                data = json.loads(script.string)
                pp = data.get("props", {}).get("pageProps", {})
                products = (
                    pp.get("initialData", {}).get("data", {}).get("products")
                    or pp.get("products")
                    or pp.get("catalog", {}).get("products")
                    or pp.get("data", {}).get("products")
                    or []
                )
                for p in products[:20]:
                    title = p.get("name", "")
                    price_info = p.get("price", {})
                    price = price_info.get("sale") or price_info.get("regular") or price_info.get("value")
                    img = p.get("image", {}).get("url", "") if isinstance(p.get("image"), dict) else p.get("image", "")
                    slug = p.get("slug", "") or p.get("url", "")
                    if not title or not price:
                        continue
                    results.append({
                        "title": title,
                        "price": float(price),
                        "price_text": f"AED {float(price):,.2f}",
                        "source": "Carrefour UAE",
                        "source_type": "web",
                        "url": f"{BASE}/mafuae/en/{slug}" if slug else BASE,
                        "image": img,
                        "location": "UAE (online + in-store)",
                        "shipping": "Home Delivery / Click & Collect",
                        "condition": "New",
                        "currency": "AED",
                    })
                if results:
                    return results
        except Exception:
            pass

    # ── 3. HTML fallback ─────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(page_urls[0], headers=headers)
            soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("div[class*='product-card'], div[class*='productCard'], article[class*='product']")[:20]:
            title_el = item.select_one("h2, h3, [class*='title'], [class*='name']")
            price_el = item.select_one("[class*='price']")
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
                "source": "Carrefour UAE", "source_type": "web", "url": href,
                "image": img_el.get("src", "") if img_el else None,
                "location": "UAE (online + in-store)", "shipping": "Home Delivery / Click & Collect",
                "condition": "New", "currency": "AED",
            })
    except Exception:
        pass

    return results
