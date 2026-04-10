"""Google Shopping scraper — aggregated results for UAE market."""
import httpx
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    # Use UAE locale (gl=ae) for regional pricing
    url = (
        f"https://www.google.com/search"
        f"?q={quote_plus(query)}"
        f"&tbm=shop"
        f"&hl=en"
        f"&gl=ae"
        f"&cr=countryAE"
        f"&num=20"
    )
    headers = get_headers("https://www.google.com")
    headers["Accept-Language"] = "en-AE,en;q=0.9"
    # Consent cookie to skip GDPR prompts
    headers["Cookie"] = "CONSENT=YES+cb; SOCS=CAESEwgDEgk4OTM5ODg4MjcaAmVuIAEaBgiA7JqmBg=="

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            html = r.text
    except Exception:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    # ── 1. Try JSON-LD structured data ───────────────────────────────
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                # ItemList containing Product entries
                if item.get("@type") == "ItemList":
                    for el in item.get("itemListElement", []):
                        product = el.get("item", el)
                        _append_from_ld(product, results)
                elif item.get("@type") in ("Product", "Offer"):
                    _append_from_ld(item, results)
        except (json.JSONDecodeError, AttributeError):
            pass

    if results:
        return results[:20]

    # ── 2. HTML selectors (Google changes these often) ───────────────
    # Try multiple known container patterns
    containers = (
        soup.select("div.sh-dgr__content")
        or soup.select("div[data-docid]")
        or soup.select("div.KZmu8e")
        or soup.select("li.eIuuYe")
        or soup.select("div.Ged2g")
        or soup.select("div[class*='sh-dlr__list-result']")
    )

    for item in containers[:20]:
        # Title — look for the most prominent text element
        title_el = (
            item.select_one("h4")
            or item.select_one("div.tAxDx")
            or item.select_one("div[class*='title']")
            or item.select_one("h3")
            or item.select_one("[aria-label]")
        )
        # Price — several known class patterns
        price_el = (
            item.select_one("span.a8Pemb")
            or item.select_one("span.HRLxBb")
            or item.select_one("div.e10twf")
            or item.select_one("[class*='price']")
            or item.select_one("span[aria-label*='AED']")
            or item.select_one("span[aria-label*='price']")
        )
        store_el = (
            item.select_one("div.aULzUe")
            or item.select_one("div.E5ocAb")
            or item.select_one("[class*='merchant']")
            or item.select_one("[class*='store']")
        )
        link_el = item.select_one("a")
        img_el = item.select_one("img")

        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True)
        # Google Shopping shows AED prices for gl=ae
        price = parse_price(price_text)
        if price is None:
            continue

        href = link_el.get("href", "") if link_el else ""
        if href.startswith("/"):
            href = "https://www.google.com" + href

        store = store_el.get_text(strip=True) if store_el else "Google Shopping"

        # Determine currency from price text
        currency = "AED" if "AED" in price_text.upper() else "USD"
        price_display = f"AED {price:,.2f}" if currency == "AED" else f"${price:,.2f}"

        results.append({
            "title": title,
            "price": price,
            "price_text": price_display,
            "source": store,
            "source_type": "web",
            "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE",
            "shipping": None,
            "condition": "New",
            "currency": currency,
        })

    return results


def _append_from_ld(product: dict, results: list) -> None:
    """Extract a result from a JSON-LD Product node."""
    ptype = product.get("@type", "")
    if ptype not in ("Product", "Offer", ""):
        return
    name = product.get("name", "")
    offers = product.get("offers", product if ptype == "Offer" else {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price") or offers.get("lowPrice")
    currency = offers.get("priceCurrency", "AED")
    url = offers.get("url") or product.get("url", "")
    img = product.get("image", "")
    if isinstance(img, list):
        img = img[0] if img else ""
    seller = offers.get("seller", {}).get("name", "Google Shopping") if isinstance(offers.get("seller"), dict) else "Google Shopping"

    if not name or price is None:
        return
    try:
        price_f = float(str(price).replace(",", ""))
    except ValueError:
        return

    results.append({
        "title": name,
        "price": price_f,
        "price_text": f"{currency} {price_f:,.2f}",
        "source": seller,
        "source_type": "web",
        "url": url,
        "image": img,
        "location": "UAE",
        "shipping": None,
        "condition": "New",
        "currency": currency,
    })
