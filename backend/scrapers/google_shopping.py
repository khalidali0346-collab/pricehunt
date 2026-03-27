"""Google Shopping scraper."""
import httpx
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=shop&hl=en&gl=us"
    headers = get_headers("https://www.google.com")
    headers["Cookie"] = "CONSENT=YES+; SOCS=CAESEwgDEgk4OTM5ODg4MjcaAmVuIAEaBgiA7JqmBg=="

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Google Shopping result containers — class names change but structure is consistent
    # Try multiple known selectors
    items = (
        soup.select("div.sh-dgr__content")
        or soup.select("div.sh-pr__product-results-grid > div")
        or soup.select("li.eIuuYe")
    )

    for item in items[:20]:
        # Title
        title_el = (
            item.select_one("h4")
            or item.select_one("div.tAxDx")
            or item.select_one("[aria-label]")
        )
        # Price
        price_el = (
            item.select_one("span.a8Pemb")
            or item.select_one("span.HRLxBb")
            or item.select_one("div.e10twf")
        )
        # Store
        store_el = item.select_one("div.aULzUe") or item.select_one("div.E5ocAb")
        # Link
        link_el = item.select_one("a")
        # Image
        img_el = item.select_one("img")

        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True)
        price = parse_price(price_text)
        if price is None:
            continue

        href = link_el.get("href", "") if link_el else ""
        if href.startswith("/"):
            href = "https://www.google.com" + href

        results.append(
            {
                "title": title,
                "price": price,
                "price_text": f"${price:,.2f}",
                "source": store_el.get_text(strip=True) if store_el else "Google Shopping",
                "source_type": "web",
                "url": href,
                "image": img_el.get("src", "") if img_el else None,
                "location": None,
                "shipping": None,
                "condition": "New",
            }
        )

    return results
