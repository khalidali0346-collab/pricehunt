"""Virgin Megastore UAE — electronics, gaming, entertainment."""
import httpx, json, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

BASE = "https://www.virginmegastore.ae"


def _search_next_data(data: dict) -> list:
    """Try multiple known paths inside __NEXT_DATA__ for product hits."""
    pp = data.get("props", {}).get("pageProps", {})
    candidates = [
        pp.get("searchResults", {}).get("hits", []),
        pp.get("products", {}).get("hits", []),
        pp.get("catalog", {}).get("hits", []),
        pp.get("items", []),
        pp.get("hits", []),
        pp.get("data", {}).get("hits", []),
        pp.get("data", {}).get("products", []),
        pp.get("initialData", {}).get("hits", []),
    ]
    for c in candidates:
        if isinstance(c, list) and c:
            return c
    return []


def _hit_to_result(p: dict) -> dict | None:
    title = p.get("name", "") or p.get("title", "")
    if not title or len(title) < 6:
        return None

    # Price: try AED-keyed dict first, then scalar
    price_raw = (
        (p.get("price") or {}).get("AED")
        if isinstance(p.get("price"), dict) else p.get("price")
    ) or p.get("salePrice") or p.get("sale_price") or p.get("currentPrice")

    if price_raw is None:
        return None

    try:
        price = float(str(price_raw).replace(",", ""))
    except ValueError:
        return None

    if price < 0.5 or price > 500_000:
        return None

    sku = p.get("sku", "") or p.get("objectID", "") or p.get("id", "")
    img = p.get("image", "") or p.get("thumbnail", "") or p.get("imageUrl", "")
    url = p.get("url", "") or (f"{BASE}/en/product/{sku}" if sku else BASE)
    if url and not url.startswith("http"):
        url = BASE + url

    return {
        "title": title,
        "price": price,
        "price_text": f"AED {price:,.2f}",
        "source": "Virgin Megastore",
        "source_type": "web",
        "url": url,
        "image": img,
        "location": "UAE (online + in-store)",
        "shipping": "Home Delivery / In-store",
        "condition": "New",
        "currency": "AED",
    }


# Strict selectors — the generic div[class*='product'] caused false positives
_PRODUCT_SELECTORS = [
    "li.product-item",
    "div.product-item",
    "article.product-card",
    "div[class='product-card']",   # exact match, not contains
    "div[data-testid='product-card']",
    "div[data-product-id]",
    "div[data-sku]",
]


async def scrape(query: str) -> list[dict]:
    url = f"{BASE}/en/search?q={quote_plus(query)}&sort=price-asc"
    headers = get_headers(BASE)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results: list[dict] = []

    # ── 1. __NEXT_DATA__ JSON (most reliable) ──
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            hits = _search_next_data(json.loads(script.string))
            for hit in hits[:20]:
                item = _hit_to_result(hit)
                if item:
                    results.append(item)
            if results:
                return results
        except Exception:
            pass

    # ── 2. Inline window.__STORE__ / window.__STATE__ variables ──
    for script_tag in soup.find_all("script", src=False):
        raw = script_tag.string or ""
        match = re.search(r'window\.__(?:STORE|STATE|DATA)__\s*=\s*(\{.+?\});', raw, re.S)
        if match:
            try:
                hits = _search_next_data(json.loads(match.group(1)))
                for hit in hits[:20]:
                    item = _hit_to_result(hit)
                    if item:
                        results.append(item)
                if results:
                    return results
            except Exception:
                pass

    # ── 3. Conservative HTML fallback — strict selectors only ──
    for selector in _PRODUCT_SELECTORS:
        items = soup.select(selector)
        if not items:
            continue
        for item in items[:20]:
            title_el = (
                item.select_one("a.product-item-link")
                or item.select_one("[class='product-name']")
                or item.select_one("h2")
                or item.select_one("h3")
            )
            price_el = item.select_one("span.price") or item.select_one("[class='price']")
            link_el = item.select_one("a")
            img_el = item.select_one("img")

            if not title_el or not price_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 6:
                continue

            price = parse_price(price_el.get_text(strip=True))
            if not price or price < 0.5:
                continue

            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = BASE + href

            results.append({
                "title": title,
                "price": price,
                "price_text": f"AED {price:,.2f}",
                "source": "Virgin Megastore",
                "source_type": "web",
                "url": href,
                "image": img_el.get("src", "") if img_el else None,
                "location": "UAE (online + in-store)",
                "shipping": "Home Delivery / In-store",
                "condition": "New",
                "currency": "AED",
            })
        if results:
            break

    return results
