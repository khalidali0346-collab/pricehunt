"""Craigslist scraper — great for real local prices."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

# Map of common city names to Craigslist subdomains
CITY_MAP = {
    "new york": "newyork",
    "nyc": "newyork",
    "los angeles": "losangeles",
    "la": "losangeles",
    "chicago": "chicago",
    "houston": "houston",
    "phoenix": "phoenix",
    "philadelphia": "philadelphia",
    "san antonio": "sanantonio",
    "san diego": "sandiego",
    "dallas": "dallas",
    "san jose": "sfbay",
    "austin": "austin",
    "jacksonville": "jacksonville",
    "san francisco": "sfbay",
    "sf": "sfbay",
    "columbus": "columbus",
    "charlotte": "charlotte",
    "indianapolis": "indianapolis",
    "seattle": "seattle",
    "denver": "denver",
    "boston": "boston",
    "miami": "miami",
    "atlanta": "atlanta",
    "portland": "portland",
    "las vegas": "lasvegas",
    "minneapolis": "minneapolis",
    "detroit": "detroit",
    "orlando": "orlando",
}

DEFAULT_CITY = "newyork"


def resolve_city(location: str | None) -> str:
    if not location:
        return DEFAULT_CITY
    key = location.lower().strip()
    return CITY_MAP.get(key, key.replace(" ", ""))


async def scrape(query: str, location: str | None = None) -> list[dict]:
    city = resolve_city(location)
    url = (
        f"https://{city}.craigslist.org/search/sss"
        f"?query={quote_plus(query)}&sort=priceasc&hasPic=1"
    )
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=get_headers("https://craigslist.org"))
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # New Craigslist layout uses <li class="cl-search-result">
    items = soup.select("li.cl-search-result")
    # Fallback to old layout
    if not items:
        items = soup.select("li.result-row")

    for item in items[:24]:
        # New layout
        title_el = item.select_one("a.cl-app-anchor") or item.select_one("a.result-title")
        price_el = item.select_one("span.priceinfo") or item.select_one("span.result-price")
        img_el = item.select_one("img")
        location_el = item.select_one("span.location") or item.select_one("span.result-hood")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title:
            continue

        price_text = price_el.get_text(strip=True) if price_el else ""
        price = parse_price(price_text)

        href = title_el.get("href", "")
        if href and not href.startswith("http"):
            href = f"https://{city}.craigslist.org{href}"

        loc_text = location_el.get_text(strip=True).strip("()") if location_el else city.title()

        results.append(
            {
                "title": title,
                "price": price,
                "price_text": price_text or "Price not listed",
                "source": "Craigslist",
                "source_type": "local",
                "url": href,
                "image": img_el.get("src", "") if img_el else None,
                "location": loc_text or city.title(),
                "shipping": "Local pickup",
                "condition": "Used/Unknown",
            }
        )

    return results
