"""Dubizzle UAE scraper — classifieds for UAE (like Craigslist but for MENA)."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

CITY_MAP = {
    "dubai": "dubai",
    "abu dhabi": "abu-dhabi",
    "abudhabi": "abu-dhabi",
    "sharjah": "sharjah",
    "ajman": "ajman",
    "ras al khaimah": "ras-al-khaimah",
    "fujairah": "fujairah",
    "umm al quwain": "umm-al-quwain",
}

DEFAULT_CITY = "dubai"


def resolve_city(location: str | None) -> str:
    if not location:
        return DEFAULT_CITY
    key = location.lower().strip()
    return CITY_MAP.get(key, DEFAULT_CITY)


async def scrape(query: str, location: str | None = None) -> list[dict]:
    city = resolve_city(location)
    url = (
        f"https://uae.dubizzle.com/motors/used-cars/?keywords={quote_plus(query)}"
    )
    # General search URL
    url = f"https://uae.dubizzle.com/search/?q={quote_plus(query)}&location={city}"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=get_headers("https://uae.dubizzle.com"))
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Dubizzle listing cards
    items = (
        soup.select("article[data-testid='listing-card']")
        or soup.select("div[class*='listing']")
        or soup.select("li[class*='item']")
        or soup.select("div[class*='card']")
    )

    for item in items[:24]:
        title_el = (
            item.select_one("h2")
            or item.select_one("h3")
            or item.select_one("[class*='title']")
        )
        price_el = (
            item.select_one("[class*='price']")
            or item.select_one("span[class*='Price']")
        )
        link_el = item.select_one("a")
        img_el = item.select_one("img")
        location_el = item.select_one("[class*='location']") or item.select_one("[class*='Location']")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title:
            continue

        price_text = price_el.get_text(strip=True) if price_el else ""
        price = parse_price(price_text)

        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://uae.dubizzle.com" + href

        loc_text = location_el.get_text(strip=True) if location_el else city.title()

        results.append({
            "title": title,
            "price": price,
            "price_text": f"AED {price:,.0f}" if price else price_text or "Price on request",
            "source": "Dubizzle",
            "source_type": "local",
            "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": loc_text,
            "shipping": "Local pickup / Delivery",
            "condition": "Used/New",
            "currency": "AED",
        })

    return results
