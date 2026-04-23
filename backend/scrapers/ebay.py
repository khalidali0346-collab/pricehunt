"""eBay scraper — searches buy-it-now listings sorted by lowest price."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = (
        f"https://www.ebay.com/sch/i.html"
        f"?_nkw={quote_plus(query)}&_sop=15&LH_BIN=1&_ipg=48"
    )
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=get_headers("https://www.ebay.com"))
            if r.status_code != 200:
                return []
            html = r.text
    except Exception:
        return []

    # eBay sometimes returns a consent/interstitial page — detect it
    if "s-item" not in html and "srp-results" not in html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    for item in soup.select("li.s-item")[:24]:
        # Title lives inside s-item__title — could be a span, h3, or div
        title_el = (
            item.select_one(".s-item__title span[role='heading']")
            or item.select_one(".s-item__title span")
            or item.select_one("h3.s-item__title")
            or item.select_one(".s-item__title")
        )
        price_el = item.select_one("span.s-item__price")
        link_el = item.select_one("a.s-item__link")
        img_el = item.select_one("img.s-item__image-img")
        location_el = item.select_one("span.s-item__location")
        shipping_el = item.select_one("span.s-item__shipping")
        condition_el = item.select_one("span.SECONDARY_INFO")

        if not title_el or not price_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        if not title or title in ("Shop on eBay", "New Listing"):
            continue

        price_text = price_el.get_text(strip=True)
        # Skip price ranges — pick the lower bound
        if " to " in price_text:
            price_text = price_text.split(" to ")[0]

        price = parse_price(price_text)
        if price is None:
            continue

        # Convert USD → AED (fixed peg: 1 USD = 3.67 AED)
        aed = round(price * 3.67, 2)
        results.append(
            {
                "title": title,
                "price": aed,
                "price_text": f"AED {aed:,.2f}",
                "source": "eBay",
                "source_type": "web",
                "url": link_el.get("href", ""),
                "image": img_el.get("src", "") if img_el else None,
                "location": location_el.get_text(strip=True).replace("from ", "") if location_el else "Global",
                "shipping": shipping_el.get_text(strip=True) if shipping_el else "Ships to UAE",
                "condition": condition_el.get_text(strip=True) if condition_el else "New",
                "currency": "AED",
            }
        )

    return results
