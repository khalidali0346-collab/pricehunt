"""AliExpress scraper — global marketplace, ships to UAE with AE-specific pricing."""
import httpx
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

# 1 USD ≈ 3.67 AED (fixed peg)
USD_TO_AED = 3.67


async def scrape(query: str) -> list[dict]:
    """Scrape AliExpress search results for UAE shoppers."""
    url = (
        f"https://www.aliexpress.com/wholesale"
        f"?SearchText={quote_plus(query)}"
        f"&SortType=price_asc"
        f"&shipCountry=ae"
        f"&CatId=0"
    )
    headers = get_headers("https://www.aliexpress.com")
    headers["Accept-Language"] = "en-US,en;q=0.9"
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

    results = []

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                return []
            html = r.text
    except Exception:
        return []

    # ── Try JSON embedded in window._dida_config_ or __NEXT_DATA__ ──
    json_match = re.search(
        r'window\.__SEARCH_RESULT_DATA__\s*=\s*(\{.+?\});?\s*</script',
        html, re.S
    )
    if not json_match:
        json_match = re.search(
            r'"mods"\s*:\s*\{.*?"itemList"\s*:\s*\{.*?"content"\s*:\s*(\[.+?\])',
            html, re.S
        )

    if json_match:
        try:
            raw = json_match.group(1)
            items = json.loads(raw)
            if isinstance(items, list):
                for item in items[:20]:
                    title = (
                        item.get("title", {}).get("displayTitle", "")
                        or item.get("title", "")
                        or item.get("name", "")
                    )
                    price_info = item.get("prices", {}) or item.get("price", {})
                    usd_str = (
                        price_info.get("salePrice", {}).get("minPrice")
                        or price_info.get("minPrice")
                        or price_info.get("price")
                    )
                    if not title or usd_str is None:
                        continue
                    try:
                        usd = float(str(usd_str).replace(",", ""))
                    except ValueError:
                        continue
                    aed = round(usd * USD_TO_AED, 2)
                    product_id = item.get("productId") or item.get("itemId", "")
                    img = (
                        item.get("image", {}).get("imgUrl", "")
                        or item.get("thumbnail", "")
                        or item.get("imgUrl", "")
                    )
                    if img and img.startswith("//"):
                        img = "https:" + img
                    results.append({
                        "title": title,
                        "price": aed,
                        "price_text": f"AED {aed:,.2f}",
                        "source": "AliExpress",
                        "source_type": "web",
                        "url": f"https://www.aliexpress.com/item/{product_id}.html" if product_id else url,
                        "image": img,
                        "location": "Ships to UAE",
                        "shipping": "Free / Low-cost Shipping",
                        "condition": "New",
                        "currency": "AED",
                    })
                if results:
                    return results
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # ── HTML fallback ──
    soup = BeautifulSoup(html, "lxml")
    for item in soup.select(
        "div[class*='manhattan--container'], "
        "div[class*='product-snippet'], "
        "div[class*='search-item'], "
        "div.item"
    )[:20]:
        title_el = (
            item.select_one("h3")
            or item.select_one("[class*='title']")
            or item.select_one("[class*='name']")
        )
        price_el = (
            item.select_one("[class*='price--current']")
            or item.select_one("[class*='sale-price']")
            or item.select_one("[class*='price']")
        )
        link_el = item.select_one("a")
        img_el = item.select_one("img")

        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        raw_price_text = price_el.get_text(strip=True)
        usd = parse_price(raw_price_text)
        if not usd:
            continue
        aed = round(usd * USD_TO_AED, 2)

        href = link_el.get("href", "") if link_el else ""
        if href.startswith("//"):
            href = "https:" + href
        elif href and not href.startswith("http"):
            href = "https://www.aliexpress.com" + href

        img_src = ""
        if img_el:
            img_src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")
            if img_src.startswith("//"):
                img_src = "https:" + img_src

        results.append({
            "title": title,
            "price": aed,
            "price_text": f"AED {aed:,.2f}",
            "source": "AliExpress",
            "source_type": "web",
            "url": href,
            "image": img_src,
            "location": "Ships to UAE",
            "shipping": "Free / Low-cost Shipping",
            "condition": "New",
            "currency": "AED",
        })

    return results
