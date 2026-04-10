"""Noon.com scraper — biggest MENA e-commerce platform."""
import httpx
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


def _extract_hits_from_next_data(data: dict) -> list:
    """Try multiple known data paths in Noon's Next.js JSON."""
    page_props = data.get("props", {}).get("pageProps", {})

    # Path variants observed across Noon's Next.js versions
    candidates = [
        # v1 – catalog.hits
        page_props.get("catalog", {}).get("hits", []),
        # v2 – searchResults.hits
        page_props.get("searchResults", {}).get("hits", []),
        # v3 – initialState.catalog.hits
        page_props.get("initialState", {}).get("catalog", {}).get("hits", []),
        # v4 – items directly
        page_props.get("items", []),
        # v5 – products list
        page_props.get("products", []),
        # v6 – data.products
        page_props.get("data", {}).get("products", []),
        # v7 – nested catalog under initialData
        page_props.get("initialData", {}).get("catalog", {}).get("hits", []),
    ]
    for c in candidates:
        if c:
            return c
    return []


def _hit_to_result(hit: dict) -> dict | None:
    title = hit.get("name", "") or hit.get("title", "")
    brand = hit.get("brand", "") or hit.get("brand_name", "")
    if brand and not title.lower().startswith(brand.lower()):
        title = f"{brand} {title}".strip()

    price = (
        hit.get("sale_price")
        or hit.get("price")
        or hit.get("current_price")
        or hit.get("offer_price")
    )
    if not title or price is None:
        return None

    sku = hit.get("sku", "") or hit.get("id", "") or hit.get("objectID", "")

    img_keys = hit.get("image_keys") or hit.get("images") or []
    img_key = img_keys[0] if img_keys else hit.get("thumbnail", "") or hit.get("image", "")
    img_url = (
        f"https://f.nooncdn.com/p/{img_key}?format=avif"
        if img_key and not img_key.startswith("http")
        else img_key or None
    )

    return {
        "title": title,
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
    }


async def scrape(query: str) -> list[dict]:
    headers = get_headers("https://www.noon.com")
    headers["Accept-Language"] = "en-AE,en;q=0.9"

    results: list[dict] = []

    # ── 1. Try Noon's internal REST API ──────────────────────────────
    api_endpoints = [
        f"https://www.noon.com/uae-en/api/catalog/search?q={quote_plus(query)}&lang=en&countryCode=ae&sortBy=price_asc",
        f"https://www.noon.com/_svc/catalog/api/search/search?q={quote_plus(query)}&lang=en&country=ae&sort[]=price_asc&page=1&limit=40",
    ]
    for api_url in api_endpoints:
        try:
            api_headers = {**headers, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                r = await client.get(api_url, headers=api_headers)
                if r.status_code == 200:
                    data = r.json()
                    hits = (
                        data.get("hits")
                        or data.get("products")
                        or data.get("items")
                        or data.get("data", {}).get("hits")
                        or data.get("data", {}).get("products")
                        or []
                    )
                    for hit in hits[:20]:
                        r2 = _hit_to_result(hit)
                        if r2:
                            results.append(r2)
                    if results:
                        return results
        except Exception:
            pass

    # ── 2. Scrape the search page and read __NEXT_DATA__ ─────────────
    url = f"https://www.noon.com/uae-en/search/?q={quote_plus(query)}&sortBy=price_asc"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            hits = _extract_hits_from_next_data(data)
            for hit in hits[:20]:
                item = _hit_to_result(hit)
                if item:
                    results.append(item)
            if results:
                return results
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # ── 3. HTML fallback ─────────────────────────────────────────────
    for item in soup.select(
        "div[class*='productContainer'], "
        "div[class*='product-card'], "
        "div[data-qa='product-block']"
    )[:20]:
        title_el = item.select_one("[class*='name']") or item.select_one("h3") or item.select_one("h2")
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
