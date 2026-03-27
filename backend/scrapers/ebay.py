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
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    for item in soup.select("li.s-item")[:24]:
        title_el = item.select_one("div.s-item__title span")
        price_el = item.select_one("span.s-item__price")
        link_el = item.select_one("a.s-item__link")
        img_el = item.select_one("img.s-item__image-img")
        location_el = item.select_one("span.s-item__location")
        shipping_el = item.select_one("span.s-item__shipping")
        condition_el = item.select_one("span.SECONDARY_INFO")

        if not title_el or not price_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        if title in ("Shop on eBay", ""):
            continue

        price_text = price_el.get_text(strip=True)
        # Skip price ranges — pick the lower bound
        if " to " in price_text:
            price_text = price_text.split(" to ")[0]

        price = parse_price(price_text)
        if price is None:
            continue

        results.append(
            {
                "title": title,
                "price": price,
                "price_text": f"${price:,.2f}",
                "source": "eBay",
                "source_type": "web",
                "url": link_el.get("href", ""),
                "image": img_el.get("src", "") if img_el else None,
                "location": location_el.get_text(strip=True).replace("from ", "") if location_el else None,
                "shipping": shipping_el.get_text(strip=True) if shipping_el else None,
                "condition": condition_el.get_text(strip=True) if condition_el else None,
            }
        )

    return results
