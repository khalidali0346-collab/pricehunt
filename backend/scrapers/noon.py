"""Noon.com scraper — Playwright (with httpx fallback) + Algolia API attempt."""
import json, re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .browser import fetch_rendered
from .utils import get_headers, parse_price

BASE = "https://www.noon.com"


async def _try_algolia(query: str, app_id: str, api_key: str) -> list[dict]:
    """Call Noon's Algolia search directly."""
    url = f"https://{app_id}-dsn.algolia.net/1/indexes/*/queries"
    payload = {
        "requests": [{
            "indexName": "products_ae_en",
            "params": f"query={quote_plus(query)}&hitsPerPage=20&filters=&facets=*"
        }]
    }
    headers = {
        "X-Algolia-Application-Id": app_id,
        "X-Algolia-API-Key": api_key,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, json=payload, headers=headers)
            if r.status_code == 200:
                data = r.json()
                hits = data.get("results", [{}])[0].get("hits", [])
                results = []
                for h in hits[:20]:
                    title = h.get("name", "") or h.get("title", "")
                    brand = h.get("brand", "")
                    if brand and not title.lower().startswith(brand.lower()):
                        title = f"{brand} {title}".strip()
                    price = h.get("sale_price") or h.get("price") or h.get("current_price")
                    if not title or price is None:
                        continue
                    sku = h.get("sku", "") or h.get("objectID", "")
                    img_keys = h.get("image_keys") or []
                    img_key = img_keys[0] if img_keys else h.get("thumbnail", "")
                    img_url = f"https://f.nooncdn.com/p/{img_key}?format=avif" if img_key and not img_key.startswith("http") else img_key or None
                    results.append({
                        "title": title, "price": float(price),
                        "price_text": f"AED {float(price):,.2f}",
                        "source": "Noon", "source_type": "web",
                        "url": f"{BASE}/uae-en/{sku}/",
                        "image": img_url, "location": "UAE",
                        "shipping": "Noon Express", "condition": "New", "currency": "AED",
                    })
                return results
    except Exception:
        pass
    return []


async def _extract_algolia_creds(html: str):
    """Pull Algolia app ID + search key from Noon's page source."""
    app_id = re.search(r'"applicationId"\s*:\s*"([A-Z0-9]{8,})"', html)
    api_key = re.search(r'"searchApiKey"\s*:\s*"([a-f0-9]{20,})"', html)
    if not app_id:
        app_id = re.search(r'ALGOLIA_APP_ID["\s:=]+([A-Z0-9]{8,})', html)
    if not api_key:
        api_key = re.search(r'ALGOLIA_(?:SEARCH_)?API_KEY["\s:=]+([a-f0-9]{20,})', html)
    if app_id and api_key:
        return app_id.group(1), api_key.group(1)
    return None, None


async def scrape(query: str) -> list[dict]:
    url = f"{BASE}/uae-en/search/?q={quote_plus(query)}&sortBy=price_asc"

    # ── 1. Try fetching page (Playwright or httpx) ──
    html = await fetch_rendered(
        url,
        wait_selector="[data-qa='product-block'], div[class*='productContainer']",
    )

    results = []

    if html:
        # ── 2. Try extracting Algolia creds and querying directly ──
        app_id, api_key = await _extract_algolia_creds(html)
        if app_id and api_key:
            results = await _try_algolia(query, app_id, api_key)
            if results:
                return results

        soup = BeautifulSoup(html, "lxml")

        # ── 3. __NEXT_DATA__ ──
        script = soup.select_one("script#__NEXT_DATA__")
        if script:
            try:
                data = json.loads(script.string)
                pp = data.get("props", {}).get("pageProps", {})
                hits = (
                    pp.get("catalog", {}).get("hits")
                    or pp.get("searchResults", {}).get("hits")
                    or pp.get("initialState", {}).get("catalog", {}).get("hits")
                    or pp.get("items") or pp.get("hits") or []
                )
                for h in hits[:20]:
                    title = h.get("name", "") or h.get("title", "")
                    brand = h.get("brand", "")
                    if brand and not title.lower().startswith(brand.lower()):
                        title = f"{brand} {title}".strip()
                    price = h.get("sale_price") or h.get("price") or h.get("current_price")
                    if not title or price is None:
                        continue
                    sku = h.get("sku", "") or h.get("id", "")
                    img_keys = h.get("image_keys") or []
                    img_key = img_keys[0] if img_keys else h.get("thumbnail", "")
                    img_url = f"https://f.nooncdn.com/p/{img_key}?format=avif" if img_key and not img_key.startswith("http") else img_key or None
                    results.append({
                        "title": title, "price": float(price),
                        "price_text": f"AED {float(price):,.2f}",
                        "source": "Noon", "source_type": "web",
                        "url": f"{BASE}/uae-en/{sku}/",
                        "image": img_url, "location": "UAE",
                        "shipping": "Noon Express", "condition": "New", "currency": "AED",
                    })
                if results:
                    return results
            except Exception:
                pass

        # ── 4. HTML fallback ──
        for item in soup.select("[data-qa='product-block'], div[class*='productContainer'], div[class*='product-card']")[:20]:
            title_el = item.select_one("[class*='name']") or item.select_one("h3") or item.select_one("h2")
            price_el = item.select_one("[class*='price']") or item.select_one("strong")
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
                "source": "Noon", "source_type": "web", "url": href,
                "image": img_el.get("src", "") if img_el else None,
                "location": "UAE", "shipping": "Noon Express", "condition": "New", "currency": "AED",
            })

    return results
