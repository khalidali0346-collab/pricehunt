"""Dubizzle UAE — Playwright-powered classifieds scraper."""
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .browser import fetch_rendered
from .utils import parse_price

CITY_MAP = {
    "dubai": "dubai", "abu dhabi": "abu-dhabi", "abudhabi": "abu-dhabi",
    "sharjah": "sharjah", "ajman": "ajman",
}
DEFAULT_CITY = "dubai"


def resolve_city(location):
    if not location:
        return DEFAULT_CITY
    return CITY_MAP.get(location.lower().strip(), DEFAULT_CITY)


async def scrape(query: str, location: str = None) -> list[dict]:
    city = resolve_city(location)
    url = f"https://uae.dubizzle.com/search/?q={quote_plus(query)}&location={city}"
    html = await fetch_rendered(
        url,
        wait_selector="article[data-testid='listing-card'], div[class*='listing']",
    )
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    items = (
        soup.select("article[data-testid='listing-card']")
        or soup.select("div[class*='listing-card']")
        or soup.select("div[class*='listing']")
    )

    for item in items[:24]:
        title_el = item.select_one("h2") or item.select_one("h3") or item.select_one("[class*='title']")
        price_el = item.select_one("[class*='price']") or item.select_one("span[class*='Price']")
        link_el = item.select_one("a")
        img_el = item.select_one("img")
        loc_el = item.select_one("[class*='location']")

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
        loc_text = loc_el.get_text(strip=True) if loc_el else city.title()
        results.append({
            "title": title, "price": price,
            "price_text": f"AED {price:,.0f}" if price else price_text or "Price on request",
            "source": "Dubizzle", "source_type": "local", "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": loc_text, "shipping": "Local pickup / Delivery",
            "condition": "Used/New", "currency": "AED",
        })
    return results
